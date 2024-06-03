from bottle import default_app, get, post, request, response, run, static_file, template, delete, put
from bottle import redirect
import smtplib
import sqlite3
import time
import uuid
import git
import x
import logging
logging.basicConfig(level=logging.DEBUG)
import os
from icecream import ic
import bcrypt
import json
from bottle import json_dumps
import credentials

# Routes for the roles
import routes.customer
import routes.partner
import routes.admin



# Set up basic configuration for logging
logging.basicConfig(level=logging.DEBUG)

############################# Git hook
 
@post('/secret_url_for_git_hook')
def git_update():
  repo = git.Repo('./airbnb')
  origin = repo.remotes.origin
  repo.create_head('main', origin.refs.main).set_tracking_branch(origin.refs.main).checkout()
  origin.pull()
  return ""
 
 
##############################
@get("/app.css")
def _():
    return static_file("app.css", ".")


##############################
@get("/<file_name>.js")
def _(file_name):
    return static_file(file_name+".js", ".")

##############################
@get("/mixhtml.js")
def _():
    return static_file("mixhtml.js", ".")

#############################
@get("/images/<item_splash_image>")
def _(item_splash_image):
    return static_file(item_splash_image, root="images")

#############################
# This defines a route for the root URL (/). 
@get("/")
# When a GET request is made to this URL, the index function is executed.
def index():
    # conn = None initializes the conn variable to None to hold the database connection later.
    # Initializing it to None ensures it exists even if an exception is raised before the connection is established. It was to make sure that I actually got the exception message
    conn = None
    # The try block is used to catch any exceptions that may occur during the execution of the code inside it.
    try:
        # conn = x.get_db_connection() opens a connection to the database using a helper function get_db_connection defined in the x module.
        # The connection object is stored in the variable conn.
        conn = x.get_db_connection()
        
        # Her laver jeg et "request" og bruger methoden get_cookie, som modtager værdien af den specifikke cookie. Session er navnet af cookien
        # Session cookie bruger jeg for at gemme data for den specifikke bruger, for eksempel specifikke request fra den samme bruger. Det kan bruges for for eksempel user preferences.
        # Jeg bruger user_session for at håndtere user sessions

        # COOKIE SECRET USEFUL:
        # secret=x.COOKIE_SECRET: This is an argument passed to get_cookie method saying that the get_cookie method should use a secret key to sign and verify the cookie, so it's authentic and approved. Think of this as the government putting an official stamp on a document to signify that it is authentic and approved.
        # When the client sends the cookie back to the server, the server checks the signature.This is like the government checking the stamp on a document to ensure it's still valid and hasn't been forged or altered.
        # When the clients sens the cookie back to the server, it getting verified (checking the stamp). The server separates the data from the signature and generates a new signature using the COOKIE_SECRET. 
        # Det med at når klienten sender cookie tilbage til serveren så bliver den verificeret ved at når en ny handling sker fra brugeren, så bliver den data seperareret fra signaturen, men den nye handling vil generere en ny signatur som så bliver sammenlignet med vores cookie_secret --> If the new signature matches the original signature, it means the cookie has not been altered and is accepted as valid.

        user_session = request.get_cookie("session", secret=x.COOKIE_SECRET)

        # Vi sætter user_id til none, så user_id har en defineret værdi selvom der ikke er nogen aktiv user-session. We set it to none, so that we show user_id is expected to be set based on the presence of a user session. It signals that user_id will be assigned a value conditionally
        user_id = None
        if user_session:
            # user_session is the result of the previous, where we attempt to retrieve and verify the session cookie
            # json.loads is used to convert the JSON string into a Python dictionary
            user = json.loads(user_session)
            # user now contains: {"user_id": "12345", "role": "customer"}
            # user_id is a variable that will store the ID of the currently logged-in user if the session exists.
            # after the json.loads, user is a dictionary that contains the sessiondata
            user_id = user['user_id']
            # user_id now contains: "12345"
            # WE have just converted the, user-JSONstring into a python dictionary, where we now want to extract the value 'user_id' from our user-dictionary/data
            # By extracting the user_id, the application can know which user is currently logged in. This is useful for personalizing the user experience, accessing user-specific data, and performing actions on behalf of the user.


        # items.*: This part of the query selects all columns from the items table. The * is a wildcard that tells the database to return all columns for each row in the items table. This is done to make sure that all the information about each item (e.g., item_name, item_lat, item_lon, item_stars, etc.) is retrieved.
        # GROUP_CONCAT(items_images.image_url): This is a SQL aggregate function that concatenates values from multiple rows into a single string. Here, it concatenates all image_url values from the items_images table that are associated with each item in the items table.
        # as item_images: This part renames the concatenated result to item_images, making it easier to reference in the code.
        # This is done to collect all image URLs for each item into a single string, which can then be split into a list in the application code. This helps to keep the relationship between items and their images intact and makes it easier to process and display them in the application.
        # FROM items: Specifies the items table as the primary table.
        # LEFT JOIN items_images ON items.item_pk = items_images.item_fk: Joins the items table with the items_images table on the primary key of the items table (item_pk) and the foreign key in the items_images table (item_fk).
        # WHERE items.item_is_blocked = 0: Filters the results to include only items that are not blocked.
        # GROUP BY items.item_pk: Groups the results by each item's primary key, ensuring that each item appears only once in the result set.
        # ORDER BY items.item_created_at DESC: Orders the results by the creation date of the items in descending order, showing the newest items first.
        query = """
        SELECT items.*, GROUP_CONCAT(items_images.image_url) as item_images
        FROM items
        LEFT JOIN items_images ON items.item_pk = items_images.item_fk
        WHERE items.item_is_blocked = 0
        GROUP BY items.item_pk
        ORDER BY items.item_created_at DESC
        """
        # Executes the SQL query and fetches all the results. "items" is now a list of rows, where each row is a dictionary representing an item and its associated images.
        items = conn.execute(query).fetchall()

        # This line converts each row (which is already a dictionary) into a dictionary explicitly. This step is redundant because the rows are already dictionaries (dict_factory and the get_db_connection function already does this), but it ensures that the rows are in the correct format.
        # In summary, by using get_db_connection, which sets db.row_factory = dict_factory, you ensure that every row fetched from the database in your route is a dictionary. This allows you to access columns by name, making your code more readable and maintainable.
        # This line uses a list comprehension to iterate over each item in the items list.
        # dict(item): Converts each row (originally in a special SQLite row format) into a standard Python dictionary.
        # Result: items_dict is now a list of dictionaries, making it easier to manipulate and work with in Python.
        items_dict = [dict(item) for item in items]
        # Iterates over each item in items_dict.
        for item in items_dict:
            # if item['item_images']: Checks if the item_images field is not empty.
            if item['item_images']:
                # item['item_images']: Accesses the item_images field of the current item.
                # item['item_images'].split(','): Splits the concatenated string of image URLs (separated by commas) into a list.
                # .split(','): Splits the string at each comma, resulting in a list of image URLs.
                # The resulting list is then assigned back to item['item_images'].
                item['item_images'] = item['item_images'].split(',')
                # The reason why we split the concatenated string into a list for each item is to make ti easier for me to hadnle and display multiple images associated with each item. In my database each item can have multiple associated iamges and they are stored in a seperate table items_images and linked tot he items by a foreign key. To retrieve items and their images from the database I use the GROUP CONCAT to combine all the image URLS for each item into a single comma-separated string. This is better when I want to pass data to my templates it's more convenient to wrok with lists of iamge URLS rather than single concatenated string. For example if I want to display all images of an item, having a list allows me to easily iterate over each image url.

        # Purpose: Converts the items_dict list of dictionaries into a JSON string. This JSON string can be easily used in my template or passed to JavaScript for client-side processing.
        items_json = json.dumps(items_dict)

        # Purpose: Selects the first few items to be displayed initially. Function: slicing the list
        # items_dict[:x.ITEMS_PER_PAGE]
        # x.ITEMS_PER_PAGE is a constant that defines how many items to display per page. (in my x module it's 2)
        # items_dict[:x.ITEMS_PER_PAGE] slices the items_dict list to get only the first ITEMS_PER_PAGE items.
        initial_items = items_dict[:x.ITEMS_PER_PAGE]
        # So my intial_items list will look like this: initial_items = [{"item_pk": "1", "item_name": "Example Item 1", "item_images": ["image1.jpg", "image2.jpg"]}, {"item_pk": "2", "item_name": "Example Item 2", "item_images": ["image3.jpg", "image4.jpg"]}]

        # Debugging line
        print("Items JSON:", items_json)  

        # items_json=items_json: Passes the JSON string of all items to the template.
        # items=initial_items: Passes the list of initial items to display to the template.
        # mapbox_token=credentials.mapbox_token: Passes the Mapbox token (for rendering maps) to the template.
        # json=json: Passes the json module to the template (useful for JavaScript within the template).
        return template("index.html", items_json=items_json, items=initial_items, mapbox_token=credentials.mapbox_token, json=json)
    except Exception as ex:
        ic(ex)
        response.status = 500
        return "An error occurred while fetching items."
    finally:
        if conn:
            conn.close()





