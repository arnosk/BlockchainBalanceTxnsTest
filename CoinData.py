"""
Created on November 20, 2022

@author: arno

Data Classes for Coin data

"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CoinData:
    """Dataclass for coin data
    """
    siteid: str
    name: str = ''
    symbol: str = ''
    chain: str = ''
    base: Optional[str] = ''  # only use in CoinSearchAlcor

    def __post_init__(self):
        """Set coin name when not given

        Used when manual input
        """
        if self.name == '':
            self.name = self.siteid


@dataclass
class CoinPriceData:
    """Dataclass for coin price
    """
    date: datetime  # = field(default_factory=datetime.utcnow)
    coin: CoinData
    curr: str = ''
    exchange: str = ''  # is in fact marketdata
    price: float = 0
    volume: float = 0
    active: bool = True
    error: str = ''


@dataclass
class CoinMarketData:
    """Dataclass for coin market
    """
    coin: CoinData
    curr: str = ''
    exchange: str = ''
    pair: str = ''
    active: bool = True
    error: str = ''
    route: str = ''


@dataclass
class CoinSearchData:
    """Dataclass for showing search results of coin data

    General class
    """
    coin: CoinData
    base: str = ''
    market_cap_rank: int = 0
    volume: float = 0
    change: float = 0
    route: str = ''
    image_thumb: str = ''
    image_large: str = ''
