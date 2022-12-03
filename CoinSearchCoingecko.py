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

import config
import DbHelper
from CoinSearch import CoinSearch
from Db import Db
from DbPostgresql import DbPostgresql
from DbSqlite3 import DbSqlite3


class CoinSearchCoingecko(CoinSearch):
    """Class for searching a coin on the coingecko website
    """

    def __init__(self) -> None:
        self.table_name = DbHelper.DbTableName.coinCoingecko.name
        super().__init__()

    def insert_coin(self, db: Db, params: dict) -> int:
        """Insert a new coin to the coins table

        And download the thumb and large picture of the coin

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
        query = 'INSERT INTO {} (siteid, name, symbol) ' \
                'VALUES(?,?,?)'.format(self.table_name)
        args = (params['id'],
                params['name'],
                params['symbol'])
        res = db.execute(query, args)
        db.commit()
        return res

    def save_images(self, image_urls, coin_name: str):
        """Save image files for one coin

        image_urls = list if urls for images
        coin_name = string with name of coin
        """
        if 'thumb' in image_urls:
            self.save_file(image_urls['thumb'], 'CoinImages', 'coingecko_%s_%s' % (
                coin_name, 'thumb'))
        if 'small' in image_urls:
            self.save_file(image_urls['small'], 'CoinImages', 'coingecko_%s_%s' % (
                coin_name, 'small'))
        if 'large' in image_urls:
            self.save_file(image_urls['large'], 'CoinImages', 'coingecko_%s_%s' % (
                coin_name, 'large'))

    def download_images(self, db: Db):
        """Download image files for all coins in database from Coingecko

        db = instance of Db
        """
        # Get all coingeckoid's from database
        coins = db.query('SELECT siteid FROM {}'.format(self.table_name))
        coins = [i[0] for i in coins]

        # Retrieve coin info from coingecko
        for c in coins:
            url = '''{}/coins/{}?
                    localization=false&
                    tickers=false&
                    market_data=false&
                    community_data=false&
                    developer_data=false&
                    sparkline=false
                '''.format(config.COINGECKO_URL, c)
            resp = self.req.get_request_response(url)
            params_image = resp['image']

            # Save image files
            self.save_images(params_image, c)

    def search_id_web(self, search_str: str) -> list:
        """Search request to Coingecko

        search_str = string to search in assets
        return value = list with search results
        """
        url = '{}/search?query={}'.format(config.COINGECKO_URL, search_str)
        resp = self.req.get_request_response(url)
        res_coins = resp['coins']
        return res_coins

    def get_search_id_db_query(self) -> str:
        """Query for searching coin in database

        return value = query for database search with 
                       ? is used for the search item
        """
        coin_search_query = '''SELECT siteid, name, symbol FROM {} WHERE
                                siteid like ? or
                                name like ? or
                                symbol like ?
                            '''.format(self.table_name)
        return coin_search_query

    def search(self, db: Db, coin_search: str):
        """Search coins in own database (if table exists)

        Show the results

        Search coins from internet (Coingecko)
        Show the results

        User can select a row number, from the table of search results
        To add that coin to the coins table, if it doesn't already exists

        db = instance of Db
        coin_search = string to search in assets
        """
        # Check if coin already in database
        db_result = self.search_id_db(db, coin_search)
        self.print_search_result(db_result, 'Database')

        # Do search on coingecko
        cs_result = self.search_id_web(coin_search)
        self.print_search_result(cs_result, 'CoinGecko', ['thumb', 'large'])

        # ask user which row is the correct answer
        user_input = self.input_number('Select correct coin to store in database, or (N)ew search, or (Q)uit: ',
                                       0, len(cs_result)-1)

        # if coin is selected, add to database (replace or add new row in db?)
        # go back to search question / exit
        self.handle_user_input(db, user_input, cs_result, 'id', 'name')

    def get_all_assets(self) -> list:
        """Get all assets from Coingecko

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
        url_list = '{}/coins/list?include_platform=true'.format(
            config.COINGECKO_URL)
        resp = self.req.get_request_response(url_list)
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
            cs.download_images(db)
        else:
            print('No database, exiting')
    else:
        while True:
            if coin_search == None:
                coin_search = input('Search for coin: ')
            cs.search(db, coin_search)
            coin_search = None


if __name__ == '__main__':
    __main__()
