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
from CoinData import CoinData, CoinMarketData, CoinPriceData

import config
import DbHelper
from CoinPrice import CoinPrice, add_standard_arguments
from Db import Db
from DbPostgresql import DbPostgresql
from DbSqlite3 import DbSqlite3


class CoinPriceAlcor(CoinPrice):
    """Class for retrieving price data of a set of coins on the Alcor website
    """

    def __init__(self) -> None:
        self.table_name = DbHelper.DbTableName.coinAlcor.name
        self.markets: dict[str, CoinMarketData] = {}
        super().__init__()

    def get_price_current(self, coindata: list[CoinData]) -> list[CoinPriceData]:
        """Get alcor current price

        coins = list of market id and chain
        **kwargs = extra arguments in url 
        """
        # make dict with coins list per chain (key)
        coin_srch: dict[str, list[CoinData]] = {}
        for coin in coindata:
            key_chain = coin.chain
            val_coin = coin
            coin_srch.setdefault(key_chain, []).append(val_coin)

        # get all market data per chain, and then search through that list for the id's
        prices: list[CoinPriceData] = []
        for key_chain, val_coins in coin_srch.items():
            url = config.ALCOR_URL.replace('?', key_chain) + '/markets'
            resp = self.req.get_request_response(url)

            # search through result for coin in the list
            for item in resp['result']:
                for coin in val_coins:
                    if item['id'] == coin.siteid:
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

        coins = list of [chain, coinid] with assets or token contracts for market base
        date = historical date 
        """
        # convert date to unix timestamp
        dt = parser.parse(date)  # local time
        ts = int(dt.timestamp())

        # make parameters
        params = {}
        params['resolution'] = 60
        params['from'] = ts - 3600
        params['to'] = ts + 3600

        prices: list[CoinPriceData] = []
        i = 0
        for coin in coindata:
            i += 1
            self.show_progress(i, len(coindata))

            # get coin base
            coin_base = self.markets[coin.siteid].curr  # curr from previous

            url = config.ALCOR_URL.replace(
                '?', coin.chain) + '/markets/{}/charts'.format(coin.siteid)
            params_try = copy.deepcopy(params)
            nr_try = 1

            # try to get history data from and to specific date
            # increase time range until data is found
            while True:
                url_try = self.req.api_url_params(url, params_try)
                resp = self.req.get_request_response(url_try)

                # check for correct res
                if resp['status_code'] == 'error':
                    # got no status from request, must be an error
                    prices.append(CoinPriceData(
                        date=dt,
                        coin=coin,
                        curr=coin_base,
                        price=math.nan,
                        volume=math.nan,
                        error=resp['error']))
                    break

                else:
                    res = resp['result']

                    if len(res) > 0:
                        # select result with timestamp nearest to desired date ts
                        res_minimal = {}
                        timediff_minimal = 10**20
                        for res in res:
                            timediff = abs(ts*1000 - res['time'])
                            if timediff < timediff_minimal:
                                # remember record
                                res_minimal = res
                                timediff_minimal = timediff

                        # record
                        prices.append(CoinPriceData(
                            date=self.convert_timestamp_n(res_minimal['time'], True),
                            coin=coin,
                            curr=coin_base,
                            price=res_minimal['open'],
                            volume=res_minimal['volume']))
                        break

                    elif nr_try > 10:
                        # if too many retries for date ranges, stop
                        prices.append(CoinPriceData(
                            date=dt,
                            coin=coin,
                            curr=coin_base,
                            price=math.nan,
                            volume=math.nan,
                            error=resp['no data found']))
                        break

                    else:
                        # retry same coin with new date range
                        nr_try += 1
                        params_try['from'] -= 2**(2*nr_try) * 3600
                        params_try['to'] += 2**(2*nr_try) * 3600

        return prices


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
                     '_current_coins_%s' % (current_date))
    print()


if __name__ == '__main__':
    __main__()
