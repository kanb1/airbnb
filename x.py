import sqlite3
# Create a Path object for the database, Check if the path exists, Open a connection to the database
import pathlib
from bottle import request, response
# regular expressions. re.match for validation purposes later on.
import re 

############################## dict_factory
# Transforming query rows into dictionaries.
def dict_factory(cursor, row):
    # Extracts column names, and creates a list of column names whereas col[0] gives the name of the column from the cursor.description, which is a tuple contianing dtails about each column in the result set of the query
    col_names = [col[0] for col in cursor.description]
    # Creates a dictionary from columns and row data. Each key is a column name and each value is the corresponding value from the current row. zip() pairs each column name with its corresponding value in the row
    return {key: value for key, value in zip(col_names, row)}

# the dict_factory can be directly used in my sqlite connection setup have easy access to row data by column names

########################### DB connection
def get_db_connection():
    db = sqlite3.connect(str(pathlib.Path(__file__).parent.resolve())+"/airbnb.db")
    # Enables column access by name
    db.row_factory = dict_factory
    return db

########################### TEST DB connection
def create_tables():
    db = None
    try:
        db = get_db_connection()
         # cursors are used to execute sql queries and commands on the db, after I prep a sql query like isnert, select osv, I use a cursor to execute this query.
    # basically allows me to manipulate the records of the database and acts like a pointer that lets me execute sql commands and retrieve data!
    # cur = db_conn.cursor()
        cursor = db.cursor()
        print("Creating tables...")
        cursor.execute('''
            DROP TABLE IF EXISTS users;
            CREATE TABLE users(
                user_pk TEXT PRIMARY KEY,
                user_username TEXT,
                user_name TEXT,
                user_last_name TEXT,
                user_email TEXT UNIQUE,
                user_password TEXT,
                user_role TEXT,
                user_created_at INTEGER,
                user_updated_at INTEGER,
                user_is_verified INTEGER,
                user_is_blocked INTEGER
            ) WITHOUT ROWID;
        ''')
        db.commit()
        print("Tables created successfully.")
    except sqlite3.Error as error:
        print(f"Error while creating tables: {error}")
    finally:
        if db:
            db.close()


# test the db connection
def test_db_connection():
    db = None
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT sqlite_version() AS version;")
        result = cursor.fetchone()
        if result:
            # Now accessing using the column name 'version'
            print("SQLite database version:", result['version'])
        else:
            print("No result returned from database version query.")
    except sqlite3.Error as error:
        print("SQLite error:", error)
    finally:
        if db:
            db.close()

########################### 

