'''
Created on Mar 23, 2022

@author: arno

Database Helper Utilities Class

more info: https://github.com/xfoobar/slim_helper/blob/main/slim_helper/db_helper.py

'''
from enum import Enum,auto

class DbType(Enum):
    sqlite = auto()
    postgresql = auto()

    @classmethod
    def hasMember(cls, member):
        return member in cls._member_names_

class DbHelper():
    '''
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

    '''

    def __init__(self, config:dict, db_type:str):
        self.conn = None
        self.config = config
        self.checkTable = {}
        db_type = db_type.lower()
        if DbType.hasMember(db_type):
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
        if not self.conn:
            if self.db_type == DbType.sqlite:
                import sqlite3
                dbname = self.config['dbname']
                if create:
                    self.conn = sqlite3.connect(dbname, timeout=10)
                    print('Open sqlite3: Database connected')
                else:
                    self.conn = sqlite3.connect('file:%s?mode=rw'%dbname, uri=True)
                    print('Open sqlite3: Database not connected.')
                
                
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

    # Check database existence
    # and if set check table existence
    def checkDb(self, table_name: str = None):
        check = False

        # check existance of database
        if self.conn is None:
            try:
                self.open(create = False)
            except:
                check = False

        # check existance of table if there is a connection to database
        if self.conn is not None:
            if table_name is not None:
                if self.db_type == DbType.sqlite:
                    queryCheckTable = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
                elif self.db_type == DbType.postgresql:
                    queryCheckTable = "SELECT exists(SELECT * FROM information_schema.tables WHERE table_name=?)"

                if self.query(queryCheckTable, (table_name,)):
                    # Database exists and table exists
                    check = True
                    print("'{}' table exist".format(table_name))
                else:
                    print("'{}' table not exist.".format(table_name))
            else:
                # Database exists and no check on table name
                check = True

        if table_name is not None:
            self.checkTable[table_name] = check

        return check

    def execute(self, sql: str, params: [] = None) -> int:
        print("Execute:", sql, params)
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

    def query(self, sql: str, params: [] = None) -> []:
        print("Query:", sql, params)
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

    def getDbType(self):
        return self.db_type

    def hasConnection(self):
        return self.conn != None

# Extension of DbHelper for specific Arko program
class DbHelperArko(DbHelper):
    def __init__(self, config:dict, db_type:str):
        super().__init__(config, db_type)

    def createTable(self, table_name: str):
        if self.db_type == DbType.postgresql:
            primarykey = "SERIAL PRIMARY KEY"
        elif self.db_type == DbType.sqlite:
            primarykey = "INTEGER PRIMARY KEY AUTOINCREMENT"
        else:
            primarykey = "INT AUTO_INCREMENT PRIMARY KEY"

        query = '''CREATE TABLE coins (
                    id {},
                    coingeckoid VARCHAR(80),
                    name VARCHAR(80) NOT NULL,
                    symbol VARCHAR(40) NOT NULL
                    )
                '''.format(primarykey)
        self.execute(query)
        

def __main__():
    pass

if __name__=='__main__':
    __main__()
