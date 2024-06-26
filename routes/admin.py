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
import random


# Set up basic configuration for logging
logging.basicConfig(level=logging.DEBUG)

############################# THIS SCRIPT CREATES THE ADMIN WHEN I RUN THE APP
# def create_admin_user():
#     admin_email = "admin@admin.com"
#     admin_password = "admin"
#     hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
#     user_id = str(uuid.uuid4())
#     created_at = int(time.time())

#     conn = sqlite3.connect('airbnb.db') 
#     cursor = conn.cursor()
    
#     cursor.execute("""
#         INSERT INTO users (user_pk, user_username, user_name, user_last_name, user_email, user_password, user_role, user_created_at, user_updated_at, user_is_verified, user_is_blocked)
#         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#     """, (user_id, "adminTest", "AdminTest", "UserTest2", admin_email, hashed_password, "admin", created_at, created_at, 1, 0))
    
#     conn.commit()
#     conn.close()
#     print("Admin user created with email:", admin_email)
#     print("Hashed password:", hashed_password)

# create_admin_user()


############################# Generate Bcrypt Hash for Admin Password
@get("/admin-login")
def admin_login():
    return template("admin_login.html")

#############################
@post("/admin-login")
def do_admin_login():
    try:
        email = request.forms.get('admin_email')
        password = request.forms.get('admin_password')
        ic(email, password)  # Debugging output

        db = x.get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE user_email = ? AND user_role = 'admin'", (email,))
        admin = cursor.fetchone()
        ic(admin)  # Debugging output

        if admin:
            # Check if the account is marked as deleted
            if admin['user_is_deleted'] == 1:
                ic("Account is deleted")
                response.status = 403
                return "This account has been deleted."

            # Fetch the stored hashed password
            stored_hash = admin['user_password']
            ic(stored_hash)  # Debugging output

            # Check the password
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                ic("Password correct")  # Confirm password match

                # Remove the password from the admin object for security
                admin.pop('user_password', None)
                ic(admin)  # Debugging output

                if admin['user_is_verified'] == 1:
                    # Storing user ID & role in the cookie
                    # Creates a session data dictionary with the userID and role
                    session_data = {'user_id': admin['user_pk'], 'role': admin['user_role']}
                    # serialize the session data to a JSON string
                    session_data_serialized = json.dumps(session_data)

                    try:
                        import production
                        is_cookie_https = True
                    except ImportError:
                        is_cookie_https = False

                    # sets a secure session cookie with the session data (cookie secret)
                    response.set_cookie("session", session_data_serialized, secret=x.COOKIE_SECRET, httponly=True, secure=is_cookie_https)
                    ic("Session set, redirecting...")
                    
                    # Den er godkendt, derefter sætter headeren til lokationen admin-dashboard
                    response.status = 303
                    response.set_header("Location", "/admin-dashboard")

                    x.no_cache()


                    
                else:
                    ic("Account not verified")
                    response.status = 403
                    return "Please verify your account"
            else:
                ic("Invalid password")
                response.status = 403
                return "Invalid password"
        else:
            ic("Admin user not found")
            response.status = 404
            return "Admin user not found"

    except Exception as ex:
        ic("Login error:", ex)
        print(f"An error occurred: {str(ex)}")
        print(f"Exception type: {type(ex).__name__}, Exception args: {ex.args}")
        response.status = 500  # Set HTTP status to 500 to indicate server error
        return "Problems logging in."
        
    finally:
        if "db" in locals():
            db.close()


############################## ADMIN DASHBOARD
@get("/admin-dashboard")
def admin_dashboard():
    x.no_cache()
    user_session = request.get_cookie("session", secret=x.COOKIE_SECRET)
    if user_session and json.loads(user_session).get('role') == 'admin':
        response.status = 200
        return template('admin_dashboard.html')
    else:
        response.status = 401
        # også ift no_cache, så redirecter den til denne her side, da det er /customer-dashboard der bliver kaldt under login (og admin/partner hvis det er de)
        return redirect("/login")
    # ic(user_session) 
    # if user_session:
    #     session_data = json.loads(user_session)
    #     ic(session_data)
    #     if session_data.get('role') == 'admin':
    #         return template('admin_dashboard.html')
    #     else:
    #         ic("User role is not admin")
    # else:
    #     ic("No user session found")
    # return redirect("/login")



    

#############################
@get('/admin-logout')
def admin_logout():
    try:
        x.no_cache()
        response.delete_cookie("session", secret=x.COOKIE_SECRET)
        response.status = 200

    except Exception as ex:
        print(ex)
        response.status = 500
        return "Error logging out."
    finally:
        return redirect("/")

