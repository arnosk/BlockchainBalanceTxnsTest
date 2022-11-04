"""
Created on Mar 23, 2022

@author: arno

Collecting prices

Coingecko
"""
import argparse
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


class CoinPriceCoingecko(CoinPrice):
    """Class for retrieving price data of a set of coins on the coingecko website
    """

    def __init__(self) -> None:
        super().__init__()

    def show_progress(self, nr: int, total: int):
        """Show progress to standard output
        """
        print("\rRetrieving nr {:3d} of {}".format(
            nr, total), end='', flush=True)
        #sys.stdout.write("Retrieving nr {:3d} of {}\r".format(nr, total))
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
            print("File written: %s" % (filepath))

        if output_xls is not None:
            filepath = Path('%s%s%s.xlsx' % (outputpath, output_xls, suffix))
            filepath.parent.mkdir(parents=True, exist_ok=True)
            df.to_excel(filepath)
            print("File written: %s" % (filepath))

    def add_coin_symbol(self, db: DbHelperArko, prices: dict):
        """Adds a new column with the symbol name

        Symbol name is retrieved from the database

        db = instance of DbHelperArko
        prices = a dictionary with coin id from coingecko and prices
        """
        coins = db.query("SELECT coingeckoid, symbol FROM {}".format(
            db.table['coinCoingecko']))
        for price_key, price_val in prices.items():
            print(price_val, price_key)
            if isinstance(price_val, dict):
                for coin_key, coin_val in coins:
                    if price_key == coin_key:
                        price_val["symbol"] = coin_val
            if isinstance(price_val, list):
                for coin_key, coin_val in coins:
                    if price_key == coin_key:
                        price_val.append(coin_val)

        return prices

    def get_price_hist(self, req: RequestHelper, coins, curr, date):
        """Get coingecko history price

        one price per day, not suitable for tax in Netherlands on 31-12-20xx 23:00
        coins can be a list of strings or a single string
        Thumbnail image is available

        req = instance of RequestHelper
        coins = one string or list of strings with assets for market base
        curr = one string or list of strings with assets for market quote
        date = historical date 
        """
        if not isinstance(coins, list):
            coins = [coins]
        if not isinstance(curr, list):
            curr = [curr]

        # set date in correct format for url call
        dt = parser.parse(date)
        date = dt.strftime("%d-%m-%Y")

        prices = {}
        i = 0
        for coin in coins:
            i += 1
            self.show_progress(i, len(coins))
            url = "https://api.coingecko.com/api/v3/coins/" + \
                coin+"/history?date="+date+"&localization=false"
            resp = req.get_request_response(url)
            market_data_exist = "market_data" in resp
            #print("coin:", coin)
            #print("price of "+coin+" "+date+": ", resp['market_data']['current_price'][currency],currency)
            #print("MarketCap of "+coin+" "+date+": ", resp['market_data']['market_cap'][currency],currency)
            # init price
            price = {}
            if resp['status_code'] == "error":
                # got no status from request, must be an error
                for c in curr:
                    price[c] = resp['error']
            else:
                price["symbol"] = resp['symbol']
                for c in curr:
                    price[c] = "no data"

                for c in curr:
                    if market_data_exist:
                        if c in resp['market_data']['current_price']:
                            price[c] = resp['market_data']['current_price'][c]

            prices[coin] = price

        return prices

    def get_price(self, req: RequestHelper, coins, curr, **kwargs):
        """Get coingecko current price

        Thumbnail image is available

        req = instance of RequestHelper
        coins = one string or list of strings with assets for market base
        curr = one string or list of strings with assets for market quote
        **kwargs = extra arguments in url 
        """
        # convert list to comma-separated string
        if isinstance(coins, list):
            coins = ','.join(coins)
        if isinstance(curr, list):
            curr = ','.join(curr)

        # make parameters
        kwargs['ids'] = coins
        kwargs['vs_currencies'] = curr
        kwargs['include_last_updated_at'] = True

        url = "https://api.coingecko.com/api/v3/simple/price"
        url = req.api_url_params(url, kwargs)
        resp = req.get_request_response(url)

        # remove status_code from dictionary
        resp.pop("status_code")

        # convert timestamp to date
        resp = self.convert_timestamp_lastupdated(resp)

        return resp

    def get_token_price(self, req: RequestHelper, chain, contracts, curr, **kwargs):
        """Get coingecko current price of a token

        req = instance of RequestHelper
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

        url = "https://api.coingecko.com/api/v3/simple/token_price/"+chain
        url = req.api_url_params(url, kwargs)
        resp = req.get_request_response(url)

        # remove status_code from dictionary
        resp.pop("status_code")

        # convert timestamp to date
        resp = self.convert_timestamp_lastupdated(resp)

        return resp

    def get_price_hist_marketchart(self, req: RequestHelper, chain, coins_contracts, curr, date):
        """Get coingecko history price of a coin or a token

        coins_contracts can be a list of strings or a single string
        If chain = "none" or None search for a coins otherwise search for token contracts

        req = instance of RequestHelper
        chain = chain where contracts are or None for coins search
        coins_contracts = one string or list of strings with assets or token contracts for market base
        curr = one string or list of strings with assets for market quote
    >>>           (if list only first currency will be used)
        date = historical date 
        """
        if not isinstance(coins_contracts, list):
            contracts = [coins_contracts]
        if isinstance(curr, list):
            curr = curr[0]

        # convert date to unix timestamp
        dt = parser.parse(date)  # local time
        ts = int(dt.timestamp())

        # make parameters
        params = {}
        params['vs_currency'] = curr
        params['from'] = ts
        params['to'] = ts+3600

        if (chain is not None):
            chain = chain.lower()

        prices = {}
        i = 0
        for coin_contract in coins_contracts:
            i += 1
            self.show_progress(i, len(coins_contracts))
            if (chain == 'none' or chain is None):
                url = "https://api.coingecko.com/api/v3/coins/" + \
                    coin_contract+"/market_chart/range"
            else:
                url = "https://api.coingecko.com/api/v3/coins/"+chain + \
                    "/contract/"+coin_contract+"/market_chart/range"
            url = req.api_url_params(url, params)
            resp = req.get_request_response(url)

            if resp['status_code'] == "error":
                # got no status from request, must be an error
                prices[coin_contract] = [resp['error'], 0]
            else:
                price = resp['prices']
                if (len(price) > 0):
                    # convert timestamp to date
                    for p in price:
                        p[0] = self.convert_timestamp(p[0], True)

                    prices[coin_contract] = price[0]
                else:
                    # no data, set empty record
                    prices[coin_contract] = ['no data', 0]

        return prices


def __main__():
    """Get Coingecko price history

    Arguments:
    - date for historical prices
    - coin search prices for specfic coin
    - output file for saving results in a csv file
    """
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-d', '--date', type=str,
                           help='Historical date to search on Coingecko, format: 2011-11-04T00:05:23+04:00', 
                           default='2022-05-01T23:00')
    argparser.add_argument('-c', '--coin', type=str,
                           help='List of coins to search on Coingecko')
    argparser.add_argument('-oc', '--output_csv', type=str,
                           help='Filename and path to output CSV file', required=False)
    argparser.add_argument('-ox', '--output_xls', type=str,
                           help='Filename and path to the output Excel file', required=False)
    args = argparser.parse_args()
    date = args.date
    coin_str = args.coin
    output_csv = args.output_csv
    output_xls = args.output_xls
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    print("Current date:", current_date)

    # init pandas displaying
    pd.set_option('display.max_rows', None)
    pd.set_option('display.float_format', '{:.6e}'.format)

    # init session
    cp = CoinPriceCoingecko()
    db = DbHelperArko(config.DB_CONFIG, config.DB_TYPE)
    req = RequestHelper()

    # check if database and table coins exists and has values
    db_exist = db.check_db(table_name=db.table['coinCoingecko'])
    print('Database and table coins exist: %s' % db_exist)

    # Determine which coins to retrieve prices for
    # From arguments, from database, or take default
    if coin_str != None:
        coins = re.split('[;,]', coin_str)
    elif db_exist:
        coins = db.query("SELECT coingeckoid FROM {}".format(
            db.table['coinCoingecko']))
        coins = [i[0] for i in coins]
    else:
        coins = ["bitcoin", "litecoin", "cardano", "solana", "ardor", "proton"]

    curr = ["usd", "eur", "btc", "eth"]
    chain = "binance-smart-chain"
    contracts = ["0x62858686119135cc00C4A3102b436a0eB314D402",
                 "0xacfc95585d80ab62f67a14c566c1b7a49fe91167"]

    print("* Current price of coins")
    price = cp.get_price(req, coins, curr)
    if db_exist:
        price = cp.add_coin_symbol(db, price)
    df = pd.DataFrame(price).transpose()
    df = df.sort_index(key=lambda x: x.str.lower())
    print()
    print(df)
    cp.write_to_file(df, output_csv, output_xls,
                     "_current_coins_%s" % (current_date))
    print()

    print("* History price of coins")
    price = cp.get_price_hist(req, coins, curr, date)
    df = pd.DataFrame(price).transpose()
    df = df.sort_index(key=lambda x: x.str.lower())
    print()
    print(date)
    print(df)
    cp.write_to_file(df, output_csv, output_xls, "_hist_%s" % (date))
    print()

    print("* History price of coins via market_chart")
    price = cp.get_price_hist_marketchart(req, None, coins, curr[0], date)
    if db_exist:
        price = cp.add_coin_symbol(db, price)
    df = pd.DataFrame(price).transpose()
    df = df.sort_index(key=lambda x: x.str.lower())
    print()
    print(df)
    cp.write_to_file(df, output_csv, output_xls,
                     "_hist_marketchart_%s" % (date))
    print()

    print("* Current price of token")
    price = cp.get_token_price(req, chain, contracts, curr)
    df = pd.DataFrame(price).transpose()
    df = df.sort_index(key=lambda x: x.str.lower())
    print()
    print(df)
    cp.write_to_file(df, output_csv, output_xls,
                     "_current_token_%s" % (current_date))
    print()

    print("* History price of token via market_chart")
    price = cp.get_price_hist_marketchart(req, chain, contracts, curr[0], date)
    df = pd.DataFrame(price).transpose()
    df = df.sort_index(key=lambda x: x.str.lower())
    print()
    print(df)
    cp.write_to_file(df, output_csv, output_xls,
                     "_hist_marketchart_token_%s" % (date))
    print()


if __name__ == '__main__':
    __main__()