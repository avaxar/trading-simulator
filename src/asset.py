import enum
import math
from pathlib import Path

import numpy

from . import utils


NPZ_INTERVAL = 5  # 5 seconds
STOCK_TIME_OFFSET = 3600 * 9  # Opening time is set at 9AM


class AssetType(enum.Enum):
    STOCK = enum.auto()
    CRYPTO = enum.auto()


class Asset:
    def __init__(self, symbol: str, asset_type: AssetType, path: Path):
        self.symbol = symbol
        self.asset_type = asset_type
        self.path = path

        npz = numpy.load(path)
        self.days = [npz.get(f) for f in sorted(npz.files)]

        self.invested_money = 0
        self.invested_amount = 0
        self.returned_money = 0
        self.returned_amount = 0

    def is_stock(self) -> bool:
        return self.asset_type == AssetType.STOCK

    def is_crypto(self) -> bool:
        return self.asset_type == AssetType.CRYPTO

    @property
    def pseudonym(self):
        return utils.caesar(self.symbol)

    def price(self, t: float) -> float:
        if self.is_stock():
            t -= STOCK_TIME_OFFSET

        day = int(t // 86400)
        t = int(t % 86400) // NPZ_INTERVAL

        if 0 <= day < len(self.days):
            if 0 <= t < len(self.days[day]):
                return self.days[day][t]
            else:
                return math.nan
        else:
            return math.nan

    def has_ended(self, t: float) -> bool:
        if self.is_stock():
            t -= STOCK_TIME_OFFSET

        return t // 86400 >= len(self.days)

    def buy(self, amount: float, t: float):
        price = self.price(t)

        self.invested_money += amount * price
        self.invested_amount += amount

        utils.log(
            time=t,
            symbol=self.symbol,
            action="buy",
            amount=amount,
            balance=amount * price,
        )

    def sell(self, amount: float, t: float):
        price = self.price(t)

        self.returned_money += amount * price
        self.returned_amount += amount

        utils.log(
            time=t,
            symbol=self.symbol,
            action="sell",
            amount=amount,
            balance=amount * price,
        )
