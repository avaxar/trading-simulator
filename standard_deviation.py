import math

import pygame

pygame.init()

import src.utils as utils
from src.asset import *


assets = [
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

for asset in assets:
    print(asset.symbol)

    days_li = []

    for day in asset.days:
        if asset.is_crypto():
            day = day[
                STOCK_TIME_OFFSET // NPZ_INTERVAL : STOCK_TIME_OFFSET // NPZ_INTERVAL
                + 4656
            ]

        samples = list(filter(lambda x: not math.isnan(x), day))

        if not samples:
            continue

        mean = sum(samples) / len(samples)
        samples = list(map(lambda x: x / mean, samples))
        mean = 1

        days_li.append(
            math.sqrt(sum(map(lambda x: (x - mean) ** 2, samples)) / (len(samples) - 1))
        )

    print(days_li)
    print(f"Average: {sum(days_li) / len(days_li)}\n")
