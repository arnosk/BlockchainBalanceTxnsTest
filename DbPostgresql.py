"""
Created on Nov 3, 2022

@author: arno

Database Helper Utilities Class

"""
import psycopg2

from Db import Db


class DbPostgresql(Db):
    """PostgreSQL database helper class

    constructor:
        config(Dict): Database connection params

    usage:
        # PostgreSQL:
        config={'host':'localhost','port':'5432','dbname':'foobar','user':'foobar','password':'foobar'}
        db=DbPostreSql(config,'postgresql')

        # Next do sql stuff
        db.open()
        ...
        db.close()
    """

    def open(self):
        """Function to open a connection to the database

        In PostgreSQL, default username is 'postgres' and password is 'postgres'.
        And also there is a default database exist named as 'postgres'.
        Default host is 'localhost' or '127.0.0.1'
        And default port is '54322'.
        """
        if not self.conn:
            host = self.config['host']
            port = self.config['port']
            dbname = self.config['dbname']
            user = self.config['user']
            password = self.config['password']
            try:
                self.conn = psycopg2.connect(
                    host=host,
                    port=port,
                    dbname=dbname,
                    user=user,
                    password=password
                )
            except Exception as e:
                print('Open postgresql: Database not connected.')
                print(e)
                raise ValueError(e)
        else:
            raise RuntimeError('Database connection already exists')

    def get_query_check_table(self) -> str:
        """Get the query for check if table exists in database
        """
        return 'SELECT exists(SELECT * FROM information_schema.tables WHERE table_name=?)'

    def get_execute_result(self, cursor) -> int:
        """Get result from executing a query

        return value = rowcount
        """
        return cursor.rowcount

    def get_create_primary_key_str(self) -> str:
        """Get the string to create a primary key for the specific databse type
        """
        return 'SERIAL PRIMARY KEY'
