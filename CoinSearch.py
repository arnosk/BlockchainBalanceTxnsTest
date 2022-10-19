"""
Created on October 13, 2022

@author: arno

Base Class CoinSearch

"""
import sys

import DbHelper
import RequestHelper


class CoinSearch:
    """Base class for searching a coin on an exchange or provider
    """

    def __init__(self) -> None:
        pass

    def search(self, req: RequestHelper, db: DbHelper, coin_search: str, assets: dict):
        """Searching coins on exchange

        Search coins in own database (if table exists)
        Show the results

        Search coins from exchange assets (already in assets)
        Show the results

        User can select a row number, from the table of search results
        To add that coin to the coins table, if it doesn't already exists

        req = instance of RequestHelper
        db = instance of DbHelperArko
        coin_search = string to search in assets
        assets = dictionary where each key is a chain with a list of string with assets from Alcor
        """
        pass

    def insertCoin(self, req: RequestHelper, db: DbHelper, params: dict):
        """Insert coin in database

        Insert a new coin to the coins table
        And download the thumb and large picture of the coin


        req = instance of RequestHelper
        db = instance of DbHelperArko
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