############################# This route handles requests to get items for a specific page number.
# URL Parameter: <page_number> is a dynamic parameter in the URL that specifies which page of items to retrieve.
# Even though there's only one page visually on your website, the "Load More" button allows you to load more items in increments, which conceptually works like paginating through pages.

# In the sense of my code, the page number is used to calculate which items to load next. It's a way to keep track of how many times the user has clicked the "Load More" button to fetch the next set of items.
# When the page first loads, it fetches and displays the first set of items (e.g., the first 10 items). This is considered page 1. The initial items are loaded with this part of the index route: initial_items = items_dict[:x.ITEMS_PER_PAGE]
# When the user clicks the "Load More" button, it sends a request to the server for the next set of items.
# The request includes the next page number as part of the URL, e.g., /items/page/2 for the second set of items.
# This is handled by the get_items_page route below. This route handles fetching the next set of items when the "Load More" button is clicked.
@get("/items/page/<page_number>")
def get_items_page(page_number):
    try:
        conn = x.get_db_connection()
        # The get_items_page function calculates the offset based on the page number:
        # The page_number comes from the URL as a string (e.g., "1", "2", "3").
        # If the page number is 2, the offset is (2 - 1) * 10 = 10, meaning the server will skip the first 10 items and load the next set of items.
        # The server responds with the next set of items and the client updates the page to show these new items without reloading the entire page.
        # The server also updates the "Load More" button to fetch the next page (e.g., page 3).
        # int(page_number) converts this string into an integer so we can do arithmetic with it.
        # offset: Calculates how many items to skip in the database query.
        offset = (int(page_number) - 1) * x.ITEMS_PER_PAGE


        # GROUP CONCAT: Concatenates all image_url values from the items_images table into a single string, separated by commas. This concatenated string is given the alias item_images.

        # LEFT JOIN: ON items.item_pk = items_images.item_fk: Specifies the join condition where item_pk from the items table matches item_fk from the items_images table.

        # ON items.item_pk = items_images.item_fk: Specifies the condition for the join. If an item does not have any images, it will still be included in the result with item_images being NULL.

        # LIMIT ? OFFSET ?: Fetches a limited number of items based on the page number and offset. The question marks (?) are placeholders for parameters that will be supplied later.
        

        query = """
        SELECT items.*, GROUP_CONCAT(items_images.image_url) as item_images
        FROM items
        LEFT JOIN items_images ON items.item_pk = items_images.item_fk
        WHERE items.item_is_blocked = 0
        GROUP BY items.item_pk
        ORDER BY items.item_created_at DESC
        LIMIT ? OFFSET ?
        """

        # (x.ITEMS_PER_PAGE, offset): A tuple of parameters that replaces the placeholders (?) in the SQL query. The first parameter is the number of items to fetch, and the second parameter is the offset telling how many to skip.
        # So the executing will run like: Initial load, First button load = This returns the first 2 items., SEcond load = This skips the first 2 items and returns the next two, Third load = Skips the first 4 items and returns the next 2
        # fetchall():Retrieves all the rows resulting from the query execution. This will be a list of tuples, each tuple representing a row from the items table.
        items = conn.execute(query, (x.ITEMS_PER_PAGE, offset)).fetchall()
        # Converts each row from the query result into a dictionary. This allows for easier access to the columns by their names.
        items_dict = [dict(item) for item in items]
        # Iterates through each item (dictionary) in the items_dict list.
        for item in items_dict:
            # Checks if the item_images field is not empty or null.
            if item['item_images']:
                # Splits the concatenated image URLs (which are in a single string) into a list of individual image URLs. This makes it easier to work with multiple images for each item.
                item['item_images'] = item['item_images'].split(',')

        # Converts the items_dict list of dictionaries into a JSON string. This is useful for sending the data to the front-end, where it can be parsed and used by JavaScript.
        items_json = json.dumps(items_dict)

        # To generate the HTML content for each item dynamically.
        # items_dict is assumed to be a list of dictionaries, where each dictionary represents an item with its details
        # For each item in items_dict, the template function is called with two arguments: item.html template and the item, so each item is passed as an item variable to the template
        # The "".join()) part takes the list of HTML strings produced by the list comprehension and concatenates them into a single string.
        # The purpose of this line is to generate a single HTML string that includes the rendered HTML for each item in items_dict. Each item is processed with the _item.html template, and the results are concatenated together.

        # Iterates over each item in items_dict.
        # Renders the _item.html template with the current item as context.
        # Collects the rendered HTML strings into a list.
        # Joins the list into a single HTML string = it joins the items in the _item.html where we render the {% for image in item['item_images'] %}<img src="/images/{{image}}" alt="Item image">{% endfor %}
        html = "".join([template("_item.html", item=item) for item in items_dict])

        # This line generates the HTML for the "More" button.
        # If the number of items fetched equals x.ITEMS_PER_PAGE, it means there might be more items to load, so the "More" button is created with the next page number.
        # If fewer items are fetched, it means there are no more items to load, so the "More" button is not created.
        btn_more = template("__btn_more.html", page_number=int(page_number) + 1) if len(items) == x.ITEMS_PER_PAGE else ""

        response.status = 200

        # <template mix-function="addMarkers">{items_json}</template>: Calls a JavaScript function addMarkers with the new items' JSON data to update the map markers.
        # appends the new items to the element with id items (index.hmtl)
        # replace the more button with the updated one (it doesn't create it if there isn't more items to fetch)
        return f"""
        <template mix-target="#items" mix-bottom>
            {html}
        </template>
        <template mix-target="#more" mix-replace>
            {btn_more}
        </template>
        <template mix-function="addMarkers">{items_json}</template>
        """
    except Exception as ex:
        ic(ex)
        return "An error occurred while fetching more items."
    finally:
        if conn:
            conn.close()




