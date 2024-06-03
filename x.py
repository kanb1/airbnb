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
# For my webapp where I'm having user login sessions, caching sensitive information can pose security risks and lead to privacy breaches.
# Nocache for whenever Users expect their actions to reflect immediately, and caching might show them outdated results. For example if a user is submitting a form and wants to see the update dlist immediately (add property, all properties)
# If new properties have been added, the partner needs to see them immediately without waiting for the cache to expire. This ensures they are always aware of the latest listings.
def no_cache():

    # Useful for dynamic content that changes frequently or for security purposes

    # sets the HTTP header to instruct the browser to not cache the content of the response. The content will always be fresh and up to date
    # No cache: tells the browser that it must revalidate the content with the server before using a cached copy. Even if a cached copy exists, the browser must check with the server to see if the cached version is still valid.
    # no-store: instructs the browser and any intermediate caches to not store any part of the response at all. This is the most restrictive directive, ensuring that no copies of the response are kept.
    # must-revalidate: This directive tells caches that they must not use stale responses and must revalidate the content with the server before serving it.
    # Analogy: Think of this as ensuring that every time you open your webapp/or wherever this function is called, you always call the server to check if you need to fetch new data, and you never store data for future use.
    response.add_header("Cache-control", "no-cache, no-store, must-revalidate")

    # Pragma no-cache, This is an older header used for backward compatibility with HTTP/1.0 caches. Like Cache-Control: no-cache, it tells the browser to revalidate with the server before using a cached copy.
    # It tells the browser to revalidate the content with the server before using a cached copy.
    # If my old webapp model only understands a specific command to check with the server before using stored data. Pragma: no-cache is that command for older systems.
    response.add_header("Pragma", "no-cache")
    
    # This header sets the expiration time of the content to a date/time in the past (typically, 0 represents January 1, 1970). This tells the browser that the content is already expired and should not be cached.
    response.add_header("Expires", 0)

    # Cache-Control: Prevents the browser from storing and using cached data without validation.
    # Pragma: Ensures backward compatibility with older HTTP versions for the same purpose.
    # Expires: Forces the browser to consider the content expired immediately, ensuring that it always fetches fresh content from the server.

    # Overall Goal: These headers collectively ensure that the browser (and any intermediate caches) always fetches fresh, up-to-date content from the server and never relies on potentially outdated cached copies.

############################## dict_factory
# Transforming query rows into dictionaries.
# Takes two parameters, cursor and row
# cursor: This is a cursor object that has executed a query and holds metadata about the result set.
# row: This represents a single row of data fetched from the database.

def dict_factory(cursor, row):
    #To extract the names of the columns in the result set.
    # cursor.description is a tuple containing metadata about each column in the result set.
    # [col[0] for col in cursor.description] creates a list comprehension that iterates over each column description tuple and extracts the first element, which is the column name.
    col_names = [col[0] for col in cursor.description]

    # Creating teh dictionary
    # To create a dictionary where each key is a column name and each value is the corresponding value from the row.
    # zip(col_names, row) pairs each column name with its corresponding value from the row. This creates an iterable of tuples where each tuple contains a column name and its corresponding value.
    # {key: value for key, value in zip(col_names, row)} is a dictionary comprehension that iterates over these tuples and constructs a dictionary.
    # Analogy: If you think of a row as a line in a spreadsheet, this step pairs each cell in the row with its header, creating a dictionary where each header (column name) maps to the cell's value.
    return {key: value for key, value in zip(col_names, row)}

    # The dict_factory function transforms a database row into a dictionary where the keys are the column names and the values are the corresponding data from the row. 
    # This is useful for making the row data more accessible and readable when working with the result set of a query.