############################# View All Users
@get("/admin-users")
def admin_users():
    x.no_cache()
    if not x.validate_admin_logged():
        response.status = 401
        return redirect("/admin-login")

    conn = x.get_db_connection()
    try:
        users = conn.execute("SELECT * FROM users").fetchall()
        response.status = 200
        return template("admin_users.html", users=users)
    except Exception as ex:
        ic(ex)
        response.status = 500
        return str(ex)
    finally:
        conn.close()


############################# View All Properties
@get("/admin-properties")
def admin_properties():
    x.no_cache()

    if not x.validate_admin_logged():
        return redirect("/admin-login")

    conn = x.get_db_connection()
    try:
        properties = conn.execute("SELECT * FROM items").fetchall()
        response.status = 200
        return template("admin_properties.html", properties=properties)
    except Exception as ex:
        ic(ex)
        response.status = 500
        return str(ex)
    finally:
        conn.close()


############################# Block/Unblock User
@post("/toggle_user_block")
def toggle_user_block():
    try:

        # Retrieves the user_id from the form data, which identifies the user whose status is being toggled.
        user_id = request.forms.get("user_id")
        # Retrieves the context from the form data, defaulting to "admin_users" if not provided. This helps identify the context of the request.
        context = request.forms.get("context", "admin_users")  # Identify the context of the request

        conn = x.get_db_connection()
        # Executes a SQL query to fetch the current blocked status of the user with the provided user_id.
        current_status = conn.execute("SELECT user_is_blocked FROM users WHERE user_pk = ?", (user_id,)).fetchone()
        
        # Determine New Status and Notification Details:
        if current_status['user_is_blocked'] == 1:
            new_status = 0
            email_subject = "Account Unblocked"
            email_body = "Your account has been unblocked by the admin."
        else:
            new_status = 1
            email_subject = "Account Blocked"
            email_body = "Your account has been blocked by the admin."

        # Executes an SQL update statement to change the user_is_blocked status in the users table for the specified user_id.
        conn.execute("UPDATE users SET user_is_blocked = ? WHERE user_pk = ?", (new_status, user_id))
        conn.commit()

        # Send notification email. Fetches the user's email address from the database using the user_id.
        user_email = conn.execute("SELECT user_email FROM users WHERE user_pk = ?", (user_id,)).fetchone()['user_email']
        x.send_email(user_email, "your-email@example.com", email_subject, email_body)
        
        response.status = 200

        return f"""
        <template mix-redirect="/admin-users">
        </template>
        """

    except Exception as ex:
        ic(ex)
        response.status = 500
        return str(ex)
        
    finally:
        if conn:
            conn.close()
      


############################# Block/Unblock Property
@post("/toggle_property_block")
def toggle_property_block():
    try:

        item_id = request.forms.get("item_id")
        context = request.forms.get("context", "admin_properties")  # Identify the context of the request

        conn = x.get_db_connection()
        # Executes a SQL query to fetch the current blocked status of the property with the provided item_id.
        current_status = conn.execute("SELECT item_is_blocked FROM items WHERE item_pk = ?", (item_id,)).fetchone()
        
        # If current_status is None, it means the property with the given item_id does not exist.
        if not current_status:
            response.status = 404
            return "Property not found."

        if current_status['item_is_blocked'] == 1:
            new_status = 0
            email_subject = "Property Unblocked"
            email_body = "Your property has been unblocked by the admin."
        else:
            new_status = 1
            email_subject = "Property Blocked"
            email_body = "Your property has been blocked by the admin."

        # Executes an SQL update statement to change the item_is_blocked status in the items table for the specified item_id.
        conn.execute("UPDATE items SET item_is_blocked = ? WHERE item_pk = ?", (new_status, item_id))
        conn.commit()

        # Fetches the user_id (owner of the property) from the items table using the item_id.
        user_id = conn.execute("SELECT item_owner_fk FROM items WHERE item_pk = ?", (item_id,)).fetchone()['item_owner_fk']
        # Fetches the owner's email address from the users table using the user_id.
        user_email = conn.execute("SELECT user_email FROM users WHERE user_pk = ?", (user_id,)).fetchone()['user_email']

        # sends the notification email to the property owner
        try:
            x.send_email(user_email, "your-email@example.com", email_subject, email_body)
        except Exception as ex:
            ic("Email sending failed:", ex)
        
        response.status = 200

        return """
        <template mix-redirect="/admin-properties"></template>
        """

    except Exception as ex:
        ic(ex)
        response.status = 500
        return str(ex)
    finally:
        if conn:
            conn.close()

