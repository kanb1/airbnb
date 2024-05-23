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
import json

COOKIE_SECRET = "97981c49-a651-4d36-9eb5-2b78e0c06c63"
ITEMS_PER_PAGE = 2

###################################### NO CACHE 
def no_cache():
    # sets the HTTP header to instruct the browser to not cache the content of the response

    # This entire string is considered as the value for the Cache-Control header. The commas separate different directives that apply to caching mechanisms.
    # no-cache directs the browser to revalidate with the server before serving the page from the cache
    # no-store tells the browser not to store any version of the response, even in the private cache.
    # must-revalidate tells the browser that it must revalidate with the server before serving this content after it has become stale.
    response.add_header("Cache-control", "no-cache, no-store, must-revalidate")

    # Pragma no-cache, This is an older header used for backward compatibility with HTTP/1.0 caches. Like Cache-Control: no-cache, it tells the browser to revalidate with the server before using a cached copy.

    response.add_header("Pragma", "no-cache")
    
    # This header sets the expiration time of the content to a date/time in the past (typically, 0 represents January 1, 1970). This tells the browser that the content is already expired and should not be cached.
    response.add_header("Expires", 0)

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
def confirm_user_password(user_password, confirmed_password):
    if user_password != confirmed_password:
        error = "Confirm password does not match the password"
        raise Exception(400, error)
    return confirmed_password


###################################### DEFINE EMAIL SENDING FUNCTION
def send_email(to_email, from_email, subject, email_body):

    try:
        # Email message setup:

        # Creates a new multipart email message which can include both text and attachments
        message = MIMEMultipart()
        # Headers of the email = The respective parameters passed to the function
        message["To"] = to_email
        message["From"] = from_email
        message["Subject"] = subject


        # Email body:

        # MIMETEXT can be added to the message, where here it's used to add the email_body as HTML content
        messageText = MIMEText(email_body, 'html')
        # we attach the MIMEText part to the multipart message
        message.attach(messageText)


        # Email server authentication info:
        load_dotenv()
        email = os.getenv('EMAIL_USER')
        password = os.getenv('EMAIL_PASSWORD')


        # Setup SMTP server:

        # Sets up the connection to the SMTP server at the adress and port 
        server = smtplib.SMTP('smtp.gmail.com', 587)
        # sendt the EHLO command to the server, which is a greeting and can also help with initiating the TLS connection
        server.ehlo('Gmail')
        # puts the connection to the SMTP server into TLS mode, which encrupts the rest of the session
        server.starttls()
        # logs in to the SMTP server with the specified credentials
        server.login(email, password)


        # Send email:

        # sends the email, message.as_stsirng() converts the MIME multipart message into a string format suitable for sending
        server.sendmail(from_email, to_email, message.as_string())


        # Close SMTP server connection:
        server.quit()

    except Exception as ex:
        print(ex)
        return "oops couldn't send email"
    finally:
        pass

###################################### SESSION VALIDATION
# This function checks if a user is logged in by validating the session cookie. It can throw an exception if the user is not logged in, which I can catch to handle unauthorized access.
def validate_user_logged():
    user_session = request.get_cookie("session", secret=x.COOKIE_SECRET)
    if not user_session:
        ic("No valid session found")  # Debug output
        raise Exception("User must log in", 401)  # This should handle redirection or error management


###################################### SESSION VALIDATIONS FOR ROLES, USEFUL FOR ROLE ACCESS - CUSTOMER 

def validate_customer_logged():
    user_session = request.get_cookie("session", secret=COOKIE_SECRET)
    if not user_session:
        print("No valid session found")  # Debug output
        return False
    try:
        user = json.loads(user_session)
        print("Session data found:", user)  # Debug output
        return user.get('role') == 'customer'
    except json.JSONDecodeError as e:
        print(f"Error decoding session data: {e}")
        return False

###################################### SESSION VALIDATION FOR ROLES - PARTNER 

def validate_partner_logged():
    user_session = request.get_cookie("session", secret=COOKIE_SECRET)
    if not user_session:
        print("No valid session found")  # Debug output
        return False
    try:
        user = json.loads(user_session)
        print("Session data found:", user)  # Debug output
        return user.get('role') == 'partner'
    except json.JSONDecodeError as e:
        print(f"Error decoding session data: {e}")
        return False

###################################### SESSION VALIDATION FOR ROLES - ADMIN 

def validate_admin_logged():
    user_session = request.get_cookie("session", secret=COOKIE_SECRET)
    if not user_session:
        print("No valid session found")  # Debug output
        return False
    try:
        user = json.loads(user_session)
        print("Session data found:", user)  # Debug output
        return user.get('role') == 'admin'
    except json.JSONDecodeError as e:
        print(f"Error decoding session data: {e}")
        return False

###################################### VALIDATE NEWLY CREATED ITEMS
ITEM_NAME_REGEX = r'^[a-zA-Z0-9 ]{3,50}$'
ITEM_PRICE_REGEX = r'^\d+(\.\d{1,2})?$'

def validate_item_name(item_name):
    if not item_name or len(item_name) < 3:
        raise ValueError("Invalid item name")
    return item_name


def validate_item_price(item_price):
    try:
        price = float(item_price)
        if price <= 0:
            raise ValueError("Price must be positive")
        return price
    except ValueError:
        raise ValueError("Invalid price format")


def validate_item_images(current_images, new_images = []):
    total_images = current_images + [img.filename for img in new_images]
    if len(total_images) < 3 or len(total_images) > 6:
        raise ValueError("You should have at least 3 images and a maximum of 6 images.")
    for image in new_images:
        if not image.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            raise ValueError("Invalid image format")
    return total_images


###################################### GET CURRENT USER_ID from the session (for partner properties)
# Function to get the current user ID from the session
def get_current_user_id():
    user_session = request.get_cookie("session", secret=COOKIE_SECRET)
    if not user_session:
        return None
    try:
        user = json.loads(user_session)
        return user.get('user_id')
    except json.JSONDecodeError as e:
        ic(f"Error decoding session data: {e}")
        return None



###################################### GROUP THE IMAGES
# This function will group the images for each item and return a list of items where each item has a list of its associated images
def group_images(rows):
    items = {}
    for row in rows:
        item_pk = row['item_pk']
        if item_pk not in items:
            items[item_pk] = {
                'item_pk': item_pk,
                'item_name': row['item_name'],
                'item_stars': row['item_stars'],
                'item_price_per_night': row['item_price_per_night'],
                'item_images': []
            }
        items[item_pk]['item_images'].append(row['image_url'])
    return list(items.values())






