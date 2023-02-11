import asyncio
import math
import platform
import sys
import json
import os

import pygame

pygame.init()

import src.utils as utils
from src.asset import Asset, AssetType, STOCK_TIME_OFFSET
from src.chart import Chart


###########
# Globals #
###########


window = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
clock = pygame.time.Clock()

balance = 1000000
assets = [
    # The file names are ambigious, as we don't want the participants to know
    # which stock/crypto they're trading with.
    Asset("AAPL", AssetType.STOCK, utils.DIR / "assets" / "A.npz"),
    Asset("AMZN", AssetType.STOCK, utils.DIR / "assets" / "B.npz"),
    Asset("META", AssetType.STOCK, utils.DIR / "assets" / "C.npz"),
    Asset("TSLA", AssetType.STOCK, utils.DIR / "assets" / "D.npz"),
    Asset("TWTR", AssetType.STOCK, utils.DIR / "assets" / "E.npz"),
    Asset("BTC", AssetType.CRYPTO, utils.DIR / "assets" / "F.npz"),
    Asset("DOGE", AssetType.CRYPTO, utils.DIR / "assets" / "G.npz"),
    Asset("ETH", AssetType.CRYPTO, utils.DIR / "assets" / "H.npz"),
    Asset("LTC", AssetType.CRYPTO, utils.DIR / "assets" / "I.npz"),
    Asset("XMR", AssetType.CRYPTO, utils.DIR / "assets" / "J.npz"),
]

sim_time = (
    3600 * 24 * 7 + STOCK_TIME_OFFSET
)  # Start by the second day's stock opening hour to give slight history
sim_speed = 1

cur_asset = 0
num_input = ""
zoom_back = 128

chart: Chart = None


##########################################
# Save & load (Not the most secure, lol) #
##########################################


def save():
    with open("save.json", "w") as f:
        json.dump(
            {
                "balance": balance,
                "time": sim_time,
                "assets": {
                    i: {
                        "invested_money": asset.invested_money,
                        "invested_amount": asset.invested_amount,
                        "returned_money": asset.returned_money,
                        "returned_amount": asset.returned_amount,
                    }
                    for i, asset in enumerate(assets)
                },
            },
            f,
        )


def load():
    global balance, sim_time

    with open("save.json", "r") as f:
        di = json.load(f)

        balance = di["balance"]
        sim_time = di["time"]

        for i, asset in di["assets"].items():
            for key, value in asset.items():
                setattr(assets[int(i)], key, value)


###################
# Actual main bit #
###################


def setup():
    global chart

    pygame.display.set_caption("Client Trading Simulator")

    chart = Chart(
        lambda x: assets[cur_asset].price(x),
        800,
        600,
        x_repr=lambda x: utils.to_time(x, zoom_back > 86400),
        y_repr=lambda y: f"${y:.2f}",
    )

    if os.path.isfile("save.json"):
        load()


