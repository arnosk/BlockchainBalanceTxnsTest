"""
Created on October 15, 2022

@author: arno

Class CoinSearchAlcor

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


class CoinSearchAlcor(CoinSearch):
    """Class for searching a coin on the alcor exchange
    """

    def __init__(self) -> None:
        self.table_name = DbHelper.DbTableName.coinAlcor.name
        super().__init__()

    def insert_coin(self, req: RequestHelper, db: Db, params: dict):
        """Insert a new coin to the coins table

        req = instance of RequestHelper
        db = instance of DbHelperArko
        params = dictionary with retrieved coin info from Alcor
        """
        query = 'INSERT INTO {} (alcorid, base, quote, chain) ' \
                'VALUES(?,?,?,?)'.format(self.table_name)
        args = (params['id'],
                params['base'],
                params['quote'],
                params['chain'])
        db.execute(query, args)
        db.commit()

    def simplify_coinitems(self, coins: list) -> list:
        """Return a simpler structure of coin items

        {'id': 157,
        'base_token': {"symbol":{"name":"XUSDC","precision":6},"contract":"xtokens","str":"XUSDC@xtokens"},
        'quote_token': {"symbol":{"name":"FREEOS","precision":4},"contract":"freeostokens","str":"FREEOS@freeostokens"},
        'chain': 'proton',
        'ticker_id': 'FREEOS-freeostokens_XUSDC-xtokens'
        }

        coins = list with result from web
        return value = simplified list
        """
        result = []
        for item in coins:
            result.append(
                {'quote': item['quote_token']['str'],  # item['quote_token']['symbol']['name']
                'base': item['base_token']['str'], # item['base_token']['symbol']['name']
                'chain': item['chain'],
                'volume24': item['volume24'],
                'volumeM': item['volumeMonth'],
                'id': item['id'],
                'ticker': item['ticker_id'] if 'ticker_id' in item else '-',
                'frozen': item['frozen']
                }
            )
        return result

    def search_id_assets(self, search_str: str, assets) -> list:
        """Search for coin in list of all assets

        search_str: str = string to search in assets
        assets = list of assets from Alcor
        return value = list with search results
        """
        s = search_str.lower()
        res_coins = []
        for asset in assets.values():
            res_coin = [item for item in asset
                        if (re.match(s, item['base_token']['symbol']['name'].lower()) or
                            re.search(s, item['base_token']['str'].lower()) or
                            re.match(s, item['quote_token']['symbol']['name'].lower()) or
                            re.search(s, item['quote_token']['str'].lower()))]
            res_coins.extend(res_coin)
        return res_coins

    def get_search_id_db_query(self) -> str:
        """Query for searching coin in database

        return value = query for database search with 
                       ? is used for the search item
        """
        coin_search_query = '''SELECT * FROM {} WHERE
                                base like ? or
                                quote like ?
                            '''.format(self.table_name)
        return coin_search_query

    def search(self, req: RequestHelper, db: Db, coin_search: str, assets: dict):
        """Search coins in own database (if table exists)

        Show the results

        Search coins from Alcor assets (already in assets)
        Show the results

        User can select a row number, from the table of search results
        To add that coin to the coins table, if it doesn't already exists

        req = instance of RequestHelper
        db = instance of DbHelperArko
        coin_search = string to search in assets
        assets = dictionary where each key is a chain with a list of string with assets from Alcor
        """
        # Check if coin already in database
        db_result = self.search_id_db(db, coin_search)
        self.print_search_result(db_result, 'Database')

        # Do search on Alcor assets in memory
        cs_result = self.search_id_assets(coin_search, assets)
        cs_result = self.simplify_coinitems(cs_result)
        self.print_search_result(cs_result, 'Alcor', ['ticker', 'frozen'])

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
            # coin selected add to
            print('Number chosen = %s' % user_input)
            coin = cs_result[user_input]
            print(coin)

            # check if database exist, in case of sqlite create database
            if not db.has_connection():
                db.open()

            # check if coin name, symbol is already in our database
            if db.has_connection():
                # if table doesn't exist, create table coins
                if not db.check_table(self.table_name):
                    DbHelper.create_table(db, self.table_name)

                db_result = db.query('SELECT * FROM %s WHERE alcorid="%s"' %
                                     (self.table_name, coin['id']))
                if len(db_result):
                    print('Database already has a row with the coin %s' %
                          (coin['ticker_id']))
                else:
                    # add new row to table coins
                    self.insert_coin(req, db, coin)
            else:
                print('No database connection')


def __main__():
    """Get Alcor search assets and store in database

    Arguments:
    - coin to search
    - chain to search or if not present all chains
    """
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-c', '--coin', type=str,
                           help='Coin name to search on Alcor')
    argparser.add_argument('-ch', '--chain', type=str,
                           help='Chain name to search on Alcor')
    args = argparser.parse_args()
    coin_search = args.coin
    chain_str = args.chain

    # Select chain from argument or take default all chains
    if chain_str != None:
        chains = re.split('[;,]', chain_str)
    else:
        chains = config.ALCOR_CHAINS

    # init session
    cs = CoinSearchAlcor()
    req = RequestHelper()
    if config.DB_TYPE == 'sqlite':
        db = DbSqlite3(config.DB_CONFIG)
    elif config.DB_TYPE == 'postgresql':
        db = DbPostgresql(config.DB_CONFIG)
    else:
        print('No database configuration')
        raise

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

    # get all assets from Alcor
    coin_assets = {}
    for chain in chains:
        url_list = config.ALCOR_URL.replace('?', chain) + '/markets'
        print(url_list)
        resp = req.get_request_response(url_list)
        coin_assets[chain] = resp['result']

    while coin_assets != None:
        if coin_search == None:
            coin_search = input('Search for coin: ')
        cs.search(req, db, coin_search, coin_assets)
        coin_search = None


if __name__ == '__main__':
    __main__()
