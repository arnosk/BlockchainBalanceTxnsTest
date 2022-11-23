"""
Created on October 15, 2022

@author: arno

Base Class CoinPrice

"""
from argparse import ArgumentParser
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

import config
import Db
from RequestHelper import RequestHelper


class CoinPrice(ABC):
    """Base class for looking up the price of a coin on an exchange or provider
    """

    def __init__(self) -> None:
        self.req = RequestHelper()

    def show_progress(self, nr: int, total: int):
        """Show progress to standard output
        """
        print("\rRetrieving nr {:3d} of {}".format(
            nr, total), end='', flush=True)
        #sys.stdout.write("Retrieving nr {:3d} of {}\r".format(nr, total))
        # sys.stdout.flush()

    def convert_timestamp_n(self, ts: int, ms: bool=False) -> datetime:
        """Convert timestamp to date string

        ts = timestamp in sec if ms = False
        ts = timestamp in msec if ms = True
        """
        if ms:
            ts = int(ts/1000)
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt

    def convert_timestamp(self, ts, ms=False) -> str:
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
        suffix = re.sub(r'[:;,!@#$%^&*()]', '', suffix)
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


def add_standard_arguments(exchange: str = '') -> ArgumentParser:
    """Add default arguments

    Only used in standalone running from command prompt
    """
    if exchange != '':
        exchange = f' on {exchange}'

    argparser = ArgumentParser()
    argparser.add_argument('-d', '--date', type=str,
                           help=f'Historical date to search{exchange}, format: 2011-11-04T00:05:23+04:00',
                           default='2022-05-01T23:00')
    argparser.add_argument('-c', '--coin', type=str,
                           help=f'List of coins to search{exchange}', required=False)
    argparser.add_argument('-oc', '--output_csv', type=str,
                           help='Filename and path to output CSV file', required=False)
    argparser.add_argument('-ox', '--output_xls', type=str,
                           help='Filename and path to the output Excel file', required=False)
    return argparser
