"""
Created on Mar 23, 2022

@author: arno

Database Helper Utilities Class

more info: https://github.com/xfoobar/slim_helper/blob/main/slim_helper/db_helper.py
"""
from enum import Enum,auto


class DbType(Enum):
    """Class for enumerating databse types
    
    Possible types:
    SQLite and PostgreSQL
    """
    sqlite = auto()
    postgresql = auto()

    @classmethod
    def has_member(cls, member):
        return member in cls._member_names_


class DbHelper():
    """Class for database actions

    constructor:
        config(Dict): Database connection params
        db_type(str): Database type
    usage:
        # SQlite:
        config = {'dbname':':memory:'}
        db=DbHelper(config,'sqlite')

        # PostgreSQL:
        config={'host':'localhost','port':'5432','dbname':'foobar','user':'foobar','password':'foobar'}
        db=DbHelper(config,'postgresql')

        # Next do sql stuff
        db.open()
        ...
        db.close()

    """

    def __init__(self, config:dict, db_type:str):
        self.conn = None
        self.config = config
        self.chk_table = {}
        db_type = db_type.lower()
        if DbType.has_member(db_type):
            self.db_type = DbType[db_type]
        else:
            raise ValueError('Unknown database type: {}'.format(db_type))

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        if self.conn:
            self.commit()
            self.conn.close()
            self.conn = None

    def open(self, create = True):
        """Function to open a connection to the database

        create = For SQLite: When create is True it creates a new database when it doesnot exists
        """
        if not self.conn:
            if self.db_type == DbType.sqlite:
                import sqlite3
                dbname = self.config['dbname']
                if create:
                    self.conn = sqlite3.connect(dbname, timeout=10)
                    print('Open sqlite3: Database connected %s'%self.conn)
                else:
                    self.conn = sqlite3.connect('file:%s?mode=rw'%dbname, uri=True)
                    print('Open sqlite3: Database connected %s'%self.conn)
                
                
            elif self.db_type == DbType.postgresql:
                import psycopg2
                # In PostgreSQL, default username is 'postgres' and password is 'postgres'.
                # And also there is a default database exist named as 'postgres'.
                # Default host is 'localhost' or '127.0.0.1'
                # And default port is '54322'.
                host = self.config['host']
                port = self.config['port']
                dbname = self.config['dbname']
                user = self.config['user']
                password = self.config['password']
                try:
                    self.conn = psycopg2.connect(
                        host = host,
                        port = port,
                        dbname = dbname,
                        user = user,
                        password = password
                    )
                    print('Open postgresql: Database connected')
                except Exception as e:
                    print('Open postgresql: Database not connected.')
                    print(e)
                    raise ValueError(e)
        else:
            raise RuntimeError('Database connection already exists')


    def check_db(self, table_name: str = None):
        """Check database

        Check wether the database exists and can be found
        If provided with a table_name also check if this table is already created

        table_name = string with a name of a table to check if it iexists in database
                     if None table check is skipped
        """
        check = False

        # check existance of database
        if self.conn is None:
            try:
                self.open(create = False)
            except:
                check = False

        # check existance of table
        if self.conn is not None:
            if table_name is not None:
                if self.db_type == DbType.sqlite:
                    query_chk_table = 'SELECT name FROM sqlite_master WHERE type="table" AND name=?'
                elif self.db_type == DbType.postgresql:
                    query_chk_table = 'SELECT exists(SELECT * FROM information_schema.tables WHERE table_name=?)'

                if self.query(query_chk_table, (table_name,)):
                    # Database exists and table exists
                    check = True
                    print('"{}" table exist'.format(table_name))
                else:
                    print('"{}" table not exist.'.format(table_name))
            else:
                # Database exists and no check on table name
                check = True

        if table_name is not None:
            self.chk_table[table_name] = check

        return check


    def check_table(self, table_name):
        """Check wether the a table exists
        
        Uses a query or a memory field if already queried

        table_name = string with a name of a table to check if it iexists in database
        """
        if table_name in self.chk_table:
            return self.chk_table[table_name]
        else:
            return self.check_db(table_name)
        


    def execute(self, sql: str, params = None) -> int:
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
        if self.db_type == DbType.sqlite:
            result = self.conn.total_changes
        elif self.db_type == DbType.postgresql:
            result = cursor.rowcount
        cursor.close()
        return result

    def query(self, sql: str, params = None):
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

    def get_db_type(self):
        return self.db_type

    def has_connection(self):
        return self.conn != None


class DbHelperArko(DbHelper):
    """Extension of DbHelper

    With special features/functions for Arko program
    """

    def __init__(self, config:dict, db_type:str):
        self.table = {'coinCoingecko':'coinCoingecko',
                      'coinCryptowatch':'coinCryptowatch',
                      'coinAlcor':'coinAlcor'}
        super().__init__(config, db_type)

    def createTable(self, table_name: str):
        """Create a new table

        table_name = table to create
                     (must exist in table list)
        """
        if self.db_type == DbType.postgresql:
            primary_key = 'SERIAL PRIMARY KEY'
        elif self.db_type == DbType.sqlite:
            primary_key = 'INTEGER PRIMARY KEY AUTOINCREMENT'
        else:
            primary_key = 'INT AUTO_INCREMENT PRIMARY KEY'

        query = ''
        if table_name == self.table['coinCoingecko']: 
            query = '''CREATE TABLE {} (
                        id {},
                        coingeckoid VARCHAR(80) NOT NULL,
                        name VARCHAR(80) NOT NULL,
                        symbol VARCHAR(40) NOT NULL
                        )
                    '''.format(table_name, primary_key)
        elif table_name == self.table['coinCryptowatch']: 
            query = '''CREATE TABLE {} (
                        id {},
                        name VARCHAR(80) NOT NULL,
                        symbol VARCHAR(40) NOT NULL
                        )
                    '''.format(table_name, primary_key)
        elif table_name == self.table['coinAlcor']: 
            query = '''CREATE TABLE {} (
                        id {},
                        chain VARCHAR(20) NOT NULL,
                        alcorid INT NOT NULL,
                        base VARCHAR(80) NOT NULL,
                        quote VARCHAR(80) NOT NULL
                        )
                    '''.format(table_name, primary_key)
            
        self.execute(query)


def __main__():
    pass

if __name__=='__main__':
    __main__()
