"""
Created on October 13, 2022

@author: arno

Base Class CoinSearch

"""
import os
import shlex
import sys
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import List

import cfscrape
import pandas as pd

import DbHelper
from CoinData import CoinData, CoinSearchData
from Db import Db
from RequestHelper import RequestHelper


@dataclass
class Command:
    """Class that represents a command."""

    command: str
    arguments: List[str]

    def __post_init__(self):
        self.command = self.command.lower()
        self.arguments = [x.lower() for x in self.arguments]


class CoinSearch(ABC):
    """Base class for searching a coin on an exchange or provider
    """
    table_name: str

    def __init__(self) -> None:
        self.req = RequestHelper()

    @abstractmethod
    def insert_coin(self, db: Db, coin: CoinSearchData) -> int:
        """Insert coin in database

        Insert a new coin to the coins table
        And download the thumb and large picture of the coin

        db = instance of Db
        coin = search data with retrieved coin info from web
        """
        pass

    @abstractmethod
    def search(self, db: Db, coin_search: str, assets: dict):
        """Searching coins on exchange

        Search coins in own database (if table exists)
        Show the results

        Search coins from exchange assets (already in assets)
        Show the results

        User can select a row number, from the table of search results
        To add that coin to the coins table, if it doesn't already exists

        db = instance of Db
        coin_search = string to search in assets
        assets = dictionary where each key is a chain with a list of string with assets from Alcor
        """
        pass

    @abstractmethod
    def get_search_id_db_query(self) -> str:
        """Query for searching coin in database

        return value = query for database search with 
                       ? is used for the search item
        """
        pass

    def save_images(self, image_urls: dict, coin_name: str):
        """Save image files for one coin

        image_urls = dict if urls for images
        coin_name = string with name of coin
        """
        pass

    def save_file(self, url: str, folder: str, filename: str):
        """Download and safe a file from internet

        If folder doesn't exists, create the folder

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

    def search_id_db(self, db: Db, coin_search: str) -> list[CoinData]:
        """Search for coin in database

        db = database
        coin_search = coin name to be searched
        return value = list with search results
        """
        coindata = []
        if db.check_table(self.table_name):
            coin_search_str = '%{}%'.format(coin_search)
            coin_search_query = self.get_search_id_db_query()

            # Create params tuple of n search items
            n = coin_search_query.count('?')
            params = (coin_search_str,)*n

            db_result = db.query(coin_search_query, params)
            print(db_result)
            print(type(db_result))
            coindata = [CoinData(*x) for x in db_result]
        return coindata

    def print_search_result(self, items: list, text: str, col_drop=[]):
        """Print search result to terminal

        items = list of items to be printed on screen
        text = heading above the printed results
        col_drop = list with columns names not to be shown
        """
        # init pandas displaying
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_colwidth', 20)
        pd.set_option('display.float_format', '{:.6e}'.format)

        if (len(items) > 0):
            df = pd.json_normalize(data=[asdict(obj) for obj in items])
            #itemsdf = pd.DataFrame(items)
            df = df.drop(
                ['route', 'image_thumb', 'image_large'], axis=1, errors='ignore')
            if col_drop != []:
                df = df.drop(col_drop, axis=1, errors='ignore')
            print('Search from', text)
            print(df)
        else:
            print('Coin not found from', text)

    def insert_coin_check(self, db: Db, coin: CoinSearchData):
        """Check for existence of selected coin before inserting coin in database

        The selected row is inserted into the table, if it doesn't already exists

        db = instance of Db
        coin = search data with retrieved coin info from web
        """
        coin_id = coin.coin.siteid
        coin_name = coin.coin.name

        # check if coin name, symbol is already in our database
        if db.has_connection():
            # if table doesn't exist, create table coins
            if not db.check_table(self.table_name):
                DbHelper.create_table(db, self.table_name)

            db_result = db.query('SELECT * FROM {} WHERE siteid=?'.format(self.table_name),
                                 (coin_id,))
            if len(db_result):
                print('Database already has a row with the coin %s' %
                      (coin_name))
            else:
                # add new row to table coins
                insert_result = self.insert_coin(db, coin)
                if insert_result > 0:
                    print('%s added to the database' % (coin_name))

                    # safe coin images
                    images_urls = {'thumb': coin.image_thumb,
                                   'large': coin.image_large}
                    self.save_images(images_urls, coin_name)
                else:
                    print('Error adding %s to database' % (coin_name))
        else:
            print('No database connection')

    def input_coin_row(self, db: Db, coinsearch: list[CoinSearchData]):
        """UI for asking row number

        Handle user input after selecting coin

        New search, skips the function
        Quit exits the program
        Other the selected row is inserted into the table, if it doesn't already exists

        db = instance of Db
        user_input = char or integer with row number
        coinsearch = result from search

        """
        minimal = 0
        maximum = len(coinsearch) - 1
        message = 'Select coin to store in database, or (N)ew search, or (Q)uit'

        while True:
            # read a command with arguments from the input
            command, *arguments = shlex.split(input(f'{message} $ '))
            cmd = Command(command, arguments)

            match cmd:
                case Command(command='new' | 'n'):
                    print('New search')
                    break
                case Command(command='quit' | 'q' | 'exit' | 'e', arguments=['--force' | '-f', *rest]):
                    print("Sending SIGTERM to all processes and quitting the program.")
                    sys.exit('Exiting')
                case Command(command='quit' | 'q' | 'exit' | 'e'):
                    sys.exit('Exiting')
                case _:
                    try:
                        value = int(cmd.command)
                    except ValueError:
                        print(f'Unknown command {cmd.command!r}.')
                    else:
                        if (value >= minimal and value <= maximum):
                            self.insert_coin_check(db, coinsearch[value])
                            break
                        else:
                            print('No correct row number! Try again.')
