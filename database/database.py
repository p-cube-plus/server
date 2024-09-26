import pymysql
import configparser
from pymysqlpool.pool import Pool
from functools import wraps

config = configparser.ConfigParser()
config.read_file(open('config/config.ini'))

db_config = {
        'host': config['database']['host'],
    'user': config['database']['user'],
    'password': config['database']['password'],
    'db': config['database']['db'],
    'port': int(config['database']['port']),
    'charset': config['database']['charset'],
    'cursorclass': pymysql.cursors.DictCursor,
}

class Database:
    _pool = None

    def __init__(self, use_pool = True):
        if use_pool:
            if Database._pool is None:
                Database._pool = Pool(**db_config)
                Database._pool.init()
            self.conn = Database._pool.get_conn()
        else:
            self.conn = pymysql.connect(**db_config)

        self.use_pool = use_pool
        self.conn.ping(reconnect=True)
        self.conn.commit()
        self.cursor = self.conn.cursor()

    def ping_reconnect(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            self.conn.ping(reconnect=True)
            return func(self, *args, **kwargs)
        return wrapper

    @ping_reconnect
    def execute(self, query, args={}):
        self.cursor.execute(query, args)
        
    @ping_reconnect
    def execute_many(self, query, args=[]):
        self.cursor.executemany(query, args)

    @ping_reconnect
    def execute_one(self, query, args={}):
        self.cursor.execute(query, args)
        row = self.cursor.fetchone()    # fetchone()은 한번 호출에 하나의 Row 만을 가져올 때 사용된다.
        return row

    @ping_reconnect
    def execute_all(self, query, args={}):
        self.cursor.execute(query, args)
        row = self.cursor.fetchall()    # fetchall() 메서드는 모든 데이터를 한꺼번에 가져올 때 사용된다.
        return row

    def commit(self):
        self.conn.commit()

    def close(self):
        if self.use_pool:
            Database._pool.release(self.conn)
        else:
            self.conn.close()