"""
Created on Aug 31, 2022

@author: arno

Collecting prices

Alcor
"""
import argparse
import copy
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import openpyxl
import pandas as pd
from dateutil import parser

import config
from CoinPrice import CoinPrice
from DbHelper import DbHelperArko
from RequestHelper import RequestHelper


class CoinPriceAlcor(CoinPrice):
    """Class for retrieving price data of a set of coins on the Alcor website
    """

    def __init__(self) -> None:
        super().__init__()

    def show_progress(self, nr: int, total: int):
        """Show progress to standard output
        """
        print('\rRetrieving nr {:3d} of {}'.format(
            nr, total), end='', flush=True)
        #sys.stdout.write('Retrieving nr {:3d} of {}\r'.format(nr, total))
        # sys.stdout.flush()

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

        resp = a list of dictionaries with history data from alcor
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

    def add_coin_symbol(self, db: DbHelperArko, prices: dict):
        """Adds a new column with the symbol name

        Symbol name is retrieved from the database

        db = instance of DbHelperArko
        prices = a dictionary with coin id from Alcor and prices
        """
        coins = db.query(
            'SELECT alcorid, quote FROM {}'.format(db.table['coinAlcor']))
        for price_key, price_val in prices.items():
            print(price_val, price_key)
            if isinstance(price_val, dict):
                for coin_key, coin_val in coins:
                    if price_key == coin_key:
                        price_val['symbol'] = coin_val
            if isinstance(price_val, list):
                for coin_key, coin_val in coins:
                    if price_key == coin_key:
                        price_val.append(coin_val)

        return prices

    def get_price(self, req: RequestHelper, coins, **kwargs):
        """Get alcor current price

        req = instance of RequestHelper
        coins = list of market id and chain
        **kwargs = extra arguments in url 
        """
        # refactor coins list into dict a list of id's (value) per chain (key)
        coin_srch = {}
        for item in coins:
            key_chain = item[0]
            val_coin = item[1]
            coin_srch.setdefault(key_chain, []).append(val_coin)

        # get all market data per chain, and then search through that list for the id's
        prices = {}
        for key_chain, val_coins in coin_srch.items():
            url = config.ALCOR_URL.replace('?', key_chain) + '/markets'
            url = req.api_url_params(url, kwargs)
            resp = req.get_request_response(url)

            # remove status_code from dictionary
            # resp.pop('status_code')

            #res_coins = []
            for item in resp['result']:
                if item['id'] in val_coins:
                    # res_coins.append(item)
                    prices.setdefault(item['quote_token']['str'], []).append(
                        item['last_price'])
                    prices.setdefault(item['quote_token']['str'], []).append(
                        item['base_token']['str'])

            # prices.append(res_coins)

        # convert timestamp to date
        #resp = convert_timestamp_lastupdated(resp)
        return prices

    def get_price_hist_marketchart(self, req: RequestHelper, coins, date):
        """Get alcor history price of a coin via market chart data

        req = instance of RequestHelper
        coins = list of [chain, coinid] with assets or token contracts for market base
        date = historical date 
        """

        # convert date to unix timestamp
        dt = parser.parse(date)  # local time
        ts = int(dt.timestamp())

        # make parameters
        params = {}
        params['resolution'] = 60
        params['from'] = ts  # -3600
        params['to'] = ts  # +3600

        prices = {}
        i = 0
        for coin in coins:
            i += 1
            self.show_progress(i, len(coins))

            url = config.ALCOR_URL.replace(
                '?', coin[0]) + '/markets/{}/charts'.format(coin[1])
            params_try = copy.deepcopy(params)
            nr_try = 1

            # get coin name
            if len(coin) > 2:
                coin_name = coin[2]
                coin_base = coin[3]
            else:
                coin_name = str(coin[1]).zfill(3)
                coin_base = '-'

            # try to get history data from and to specific date
            # increase time range until data is found
            while True:
                url_try = req.api_url_params(url, params_try)
                resp = req.get_request_response(url_try)

                # check for correct res
                if resp['status_code'] == 'error':
                    # got no status from request, must be an error
                    prices[coin_name] = [resp['error'], 0, coin_base]
                    break

                else:
                    res = resp['result']

                    if len(res) > 0:
                        # select res with timestamp nearest to desired date ts
                        res_minimal = {}
                        timediff_minimal = -1
                        for res in res:
                            timediff = abs(ts*1000 - res['time'])
                            if timediff < timediff_minimal or timediff_minimal == -1:
                                # remember record
                                res_minimal = res
                                timediff_minimal = timediff

                        # convert timestamp to date
                        res_minimal['time'] = self.convert_timestamp(
                            res_minimal['time'], True)

                        # take first record?
                        prices[coin_name] = [res_minimal['time'],
                                             res_minimal['open'], coin_base]
                        break

                    elif nr_try > 10:
                        # if too many retries for date ranges, stop
                        prices[coin_name] = ['no data', 0, coin_base]
                        break

                    else:
                        # retry same coin with new date range
                        params_try['from'] -= 2**nr_try * 3600
                        params_try['to'] += 2**nr_try * 3600
                        nr_try += 1

        return prices


