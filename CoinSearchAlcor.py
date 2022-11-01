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
from DbHelper import DbHelperArko, DbType
from RequestHelper import RequestHelper
from CoinSearch import CoinSearch


class CoinSearchAlcor(CoinSearch):
    """Class for searching a coin on the alcor exchange
    """

    def __init__(self) -> None:
        super().__init__()

    def insert_coin(self, req: RequestHelper, db: DbHelperArko, params: dict):
        """Insert a new coin to the coins table

        And download the thumb and large picture of the coin


        req = instance of RequestHelper
        db = instance of DbHelperArko
        params = dictionary with retrieved coin info from Alcor
                {'id': 62,
                'symbol': 'doge',
                'name': 'Dogecoin',
                'fiat': False,
                'route': 'https://api.cryptowat.ch/assets/doge'
                }
        """
        print(params)
        #safeFile(req, params['thumb'], 'CoinImages', 'coingecko_%s_%s.png'%(params['id'],'thumb'))
        #safeFile(req, params['large'], 'CoinImages', 'coingecko_%s_%s.png'%(params['id'],'large'))
        query = 'INSERT INTO {} (alcorid, base, quote, chain) ' \
                'VALUES(?,?,?,?)'.format(db.table['coinAlcor'])
        args = (params['id'],
                params['base_token']['str'],
                params['quote_token']['str'],
                params['chain'])
        db.execute(query, args)
        db.commit()

    def search_id(self, search_str: str, assets):
        """Search for coin in list of all assets

        search_str: str = string to search in assets
        assets = list of assets from Alcor
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

    def search(self, req: RequestHelper, db: DbHelperArko, coin_search: str, assets: dict):
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
        pd.set_option('display.max_colwidth', 20)

        # Check if coin already in database and add to search result on row 0
        db_result = []
        if db.check_table(db.table['coinAlcor']):
            coin_search_str = '%{}%'.format(coin_search)
            coin_search_query = '''SELECT * FROM {} WHERE
                                    base like ? or
                                    quote like ?
                            '''.format(db.table['coinAlcor'])
            db_result = db.query(coin_search_query,
                                 (coin_search_str, coin_search_str))
            if (len(db_result) > 0):
                db_resultdf = pd.DataFrame(db_result)
                print('Search in database:')
                print(db_resultdf)

        # Do search on Alcor assets in memory
        cw_result_coin = self.search_id(coin_search, assets)
        if (len(cw_result_coin) > 0):
            cw_result_coin_print = []
            for item in cw_result_coin:
                print(type(item))
                print(item)
                print(item['base_token'])
                print('--------------------')
                cw_result_coin_print.append(
                    {'quote': item['quote_token']['str'],  # item['quote_token']['symbol']['name']
                     # item['base_token']['symbol']['name']
                     'base': item['base_token']['str'],
                     'chain': item['chain'],
                     'volume24': item['volume24'],
                     'volumeM': item['volumeMonth'],
                     'id': item['id'],
                     'ticker': item['ticker_id'] if 'ticker_id' in item else '-',
                     'frozen': item['frozen']
                     }
                )
            cw_result_coindf = pd.DataFrame(cw_result_coin_print)
            # .filter(['quote_token', 'base_token'], axis=1)
            cw_result_coindf_print = cw_result_coindf
            print('Search from Alcor:')
            print(cw_result_coindf_print)
        else:
            print('Coin not found')

        # ask user which row is the correct answer
        user_input = self.input_number('Select correct coin to store in database, or (N)ew search, or (Q)uit: ',
                                       0, len(cw_result_coin)-1)

        # if coin is selected, add to database (replace or add new row in db?)
        # go back to search question / exit
        if user_input == 'n':
            print('New search')
        elif user_input == 'q':
            sys.exit('Exiting')
        else:
            # coin selected add to
            print('Number chosen = %s' % user_input)
            coin = cw_result_coin[user_input]
            print(coin)

            # check if database exist, in case of sqlite create database
            if not db.has_connection():
                if db.get_db_type() == DbType.sqlite:
                    db.open()
                else:
                    print('No database %s, do new search' % db.get_db_type())

            # check if coin name, symbol is already in our database
            if db.has_connection():
                # if table doesn't exist, create table coins
                if not db.check_table(db.table['coinAlcor']):
                    db.create_table(db.table['coinAlcor'])
                    db.chk_table[db.table['coinAlcor']] = True

                db_result = db.query('SELECT * FROM %s WHERE alcorid="%s"' %
                                     (db.table['coinAlcor'], coin['id']))
                if len(db_result):
                    print('Database already has a row with the coin %s' %
                          (coin['ticker_id']))
                else:
                    # add new row to table coins
                    self.insert_coin(req, db, coin)


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
    db = DbHelperArko(config.DB_CONFIG, config.DB_TYPE)
    req = RequestHelper()

    db_exist = db.check_db()
    print('Database exists:', db_exist)
    print('Database exists:', db.has_connection())
    db_table_exist = db.check_db(table_name=db.table['coinAlcor'])
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
