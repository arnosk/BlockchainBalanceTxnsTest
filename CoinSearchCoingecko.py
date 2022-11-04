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
import os
import sys

import cfscrape
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

        scraper = cfscrape.create_scraper()
        cfurl = scraper.get(url).content

        with open(file, 'wb') as f:
            f.write(cfurl)

    def insert_coin(self, req: RequestHelper, db: Db, params: dict):
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
        """
        self.save_file(req, params['thumb'], 'CoinImages',
                       'coingecko_%s_%s' % (params['id'], 'thumb'))
        self.save_file(req, params['large'], 'CoinImages',
                       'coingecko_%s_%s' % (params['id'], 'large'))
        query = 'INSERT INTO {} (coingeckoid, name, symbol) ' \
                'VALUES(?,?,?)'.format(self.table_name)
        args = (params['id'], params['name'], params['symbol'])
        db.execute(query, args)
        db.commit()

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

    def search_id(self, req: RequestHelper, search_str: str):
        """Search request to Coingecko

        req = instance of RequestHelper
        search_str = string to search in assets
        """
        url = 'https://api.coingecko.com/api/v3/search?query='+search_str
        resp = req.get_request_response(url)
        res_coins = resp['coins']
        return res_coins

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
        pd.set_option('display.max_colwidth', 20)

        # Check if coin already in database and add to search result on row 0
        db_result = []
        if db.check_table(self.table_name):
            coin_search_str = '%{}%'.format(coin_search)
            coin_search_query = '''SELECT * FROM {} WHERE
                                    coingeckoid like ? or
                                    name like ? or
                                    symbol like ?
                                '''.format(self.table_name)
            db_result = db.query(coin_search_query,
                                 (coin_search_str, coin_search_str, coin_search_str))
            if (len(db_result) > 0):
                db_resultdf = pd.DataFrame(db_result)
                print('Search in database:')
                print(db_resultdf)

        # Do search on coingecko
        cg_result = self.search_id(req, coin_search)
        cg_resultdf = pd.DataFrame(cg_result)
        print('Search from coingecko:')
        print(cg_resultdf)

        # ask user which row is the correct answer
        user_input = self.input_number('Select correct coin to store in database, or (N)ew search, or (Q)uit: ',
                                       0, len(cg_result)-1)

        # if coin is selected, add to database (replace or add new row in db?)
        # go back to search question / exit
        if user_input == 'n':
            print('New search')
        elif user_input == 'q':
            sys.exit('Exiting')
        else:
            # coin selected add to
            print('Number chosen = %s' % user_input)
            coin = cg_result[user_input]
            print(coin)

            # check if database exist, in case of sqlite create database
            if not db.has_connection():
                db.open()

            # check if coingecko id is already in our database
            if db.has_connection():
                # if table doesn't exist, create table coins
                if not db.check_table(self.table_name):
                    DbHelper.create_table(db, self.table_name)

                db_result = db.query('SELECT * FROM %s WHERE coingeckoid="%s"' %
                                     (self.table_name, coin['id']))
                if len(db_result):
                    print('Database already has a row with the coin %s' %
                          (coin['id']))
                else:
                    # add new row to table coins
                    self.insert_coin(req, db, coin)
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
        print('No database configuration')
        raise

    db_exist = db.check_db()
    print('Database exists:', db_exist)
    print('Database exists:', db.has_connection())
    db_table_exist = db.check_table(cs.table_name)
    print('Table coins exist:', db_table_exist)

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
