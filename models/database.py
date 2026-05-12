import pymysql
import os

_db = None

def get_db():
    global _db
    if _db is None:
        _db = pymysql.connect(
            host=os.environ.get("MYSQLHOST"),
            port=int(os.environ.get("MYSQLPORT", 3306)),
            user=os.environ.get("MYSQLUSER"),
            password=os.environ.get("MYSQLPASSWORD"),
            database=os.environ.get("MYSQLDATABASE"),
            cursorclass=pymysql.cursors.DictCursor
        )
    return _db

def get_db_connection():
    return get_db()