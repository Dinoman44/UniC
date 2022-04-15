import sqlite3

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

db = getConnection("unic.db")

query = "CREATE TABLE IF NOT EXISTS users (user_id varchar(50) NOT NULL, username varchar(300) NOT NULL, bio varchar(400), email varchar(300) NOT NULL,picture varchar(120) NOT NULL, phone_num varchar(256), latitude DECIMAL(20, 17), longitude DECIMAL(20, 17), location TEXT);"

print(executeWriteQuery(db, query))

query = "CREATE TABLE IF NOT EXISTS listings (listing_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, seller varchar(50) NOT NULL, item_name varchar(100) NOT NULL,description varchar(300) NOT NULL, category varchar(100) NOT NULL, usage varchar(3) NOT NULL, availability BOOL NOT NULL, timestamp varchar(30) NOT NULL);"

print(executeWriteQuery(db, query))

query = "CREATE TABLE IF NOT EXISTS mentors (mentor_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, mentor varchar(50) NOT NULL, description varchar(300) NOT NULL, area varchar(100) NOT NULL);"

print(executeWriteQuery(db, query))

# USERS
# user_id | username | email | picture | phone_num | latitude | longitude | location

# LISTINGS
# listing_id | seller | item_name | description | availability | category | usage

# MENTORS
# mentor_id | mentor | description | area