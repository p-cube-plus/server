import pymysql
import configparser
from pymysqlpool.pool import Pool

config = configparser.ConfigParser()
config.read_file(open('config/config.ini'))

class Database:
    _pool = None

    def __init__(self):
        if Database._pool is None:
            Database._pool = Pool(
                host = config['database']['host'],
                user = config['database']['user'],
                password = config['database']['password'],
                db = config['database']['db'],
                port = int(config['database']['port']),
                charset = config['database']['charset'],
                cursorclass=pymysql.cursors.DictCursor,
            )
            Database._pool.init()

        self.conn = Database._pool.get_conn()
        self.conn.commit()
        self.cursor = self.conn.cursor()

    def execute(self, query, args={}):
        self.cursor.execute(query, args)
        
    def execute_many(self, query, args=[]):
        self.cursor.executemany(query, args)

    def execute_one(self, query, args={}):
        self.cursor.execute(query, args)
        row = self.cursor.fetchone()    # fetchone()은 한번 호출에 하나의 Row 만을 가져올 때 사용된다.
        return row

    def execute_all(self, query, args={}):
        self.cursor.execute(query, args)
        row = self.cursor.fetchall()    # fetchall() 메서드는 모든 데이터를 한꺼번에 가져올 때 사용된다.
        return row

    def commit(self):
        self.conn.commit()

    def close(self):
        Database._pool.release(self.conn)