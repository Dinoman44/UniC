import sqlite3
from flask import redirect, session, request
from functools import wraps

# connect database with sqlite3
def getConnection(db):
    connection = sqlite3.connect(db, check_same_thread=False)
    return connection


# execute a write query into database
def executeWriteQuery(connection, query, placeholders=()):
    cursor = connection.cursor()
    print(query, placeholders)
    cursor.execute(query, placeholders)
    connection.commit()
    return True


# execute a read query from database
def executeReadQuery(connection, query, placeholders=()):
    cursor = connection.cursor()
    print(query, placeholders)
    cursor.execute(query, placeholders)
    return cursor.fetchall()


# decorates routes to require login
def login_required(f):
    # http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function
