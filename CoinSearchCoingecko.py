"""
Created on Mar 29, 2022

@author: arno

Coingecko search
Search id for coins to finally get price from coingecko
Search if coin already is in database
Put choosen coin in database and downloads coin image

Response is a dictionary with keys
coins, exchanges, icos, categories, nfts
the key coins has a list of the search result of coins
{
  'coins': [
    {
      'id': 'astroelon',
      'name': 'AstroElon',
      'symbol': 'ELONONE',
      'market_cap_rank': null,
      'thumb': 'https://assets.coingecko.com/coins/images/16082/thumb/AstroElon.png',
      'large': 'https://assets.coingecko.com/coins/images/16082/large/AstroElon.png'
    }
  ],
  'exchanges': [] ...
"""
import argparse
import sys

import pandas as pd

import config
import DbHelper
from CoinSearch import CoinSearch
from Db import Db
from DbPostgresql import DbPostgresql
from DbSqlite3 import DbSqlite3
from RequestHelper import RequestHelper


class CoinSearchCoingecko(CoinSearch):
    """Class for searching a coin on the coingecko website
    """

    def __init__(self) -> None:
        self.table_name = DbHelper.DbTableName.coinCoingecko.name
        super().__init__()

    def insert_coin(self, req: RequestHelper, db: Db, params: dict) -> int:
        """Insert a new coin to the coins table

        And download the thumb and large picture of the coin

        req = instance of RequestHelper
        db = instance of Db
        params = dictionary with retrieved coin info from coingecko
                {'id': 'dogecoin',
                'name': 'Dogecoin',
                'symbol': 'DOGE',
                'market_cap_rank': 10,
                'thumb': 'https://assets.coingecko.com/coins/images/5/thumb/dogecoin.png',
                'large': 'https://assets.coingecko.com/coins/images/5/large/dogecoin.png'
                }
        return value = rowcount or total changes 
        """
        query = 'INSERT INTO {} (coingeckoid, name, symbol) ' \
                'VALUES(?,?,?)'.format(self.table_name)
        args = (params['id'], 
                params['name'], 
                params['symbol'])
        res = db.execute(query, args)
        db.commit()
        return res

    def download_images(self, req: RequestHelper, db: Db):
        """Download image files for all coins in database from Coingecko

        req = instance of RequestHelper
        db = instance of Db
        """
        # Get all coingeckoid's from database
        coins = db.query('SELECT coingeckoid FROM {}'.format(self.table_name))
        coins = [i[0] for i in coins]

        # Retrieve coin info from coingecko
        for c in coins:
            url = '''https://api.coingecko.com/api/v3/coins/{}?
                    localization=false&
                    tickers=false&
                    market_data=false&
                    community_data=false&
                    developer_data=false&
                    sparkline=false
                '''.format(c)
            resp = req.get_request_response(url)
            params_image = resp['image']

            # Save image files
            self.save_file(
                req, params_image['thumb'], 'CoinImages', 'coingecko_%s_%s' % (c, 'thumb'))
            self.save_file(
                req, params_image['small'], 'CoinImages', 'coingecko_%s_%s' % (c, 'small'))
            self.save_file(
                req, params_image['large'], 'CoinImages', 'coingecko_%s_%s' % (c, 'large'))

    def search_id_web(self, req: RequestHelper, search_str: str) -> list:
        """Search request to Coingecko

        req = instance of RequestHelper
        search_str = string to search in assets
        return value = list with search results
        """
        url = 'https://api.coingecko.com/api/v3/search?query='+search_str
        resp = req.get_request_response(url)
        res_coins = resp['coins']
        return res_coins
    
    def get_search_id_db_query(self) -> str:
        """Query for searching coin in database

        return value = query for database search with 
                       ? is used for the search item
        """
        coin_search_query = '''SELECT * FROM {} WHERE
                                coingeckoid like ? or
                                name like ? or
                                symbol like ?
                            '''.format(self.table_name)
        return coin_search_query

    def search(self, req: RequestHelper, db: Db, coin_search: str):
        """Search coins in own database (if table exists)

        Show the results

        Search coins from internet (Coingecko)
        Show the results

        User can select a row number, from the table of search results
        To add that coin to the coins table, if it doesn't already exists

        req = instance of RequestHelper
        db = instance of DbHelperArko
        coin_search = string to search in assets
        """
        # Check if coin already in database
        db_result = self.search_id_db(db, coin_search)
        self.print_search_result(db_result, 'Database')

        # Do search on coingecko
        cs_result = self.search_id_web(req, coin_search)
        self.print_search_result(cs_result, 'CoinGecko')

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
            coin_id = coin['id']
            coin_name = coin['name']

            # check if coingecko id is already in our database
            if db.has_connection():
                # if table doesn't exist, create table coins
                if not db.check_table(self.table_name):
                    DbHelper.create_table(db, self.table_name)

                db_result = db.query('SELECT * FROM %s WHERE coingeckoid="%s"' %
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
                    
                    # safe coin images
                    self.save_file(req, coin['thumb'], 'CoinImages',
                                'coingecko_%s_%s' % (coin_name, 'thumb'))
                    self.save_file(req, coin['large'], 'CoinImages',
                                'coingecko_%s_%s' % (coin_name, 'large'))
            else:
                print('No database connection')

    def get_all_assets(self, req: RequestHelper):
        """Get all assets from Coingecko

        req = instance of RequestHelper
        result = {
            {'id': 'astroelon',
            'symbol': 'elonone',
            'name': 'AstroElon',
            'platforms': {
                'ethereum': '0x...'
                }
            },...
        }
        """
        url_list = 'https://api.coingecko.com/api/v3/coins/list?include_platform=true'
        resp = req.get_request_response(url_list)
        assets = resp['result']
        return assets


def __main__():
    """Get Coingecko search assets and store in databse

    Arguments:
    - coin to search
    - image, save image file for all coins in database
    """
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-c', '--coin', type=str,
                           help='Coin name to search on Coingecko')
    argparser.add_argument('-i', '--image', action='store_true',
                           help='Save image file for all coins in database')
    args = argparser.parse_args()
    coin_search = args.coin

    # init session
    cs = CoinSearchCoingecko()
    req = RequestHelper()
    if config.DB_TYPE == 'sqlite':
        db = DbSqlite3(config.DB_CONFIG)
    elif config.DB_TYPE == 'postgresql':
        db = DbPostgresql(config.DB_CONFIG)
    else:
        raise RuntimeError('No database configuration')

    db.check_db()
    db_table_exist = db.check_table(cs.table_name)

    if args.image:
        if db_table_exist:
            cs.download_images(req, db)
        else:
            print('No database, exiting')
    else:
        while True:
            if coin_search == None:
                coin_search = input('Search for coin: ')
            cs.search(req, db, coin_search)
            coin_search = None


if __name__ == '__main__':
    __main__()
