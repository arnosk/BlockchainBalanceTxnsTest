"""
Created on Mar 23, 2022

@author: arno

Collecting prices

Coingecko
"""
import math
import re
from datetime import datetime

from dateutil import parser

import config
import DbHelper
from CoinData import CoinData, CoinPriceData
from CoinPrice import CoinPrice, add_standard_arguments
from Db import Db
from DbPostgresql import DbPostgresql
from DbSqlite3 import DbSqlite3


class CoinPriceCoingecko(CoinPrice):
    """Class for retrieving price data of a set of coins on the coingecko website
    """

    def __init__(self) -> None:
        self.table_name = DbHelper.DbTableName.coinCoingecko.name
        super().__init__()

    def get_price_current(self, coindata: list[CoinData], currencies: list[str]) -> list[CoinPriceData]:
        """Get coingecko current price

        coins = list of CoinData objects with assets for market base
        curr = one string or list of strings with assets for market quote
        """
        # convert list to comma-separated string
        coins = ','.join(coin.siteid for coin in coindata)
        curr = ','.join(currencies)

        # make parameters
        params = {}
        params['ids'] = coins
        params['vs_currencies'] = curr
        params['include_last_updated_at'] = True

        url = '{}/simple/price'.format(config.COINGECKO_URL)
        url = self.req.api_url_params(url, params)
        resp = self.req.get_request_response(url)

        # remove status_code from dictionary
        resp.pop('status_code')

        # create list of CoinPriceData from respone
        prices: list[CoinPriceData] = []
        for resp_key, resp_val in resp.items():
            for coin in coindata:
                if resp_key == coin.siteid:
                    date = self.convert_timestamp_n(
                        resp_val['last_updated_at'])
                    for currency in currencies:
                        if currency in resp_val:
                            prices.append(CoinPriceData(
                                date=date,
                                coin=coin,
                                curr=currency,
                                price=resp_val[currency]))

        return prices

    def get_price_current_token(self, chain, contracts, curr, **kwargs):
        """Get coingecko current price of a token

        chain = chain where contracts are
        contracts = one string or list of strings with token contracts for market base
        curr = one string or list of strings with assets for market quote
        **kwargs = extra arguments in url 
        """
        # convert list to comma-separated string
        if isinstance(contracts, list):
            contracts = ','.join(contracts)
        if isinstance(curr, list):
            curr = ','.join(curr)

        # make parameters
        kwargs['contract_addresses'] = contracts
        kwargs['vs_currencies'] = curr
        kwargs['include_last_updated_at'] = True

        url = '{}/simple/token_price/{}'.format(config.COINGECKO_URL, chain)
        url = self.req.api_url_params(url, kwargs)
        resp = self.req.get_request_response(url)

        # remove status_code from dictionary
        resp.pop('status_code')

        # convert timestamp to date
        resp = self.convert_timestamp_lastupdated(resp)

        return resp

    def get_price_hist(self, coindata: list[CoinData], currencies: list[str], date: str) -> list[CoinPriceData]:
        """Get coingecko history price

        one price per day, not suitable for tax in Netherlands on 31-12-20xx 23:00
        coins can be a list of strings or a single string
        Thumbnail image is available

        coins = one string or list of strings with assets for market base
        curr = one string or list of strings with assets for market quote
        date = historical date 
        """
        # set date in correct format for url call
        dt = parser.parse(date)
        date = dt.strftime('%d-%m-%Y_%H:%M')

        prices: list[CoinPriceData] = []
        i = 0
        for coin in coindata:
            i += 1
            self.show_progress(i, len(coindata))
            url = '{}/coins/{}/history?date={}&localization=false'.format(
                config.COINGECKO_URL, coin.siteid, date)
            resp = self.req.get_request_response(url)
            market_data_exist = 'market_data' in resp
            #print('coin:', coin)
            #print('price of '+coin+' '+date+': ', resp['market_data']['current_price'][currency],currency)
            #print('MarketCap of '+coin+' '+date+': ', resp['market_data']['market_cap'][currency],currency)

            if resp['status_code'] == 'error':
                # got no status from request, must be an error
                for currency in currencies:
                    prices.append(CoinPriceData(
                        date=dt,
                        coin=coin,
                        curr=currency,
                        price=math.nan,
                        volume=math.nan,
                        error=resp['error']))
            else:
                for currency in currencies:
                    # default values when not found in response
                    price = math.nan
                    volume = math.nan
                    error = 'no data found'

                    # get data from respones
                    if market_data_exist:
                        if currency in resp['market_data']['current_price']:
                            price=resp['market_data']['current_price'][currency]
                            volume=resp['market_data']['total_volume'][currency]
                            error = ''

                    # add CoinPriceData
                    prices.append(CoinPriceData(
                        date=dt,
                        coin=coin,
                        curr=currency,
                        price=price,
                        volume=volume,
                        error=error))

        return prices

    def get_price_hist_marketchart(self, coindata: list[CoinData], currencies: list[str], date: str, chain: str='none') -> list[CoinPriceData]:
        """Get coingecko history price of a coin or a token

        coins_contracts can be a list of strings or a single string
        If chain = 'none' or None search for a coins otherwise search for token contracts

        chain = chain where contracts are or None for coins search
        coins_contracts = one string or list of strings with assets or token contracts for market base
        curr = one string or list of strings with assets for market quote
    >>>           (if list only first currency will be used)
        date = historical date 
        """
        # convert date to unix timestamp
        dt = parser.parse(date)  # local time
        ts = int(dt.timestamp())

        # make parameters
        params = {}
        params['from'] = ts-5*3600
        params['to'] = ts+5*3600

        if (chain is not None):
            chain = chain.lower()

        prices: list[CoinPriceData] = []
        i = 0
        for coin in coindata:
            i += 1
            self.show_progress(i, len(coindata))

            for currency in currencies:
                params['vs_currency'] = currency
                if (chain == '' or chain == 'none' or chain is None):
                    url = '{}/coins/{}/market_chart/range'.format(
                        config.COINGECKO_URL, coin.siteid)
                else:
                    url = '{}/coins/{}/contract/{}/market_chart/range'.format(
                        config.COINGECKO_URL, chain, coin.siteid)
                url = self.req.api_url_params(url, params)
                resp = self.req.get_request_response(url)

                if resp['status_code'] == 'error':
                    # got no status from request, must be an error
                    prices.append(CoinPriceData(
                        date=dt,
                        coin=coin,
                        curr=currency,
                        price=math.nan,
                        volume=math.nan,
                        error=resp['error']))
                else:
                    dt_resp = dt
                    price = math.nan
                    volume = math.nan
                    error = 'no data found'
                    resp_prices = resp['prices']
                    if (len(resp_prices) > 0):

                        # select price index nearest to given datetime
                        time_diff = 10**20
                        resp_price_index = 0
                        index = 0
                        for resp_price in resp_prices:
                            if abs(resp_price[0] - ts*1000) < time_diff:
                                time_diff = abs(resp_price[0] - ts*1000)
                                resp_price_index = index
                            index += 1
                        
                        # get selected data from response
                        dt_resp = self.convert_timestamp_n(resp_prices[resp_price_index][0], True)
                        price = resp_prices[resp_price_index][1]
                        volume = resp['total_volumes'][resp_price_index][1]
                        error = ''
                        
                    prices.append(CoinPriceData(
                        date=dt_resp,
                        coin=coin,
                        curr=currency,
                        price=price,
                        volume=volume,
                        error=error))

        return prices