########################### DB connection 
def get_db_connection():
    # Opens a connection to the SQLite database.
    # pathlib.Path(__file__).parent.resolve(): Gets the absolute path of the directory containing the current file (x.py).
    # str(...) + "/airbnb.db": Constructs the full path to the airbnb.db SQLite database file.
    # sqlite3.connect(...): Connects to the SQLite database at the specified path. The db variable holds the connection object.
    db = sqlite3.connect(str(pathlib.Path(__file__).parent.resolve())+"/airbnb.db")

    # Enables column access by name
    # Sets the row_factory attribute of the database connection to dict_factory.
    # Setting row_factory to dict_factory means that rows returned from queries will be dictionaries where the keys are column names and the values are the column values. This way it's easier to work with. Because in my "/" for example, I can access columns by their column names and retrieve the values from there instead of index-access row[column_name] instead of row[0]
    # I use it in "/" and the pagination route in app.py:
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
        response.status = 500
        return "Database connection failed."
    finally:
        if db:
            db.close()

###################################### VALIDATE SIGN UP

# validate name
USER_NAME_MIN = 2
USER_NAME_MAX = 20
# ^: This asserts the position at the start of the string.
# .: This means it can be any character: match letters, digits, spaces, punctuation marks, and any other character except for the newline character. {2,20}: The preceding character (.) must appear at least 2 times and at most 20 times.
# {2,20}: This is a quantifier that specifies the preceding element (in this case, any character) must occur at least 2 times and at most 20 times.
USER_NAME_REGEX = "^.{2,20}$"

def validate_user_name(user_name):
    error = f"user_name {USER_NAME_MIN} to {USER_NAME_MAX} characters"
    user_name = request.forms.get("user_name", "")
    user_name = user_name.strip()
    if not re.match(USER_NAME_REGEX, user_name): 
        raise Exception(400, error)
    return user_name


# validate lastname
USER_LAST_NAME_MIN = 2
USER_LAST_NAME_MAX = 20
USER_LAST_NAME_REGEX = "^.{2,20}$"

def validate_user_last_name(user_last_name):
    error = f"user_last_name {USER_LAST_NAME_MIN} to {USER_LAST_NAME_MAX} characters"
    user_last_name = request.forms.get("user_last_name", "")
    user_last_name = user_last_name.strip()
    if not re.match(USER_LAST_NAME_REGEX, user_last_name): 
        raise Exception(400, error)
    return user_last_name


# validate username
USER_USER_NAME_MIN = 2
USER_USER_NAME_MAX = 20
USER_USER_NAME_REGEX = "^.{2,20}"

def validate_user_user_name(user_username):
    error = f"user_username {USER_USER_NAME_MIN} to {USER_USER_NAME_MAX} characters"
    user_username = request.forms.get("user_username", "")
    user_username = user_username.strip()
    if not re.match(USER_USER_NAME_REGEX, user_username): 
        raise Exception(400, error)
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
# email_body, the body of the email which is expected to be HTML content
def send_email(to_email, from_email, subject, email_body):

    try:
        # Email message setup:

        # MIMEmultipart() is used to create a new email message that can contain multiple parts (e.g. text and attachments)
        message = MIMEMultipart()
        # Sets the "To", "From" and "Subject" headers of the email message using the respective parameters passed to the function
        message["To"] = to_email
        message["From"] = from_email
        message["Subject"] = subject


        # Email body:

        # Creates a MIMETEXT object that represents the email body as HTML content
        messageText = MIMEText(email_body, 'html')
        # Attaches the MIMEText part to the multipart message
        message.attach(messageText)


        # Email server authentication info
        # load_dotenv() loads environment variables from a .env file into the enviroment
        load_dotenv()
        # retrieve the email user and passworf from the enviroment variables
        email = os.getenv('EMAIL_USER')
        password = os.getenv('EMAIL_PASSWORD')


        # Setup SMTP server:

        # smtplib.SMTP('smtp.gmail.com', 587) creates an SMTP object that represents a connection to the SMTP server at smtp.gmail.com on port 587.
        server = smtplib.SMTP('smtp.gmail.com', 587)
        # sends the EHLO (Extended HELO) command to the SMTP server, which is a greeting and also helps with initiating the TLS connection.
        server.ehlo('Gmail')
        # puts the connection to the SMTP server into TLS (Transport Layer Security) mode, which encrypts the rest of the session.
        server.starttls()
        # server.login(email, password) logs in to the SMTP server using the specified email and password.
        server.login(email, password)


        # Send email:

        # sends the email, message.as_stsirng() converts the MIME multipart message into a string format suitable for sending
        server.sendmail(from_email, to_email, message.as_string())


        # Close SMTP server connection:
        server.quit()

        response.status = 200
        return "Email sent successfully."
    except Exception as ex:
        print(ex)
        response.status = 500
        return "Could not send email."
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
        print("No valid session found")  
        response.status = 401
        return False
    # This block attempts to decode the session data from JSON format to a Python dictionary and assign it to the variable user.
    try:
        user = json.loads(user_session)
        print("Session data found:", user)  # Debug output
        # user.get('role'): Retrieves the value associated with the key 'role' in the user dictionary.
        return user.get('role') == 'customer'
        # This block catches exceptions that occur during JSON decoding.
    except json.JSONDecodeError as e:
        print(f"Error decoding session data: {e}")
        response.status = 500
        return False

