"""
Created on October 15, 2022

@author: arno

Class CoinSearchAlcor

"""
import argparse
import re

import config
import DbHelper
from CoinData import CoinData, CoinSearchData
from CoinSearch import CoinSearch
from Db import Db
from DbPostgresql import DbPostgresql
from DbSqlite3 import DbSqlite3


class CoinSearchAlcor(CoinSearch):
    """Class for searching a coin on the alcor exchange
    """

    def __init__(self) -> None:
        self.table_name = DbHelper.DbTableName.coinAlcor.name
        super().__init__()

    def insert_coin(self, db: Db, coin: CoinSearchData) -> int:
        """Insert a new coin to the coins table

        db = instance of Db
        coin = search data with retrieved coin info from web
        return value = rowcount or total changes 
        """
        query = 'INSERT INTO {} (siteid, base, quote, chain) ' \
                'VALUES(?,?,?,?)'.format(self.table_name)
        args = (coin.coin.siteid,
                coin.coin.base,
                coin.coin.name,  # = quote
                coin.coin.chain)
        res = db.execute(query, args)
        db.commit()
        return res

    def search_id_assets(self, search_str: str, assets) -> list[CoinSearchData]:
        """Search for coin in list of all assets

        search_str: str = string to search in assets
        assets = list of assets from Alcor
        return value = list with search results
        """
        s = search_str.lower()
        resp_coins = []
        for asset in assets.values():
            resp_coin = [item for item in asset
                         if (re.match(s, item['base_token']['symbol']['name'].lower()) or
                             re.search(s, item['base_token']['str'].lower()) or
                             re.match(s, item['quote_token']['symbol']['name'].lower()) or
                             re.search(s, item['quote_token']['str'].lower()))]
            resp_coins.extend(resp_coin)
        coinsearch = self.convert_assets_to_coinsearchdata(resp_coins)
        return coinsearch

    def convert_assets_to_coinsearchdata(self, resp: list) -> list[CoinSearchData]:
        """Convert result from site to list of CoinSearchData

        resp = list from the web
        return value = list of CoinSearchData

        {'id': 157,
        'base_token': {"symbol":{"name":"XUSDC","precision":6},"contract":"xtokens","str":"XUSDC@xtokens"},
        'quote_token': {"symbol":{"name":"FREEOS","precision":4},"contract":"freeostokens","str":"FREEOS@freeostokens"},
        'chain': 'proton',
        'ticker_id': 'FREEOS-freeostokens_XUSDC-xtokens',
        'volume24': 0, 'volumeWeek': 0, 'volumeMonth': 0,
        'change24': 0, 'changeWeek': 0,
        'frozen': false
        }
        """
        coinsearch = []
        for r in resp:
            coindata = CoinData(siteid=r['id'],
                                name=r['quote_token']['str'],
                                symbol=r['quote_token']['symbol']['name'],
                                chain=r['chain'],
                                base=r['base_token']['str'])
            coinsearch.append(CoinSearchData(coin=coindata,
                                             base=r['base_token']['symbol']['name'],
                                             volume=r['volumeWeek'],
                                             change=r['changeWeek']))
        return coinsearch

    def get_search_id_db_query(self) -> str:
        """Query for searching coin in database

        return value = query for database search with 
                       ? is used for the search item
        """
        # Sqlite use INSTR, other databases use CHARINDEX('@',quote,0) ??
        coin_search_query = '''SELECT siteid, quote, 
                                    SUBSTRING(quote,0,INSTR(quote,'@')) AS symbol, 
                                    chain, base 
                                FROM {} WHERE
                                    base like ? or
                                    quote like ?
                            '''.format(self.table_name)
        return coin_search_query

    def search(self, db: Db, coin_search: str, assets: dict):
        """Search coins in own database (if table exists)

        Show the results

        Search coins from Alcor assets (already in assets)
        Show the results

        User can select a row number, from the table of search results
        To add that coin to the coins table, if it doesn't already exists

        db = instance of Db
        coin_search = string to search in assets
        assets = dictionary where each key is a chain with a list of string with assets from Alcor
        """
        # Check if coin already in database
        db_result = self.search_id_db(db, coin_search)
        self.print_search_result(db_result, 'Database')

        # Do search on Alcor assets in memory
        cs_result = self.search_id_assets(coin_search, assets)
        self.print_search_result(cs_result, 'Alcor')

        # ask user which row is the correct answer
        self.input_coin_row(db, cs_result)

    def get_all_assets(self, chains: list) -> dict:
        '''Retrieve all assets from alcor api

        chains = list of chains in alcor ecosystem

        returns = dictionary where each key is a chain with a list of string with assets from Alcor
        '''
        coin_assets = {}
        for chain in chains:
            url_list = config.ALCOR_URL.replace('?', chain) + '/markets'
            resp = self.req.get_request_response(url_list)
            coin_assets[chain] = resp['result']
        return coin_assets


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
    if config.DB_TYPE == 'sqlite':
        db = DbSqlite3(config.DB_CONFIG)
    elif config.DB_TYPE == 'postgresql':
        db = DbPostgresql(config.DB_CONFIG)
    else:
        raise RuntimeError('No database configuration')

    db.check_db()
    db.check_table(cs.table_name)

    # get all assets from Alcor
    coin_assets = cs.get_all_assets(chains)

    while coin_assets != None:
        if coin_search == None:
            coin_search = input('Search for coin: ')
        cs.search(db, coin_search, coin_assets)
        coin_search = None


if __name__ == '__main__':
    __main__()
