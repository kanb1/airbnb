#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

#https://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@github.com/kanb1/airbnb.git

#########################
from bottle import default_app, get, post, request, response, run, static_file, template, delete, put
import sqlite3
import time
import uuid
import git
import x
import logging

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
    print("Signup function called")
    user_name = request.forms.get('user_name')
    user_email = request.forms.get('user_email')
    user_password = request.forms.get('user_password')
    user_role = request.forms.get('user_role')
    current_timestamp = int(time.time())
    # The verification token
    verification_key = uuid.uuid4().hex
    user_pk = str(uuid.uuid4())  # Create a UUID for the primary key

    db = None
    try:
        db = x.get_db_connection()
        # SQL command
        sql = """
            INSERT INTO users (
                user_pk, user_username, user_name, user_last_name, user_email, 
                user_password, user_role, user_created_at, user_updated_at, 
                user_is_verified, user_is_blocked, user_verification_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        # Parameters for the SQL command
        params = (user_pk, user_name, user_name, "", user_email, user_password, user_role, current_timestamp, current_timestamp, 0, 0, verification_key)

        # Print SQL and parameters for debugging
        print("Executing SQL:", sql)
        print("With parameters:", params)

        # Execute the SQL command
        db.execute(sql, params)
        db.commit()
        return "Signup successful! Please verify your email."
    except sqlite3.IntegrityError as e:
        print(f"Integrity Error: {e}")
        return "User already exists"
    except Exception as ex:
        print(f"An error occurred during signup: {type(ex).__name__} - {ex}")
        return "An error occurred during signup."
    finally:
        if db:
            db.close()
  
    return "Signup successful! Pleasy verify your email"
# Handle user verification

############################## CHECK USERS IN DB
@get('/users')
def get_all_user_pks():
    db = x.get_db_connection()
    try:
        db.row_factory = sqlite3.Row  # This allows access to data by column name
        cur = db.cursor()
        cur.execute('SELECT user_pk FROM users')  # Query to fetch only user_pk
        user_pks = cur.fetchall()  # Fetch all results

        # Convert results to a list of user_pk values
        user_pk_list = [row['user_pk'] for row in user_pks]
        response.content_type = 'application/json'
        return {'user_pks': user_pk_list}

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
try:
  import production
  application = default_app()
except Exception as ex:
  print("Running local server")
  run(host="127.0.0.1", port=80, debug=True, reloader=True)