###################################### SESSION VALIDATION FOR ROLES - PARTNER 

def validate_partner_logged():
    user_session = request.get_cookie("session", secret=COOKIE_SECRET)
    if not user_session:
        print("No valid session found")
        response.status = 401
        return False
    try:
        user = json.loads(user_session)
        print("Session data found:", user)  # Debug output
        return user.get('role') == 'partner'
    except json.JSONDecodeError as e:
        print(f"Error decoding session data: {e}")
        response.status = 500
        return False

###################################### SESSION VALIDATION FOR ROLES - ADMIN 

def validate_admin_logged():
    user_session = request.get_cookie("session", secret=COOKIE_SECRET)
    if not user_session:
        print("No valid session found")
        response.status = 401
        return False
    try:
        user = json.loads(user_session)
        print("Session data found:", user)  # Debug output
        return user.get('role') == 'admin'
    except json.JSONDecodeError as e:
        print(f"Error decoding session data: {e}")
        response.status = 500
        return False

###################################### VALIDATE NEWLY CREATED ITEMS
ITEM_NAME_REGEX = r'^[a-zA-Z0-9 ]{3,50}$'
ITEM_PRICE_REGEX = r'^\d+(\.\d{1,2})?$'

def validate_item_name(item_name):
    # is item_name empty or if the legnth is less than 3 raise exception
    if not item_name or len(item_name) < 3:
        response.status = 400
        raise ValueError("Invalid item name")
    # if valid, return the name
    return item_name


def validate_item_price(item_price):
    try:
        # convert itemprice to a float
        price = float(item_price)
        # checks if the price is positive
        if price <= 0:
            response.status = 400
            raise ValueError("Price must be positive")
        return price
    except ValueError:
        response.status = 400
        raise ValueError("Invalid price format")

# This function validates the images associated with an item
# current_images: A list of filenames of the images currently associated with the item.
# new_images: A list of new image files being uploaded, defaulting to an empty list if no new images are provided.
def validate_item_images(current_images, new_images = []):
    # total_images purpose: To create a complete list of all images (existing and new).
    # combines current_images and filenames from new_images
    # new_images is a list of new image files being uploaded
    # [img.filename for img in new_images]: This list comprehension iterates over each image file in new_images and extracts its filename. The filename attribute represents the name of the file as provided by the client.
    # current_images + [img.filename for img in new_images]: This concatenates the list of current image filenames with the list of new image filenames to form total_images, a combined list of all image filenames.
    total_images = current_images + [img.filename for img in new_images]
    # checks if the number is between 3 and 6, so if the legnht of the totalimage is less or more than 6
    if len(total_images) < 3 or len(total_images) > 6:
        response.status = 400
        raise ValueError("You should have at least 3 images and a maximum of 6 images.")
    # Validation of image formats to ensure that all new images are in acceptable formats
    # for image in new_images: This loop iterates over each image file in the new_images list.
    for image in new_images:
        # image.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')): This checks if the filename of the image (converted to lowercase) ends with any of the allowed file extensions.
        # lower() makes sure that the check is case-insensitive
        if not image.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            response.status = 400
            raise ValueError("Invalid image format")
    # returns the combined list of all image filenames, both current and new
    return total_images