def __main__():
    """Get Coingecko price history

    Arguments:
    - date for historical prices
    - coin search prices for specfic coin
    - output file for saving results in a csv file
    """
    argparser = add_standard_arguments('Coingecko')
    args = argparser.parse_args()
    date = args.date
    coin_str = args.coin
    output_csv = args.output_csv
    output_xls = args.output_xls
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M')
    print('Current date:', current_date)

    # init session
    cp = CoinPriceCoingecko()
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
        coin_data = [CoinData(siteid=i) for i in coins]
    elif db_table_exist:
        coins = db.query(
            'SELECT siteid, name, symbol FROM {}'.format(cp.table_name))
        coin_data = [CoinData(siteid=i[0], name=i[1], symbol=i[2])
                     for i in coins]
        coins = [i[0] for i in coins]
    else:
        coins = ['bitcoin', 'litecoin', 'cardano', 'solana', 'ardor', 'proton']
        coin_data = [CoinData(siteid=i) for i in coins]

    curr = ['usd', 'eur', 'btc', 'eth']
    chain = 'binance-smart-chain'
    contracts = ['0x62858686119135cc00C4A3102b436a0eB314D402',
                 '0xacfc95585d80ab62f67a14c566c1b7a49fe91167']

    print('* Current price of coins')
    price = cp.get_price_current(coin_data, curr)
    cp.print_coinpricedata(price)
    cp.write_to_file(price, output_csv, output_xls,
                     '_current_coins_%s' % (current_date))
    print()

    print('* History price of coins')
    price = cp.get_price_hist(coin_data, curr, date)
    cp.print_coinpricedata(price)
    cp.write_to_file(price, output_csv, output_xls,
                     '_hist_%s' % (current_date))
    print()

    print('* History price of coins via market_chart')
    price = cp.get_price_hist_marketchart(coin_data, curr, date)
    cp.print_coinpricedata(price)
    cp.write_to_file(price, output_csv, output_xls,
                     '_hist_marketchart_%s' % (current_date))
    print()

    # print('* Current price of token')
    # price = cp.get_price_current_token(chain, contracts, curr)
    # df = pd.DataFrame(price).transpose()
    # df = df.sort_index(key=lambda x: x.str.lower())
    # print()
    # print(df)
    # cp.write_to_file(df, output_csv, output_xls,
    #                  '_current_token_%s' % (current_date))
    # print()

    # print('* History price of token via market_chart')
    # price = cp.get_price_hist_marketchart(chain, contracts, curr[0], date)
    # df = pd.DataFrame(price).transpose()
    # df = df.sort_index(key=lambda x: x.str.lower())
    # print()
    # print(df)
    # cp.write_to_file(df, output_csv, output_xls,
    #                  '_hist_marketchart_token_%s' % (date))
    # print()


if __name__ == '__main__':
    __main__()
