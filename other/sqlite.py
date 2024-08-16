import sqlite3
import datetime
from loguru import logger


class db(object):
    """класс базы данных"""
    def __init__(self):
        self.connection = sqlite3.connect('../ds.sqlite')
        self.cursor = self.connection.cursor()
        self.connection.commit()
        self.check_db()


    def add(self, table, names_value, values):
        self.cursor.execute(f"INSERT INTO {table} ({names_value}) VALUES ({', '.join('?' for i in values)})", values)
        self.connection.commit()

    def get_all(self):
        return self.cursor.execute('SELECT * FROM channels').fetchall()

    def get_one(self, table, value, where='', where_value=[]):
        return self.cursor.execute(f'SELECT {value} FROM {table} {where}', where_value).fetchone()

    def delete(self, id_):
        self.cursor.execute("DELETE FROM channels WHERE auto = ?", [id_])
        self.connection.commit()


    def set(self, table, value, where='', where_value=[]):
        self.cursor.execute(f"UPDATE {table} SET {value} {where}", where_value)
        self.connection.commit()



    def check_db(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS `questions` (
                                increment      INTEGER PRIMARY KEY AUTOINCREMENT,
                                id_            TEXT   UNIQUE ON CONFLICT REPLACE,
                                description    TEXT,
                                prize          TEXT,
                        	    winner         INTEGER,
                        	    hash_answer    TEXT
                            );''')
        self.connection.commit()


