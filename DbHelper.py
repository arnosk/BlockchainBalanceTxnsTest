"""
Created on Nov 3, 2022

@author: arno

Database Helper function to create tables

"""
from Db import DbHelper, DbTableName


def create_table(Db: DbHelper, table_name: str):
    """Create a new table

    table_name = table to create
                    (must exist in table list)
    """
    primary_key = Db.get_create_primary_key_str()
    query = ''
    if table_name == DbTableName.coinCoingecko:
        query = '''CREATE TABLE {} (
                    id {},
                    coingeckoid VARCHAR(80) NOT NULL,
                    name VARCHAR(80) NOT NULL,
                    symbol VARCHAR(40) NOT NULL
                    )
                '''.format(table_name, primary_key)
    elif table_name == DbTableName.coinCryptowatch:
        query = '''CREATE TABLE {} (
                    id {},
                    name VARCHAR(80) NOT NULL,
                    symbol VARCHAR(40) NOT NULL
                    )
                '''.format(table_name, primary_key)
    elif table_name == DbTableName.coinAlcor:
        query = '''CREATE TABLE {} (
                    id {},
                    chain VARCHAR(20) NOT NULL,
                    alcorid INT NOT NULL,
                    base VARCHAR(80) NOT NULL,
                    quote VARCHAR(80) NOT NULL
                    )
                '''.format(table_name, primary_key)

    Db.execute(query)