def loop():
    global balance, sim_time, sim_speed, cur_asset, num_input, zoom_back

    dt = clock.tick() / 1000
    sim_time += dt * sim_speed

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save()
            sys.exit(0)
        elif event.type == pygame.KEYDOWN:
            # Scroll through asset
            if event.key == pygame.K_UP:
                cur_asset = (cur_asset + 1) % len(assets)

                # In case fractional input was provided earlier
                if num_input and assets[cur_asset].is_stock():
                    num_input = str(int(float(num_input)))
            elif event.key == pygame.K_DOWN:
                cur_asset = (cur_asset - 1) % len(assets)

                # In case fractional input was provided earlier
                if num_input and assets[cur_asset].is_stock():
                    num_input = str(int(float(num_input)))
            # Adjust simulation speed
            elif event.key == pygame.K_SPACE:
                sim_speed = 1
            elif event.key == pygame.K_LEFT:
                if sim_speed > 1:
                    sim_speed //= 2
            elif event.key == pygame.K_RIGHT:
                if sim_speed < 2**10:
                    sim_speed *= 2
            # `num_input`
            elif event.key == pygame.K_BACKSPACE:
                num_input = num_input[:-1]
            elif event.unicode and ord("0") <= ord(event.unicode) <= ord("9"):
                num_input += event.unicode
            elif (
                event.unicode in {".", ","}
                and "." not in num_input
                and assets[cur_asset].is_crypto()
            ):
                num_input += "."
            # Buy
            elif num_input and event.key == pygame.K_b:
                current_price = assets[cur_asset].price(sim_time)
                if math.isnan(current_price):
                    continue

                amount = float(num_input)
                total_price = current_price * amount

                if total_price <= balance:
                    balance -= total_price
                    assets[cur_asset].buy(amount, sim_time)
                    num_input = ""
            # Sell
            elif num_input and event.key == pygame.K_s:
                current_return = assets[cur_asset].price(sim_time)
                if math.isnan(current_return):
                    continue

                amount = float(num_input)
                total_return = current_return * amount

                if (
                    amount
                    <= assets[cur_asset].invested_amount
                    - assets[cur_asset].returned_amount
                ):
                    balance += total_return
                    assets[cur_asset].sell(amount, sim_time)
                    num_input = ""
        # Adjust zoom
        elif event.type == pygame.MOUSEWHEEL:
            zoom_back *= 2 ** int(-event.y)
            zoom_back = max(min(zoom_back, 2**20), 2**4)

    window.fill((5, 10, 48))

    # Balance
    window.blit(
        bal_text := utils.LARGE_FONT.render(
            f"Balance: ${balance:.4f}", True, (255, 255, 255)
        ),
        (
            window.get_width() * 0.95 - bal_text.get_width(),
            window.get_height() * 0.95 - bal_text.get_height(),
        ),
    )
    window.blit(
        dtime_text := utils.LARGE_FONT.render(
            utils.to_time(sim_time, True), True, (255, 255, 255)
        ),
        (
            window.get_width() * 0.95 - dtime_text.get_width(),
            window.get_height() * 0.95
            - dtime_text.get_height()
            - bal_text.get_height(),
        ),
    )

    # Chart
    chart.scale_x_min = sim_time - zoom_back
    chart.scale_x_max = sim_time
    chart.width = int(window.get_width() * 0.9)
    chart.height = int(window.get_height() * 0.5)
    chart.adjust_scale()
    chart.line_chart()
    window.blit(chart.surface, (window.get_width() * 0.05, window.get_height() * 0.05))

    # Price
    current_price = assets[cur_asset].price(sim_time)
    window.blit(
        text := utils.LARGE_FONT.render(
            ("SIMULATION ENDED" if assets[cur_asset].has_ended(sim_time) else "CLOSED")
            if math.isnan(current_price)
            else f"${current_price:.4f}",
            True,
            (255, 255, 255),
        ),
        (window.get_width() * 0.95 - text.get_width(), window.get_height() * 0.05),
    )

    # Cursor info
    mouse_x, mouse_y = pygame.mouse.get_pos()
    sel_time, sel_price = chart.at(mouse_x - window.get_width() * 0.05)
    if not math.isnan(sel_time) and mouse_y < chart.height + window.get_height() * 0.05:
        window.blit(
            text := utils.SMALL_FONT.render(
                f"{utils.to_time(sel_time, True)} | "
                + (
                    (
                        "SIMULATION ENDED"
                        if assets[cur_asset].has_ended(sel_time)
                        else "CLOSED"
                    )
                    if math.isnan(sel_price)
                    else f"${sel_price:.4f}"
                ),
                True,
                (255, 255, 255),
            ),
            (mouse_x - text.get_width(), mouse_y),
        )

    # Info
    window.blit(
        text := utils.SMALL_FONT.render(
            f"[{cur_asset + 1}] {assets[cur_asset].pseudonym} (U&D)"
            f" | {sim_speed}s/s (L&R) | Zoom -{zoom_back} (Scroll)",
            True,
            (255, 255, 255),
        ),
        (window.get_width() * 0.05, window.get_height() * 0.05 + chart.height),
    )

    # Extra asset info
    owned_amount = assets[cur_asset].invested_amount - assets[cur_asset].returned_amount
    total_delta = (
        assets[cur_asset].returned_money
        + owned_amount * current_price
        - assets[cur_asset].invested_money
    )

    lines = [
        f"Asset symbol     : {assets[cur_asset].pseudonym}",
        f"Asset type       : {assets[cur_asset].asset_type.name}",
        f"Trading time     : {'-' if assets[cur_asset].has_ended(sim_time) else '9:00 - 15:30' if assets[cur_asset].is_stock() else '0:00 - 23:55'}",
        f"",
        f"Owned amount     : {owned_amount:.4f}",
        f"Total investment : ${assets[cur_asset].invested_money:.4f}",
        f"Sold return      : ${assets[cur_asset].returned_money:.4f}",
        f"",
        f"Potential return : ${'UNAVAILABLE' if math.isnan(current_price) else f'{owned_amount * current_price:.4f}'}",
        f"Total delta      : -${-total_delta:.4f}"
        if total_delta < 0
        else f"Total delta      : +${'UNAVAILABLE' if math.isnan(total_delta) else f'{total_delta:.4f}'}",
    ]

    offset_y = window.get_height() * 0.05 + chart.height + text.get_height() * 2
    for line in lines:
        window.blit(
            text := utils.SMALL_FONT.render(line, True, (255, 255, 255)),
            (window.get_width() * 0.05, offset_y),
        )
        offset_y += text.get_height()

    # Input for buying
    if num_input:
        window.blit(
            text := utils.SMALL_FONT.render(
                f"(B)uying or (S)elling '{num_input}' amount of {assets[cur_asset].pseudonym} "
                + (
                    "(NOT AVAILABLE)"
                    if math.isnan(current_price)
                    else f"(${current_price * float(num_input):.4f})"
                ),
                True,
                (255, 255, 255),
            ),
            (window.get_width() * 0.05, window.get_height() * 0.95 - text.get_height()),
        )

    pygame.display.flip()


##########################
# Internal main function #
##########################


async def main():
    global window

    setup()

    while True:
        # For window resizing on the web
        if utils.WEB and (
            window.get_size()
            != (platform.window.innerWidth, platform.window.innerHeight)
        ):
            window = pygame.display.set_mode(
                (platform.window.innerWidth, platform.window.innerHeight),
                pygame.RESIZABLE,
            )

        loop()
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(main())
