"""
Created on Apr 23, 2022

@author: arno

Cryptowat.ch search

"""
import config
import RequestHelper
import DbHelper
import pandas as pd
import argparse
import sys
import re


def search_id(search_str: str, assets: list):
    """Search for coin in list of all assets

    search_str = string to search in assets
    assets = list of assets from Cryptowatch
    """
    s = search_str.lower()
    res_coins = [item for item in assets \
                if (re.match(s, item['name'].lower()) or \
                    re.match(s, item['symbol'].lower()) )]
    return res_coins


def input_number(message: str, minimal: int = 1, maximum: int = 1):
    """UI for asking row number

    message = string for printing on screen to ask for user input
    minimal = minimal allowed integer
    maximum = maximum allowed integer
    """
    while True:
        user_input = input(message)
        user_input = user_input.lower()
        if (user_input == 'n' or user_input == 'new'):
            user_input = 'n'
        elif (user_input == 'q' or user_input == 'quit'):
            sys.exit('Exiting')
        else:
            try:
                user_input = int(user_input)       
            except ValueError:
                print('No correct input! Try again.')
                continue
            else:
                if (user_input < minimal or user_input > maximum):
                    print('No correct row number! Try again.')
                    continue
        return user_input 
        break


def insert_coin(req: RequestHelper, db: DbHelper, params: dict):
    """Insert a new coin to the coins table
    
    And download the thumb and large picture of the coin

    req = instance of RequestHelper
    db = instance of DbHelperArko
    params = dictionary with retrieved coin info from Cryptowatch
            {'id': 62,
             'symbol': 'doge',
             'name': 'Dogecoin',
             'fiat': False,
             'route': 'https://api.cryptowat.ch/assets/doge'
            }
    """
    print(params)
    #safeFile(req, params['thumb'], 'CoinImages', 'coingecko_%s_%s.png'%(params['id'],'thumb'))    
    #safeFile(req, params['large'], 'CoinImages', 'coingecko_%s_%s.png'%(params['id'],'large'))    
    query = 'INSERT INTO {} (name, symbol) ' \
            'VALUES(?,?)'.format(db.table['coinCryptowatch'])
    args = (params['name'], params['symbol'])
    db.execute(query, args)
    db.commit()


def search(req: RequestHelper, db: DbHelper, coin_search: str, assets: list):
    """Search coins in own database (if table exists)
    
    Show the results
    
    Search coins from Cryptowatch assets (already in assets)
    Show the results
    
    User can select a row number, from the table of search results
    To add that coin to the coins table, if it doesn't already exists

    req = instance of RequestHelper
    db = instance of DbHelperArko
    coin_search = string to search in assets
    assets = list of string with assets from Cryptowatch
    """
    pd.set_option('display.max_colwidth', 20)

    # Check if coin already in database and add to search result on row 0
    db_result = []
    if db.check_table(db.table['coinCryptowatch']):
        coin_search_str = '%{}%'.format(coin_search)
        coin_search_query = '''SELECT * FROM {} WHERE
                                name like ? or
                                symbol like ?
                          '''.format(db.table['coinCryptowatch'])
        db_result = db.query(coin_search_query, \
                            (coin_search_str, coin_search_str))
        if (len(db_result) > 0):
            db_resultdf = pd.DataFrame(db_result)
            print('Search in database:')
            print(db_resultdf)

    # Do search on cryptowatch assets in memory
    cw_result_coin = search_id(coin_search, assets)
    if (len(cw_result_coin) > 0):
        cw_result_coindf = pd.DataFrame(cw_result_coin)
        cw_result_coindf_print = cw_result_coindf.drop('route', axis=1)
        print('Search from cryptowatch:')
        print(cw_result_coindf_print)
    else:
        print('Coin not found')
    
    # ask user which row is the correct answer
    user_input = input_number('Select correct coin to store in database, or (N)ew search, or (Q)uit: ',
                            0, len(cw_result_coin)-1)

    # if coin is selected, add to database (replace or add new row in db?)
    # go back to search question / exit
    if user_input == 'n':
        print('New search')
    elif user_input == 'q':
        sys.exit('Exiting')
    else:
        # coin selected add to
        print('Number chosen = %s'%user_input)
        coin = cw_result_coin[user_input]
        print(coin)

        # check if database exist, in case of sqlite create database
        if not db.has_connection():
            if db.get_db_type() == DbHelper.DbType.sqlite:
                db.open()
            else:
                print('No database %s, do new search'%db.get_db_type())

        # check if coin name, symbol is already in our database
        if db.has_connection():
            # if table doesn't exist, create table coins
            if not db.check_table(db.table['coinCryptowatch']):
                db.create_table(db.table['coinCryptowatch'])
                db.chk_table[db.table['coinCryptowatch']] = True
            
            db_result = db.query('SELECT * FROM %s WHERE name="%s"'%
                                (db.table['coinCryptowatch'], coin['name']))
            if len(db_result):
                print('Database already has a row with the coin %s'%(coin['name']))
            else:
                # add new row to table coins
                insert_coin(req, db, coin)
                

def __main__():
    """Get Cryptowatch search assets and store in database

    Arguments:
    - coin to search
    """
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-c', '--coin', type=str, help='Coin name to search on Coingecko')
    args = argparser.parse_args()
    coin_search = args.coin

    db = DbHelper.DbHelperArko(config.DB_CONFIG, config.DB_TYPE)
    db_exist = db.check_db()
    print('Database exists:', db_exist)
    print('Database exists:', db.has_connection())
    db_table_exist = db.check_db(table_name = db.table['coinCryptowatch'])
    print('Table coins exist:', db_table_exist)

    # init pandas displaying
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_colwidth', 20)
    pd.set_option('display.float_format', '{:.6e}'.format)

    # init request session
    req = RequestHelper.RequestHelper()
    req.update_header({'X-CW-API-Key': config.CRYPTOWATCH_API})

    # get all assets from cryptowatch
    url_list = config.CRYPTOWATCH_URL + '/assets'
    resp = req.get_request_response(url_list)
    coin_assets = resp['result']
    
    while coin_assets != None:
        if coin_search == None:
            coin_search = input('Search for coin: ')
        search(req, db, coin_search, coin_assets)
        coin_search = None


if __name__=='__main__':
    __main__()
