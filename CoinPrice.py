"""
Created on October 15, 2022

@author: arno

Base Class CoinPrice

"""
import sys
from abc import ABC, abstractmethod

import Db
import RequestHelper


class CoinPrice(ABC):
    """Base class for looking up the price of a coin on an exchange or provider
    """

    def __init__(self) -> None:
        pass
