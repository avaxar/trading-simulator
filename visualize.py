from pathlib import Path

import pygame

pygame.init()

import src.utils as utils
from src.asset import Asset, AssetType, NPZ_INTERVAL, STOCK_TIME_OFFSET
from src.chart import Chart


assets = [
    # The hile names are ambigious, as we don't want the participants to know
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

respondents = {
    logf.stem: [v for _, v in eval(f"{{ {logf.read_text('utf-8')[:-1]} }}").items()]
    for logf in Path("./visualizations").glob("*.txt")
}
res_his = {}

chart = Chart(
    lambda x: 0,
    1980,
    720,
    x_repr=lambda x: utils.to_time(x, False),
    y_repr=lambda y: f"${y:.2f}",
    fg_color=(0, 0, 0, 255),
    nan_bg_color=(0, 0, 0, 0),
)


for asset in assets:
    chart.data_lambda = lambda x: asset.price(x)
    for day in range(len(asset.days)):
        chart.scale_x_min = day * 3600 * 24
        chart.scale_x_max = (day + 1) * 3600 * 24

        if asset.is_stock():
            chart.scale_x_min += STOCK_TIME_OFFSET
            chart.scale_x_max -= (
                3600 * 24 - STOCK_TIME_OFFSET - len(asset.days[day]) * NPZ_INTERVAL
            )

        chart.adjust_scale()
        chart.line_chart()

        for respondent, entries in respondents.items():
            for entry in entries:
                if entry["symbol"] != asset.symbol:
                    continue

                ax = entry["time"]
                if not chart.scale_x_min <= ax <= chart.scale_x_max:
                    continue
                x = utils.lerp(
                    ax,
                    chart.scale_x_min,
                    chart.scale_x_max,
                    chart.y_margin,
                    chart.width,
                )

                ay = asset.price(ax)
                y = utils.lerp(
                    ay,
                    chart.scale_y_min,
                    chart.scale_y_max,
                    chart.height - chart.x_margin,
                    0,
                )

                if respondent not in res_his:
                    res_his[respondent] = {
                        ass.symbol: {
                            "buy_acts": 0,
                            "sell_acts": 0,
                            "buy_amount": 0,
                            "sell_amount": 0,
                            "buy_balance": 0,
                            "sell_balance": 0,
                        }
                        for ass in assets
                    }
                di = res_his[respondent][asset.symbol]
                if entry["action"] == "buy":
                    di["buy_acts"] += 1
                    di["buy_amount"] += entry["amount"]
                    di["buy_balance"] += entry["balance"]
                else:
                    di["sell_acts"] += 1
                    di["sell_amount"] += entry["amount"]
                    di["sell_balance"] += entry["balance"]

                pygame.draw.circle(chart.surface, (0, 0, 0, 255), (x, y), 2)
                chart.surface.blit(
                    text := utils.SMALL_FONT.render(respondent, True, (0, 0, 0, 128)),
                    (x + 3, y - text.get_height()),
                )
                chart.surface.blit(
                    text := utils.SMALL_FONT.render(
                        f"{'BELI' if entry['action'] == 'buy' else 'JUAL'} {entry['amount']}",
                        True,
                        (0, 128, 0, 128)
                        if entry["action"] == "buy"
                        else (128, 0, 0, 128),
                    ),
                    (x + 3, y),
                )

        pygame.image.save(
            chart.surface, f"./visualizations/days/{asset.symbol}-{day}.png"
        )

print(res_his)
