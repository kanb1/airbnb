from bottle import default_app, get, post, request, response, run, static_file, template, delete, put
import smtplib
import sqlite3
import time
import uuid
import git
import x
import logging
import os
from icecream import ic



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
    try:
        user_username = request.forms.get('user_username').strip()
        user_email = request.forms.get('user_email').strip()
        user_password = request.forms.get('user_password').strip()
        confirmed_password = request.forms.get('confirm_password').strip()
        user_name = request.forms.get('user_name').strip()
        user_last_name = request.forms.get('user_last_name').strip()
        user_role = request.forms.get('user_role').strip()

        validated_username = x.validate_user_user_name(user_username)
        validated_email = x.validate_user_email(user_email)
        validated_password = x.validate_user_password(user_password)
        x.confirm_user_password(validated_password, confirmed_password)
        validated_first_name = x.validate_user_name(user_name)
        validated_last_name = x.validate_user_last_name(user_last_name)


        user_role = request.forms.get('user_role')
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
        params = (user_pk, validated_username, validated_first_name, validated_last_name, validated_email, validated_password, user_role, current_timestamp, current_timestamp, 0, 0, verification_key)
        

        db.execute(sql, params)
        db.commit()
        return "Signup successful! Please check your email to verify your account"

    except sqlite3.IntegrityError as e:
        print(f"Integrity Error. User already exists: {e}")
    except Exception as ex:
        ic(ex)
    finally:
        pass
  
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


##############################
@get("/login")
def login():
  return template("login.html")



##############################
# @post("/password-reset")



##############################


# This is another way to do the 'Try/Except' clause for the production.py
# This will look for the 'PYTHONANYWHERE_DOMAIN' in the environment variable in the os.
# If it find it, it runs application = default_app()
if 'PYTHONANYWHERE_DOMAIN' in os.environ:
    application = default_app()
else:
    run(host="0.0.0.0", port=80, debug=True, reloader=True, interval=0)
# If it doesn't find it, it runs this line which runs the server locally.
