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
import pandas as pd
import cfscrape
import argparse
import sys
import RequestHelper
import DbHelper
from DbHelper import DbType
import config
import os 


def search_id(req: RequestHelper, search_str: str):
    """Search request to Coingecko

    req = instance of RequestHelper
    search_str = string to search in assets
    """
    url = 'https://api.coingecko.com/api/v3/search?query='+search_str
    resp = req.get_request_response(url)
    res_coins = resp['coins']
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


def save_file(req: RequestHelper, url: str, folder: str, filename: str):
    """Download and safe a file from internet
    
    If folder doesn't exists, create the folder

    req = instance of RequestHelper
    url = url to download file
    folder = folder for saving downloaded file
    filename = filename for saving downloaded file
    """
    os.makedirs(folder, exist_ok=True)

    url = url.split('?')[0]
    ext = url.split('.')[-1]
    file = '%s\%s.%s'%(folder, filename, ext)
       
    scraper = cfscrape.create_scraper()
    cfurl = scraper.get(url).content
    
    with open(file, 'wb') as f:
        f.write(cfurl)
        
    """
    r = req.get_request_response(url, downloadFile=True, stream=True)
    if r.ok:
        print('Saving file from url: %s as file: %s'%(url, file))
        with open(file, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 8):
                if chunk:
                    f.write(chunk)
                    f.flush()
                    os.fsync(f.fileno())
    else:  # HTTP status code 4XX/5XX
        print('Download failed: status code {}\n{}'.format(r.status_code, r.text))
    """
    


def insert_coin(req: RequestHelper, db: DbHelper, params: dict):
    """Insert a new coin to the coins table
    
    And download the thumb and large picture of the coin

    req = instance of RequestHelper
    db = instance of DbHelperArko
    params = dictionary with retrieved coin info from coingecko
            {'id': 'dogecoin',
             'name': 'Dogecoin',
             'symbol': 'DOGE',
             'market_cap_rank': 10,
             'thumb': 'https://assets.coingecko.com/coins/images/5/thumb/dogecoin.png',
             'large': 'https://assets.coingecko.com/coins/images/5/large/dogecoin.png'
            }
    """
    save_file(req, params['thumb'], 'CoinImages', 'coingecko_%s_%s'%(params['id'],'thumb'))    
    save_file(req, params['large'], 'CoinImages', 'coingecko_%s_%s'%(params['id'],'large'))    
    query = 'INSERT INTO {} (coingeckoid, name, symbol) ' \
            'VALUES(?,?,?)'.format(db.table['coinCoingecko'])
    args = (params['id'], params['name'], params['symbol'])
    db.execute(query, args)
    db.commit()


def download_images(req: RequestHelper, db: DbHelper):
    """Download image files for all coins in database from Coingecko

    req = instance of RequestHelper
    db = instance of DbHelperArko
    """
    # Get all coingeckoid's from database
    coins = db.query('SELECT coingeckoid FROM {}'.format(db.table['coinCoingecko']))
    coins = [i[0] for i in coins]
    
    # Retrieve coin info from coingecko
    for c in coins:
        url = '''https://api.coingecko.com/api/v3/coins/{}?
                 localization=false&
                 tickers=false&
                 market_data=false&
                 community_data=false&
                 developer_data=false&
                 sparkline=false
              '''.format(c)
        resp = req.get_request_response(url)
        params_image = resp['image']

        # Save image files
        save_file(req, params_image['thumb'], 'CoinImages', 'coingecko_%s_%s'%(c,'thumb'))    
        save_file(req, params_image['small'], 'CoinImages', 'coingecko_%s_%s'%(c,'small'))    
        save_file(req, params_image['large'], 'CoinImages', 'coingecko_%s_%s'%(c,'large'))    


def search(req: RequestHelper, db: DbHelper, coin_search: str):
    """Search coins in own database (if table exists)
    
    Show the results
    
    Search coins from internet (Coingecko)
    Show the results
    
    User can select a row number, from the table of search results
    To add that coin to the coins table, if it doesn't already exists

    req = instance of RequestHelper
    db = instance of DbHelperArko
    coin_search = string to search in assets
    """
    pd.set_option('display.max_colwidth', 20)

    # Check if coin already in database and add to search result on row 0
    db_result = []
    if db.check_table(db.table['coinCoingecko']):
        coin_search_str = '%{}%'.format(coin_search)
        coin_search_query = '''SELECT * FROM {} WHERE
                                coingeckoid like ? or
                                name like ? or
                                symbol like ?
                          '''.format(db.table['coinCoingecko'])
        db_result = db.query(coin_search_query, \
                            (coin_search_str, coin_search_str, coin_search_str))
        if (len(db_result) > 0):
            db_resultdf = pd.DataFrame(db_result)
            print('Search in database:')
            print(db_resultdf)

    # Do search on coingecko
    cg_result = search_id(req, coin_search)
    cg_resultdf = pd.DataFrame(cg_result)
    print('Search from coingecko:')
    print(cg_resultdf)
    
    # ask user which row is the correct answer
    user_input = input_number('Select correct coin to store in database, or (N)ew search, or (Q)uit: ',
                            0, len(cg_result)-1)

    # if coin is selected, add to database (replace or add new row in db?)
    # go back to search question / exit
    if user_input == 'n':
        print('New search')
    elif user_input == 'q':
        sys.exit('Exiting')
    else:
        # coin selected add to
        print('Number chosen = %s'%user_input)
        coin = cg_result[user_input]
        print(coin)

        # check if database exist, in case of sqlite create database
        if not db.has_connection():
            if db.get_db_type() == DbType.sqlite:
                db.open()
            else:
                print('No database %s, do new search'%db.get_db_type())

        # check if coingecko id is already in our database
        if db.has_connection():
            # if table doesn't exist, create table coins
            if not db.check_table(db.table['coinCoingecko']):
                db.create_table(db.table['coinCoingecko'])
                db.chk_table[db.table['coinCoingecko']] = True
            
            db_result = db.query('SELECT * FROM %s WHERE coingeckoid="%s"'%
                                (db.table['coinCoingecko'], coin['id']))
            if len(db_result):
                print('Database already has a row with the coin %s'%(coin['id']))
            else:
                # add new row to table coins
                insert_coin(req, db, coin)


def get_all_assets(req: RequestHelper):
    """Get all assets from Coingecko

    req = instance of RequestHelper
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
    url_list = 'https://api.coingecko.com/api/v3/coins/list?include_platform=true'
    resp = req.get_request_response(url_list)
    assets = resp['result']
    return assets    


def __main__():
    """Get Coingecko search assets and store in databse

    Arguments:
    - coin to search
    - image, save image file for all coins in database
    """
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-c', '--coin', type=str, help='Coin name to search on Coingecko')
    argparser.add_argument('-i', '--image', action='store_true', help='Save image file for all coins in database')
    args = argparser.parse_args()
    coin_search = args.coin

    req = RequestHelper.RequestHelper()
    
    db = DbHelper.DbHelperArko(config.DB_CONFIG, config.DB_TYPE)
    db_exist = db.check_db()
    print('Database exists:', db_exist)
    print('Database exists:', db.has_connection())
    db_table_exist = db.check_db(table_name = db.table['coinCoingecko'])
    print('Table coins exist:', db_table_exist)

    if args.image:
        if db_table_exist:
            download_images(req, db)
        else:
            print('No database, exiting')
    else:
        while True:
            if coin_search == None:
                coin_search = input('Search for coin: ')
            search(req, db, coin_search)
            coin_search = None

if __name__=='__main__':
    __main__()

