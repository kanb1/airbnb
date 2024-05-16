from bottle import default_app, get, post, request, response, run, static_file, template, delete, put
from bottle import redirect
import smtplib
import sqlite3
import time
import uuid
import git
import x
import logging
import os
from icecream import ic
import bcrypt
import json
from bottle import json_dumps





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
@get("/")
def _():
    return template("index.html")
 
##############################TEST database connection
@get("/test-db-connection")
def test_db_connection_route():
    try:
        x.test_db_connection()
        return "Database connection OK"
    except Exception as ex:
        logging.error("Error testing database connection", exc_info=True)
        return f"Database connection failed: {ex.__class__.__name__} - {str(ex)}"

##############################
@get("/signup")
def signup():
  return template("signup.html")

##############################
@post("/signup")
def do_signup():
    db = None
    try:
        user_username = request.forms.get('user_username').strip()
        user_email = request.forms.get('user_email').strip()
        user_password = request.forms.get('user_password').strip()
        confirmed_password = request.forms.get('confirm_password').strip()
        user_name = request.forms.get('user_name').strip()
        user_last_name = request.forms.get('user_last_name').strip()
        user_role = request.forms.get('user_role').strip()

        # Validate the inputs
        validated_username = x.validate_user_user_name(user_username)
        validated_email = x.validate_user_email(user_email)
        validated_password = x.validate_user_password(user_password)
        x.confirm_user_password(validated_password, confirmed_password)
        validated_first_name = x.validate_user_name(user_name)
        validated_last_name = x.validate_user_last_name(user_last_name)

        # Hash the password
        hashed_password = bcrypt.hashpw(user_password.encode('utf-8'), bcrypt.gensalt())

        # Setup for database entry
        current_timestamp = int(time.time())
        verification_key = uuid.uuid4().hex
        user_pk = str(uuid.uuid4())

        db = x.get_db_connection()
        sql = """
            INSERT INTO users (
                user_pk, user_username, user_name, user_last_name, user_email,
                user_password, user_role, user_created_at, user_updated_at,
                user_is_verified, user_is_blocked, user_verification_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (user_pk, validated_username, validated_first_name, validated_last_name, validated_email, hashed_password, user_role, current_timestamp, current_timestamp, 0, 0, verification_key)

        # Execute the SQL command
        db.execute(sql, params)
        db.commit()

        # Send verification email
        x.send_email(user_email, "your-email@example.com", "Verify your account", template('email_verification', key=verification_key))

        return "Signup successful! Please check your email to verify your account."

    except sqlite3.IntegrityError as e:
        return f"Integrity Error. User already exists: {e}"
    except Exception as ex:
        return str(ex)
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
        return {'user_usernames': user_pk_list}

    except Exception as e:
        response.status = 500  # Internal Server Error
        return {'error': str(e)}
    finally:
        if db:
            db.close()

############################## get render templates, post oprette noget kreeres, lave nyt, put noget skal ændres, delete fjernes
@get("/verify/<key>")
def verify(key):
    try:
        # get_db_connection() returns a connection to the database
        db = x.get_db_connection()
        cursor = db.cursor()

        # Check if the key exists and get the user_pk
        cursor.execute("SELECT user_pk FROM users WHERE user_verification_key = ?", (key,))
        user = cursor.fetchone()

        if user:
            # Update the user_is_verified to 1 for the user with the given verification key
            cursor.execute("UPDATE users SET user_is_verified = 1 WHERE user_verification_key = ?", (key,))
            db.commit()
            return f"Account with key {key} is verified successfully"
        else:
            return "Verification failed: Invalid key."

    except Exception as ex:
        print(ex)

    finally:
        if db:
            db.close()

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
        cursor.execute("SELECT * FROM users WHERE user_email = ?", (email,))
        user = cursor.fetchone()
        print(user)

        if user:
            # No need to encode the stored hash
            stored_hash = user['user_password']
            ic(user)

            # Only encode the password from the form
            if bcrypt.checkpw(password.encode(), stored_hash):
                ic("Password correct")  # Confirm password match
                
                # Remove the password from the user object, security cases
                user.pop('user_password', None) # Using pop with None ensures no error if the key doesn't exist
                # shows that user_password is not showing
                ic(user)

                if user['user_is_verified'] == 1:
                    # Storing user ID & role in the cookie

                    # I create a session object that includes those user identifiers:
                    session_data = {'user_id': user['user_pk'], 'role': user['user_role']}
                    session_data_serialized = json.dumps(session_data)
                    #then I later in the response.set_cookie send that session key with userdata to the client:

                    try:
                        import production
                        is_cookie_https = True
                    except ImportError:
                        is_cookie_https = False

                    # this is the data I want to store in my cookie, the session_data_serialized with the json userdata and my cookiekey, the "x.COOKIE_SECRET", is set as the cookie inside that response.set_cookie()
                    # in devtools u see the encrypted cookie value, which is my COOKIE_SECRET. This function, specifically the secrey key, encrypts my cookie_secret.
                    response.set_cookie("session", session_data_serialized, secret=x.COOKIE_SECRET, httponly=True, secure=is_cookie_https)
                    ic("Session set, redirecting...")
                    
                    x.no_cache()

                    return f"""
                    <template mix-redirect="/{user['user_role']}-dashboard">
                        </template>
                    """
                else:
                    return "Please verify your account"
            else:
                return "Password invalid"
        else:
            return "User is not found"

    except Exception as ex:
        ic("Login error:", ex)
        print(f"An error occurred: {str(ex)}")
        print(f"Exception type: {type(ex).__name__}, Exception args: {ex.args}")
        response.status = 500  # Set HTTP status to 500 to indicate server error
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
        return template('customer_dashboard.html')
    else:
        # også ift no_cache, så redirecter den til denne her side, da det er /customer-dashboard der bliver kaldt under login (og admin/partner hvis det er de)
        return redirect("/login")

############################## ADMIN DASHBOARD
@get("/admin-dashboard")
def admin_dashboard():
    x.no_cache()
    user_session = request.get_cookie("session", secret=x.COOKIE_SECRET)
    if user_session and json.loads(user_session).get('role') == 'admin':
        return template('admin_dashboard.html')
    else:
        return redirect("/login")

############################## PARTNER DASHBOARD
@get("/partner-dashboard")
def partner_dashboard():
    x.no_cache()
    user_session = request.get_cookie("session", secret=x.COOKIE_SECRET)
    if user_session and json.loads(user_session).get('role') == 'partner':
        return template('partner_dashboard.html')
    else:
        return redirect("/login")

############################## LOGOUT
@get('/logout')
def logout():
    try:
        response.delete_cookie("session")  # Delete the session cookie
        x.no_cache()  # Set no-cache headers
        
        return f"""
            <template mix-redirect="/login">
            </template>
        """
    except Exception as ex:
        print(ex)
        return "Error logging out."
    finally:
        pass

############################## skal ændres når deployer
run(host="127.0.0.1", port=80, debug=True, reloader=True)
