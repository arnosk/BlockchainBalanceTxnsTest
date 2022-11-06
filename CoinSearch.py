"""
Created on October 13, 2022

@author: arno

Base Class CoinSearch

"""
import os
import sys

import cfscrape
from abc import ABC, abstractmethod
import pandas as pd

from Db import Db
from RequestHelper import RequestHelper


class CoinSearch(ABC):
    """Base class for searching a coin on an exchange or provider
    """
    table_name: str

    def __init__(self) -> None:
        pass

    @abstractmethod
    def search(self, req: RequestHelper, db: Db, coin_search: str, assets: dict):
        """Searching coins on exchange

        Search coins in own database (if table exists)
        Show the results

        Search coins from exchange assets (already in assets)
        Show the results

        User can select a row number, from the table of search results
        To add that coin to the coins table, if it doesn't already exists

        req = instance of RequestHelper
        db = instance of Db
        coin_search = string to search in assets
        assets = dictionary where each key is a chain with a list of string with assets from Alcor
        """
        pass

    @abstractmethod
    def insert_coin(self, req: RequestHelper, db: Db, params: dict):
        """Insert coin in database

        Insert a new coin to the coins table
        And download the thumb and large picture of the coin


        req = instance of RequestHelper
        db = instance of Db
        params = dictionary with retrieved coin info from exchange
                {'id': 62,
                'symbol': 'doge',
                'name': 'Dogecoin',
                'fiat': False,
                'route': 'https://api.cryptowat.ch/assets/doge'
                }
        """
        pass

    def input_number(self, message: str, minimal: int = 1, maximum: int = 1):
        """UI for asking row number

        message = string for printing on screen to ask for user input
        minimal = minimal allowed integer
        maximum = maximum allowed integer
        """

        while True:
            user_input = input(message)
            user_input = user_input.lower()
            if (user_input == 'n' or user_input == 'new'):
                user_input = 'n'
            elif (user_input == 'q' or user_input == 'quit'):
                sys.exit('Exiting')
            else:
                try:
                    user_input = int(user_input)
                except ValueError:
                    print('No correct input! Try again.')
                    continue
                else:
                    if (user_input < minimal or user_input > maximum):
                        print('No correct row number! Try again.')
                        continue
            return user_input
            break

    def save_file(self, req: RequestHelper, url: str, folder: str, filename: str):
        """Download and safe a file from internet

        If folder doesn't exists, create the folder

        req = instance of RequestHelper
        url = url to download file
        folder = folder for saving downloaded file
        filename = filename for saving downloaded file
        """
        os.makedirs(folder, exist_ok=True)

        url = url.split('?')[0]
        ext = url.split('.')[-1]
        file = '%s\\%s.%s' % (folder, filename, ext)

        # Download file
        scraper = cfscrape.create_scraper()
        cfurl = scraper.get(url).content

        # Safe file
        with open(file, 'wb') as f:
            f.write(cfurl)

    @abstractmethod
    def search_id_db_query(self) -> str:
        """Query for searching coin in database

        The ? is used for the search item
        """
        pass

    def search_id_db(self, db: Db, coin_search: str) -> list:
        """Search for coin in database
        """
        db_result = []
        if db.check_table(self.table_name):
            coin_search_str = '%{}%'.format(coin_search)
            coin_search_query = self.search_id_db_query()

            # Create params tuple of n search items
            n = coin_search_query.count('?')
            params = (coin_search_str,)*n

            db_result = db.query(coin_search_query, params)
        return db_result

    def print_search_result(self, items: list, text: str, row_drop=[]):
        """Print search result to terminal
        """
        pd.set_option('display.max_colwidth', 20)

        if (len(items) > 0):
            itemsdf = pd.DataFrame(items)
            if row_drop != []:
                itemsdf = itemsdf.drop(row_drop, axis=1)
            print('Search from', text)
            print(itemsdf)
        else:
            print('Coin not found from', text)
