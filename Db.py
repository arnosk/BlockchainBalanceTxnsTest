"""
Created on Nov 3, 2022

@author: arno

Database Helper Utilities Class

"""
from abc import ABC, abstractmethod


class Db(ABC):
    """Abstract Class for database actions

    constructor:
        config(Dict): Database connection params
    """

    def __init__(self, config: dict):
        self.conn = None
        self.config = config

    def __enter__(self):
        try:
            self.open()
        except:
            self.create_db()
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        if self.conn:
            self.commit()
            self.conn.close()
            self.conn = None

    def create_db(self):
        """Function to create and open a connection to the database

        To be implemented if possible, 
        Otherwise calling this method will result in a runtime error
        """
        raise RuntimeError('Unable to create database in runtime')

    @abstractmethod
    def open(self):
        """Function to open a connection to the database
        """
        pass

    @abstractmethod
    def get_query_check_table(self) -> str:
        """Get the query for check if table exists in database
        """
        pass

    def check_table(self, table_name: str):
        """Check if table exists in database
        """
        check = False
        if self.conn is not None:
            if table_name is not None:
                query_chk_table = self.get_query_check_table()
                if self.query(query_chk_table, (table_name,)):
                    # table exists
                    check = True
                    print('"{}" table exist'.format(table_name))
                else:
                    print('"{}" table not exist.'.format(table_name))
        else:
            raise RuntimeError('Database not connected')
        return check

    def check_db(self):
        """Check wether the database exists and can be opened or created
        """
        check = False
        if self.conn is None:
            try:
                self.open()
            except:
                check = False

        if self.conn is None:
            self.create_db()

        if self.conn is not None:
            # Database exists
            check = True

        return check

    @abstractmethod
    def get_execute_result(self, cursor) -> int:
        """Get result from executing a query

        return value = rowcount or total changes
        """
        pass

    def execute(self, sql: str, params=None) -> int:
        """Execute a query

        Executes a query and returns number of rows or number of changes
        For SQLite cursor.rowcount doesn't exists

        sql = query to execute,
        params = dictionary for parameters in query
        return value = rowcount or total changes
        """
        print('Execute:', sql, params)
        cursor = self.conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        result = self.get_execute_result(cursor)
        cursor.close()
        return result

    def query(self, sql: str, params=None):
        """Execute a query and returns the result

        sql = query to execute,
        params = dictionary for parameters in query
        return value = fetched data from query
        """
        print('Query:', sql, params)
        cursor = self.conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def has_connection(self):
        return self.conn != None

    @abstractmethod
    def get_create_primary_key_str(self) -> str:
        """Get the string to create a primary key for the specific database type

        Normally: primary_key = 'INT AUTO_INCREMENT PRIMARY KEY'
        """
        pass
