"""
Created on Mar 23, 2022

@author: arno

Collecting prices

From Cryptowatch
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from tracemalloc import reset_peak

import openpyxl
import pandas as pd
from dateutil import parser

import CoinPrice
import config
from CoinPrice import CoinPrice
from DbHelper import DbHelperArko
from RequestHelper import RequestHelper


class CoinPriceCryptowatch(CoinPrice):
    """Class for retrieving price data of a set of coins on the cryptowatch website
    """

    def __init__(self) -> None:
        super().__init__()

    def show_progress(self, nr: int, total: int):
        """Show progress to standard output on one row
        """
        print('\rRetrieving nr {:3d} of {}'.format(
            nr, total), end='', flush=True)
        #sys.stdout.write('Retrieving nr {:3d} of {}\r'.format(nr, total))
        # sys.stdout.flush()

    def show_allowance(self, allowance):
        """Show allowance data to standard output on same row
        """
        allowance_str = json.dumps(allowance)[1:50]
        print('\r'+allowance_str.rjust(80), end='', flush=True)

    def convert_timestamp(self, ts, ms=False):
        """Convert timestamp to date string

        ts = timestamp in sec if ms = False
        ts = timestamp in msec if ms = True
        """
        if ms:
            ts = int(ts/1000)
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return str(dt)

    def convert_timestamp_lastupdated(self, resp):
        """Convert LastUpdated field in dictonary from timestamp to date

        resp = a list of dictionaries with history data from Coingecko
        """
        key_lastupdated = 'last_updated_at'
        for v in resp.values():
            if isinstance(v, dict):
                if key_lastupdated in v.keys():
                    ts = v[key_lastupdated]
                    v.update(
                        {key_lastupdated: self.convert_timestamp(ts, False)})
        return resp

    def write_to_file(self, df, output_csv: str, output_xls: str, suffix: str):
        """Write a dataframe to a csv file and/or excel file

        df = DataFrame to write to file
        output_csv = base filename for csv output file
        output_xls = base filename for xlsx output file
        suffix = last part of filename

        filename CSV file = config.OUTPUT_PATH+output_csv+suffix.csv
        filename XLS file = config.OUTPUT_PATH+output_xls+suffix.xlsx
        """
        suffix = re.sub('[:;,!@#$%^&*()]', '', suffix)
        outputpath = config.OUTPUT_PATH
        if outputpath != '':
            outputpath = outputpath + '\\'

        if output_csv is not None:
            filepath = Path('%s%s%s.csv' % (outputpath, output_csv, suffix))
            filepath.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(filepath)
            print('File written: %s' % (filepath))

        if output_xls is not None:
            filepath = Path('%s%s%s.xlsx' % (outputpath, output_xls, suffix))
            filepath.parent.mkdir(parents=True, exist_ok=True)
            df.to_excel(filepath)
            print('File written: %s' % (filepath))

    def get_markets(self, req: RequestHelper, coins, curr, strictness=0):
        """Get cryptowatch markets for chosen coins

        req = instance of RequestHelper
        coins = one string or list of strings with assets for market base
        curr = one string or list of strings with assets for market quote
                'coin+curr' = pair of market
        strictness = strictly (0), loose (1) or very loose (2) search for quote

        if coin does not exist as base, try as quote
        """
        if not isinstance(coins, list):
            coins = [coins]
        if not isinstance(curr, list):
            curr = [curr]

        markets = []
        for symbol in coins:
            url = config.CRYPTOWATCH_URL + '/assets/' + symbol
            resp = req.get_request_response(url)

            if resp['status_code'] == 200:
                #             res = resp['result']['markets']['base']
                res = resp['result']['markets']

                # check if base or quote exists in result
                if 'base' in res:
                    res = res['base']
                    for r in res:
                        r['coin'] = symbol
                        r['curr'] = r['pair'].replace(symbol, '')
                elif 'quote' in res:
                    res = res['quote']
                    for r in res:
                        r['curr'] = symbol
                        r['coin'] = r['pair'].replace(symbol, '')
                else:
                    print(
                        'Error, no quote or base in requested market symbol: ', symbol)

                # filter active pairs
                res = list(filter(lambda r: r['active'] == True, res))

                if strictness == 0:
                    # Strict/Exact filter only quote from currencies
                    res_0 = list(filter(lambda r: r['curr'] in curr, res))

                    # check if markets are found, else don't filter
                    if len(res_0) > 0:
                        res = res_0

                if strictness >= 1:
                    # Loose filter only quote from currencies
                    res_filter = []
                    for c in curr:
                        if strictness == 1:
                            # Loose (quote can have 0 or 1 character before and/or after given currency)
                            res_curr = list(filter(lambda r: re.match(
                                '^'+symbol+'\\w?'+c+'\\w?$', r['pair']), res))
                        else:
                            # Very Loose (quote must contain given currency)
                            res_curr = list(
                                filter(lambda r: c in r['curr'], res))
                        res_filter.extend(res_curr)
                    res = res_filter

            else:
                res = [{'active': False,
                        'coin': symbol,
                        'pair': 'error',
                        'curr': 'error',
                        'volume': 'error',
                        'error': resp['error'],
                        'route':''}]

            markets.extend(res)

        return markets

    def get_price(self, req: RequestHelper, markets):
        """Get Cryptowatch current price

        req = instance of RequestHelper
        markets = all market pairs and exchange to get price
        """
        prices = []
        i = 0
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M')
        for market in markets:
            i += 1
            self.show_progress(i, len(markets))

            if not 'error' in market:
                url_list = market['route'] + '/summary'
                resp = req.get_request_response(url_list)

                # check for correct result
                if resp['status_code'] == 'error':
                    # got no status from request, must be an error
                    res_price = resp['error']
                    res_volume = 0
                else:
                    res_price = resp['result']['price']['last']
                    res_volume = resp['result']['volume']

                res = [{'exchange': market['exchange'],
                        'pair':market['pair'],
                        'coin':market['coin'],
                        'curr':market['curr'],
                        'price':res_price,
                        'volume':res_volume,
                        'date':current_date}]

                if 'allowance' in resp:
                    allowance = resp['allowance']
                    self.show_allowance(allowance)

                prices.extend(res)

        return prices

    def get_price_hist_marketchart(self, req: RequestHelper, markets, date):
        """Get coingecko history price of a coin or a token

        coins_contracts can be a list of strings or a single string
        If chain = 'none' or None search for a coins otherwise search for token contracts

        req = instance of RequestHelper
        markets = all market pairs and exchange to get price
        date = historical date 
        """
        # convert date to unix timestamp
        dt = parser.parse(date)  # local time
        # dt = dt.replace(tzinfo=tz.UTC) # set as UTC time
        ts = int(dt.timestamp())

        # make parameters
        params = {}
        params['after'] = ts
        params['before'] = ts
        params['periods'] = 3600

        prices = []
        i = 0
        for market in markets:
            i += 1
            self.show_progress(i, len(markets))

            if not 'error' in market:
                url_list = market['route'] + \
                    '/ohlc?periods=3600&after=%s&before=%s' % (ts, ts)
                url_list = market['route'] + '/ohlc'
                url_list = req.api_url_params(url_list, params)
                resp = req.get_request_response(url_list)
                if resp['status_code'] == 'error':
                    # got no status from request, must be an error
                    res = [{'exchange': market['exchange'],
                            'pair':market['pair'],
                            'coin':market['coin'],
                            'curr':market['curr'],
                            'open':resp['error'],
                            'close':'no data',
                            'volume':'no data',
                            'date':'no data'}]
                else:
                    if len(resp['result']['3600']) > 0:
                        res = [{'exchange': market['exchange'],
                                'pair':market['pair'],
                                'coin':market['coin'],
                                'curr':market['curr'],
                                'open':resp['result']['3600'][0][1],
                                'close':resp['result']['3600'][0][4],
                                'volume':resp['result']['3600'][0][5],
                                'date':self.convert_timestamp(resp['result']['3600'][0][0])}]
                    else:
                        res = [{'exchange': market['exchange'],
                                'pair':market['pair'],
                                'coin':market['coin'],
                                'curr':market['curr'],
                                'open':'no data',
                                'close':'no data',
                                'volume':'no data',
                                'date':'no data'}]
                prices.extend(res)

                if "allowance" in resp:
                    allowance = resp['allowance']
                    self.show_allowance(allowance)

        return prices

    def filter_marketpair_on_volume(self, prices, max_markets_per_pair: int):
        """Filter the price data with same market pair. 

        Only the exchanges with the greatest volume for a market pair will stay

        prices = all prices of market pairs and exchange with volume column
        max_markets_per_pair = maximum rows of the same pair on different exchanges
                            when 0, no filtering will be done and all markets are shown
        """
        # do nothing
        if max_markets_per_pair <= 0 or len(prices) == 0:
            return prices

        # make new dictionary, with pair as key, list of price as value
        price_per_pair = {}
        for price in prices:
            if 'volume' in price:
                pair = price['pair']
                if not pair in price_per_pair.keys():
                    price_per_pair[pair] = []
                price_per_pair[pair].append(price)

        # make new list of prices with max markets per pair
        new_prices = []
        for val_prices in price_per_pair.values():
            # sort list of dictionaries of same pair on volume
            val_prices_sorted = sorted(val_prices,
                                       key=lambda d: -
                                       1 if isinstance(
                                           d['volume'], str) else d['volume'],
                                       reverse=True)

            # get the first x price items
            for i in range(0, min(len(val_prices_sorted), max_markets_per_pair)):
                new_prices.append(val_prices_sorted[i])

        return new_prices


def __main__():
    """Get Cryptowatch price history

    Arguments:
    - date for historical prices
    - coin search prices for specfic coin
    - output file for saving results in a csv file
    - max markets per pair, 0 is no maximum
    """
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-d', '--date', type=str,
                           help='Historical date to search on Cryptowatch, format: 2011-11-04T00:05:23+04:00', 
                           default='2022-05-01T23:00')
    argparser.add_argument('-c', '--coin', type=str,
                           help='List of coins to search on Cryptowatch')
    argparser.add_argument('-oc', '--output_csv', type=str,
                           help='Filename and path to output CSV file', required=False)
    argparser.add_argument('-ox', '--output_xls', type=str,
                           help='Filename and path to the output Excel file', required=False)
    argparser.add_argument('-mp', '--max_markets_per_pair', type=int,
                           help='Maximum markets per pair, 0 is no max', default=1)
    args = argparser.parse_args()
    date = args.date
    coin_str = args.coin
    output_csv = args.output_csv
    output_xls = args.output_xls
    max_markets_per_pair = args.max_markets_per_pair
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M')
    print('Current date:', current_date)

    # init pandas displaying
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_colwidth', 20)
    pd.set_option('display.float_format', '{:.6e}'.format)

    # init session
    cp = CoinPriceCryptowatch()
    db = DbHelperArko(config.DB_CONFIG, config.DB_TYPE)
    req = RequestHelper()
    req.update_header({'X-CW-API-Key': config.CRYPTOWATCH_API})

    # check if database and table coins exists and has values
    db_exist = db.check_db(table_name=db.table['coinCryptowatch'])
    print('Database and table coins exist: %s' % db_exist)

    # Determine which coins to retrieve prices for
    # From arguments, from database, or take default
    if coin_str != None:
        coins = re.split('[;,]', coin_str)
    elif db_exist:
        coins = db.query('SELECT symbol FROM {}'.format(
            db.table['coinCryptowatch']))
        coins = [i[0] for i in coins]
    else:
        coins = ['btc', 'ltc', 'ada', 'sol', 'ardr', 'xpr']

    curr = ['usd', 'btc', 'eth']

    print()
    print('* Available markets of coins')
    markets = cp.get_markets(req, coins, curr, max_markets_per_pair)
    resdf = pd.DataFrame(markets)
    resdf_print = resdf.drop('route', axis=1)
    print(resdf_print)
    print()

    print('* Current price of coins')
    price = cp.get_price(req, markets)
    price = cp.filter_marketpair_on_volume(price, max_markets_per_pair)
    print()
    if len(price) > 0:
        df = pd.DataFrame(price)  # .transpose()
        df = df.sort_values(by=['pair'], key=lambda x: x.str.lower())
        print(df)
        cp.write_to_file(df, output_csv, output_xls,
                         '_current_coins_%s' % (current_date))
    else:
        print('No data')
    print()

    print('* History price of coins via market_chart')
    price = cp.get_price_hist_marketchart(req, markets, date)
    price = cp.filter_marketpair_on_volume(price, max_markets_per_pair)
    print()
    if len(price) > 0:
        df = pd.DataFrame(price)  # .transpose()
        df = df.sort_values(by=['pair'], key=lambda x: x.str.lower())
        print(df)
        cp.write_to_file(df, output_csv, output_xls,
                         '_hist_marketchart_%s' % (date))
    else:
        print('No data')
    print()


if __name__ == '__main__':
    __main__()