def __main__():
    """Get Alcor price history

    Arguments:
    - date for historical prices
    - coin search prices for specfic coin
    - output file for saving ress in a csv file
    """
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-d', '--date', type=str,
                           help='Historical date to search on Alcor, format: 2011-11-04T00:05:23+04:00',
                           default='2022-05-01T23:00')
    argparser.add_argument('-c', '--coin', type=str,
                           help='List of coins to search on Alcor')
    argparser.add_argument('-ch', '--chain', type=str,
                           help='Chain to search on Alcor')
    argparser.add_argument('-oc', '--output_csv', type=str,
                           help='Filename and path to output CSV file', required=False)
    argparser.add_argument('-ox', '--output_xls', type=str,
                           help='Filename and path to the output Excel file', required=False)
    args = argparser.parse_args()
    date = args.date
    coin_str = args.coin
    chain_str = args.chain
    output_csv = args.output_csv
    output_xls = args.output_xls
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M')
    print('Current date:', current_date)

    # init pandas displaying
    pd.set_option('display.max_rows', None)
    pd.set_option('display.float_format', '{:.6e}'.format)

    # init session
    cp = CoinPriceAlcor()
    db = DbHelperArko(config.DB_CONFIG, config.DB_TYPE)
    req = RequestHelper()

    # check if database and table coins exists and has values
    db_exist = db.check_db(table_name=db.table['coinAlcor'])
    print('Database and table coins exist: %s' % db_exist)

    # Determine which coins to retrieve prices for
    # From arguments, from database, or take default
    if coin_str != None:
        coins = re.split('[;,]', coin_str)
        chain = chain_str if chain_str != None else 'proton'
        coins = [[chain, i] for i in coins]
    elif db_exist:
        coins = db.query(
            'SELECT chain, alcorid, quote, base FROM {}'.format(db.table['coinAlcor']))
        coins = [[i[0], i[1], i[2], i[3]] for i in coins]
    else:
        coins = [['proton', 157], ['wax', 158], ['proton', 13], ['wax', 67],
                 ['proton', 5], ['eos', 2], ['telos', 34], ['proton', 96]]

    # For testing
    #coins = [['proton', 157], ['wax', 158], ['proton', 13], ['wax', 67], ['proton', 5], ['eos', 2], ['telos', 34], ['proton', 96]]

    print('* Current price of coins')
    price = cp.get_price(req, coins)
    # if db_exist:
    #    price = _c(db_s price)
    df = pd.DataFrame(price).transpose()
    df = df.sort_index(key=lambda x: x.str.lower())
    print()
    print(df)
    cp.write_to_file(df, output_csv, output_xls,
                     '_current_coins_%s' % (current_date))
    print()

    print('* History price of coins via market_chart')
    price = cp.get_price_hist_marketchart(req, coins, date)
    # if db_exist:
    #    price = _c(db_s price)
    df = pd.DataFrame(price).transpose()
    df = df.sort_index(key=lambda x: x.str.lower())
    print()
    print(df)
    cp.write_to_file(df, output_csv, output_xls,
                     '_hist_marketchart_%s' % (date))
    print()


if __name__ == '__main__':
    __main__()