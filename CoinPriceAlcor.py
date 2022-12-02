"""
Created on Aug 31, 2022

@author: arno

Collecting prices

Alcor
"""
import copy
import math
import re
from datetime import datetime
from typing import Dict

from dateutil import parser

import config
import DbHelper
from CoinData import CoinData, CoinMarketData, CoinPriceData
from CoinPrice import CoinPrice, add_standard_arguments
from Db import Db
from DbPostgresql import DbPostgresql
from DbSqlite3 import DbSqlite3


class CoinPriceAlcor(CoinPrice):
    """Class for retrieving price data of a set of coins on the Alcor website
    """

    def __init__(self) -> None:
        self.table_name: str = DbHelper.DbTableName.coinAlcor.name
        self.markets: dict[str, CoinMarketData] = {}
        super().__init__()

    def get_price_current(self, coindata: list[CoinData]) -> list[CoinPriceData]:
        """Get alcor current price

        coindata = list of CoinData for market base and quote and chain

        returns list of CoinPriceData
        """
        # make dict per chain (key1) with a dict of coins per coinid (key2)
        coin_srch: dict[str, dict[str, CoinData]] = {}
        for coin in coindata:
            coin_srch.setdefault(coin.chain, {}).update({coin.siteid: coin})

        # get all market data for each chain from Alcor site
        prices: list[CoinPriceData] = []
        for key_chain, val_coins in coin_srch.items():
            url = config.ALCOR_URL.replace('?', key_chain) + '/markets'
            resp = self.req.get_request_response(url)

            # search through result for coin in the dict
            for item in resp['result']:
                if item['id'] in val_coins:
                    coin = val_coins[item['id']]
                    coin.name = item['quote_token']['str']
                    coin.symbol = item['quote_token']['symbol']['name']
                    coin_price_data = CoinPriceData(
                        date=datetime.now(),
                        coin=coin,
                        curr=item['base_token']['str'],
                        price=item['last_price'],
                        volume=item['volume24'])
                    coin_market_data = CoinMarketData(
                        coin=coin,
                        curr=item['base_token']['str'])

                    prices.append(coin_price_data)
                    self.markets[coin.siteid] = coin_market_data

        return prices

    def get_price_hist_marketchart(self, coindata: list[CoinData], date) -> list[CoinPriceData]:
        """Get alcor history price of a coin via market chart data

        coindata = list of CoinData for market base and quote and chain
        date = historical date 

        returns list of CoinPriceData
        """
        # convert date to unix timestamp
        dt = parser.parse(date)  # local time
        ts = int(dt.timestamp())

        # make parameters
        params = {}
        params['resolution'] = 60
        params['from'] = ts
        params['to'] = ts

        prices: list[CoinPriceData] = []
        i = 0
        for coin in coindata:
            i += 1
            self.show_progress(i, len(coindata))

            coinprice = self.get_pricedata_hist_marketchart_retry(
                coin, dt, ts, params)
            prices.append(coinprice)

        return prices

    def search_price_minimal_timediff(self, prices, ts: int, ms: bool = False):
        """Search for record in price data with the smallest time difference

        prices = results from request with price data
        ts = timestamp in sec if ms = False
        ts = timestamp in msec if ms = True

        result = record with smallest time difference with ts
        """
        timediff_minimal = 10**20
        price_minimal = {}
        ts = ts*1000 if ms == True else ts
        for price in prices:
            timediff = abs(ts - price['time'])
            if timediff < timediff_minimal:
                timediff_minimal = timediff
                price_minimal = price
        return price_minimal

    def get_pricedata_hist_marketchart_retry(self, coin: CoinData, dt, ts, params) -> CoinPriceData:
        """Get history price data for one coin from and to specific date

        with retry mechanism for bigger time range when no data is found
        increase time range until data is found

        coindata = CoinData for market base and quote and chain
        date = historical date 

        return CoinPriceData
        """
        params_try = copy.deepcopy(params)
        url = config.ALCOR_URL.replace(
            '?', coin.chain) + '/markets/{}/charts'.format(coin.siteid)

        date = dt
        coin_base = self.markets[coin.siteid].curr
        price = math.nan
        volume = math.nan
        error = 'no data found'

        for nr_try in range(1, self.nr_try_max):
            # retry same coin with new date range
            params_try['from'] -= 2**(2*nr_try) * 3600
            params_try['to'] += 2**(2*nr_try) * 3600

            url_try = self.req.api_url_params(url, params_try)
            resp = self.req.get_request_response(url_try)

            # check for correct response
            if resp['status_code'] == 'error':
                # got no status from request, must be an error
                error = resp['error']
                break
            else:
                resp_prices = resp['result']
                if len(resp_prices) > 0:
                    # select result with timestamp nearest to desired date ts
                    resp_price_minimal = self.search_price_minimal_timediff(
                        resp_prices, ts, True)

                    # set found coin price data
                    date = self.convert_timestamp_n(
                        resp_price_minimal['time'], True)
                    price = resp_price_minimal['open']
                    volume = resp_price_minimal['volume']
                    error = ''
                    break

        return CoinPriceData(date=date, coin=coin, curr=coin_base, price=price, volume=volume, error=error)


def __main__():
    """Get Alcor price history

    Arguments:
    - date for historical prices
    - coin search prices for specfic coin
    - output file for saving ress in a csv file
    """
    argparser = add_standard_arguments('Alcor')
    argparser.add_argument('-ch', '--chain', type=str,
                           help='Chain to search on Alcor')
    args = argparser.parse_args()
    date = args.date
    coin_str = args.coin
    chain_str = args.chain
    output_csv = args.output_csv
    output_xls = args.output_xls
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M')
    print('Current date:', current_date)

    # init session
    cp = CoinPriceAlcor()
    if config.DB_TYPE == 'sqlite':
        db = DbSqlite3(config.DB_CONFIG)
    elif config.DB_TYPE == 'postgresql':
        db = DbPostgresql(config.DB_CONFIG)
    else:
        raise RuntimeError('No database configuration')

    # check if database and table coins exists and has values
    db.check_db()
    db_table_exist = db.check_table(cp.table_name)

    # Determine which coins to retrieve prices for
    # From arguments, from database, or take default
    if coin_str != None:
        coins = re.split('[;,]', coin_str)
        chain = chain_str if chain_str != None else 'proton'
        coin_data = [CoinData(siteid=i, chain=chain) for i in coins]
        coins = [[chain, i] for i in coins]
    elif db_table_exist:
        coins = db.query(
            'SELECT chain, siteid, quote, base FROM {}'.format(cp.table_name))
        coin_data = [CoinData(chain=i[0], siteid=i[1], name=i[2])
                     for i in coins]  # symbol=i[3] = base???
        coins = [[i[0], i[1], i[2], i[3]] for i in coins]
    else:
        coins = [['proton', 157], ['wax', 158], ['proton', 13], ['wax', 67],
                 ['proton', 5], ['eos', 2], ['telos', 34], ['proton', 96]]
        coin_data = [CoinData(siteid=i[1], chain=i[0]) for i in coins]

    print('* Current price of coins')
    price = cp.get_price_current(coin_data)
    cp.print_coinpricedata(price)
    cp.write_to_file(price, output_csv, output_xls,
                     '_current_coins_%s' % (current_date))
    print()

    print('* History price of coins via market_chart')
    price = cp.get_price_hist_marketchart(coin_data, date)
    cp.print_coinpricedata(price)
    cp.write_to_file(price, output_csv, output_xls,
                     '_hist_marketchart_%s' % (date))
    print()


if __name__ == '__main__':
    __main__()
