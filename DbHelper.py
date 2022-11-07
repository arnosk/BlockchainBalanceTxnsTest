"""
Created on Nov 3, 2022

@author: arno

Database Helper function to create tables

"""
from enum import Enum, auto

from Db import Db


class DbTableName(Enum):
    """Class for enumerating table names
    """
    coinCoingecko = auto()
    coinCryptowatch = auto()
    coinAlcor = auto()


def create_table(Db: Db, table_name: str):
    """Create a new table

    table_name = table to create
                    (must exist in table list)
    """
    primary_key = Db.get_create_primary_key_str()
    query = ''
    if table_name == DbTableName.coinCoingecko.name:
        query = '''CREATE TABLE {} (
                    id {},
                    siteid VARCHAR(80) NOT NULL,
                    name VARCHAR(80) NOT NULL,
                    symbol VARCHAR(40) NOT NULL
                    )
                '''.format(table_name, primary_key)
    elif table_name == DbTableName.coinCryptowatch.name:
        query = '''CREATE TABLE {} (
                    id {},
                    siteid VARCHAR(80) NOT NULL,
                    name VARCHAR(80) NOT NULL,
                    symbol VARCHAR(40) NOT NULL
                    )
                '''.format(table_name, primary_key)
    elif table_name == DbTableName.coinAlcor.name:
        query = '''CREATE TABLE {} (
                    id {},
                    chain VARCHAR(20) NOT NULL,
                    siteid INT NOT NULL,
                    base VARCHAR(80) NOT NULL,
                    quote VARCHAR(80) NOT NULL
                    )
                '''.format(table_name, primary_key)

    Db.execute(query)
