"""
Created on Apr 23, 2022

@author: arno

Cryptowat.ch search

"""
import argparse
import re
import sys

import pandas as pd

import config
import DbHelper
from CoinSearch import CoinSearch
from Db import Db
from DbPostgresql import DbPostgresql
from DbSqlite3 import DbSqlite3
from RequestHelper import RequestHelper


class CoinSearchCryptowatch(CoinSearch):
    """Class for searching a coin on the cryptowatch website
    """

    def __init__(self) -> None:
        self.table_name = DbHelper.DbTableName.coinCryptowatch.name
        super().__init__()

    def insert_coin(self, req: RequestHelper, db: Db, params: dict) -> int:
        """Insert a new coin to the coins table

        req = instance of RequestHelper
        db = instance of Db
        params = dictionary with retrieved coin info from Cryptowatch
                {'id': 62,
                'sid': 'dogecoin',
                'symbol': 'doge',
                'name': 'Dogecoin',
                'fiat': False,
                'route': 'https://api.cryptowat.ch/assets/doge'
                }
        return value = rowcount or total changes 
        """
        query = 'INSERT INTO {} (siteid, name, symbol) ' \
                'VALUES(?,?,?)'.format(self.table_name)
        args = (params['sid'],
                params['name'], 
                params['symbol'])
        res = db.execute(query, args)
        db.commit()
        return res

    def search_id_assets(self, search_str: str, assets: list) -> list:
        """Search for coin in list of all assets

        search_str = string to search in assets
        assets = list of assets from Cryptowatch
        return value = list with search results
        """
        s = search_str.lower()
        res_coins = [item for item in assets
                     if (re.match(s, item['sid'].lower()) or
                         re.match(s, item['name'].lower()) or
                         re.match(s, item['symbol'].lower()))]
        return res_coins

    def get_search_id_db_query(self) -> str:
        """Query for searching coin in database

        return value = query for database search with 
                       ? is used for the search item
        """
        coin_search_query = '''SELECT * FROM {} WHERE
                                siteid like ? or
                                name like ? or
                                symbol like ?
                            '''.format(self.table_name)
        return coin_search_query

    def search(self, req: RequestHelper, db: Db, coin_search: str, assets: list):
        """Search coins in own database (if table exists)

        Show the results

        Search coins from Cryptowatch assets (already in assets)
        Show the results

        User can select a row number, from the table of search results
        To add that coin to the coins table, if it doesn't already exists

        req = instance of RequestHelper
        db = instance of Db
        coin_search = string to search in assets
        assets = list of string with assets from Cryptowatch
        """
        # Check if coin already in database
        db_result = self.search_id_db(db, coin_search)
        self.print_search_result(db_result, 'Database')

        # Do search on cryptowatch assets in memory
        cs_result = self.search_id_assets(coin_search, assets)
        self.print_search_result(cs_result, 'CryptoWatch', 'route')

        # ask user which row is the correct answer
        user_input = self.input_number('Select correct coin to store in database, or (N)ew search, or (Q)uit: ',
                                       0, len(cs_result)-1)

        # if coin is selected, add to database (replace or add new row in db?)
        # go back to search question / exit
        if user_input == 'n':
            print('New search')
        elif user_input == 'q':
            sys.exit('Exiting')
        else:
            coin = cs_result[user_input]
            coin_id = coin['sid']
            coin_name = coin['name']

            # check if coin name, symbol is already in our database
            if db.has_connection():
                # if table doesn't exist, create table coins
                if not db.check_table(self.table_name):
                    DbHelper.create_table(db, self.table_name)

                db_result = db.query('SELECT * FROM %s WHERE siteid="%s"' %
                                     (self.table_name, coin_id))
                if len(db_result):
                    print('Database already has a row with the coin %s' %
                          (coin_name))
                else:
                    # add new row to table coins
                    insert_result = self.insert_coin(req, db, coin)
                    if insert_result > 0:
                        print('%s added to the database' % (coin_name))
                    else:
                        print('Error adding %s to database' % (coin_name))
            else:
                print('No database connection')


def __main__():
    """Get Cryptowatch search assets and store in database

    Arguments:
    - coin to search
    """
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-c', '--coin', type=str,
                           help='Coin name to search on Coingecko')
    args = argparser.parse_args()
    coin_search = args.coin

    # init session
    cs = CoinSearchCryptowatch()
    req = RequestHelper()
    req.update_header({'X-CW-API-Key': config.CRYPTOWATCH_API})
    if config.DB_TYPE == 'sqlite':
        db = DbSqlite3(config.DB_CONFIG)
    elif config.DB_TYPE == 'postgresql':
        db = DbPostgresql(config.DB_CONFIG)
    else:
        raise RuntimeError('No database configuration')

    db_exist = db.check_db()
    print('Database exists:', db_exist)
    print('Database exists:', db.has_connection())
    db_table_exist = db.check_table(cs.table_name)
    print('Table coins exist:', db_table_exist)

    # init pandas displaying
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_colwidth', 20)
    pd.set_option('display.float_format', '{:.6e}'.format)

    # get all assets from cryptowatch
    url_list = config.CRYPTOWATCH_URL + '/assets'
    resp = req.get_request_response(url_list)
    coin_assets = resp['result']

    while coin_assets != None:
        if coin_search == None:
            coin_search = input('Search for coin: ')
        cs.search(req, db, coin_search, coin_assets)
        coin_search = None


if __name__ == '__main__':
    __main__()