##############################TEST database connection
@get("/test-db-connection")
def test_db_connection_route():
    try:
        x.test_db_connection()
        response.status = 200
        return "Database connection OK"
    except Exception as ex:
        response.status = 500
        return f"Database connection failed"

##############################
@get("/signup")
def signup():
  return template("signup.html")

##############################
@post("/signup")
def do_signup():
    db = None
    try:
        print(request.forms)
        # Retrieves form data from the request. If a form field is missing, it returns an empty string.
        # .strip(): Removes any leading or trailing whitespace from the form data.
        user_username = request.forms.get('user_username', '').strip()
        user_email = request.forms.get('user_email', '').strip()
        user_password = request.forms.get('user_password', '').strip()
        confirmed_password = request.forms.get('confirmed_password', '').strip()
        user_name = request.forms.get('user_name', '').strip()
        user_last_name = request.forms.get('user_last_name', '').strip()
        user_role = request.forms.get('user_role', '').strip()

        print("Password:", user_password)
        print("Confirmed Password:", confirmed_password)

        if user_password != confirmed_password:
            response.status = 400
            return "Passwords do not match."  

        # Validate the inputs
        validated_username = x.validate_user_user_name(user_username)
        validated_email = x.validate_user_email(user_email)
        validated_password = x.validate_user_password(user_password)
        x.confirm_user_password(validated_password, confirmed_password)
        validated_first_name = x.validate_user_name(user_name)
        validated_last_name = x.validate_user_last_name(user_last_name)


        # I'm hashing the password here using bcrypt.hashpw, first I encode the password to bytes because bcrypt works on bytes and not text strings as we get it. The bcrypt.hashpw then hashes the password. The bcrypt.gensalt makes the random password
        hashed_password = bcrypt.hashpw(user_password.encode('utf-8'), bcrypt.gensalt())

        # Prepare data for database entry
        # Gets the current time as an integer timestamp
        current_timestamp = int(time.time())
        # Generates a unique veriifcation key for email verification
        verification_key = uuid.uuid4().hex
        # Generates a unique primary key for the user
        user_pk = str(uuid.uuid4())

        db = x.get_db_connection()
        sql = """
            INSERT INTO users (
                user_pk, user_username, user_name, user_last_name, user_email,
                user_password, user_role, user_created_at, user_updated_at,
                user_is_verified, user_is_blocked, user_verification_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        # prepares the parameters to be used in the sql command
        params = (user_pk, validated_username, validated_first_name, validated_last_name, validated_email, hashed_password, user_role, current_timestamp, current_timestamp, 0, 0, verification_key)

        # Execute the SQL command
        db.execute(sql, params)
        db.commit()

        # Send verification email with a unique verification link. It calls a function from the module x to send the email.
        x.send_email(user_email, "your-email@example.com", "Verify your account", template('email_verification', key=verification_key))

        response.status = 201

        return "Signup successful! Please check your email to verify your account."

    except sqlite3.IntegrityError as e:
        response.status = 400
        return f"Integrity Error. User already exists: {str(e)}"
    except Exception as ex:
        response.status = 500
        logging.error(f"An error occurred: {ex}")
        return "An internal server error occurred."
    finally:
        if db:
            db.close()
  
############################## CHECK USERS IN DB
@get('/users')
def get_all_user_username():
    db = x.get_db_connection()
    try:
        db.row_factory = sqlite3.Row  # This allows access to data by column name
        cur = db.cursor()
        cur.execute('SELECT user_username FROM users')  # Query to fetch only user_pk
        user_pks = cur.fetchall()  # Fetch all results

        # Convert results to a list of user_pk values
        user_pk_list = [row['user_username'] for row in user_pks]
        response.content_type = 'application/json'
        response.status = 200
        return {'user_usernames': user_pk_list}

    except Exception as e:
        response.status = 500  # Internal Server Error
        return {'error': str(e)}
    finally:
        if db:
            db.close()

##############################
# The <key> part is a URL parameter that will be passed to the verify function and it's the verification key
# When a GET request is made to /verify/some_key_value, this function will be called with some_key_value passed as the key argument.
@get("/verify/<key>")
def verify(key):
    try:
        # get_db_connection() returns a connection to the database
        db = x.get_db_connection()
        # Creates a cursor object using the database connection. The cursor allows executing SQL commands and fetching data from the database.
        cursor = db.cursor()
        # One of the cursor methods: execute()
        # Check if the key exists and get the user_pk
        cursor.execute("SELECT user_pk FROM users WHERE user_verification_key = ?", (key,))
        # cursor method --> fetchone(), fetches a single row
        user = cursor.fetchone()

        if user:
            # Update the user_is_verified to 1 for the user with the given verification key
            cursor.execute("UPDATE users SET user_is_verified = 1 WHERE user_verification_key = ?", (key,))
            db.commit()
            response.status = 200

            return f"Account with key {key} is verified successfully"
            # return redirect("/verified-message")
            
        else:
            response.status = 400
            return "Verification failed: Invalid key."

    except Exception as ex:
        response.status = 500
        print(ex)

    finally:
        if db:
            db.close()

############################## 
# @get("/verified-message")
# def _():
#     try:
#         return template("account_verified_message.html")
#     except Exception as ex:
#         ic(ex)
#         print(ex)
#         return "An error occurred while loading the verification message template."
#     finally:
#         pass


############################## 
@get("/login")
def login():
    return template("login.html")

############################## 
@post("/login")
def _():
    try:
        email = request.forms.get('user_email')
        password = request.forms.get('user_password')
        ic(email, password)  # Debugging output

        db = x.get_db_connection()
        cursor = db.cursor()
        # Selects all the columns from the users table where the user_email matches the submitted email
        cursor.execute("SELECT * FROM users WHERE user_email = ?", (email,))
        # The result is fetched as sa single row and stored in the user variable
        user = cursor.fetchone()
        print(user)

        if user:
            # Check if the account is marked as deleted
            if user['user_is_deleted'] == 1:
                response.status = 403
                return "This account has been deleted."

            # Check if the account is blocked
            try:
                # Checks if the user is blocked, the validation function
                x.validate_user_is_not_blocked(user['user_pk'])
            except Exception as ex:
                ic(ex)
                response.status = 403
                return "Your account is blocked by the admin"

            # Retrieves the stored hashed password 
            stored_hash = user['user_password']
            ic(user)

            # Only encode the password from the form
            # Uses the bcrypt.checkpw to compare the submitted password (encoded to bytes) with the stored hashed password. If the passwords match:
            if bcrypt.checkpw(password.encode(), stored_hash):
                ic("Password correct")  # Confirm password match
                
                # pop removes the user_password key from the user dictionary for security reasons. It ensures the password hash is not stored in the session data
                user.pop('user_password', None) # Using pop with None ensures no error if the key doesn't exist
                # shows that user_password is not showing
                ic(user)

                if user['user_is_verified'] == 1:
                    # I create a session object that includes those user identifiers:
                    session_data = {'user_id': user['user_pk'], 'role': user['user_role']}
                    # then serializes it to a JSON string.
                    session_data_serialized = json.dumps(session_data)
                    #then I later in the response.set_cookie send that session key with userdata to the client:

                    #Determines whether the application is running in production mode. If so, sets the cookie to be sent only over HTTPS
                    try:
                        import production
                        is_cookie_https = True
                    except ImportError:
                        is_cookie_https = False

                    #Setting a secure session cookie if the login is successful.
                    # If the account is verified, creates a session object containing the user ID and role , serializes it to a JSON string^, and sets it as a secure, HTTP-only cookie below.
                    
                    # session: Name of the cookie.
                    # session_data_serialized: Value of the cookie (the serialized session data).
                    # secret=x.COOKIE_SECRET: Secret key to sign the cookie, ensuring its integrity.
                    # httponly=True: Prevents client-side scripts from accessing the cookie.
                    # secure=is_cookie_https: Ensures the cookie is sent only over HTTPS if in production mode.
                    response.set_cookie("session", session_data_serialized, secret=x.COOKIE_SECRET, httponly=True, secure=is_cookie_https)
                    ic("Session set, redirecting...")
                    
                    # For security. Caching can be a security risk. If a cached version of a page is store don a shared computer, another user might see sensitive information
                    x.no_cache()
                    
                    response.status = 200

                    # Redirects the user to the respective dashboard based on their role
                    return f"""
                    <template mix-redirect="/{user['user_role']}-dashboard">
                        </template>
                    """
                else:
                    response.status = 401
                    return "Please verify your account"
            else:
                response.status = 401
                return "Password invalid"
        else:
            response.status = 404
            return "User is not found"

    except Exception as ex:
        ic("Login error:", ex)
        print(f"An error occurred: {str(ex)}")
        print(f"Exception type: {type(ex).__name__}, Exception args: {ex.args}")
        response.status = 500
        return "Problems logging in."
        
    finally:
        if "db" in locals():
            db.close()


############################## CUSTOMER DASHBOARD
@get("/customer-dashboard")
def customer_dashboard():
    x.no_cache()
    user_session = request.get_cookie("session", secret=x.COOKIE_SECRET)
    if user_session and json.loads(user_session).get('role') == 'customer':
        response.status = 200
        return template('customer_dashboard.html')
    else:
        # også ift no_cache, så redirecter den til denne her side, da det er /customer-dashboard der bliver kaldt under login (og admin/partner hvis det er de)
        response.status = 401
        return redirect("/login")

############################## ADMIN DASHBOARD
# @get("/admin-dashboard")
# def admin_dashboard():
#     x.no_cache()
#     user_session = request.get_cookie("session", secret=x.COOKIE_SECRET)
#     if user_session and json.loads(user_session).get('role') == 'admin':
#         return template('admin_dashboard.html')
#     else:
#         return redirect("/login")

############################## PARTNER DASHBOARD
@get("/partner-dashboard")
def partner_dashboard():
    # CACHING:
    # If new properties have been added, the partner needs to see them immediately without waiting for the cache to expire. This ensures they are always aware of the latest listings.
    # If any property details have been updated (e.g., price changes, availability), the partner dashboard should reflect these changes immediately.
    # The partner dashboard might include user-specific information, such as recent activities, messages, or notifications. This information should always be current.
    # By not caching the dashboard, you ensure that session data is always verified in real-time. This helps in maintaining security, as it checks the session validity each time the dashboard is accessed.
    x.no_cache()
    user_session = request.get_cookie("session", secret=x.COOKIE_SECRET)
    if user_session and json.loads(user_session).get('role') == 'partner':
        response.status = 200
        return template('partner_dashboard.html')
    else:
        response.status = 401
        return redirect("/login")

############################## LOGOUT
@get('/logout')
def logout():
    try:
        response.delete_cookie("session", secret=x.COOKIE_SECRET)  # Delete the session cookie
        response.status = 200

    except Exception as ex:
        print(ex)
        response.status = 500

        return "Error logging out."
    finally:
        return redirect("/")

############################## GET FORGOT PASSWORD FORM
@get('/forgot-password')
def _():

    try:
        response.status = 200
        # <form action="/reset-password-request" method="post" id="resetForm">: Defines a form that will submit a POST request to /reset-password-request.
        # Replacer loginform med denne her resetform, den har også fået id resetForm
        return f"""
            <template mix-target="#loginForm" mix-replace>
                <form action="/reset-password-request" method="post" id="resetForm">
                    <div class="form-group">
                        <label for="reset_email">Email:</label><br>
                        <input type="email" id="reset_email" name="reset_email" required placeholder="Enter your email to reset password"><br><br>
                    </div>
                    <button type="submit" class="bg-slate-400" mix-post="/reset-password-request" mix-data="#resetForm" mix-default="Reset Password" mix-await="Sending reset link...">Send Reset Link
                    </button>
                </form>
            </template>
        """
    except Exception as ex:
        print(ex)
        response.status = 500
        return "Can't get template"
    finally:
        pass


############################## HANDLE PASSWORD RESET REQUEST
@post('/reset-password-request')
def handle_password_reset_request():
    email = request.forms.get('reset_email')
    db = x.get_db_connection()
    cursor = db.cursor()
    # Executes an sql query to find a user with the provided email address and retrieves the first matching user record
    user = cursor.execute("SELECT user_pk, user_email FROM users WHERE user_email = ?", (email,)).fetchone()
    
    if user:
        # generates a unqiue reset token 
        reset_token = str(uuid.uuid4())
        # updates the users record in the database setting the reset token
        cursor.execute("UPDATE users SET reset_token = ? WHERE user_email = ?", (reset_token, email))
        db.commit()
        
        # reset_link = f"http://127.0.0.1/reset-password/{reset_token}"
        # Proceed to send email with reset link
        # email_body = f"Please click on the link to reset your password: {reset_link}"

        # x.send_email(user_email, "kanzabokhari99@gmail.com", "Verify your account", template('email_verification', key=verification_key))

        try:
            # Calling the send_email function to send an email to the user with the reset token included in the link
            x.send_email(user['user_email'], "your-email@example.com", "Reset your password", template('reset_password_email', reset_token=f"{reset_token}"))
            response.status = 200

            return "A link to reset your password has been sent to your email."
        except Exception as e:
            response.status = 500
            print(f"Failed to send email: {e}")
            return "Failed to send reset link email."
        return "A link to reset your password has been sent to your email."
    else:
        response.status = 404
        return "No account associated with that email."



############################## HANDLE PASSWORD RESET LINK
# A route that handles GET request to reset-password where token is a placeholder for the reset token
@get('/reset-password/<token>')
def show_reset_password_form(token):
    try:
        response.status = 200
        return template('__frm_reset_password.html', token=token)
    except Exception as ex:
        response.status = 500
        return "Can't get reset password form."


############################## HANDLE THE PASSWORD UPDATE 
# <token> is the placeholder for the reset token
@put('/reset-password/<token>')
def process_reset_password(token):
    try:
        # Fetch new password and confirmed password from the form
        new_password = request.forms.get('new_password', '').strip()
        confirmed_password = request.forms.get('confirm_password', '').strip()

        # Validate new password
        validated_new_password = x.validate_user_password(new_password)  # Validates format and length
        x.confirm_user_password(validated_new_password, confirmed_password)  # Validates match

        # If validation passes, hash the new password
        hashed_password = bcrypt.hashpw(validated_new_password.encode('utf-8'), bcrypt.gensalt())

        # Connect to the database and find a user with the provided reset token
        db = x.get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT user_pk FROM users WHERE reset_token = ?", (token,))
        user = cursor.fetchone()

        if user:
            # Update the user's password in the database and clear the reset token, to invalidate the token to prevent reuse. That also makes the reset link expired once it's done. By setting the reset token to NULL the system can easily check if thr eset process has been completed for the user
            # Then we also store the new hashed password for the user
            cursor.execute("UPDATE users SET user_password = ?, reset_token = NULL WHERE user_pk = ?", (hashed_password, user['user_pk']))
            db.commit()
            response.status = 200
            return "Your password has been successfully reset."
        else:
            response.status = 400
            return "Invalid or expired reset token."
    except Exception as ex:
        response.status = 500  
        return str(ex)  # Ensuring the exception message is converted to string if it isn't already.
    finally:
        if "db" in locals(): 
            db.close()


############################## skal ændres når deployer
run(host="127.0.0.1", port=80, debug=True, reloader=True)