###################################### GET CURRENT USER_ID from the session (for partner properties)
# This function is used to retrieve the current user's unique identifier (user ID) from the session cookie. This is for more granular checks and actions that are specific ot the individueal user beyond their roles
# This ensures that only the owner of the item (who is a partner) can see the edit and delete options for that item. This is a more specific check than just verifying the role.
# By combining this and the role validation I can enforce both role-based and user-sepcific access controls in my application
# Function to get the current user ID from the session
def get_current_user_id():
    user_session = request.get_cookie("session", secret=COOKIE_SECRET)
    if not user_session:
        response.status = 401
        return None
    try:
        user = json.loads(user_session)
        return user.get('user_id')
    except json.JSONDecodeError as e:
        ic(f"Error decoding session data: {e}")
        response.status = 500
        return None

###################################### GROUP THE IMAGES - NOT USED, USING GROUP CONCAT INSTEAD (TJEK KODEFORKLARING NOTER)

# This function will group the images for each item and return a list of items where each item has a list of its associated images
# Parameter: rows is a list of dictionaries where each dictionary represents a row from a database query. Each row contains information about an item and its associated image url
def group_images(rows):
    # We create an empty dictionary where the keys (item_pk) and the values are dictionaries containing item details and a list of image URLS
    items = {}
    # iterate over each row in the list to extract item details and image URLs
    for row in rows:
        # to extract the primary key of the item from the current row, the item_pk is used as a key in the items dictionary
        item_pk = row['item_pk']
        # To check if the item with the current primary key already exists in the items dictionary.
        if item_pk not in items:
            # If the item does not exist in the dictionary, it means this is the first time we are encountering this item, and we need to initialize its entry.
            # it contains an empty list that will hold the image URLS associated with this item
            # This initialization ensures that each item has a structure to store its details and associated images.
            items[item_pk] = {
                'item_pk': item_pk,
                'item_name': row['item_name'],
                'item_stars': row['item_stars'],
                'item_price_per_night': row['item_price_per_night'],
                'item_images': []
            }
        # Purpose: To add the image URL from the current row to the item's image list.
        # row['image_url'] contains the URL of the image associated with the current row.
        # items[item_pk]['item_images'] is the list of image URLs for the item with the primary key item_pk.
        # .append(row['image_url']) adds the image URL to this list.
        items[item_pk]['item_images'].append(row['image_url'])
    # Purpose: To return a list of item dictionaries with their associated image URLs.
    # items.values() retrieves all the dictionaries stored in the items dictionary.
    # list(items.values()) converts this collection of dictionaries into a list. 
    return list(items.values())

###################################### VALIDATION FUNCTIONS TO CHECK IF THE USER/PROPERTY IS BLOCKED
#VALIDATE IF USER IS BLOCKED
def validate_user_is_not_blocked(user_id):
    conn = get_db_connection()
    try:
        # Fetch the user_isblocked status for the user with the given user_id
        # fetchone() returns the first row of the query result as a dictionary. If no rows are found it returns none
        user_status = conn.execute("SELECT user_is_blocked FROM users WHERE user_pk = ?", (user_id,)).fetchone()
        # if user_status is not noone and if the user_is_blocked field is 1, indicates user is blocked
        if user_status and user_status['user_is_blocked'] == 1:
            response.status = 403
            raise Exception("User is blocked")
    finally:
        conn.close()

#VALIDATE IF PROPERTY IS BLOCKED
def validate_item_is_not_blocked(item_id):
    conn = get_db_connection()
    try:
        item_status = conn.execute("SELECT item_is_blocked FROM items WHERE item_pk = ?", (item_id,)).fetchone()
        if item_status and item_status['item_is_blocked'] == 1:
            response.status = 403
            raise Exception("Item is blocked")
    finally:
        conn.close()







