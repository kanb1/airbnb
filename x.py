import sqlite3
from icecream import ic
# Create a Path object for the database, Check if the path exists, Open a connection to the database
import pathlib
from bottle import request, response
# regular expressions. re.match for validation purposes later on.
import re 
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

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

###################################### VALIDATE SIGN UP

# validate name
USER_NAME_MIN = 2
USER_NAME_MAX = 20
USER_NAME_REGEX = "^.{2,20}$"

def validate_user_name(user_name):
    error = f"user_name {USER_NAME_MIN} to {USER_NAME_MAX} characters"
    user_name = request.forms.get("user_name", "")
    user_name = user_name.strip()
    if not re.match(USER_NAME_REGEX, user_name): raise Exception(400, error)
    return user_name


# validate lastname
USER_LAST_NAME_MIN = 2
USER_LAST_NAME_MAX = 20
USER_LAST_NAME_REGEX = "^.{2,20}$"

def validate_user_last_name(user_last_name):
    error = f"user_last_name {USER_LAST_NAME_MIN} to {USER_LAST_NAME_MAX} characters"
    user_last_name = request.forms.get("user_last_name", "")
    user_last_name = user_last_name.strip()
    if not re.match(USER_LAST_NAME_REGEX, user_last_name): raise Exception(400, error)
    return user_last_name


# validate username
USER_USER_NAME_MIN = 2
USER_USER_NAME_MAX = 20
USER_USER_NAME_REGEX = "^.{2,20}"

def validate_user_user_name(user_username):
    error = f"user_username {USER_USER_NAME_MIN} to {USER_USER_NAME_MAX} characters"
    user_username = request.forms.get("user_username", "")
    user_username = user_username.strip()
    if not re.match(USER_USER_NAME_REGEX, user_username): raise Exception(400, error)
    return user_username


# validate email
EMAIL_REGEX = r"^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$"
EMAIL_MAX = 100

def validate_user_email(user_email):
    error = f"Email must be a valid email up to {EMAIL_MAX} characters long"
    email = request.forms.get("user_email", "").strip()
    if not re.match(EMAIL_REGEX, user_email):
        raise Exception(400, error)
    return user_email


# validate password
PASSWORD_MIN = 6
PASSWORD_MAX = 50
PASSWORD_REGEX = r"^.{6,50}$"

def validate_user_password(user_password):
    error = f"Password must be between {PASSWORD_MIN} and {PASSWORD_MAX} characters long"
    password = request.forms.get("user_password", "").strip()
    if not re.match(PASSWORD_REGEX, user_password):
        raise Exception(400, error)
    return user_password

# validate confirmed password
def confirm_user_password(user_password, confirm_password):
    confirm_password = request.forms.get("confirm_password", "").strip()
    if user_password != confirm_password:
        error = "Confirm password does not match the password"
        raise Exception(400, error)
    return confirm_password





###################################### DEFINE EMAIL SENDING FUNCTION

######################################

