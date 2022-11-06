"""
Created on Nov 3, 2022

@author: arno

Database Helper Utilities Class

"""
import sqlite3

from Db import Db


class DbSqlite3(Db):
    """SQLite3 database helper class

    constructor:
        config(Dict): Database connection params

    usage:
        # SQlite:
        config = {'dbname':':memory:'}
        db=DbSqllite3(config,'sqlite')

        # Next do sql stuff
        db.open()
        ...
        db.close()
    """

    def create_db(self):
        """Function to create and open a connection to the database
        """
        if not self.conn:
            dbname = self.config['dbname']
            self.conn = sqlite3.connect(dbname, timeout=10)
        else:
            raise RuntimeError('Database connection already exists')

    def open(self):
        """Function to only open a connection to the database
        """
        if not self.conn:
            dbname = self.config['dbname']
            self.conn = sqlite3.connect('file:%s?mode=rw' % dbname, uri=True)
        else:
            raise RuntimeError('Database connection already exists')

    def get_query_check_table(self) -> str:
        """Get the query for check if table exists in database
        """
        return 'SELECT name FROM sqlite_master WHERE type="table" AND name=?'

    def get_execute_result(self, cursor) -> int:
        """Get result from executing a query

        return value = total changes
        """
        return self.conn.total_changes

    def get_create_primary_key_str(self) -> str:
        """Get the string to create a primary key for the specific databse type
        """
        return 'INTEGER PRIMARY KEY AUTOINCREMENT'
