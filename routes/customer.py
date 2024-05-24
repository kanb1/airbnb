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



# Set up basic configuration for logging
logging.basicConfig(level=logging.DEBUG)


############################# GET MY BOOKINGS
@get("/my-bookings")
def my_bookings():
    user_session = request.get_cookie("session", secret=x.COOKIE_SECRET)
    if not user_session:
        redirect("/login")

    user = json.loads(user_session)
    user_id = user['user_id']
    
    conn = x.get_db_connection()
    try:
        q = conn.execute("""
            SELECT items.*, 
                   CASE WHEN bookings.item_id IS NOT NULL THEN 1 ELSE 0 END AS item_booked
            FROM items
            JOIN bookings ON items.item_pk = bookings.item_id
            WHERE bookings.user_id = ?
        """, (user_id,))
        booked_items = q.fetchall()
        return template("my_bookings.html", items=booked_items)
    except Exception as ex:
        return str(ex)
    finally:
        if conn:
            conn.close()
 

############################# BOOK/UNBOOK
@post("/toggle_book")
def toggle_book():
    user_session = request.get_cookie("session", secret=x.COOKIE_SECRET)
    if not user_session:
        redirect("/login")

    user = json.loads(user_session)
    user_id = user['user_id']
    item_id = request.forms.get("item_id")
    context = request.forms.get("context", "default")  # Identify the context of the request
    
    conn = x.get_db_connection()
    try:
        # Check if the item is already booked by the user
        q = conn.execute("SELECT * FROM bookings WHERE user_id = ? AND item_id = ?", (user_id, item_id))
        booking = q.fetchone()

        if booking:
            # If booked, delete the booking (unbook)
            conn.execute("DELETE FROM bookings WHERE user_id = ? AND item_id = ?", (user_id, item_id))
            conn.execute("UPDATE items SET item_booked = 0 WHERE item_pk = ?", (item_id,))
            button_text = "Book"
        else:
            # If not booked, create a new booking with UUID
            booking_pk = str(uuid.uuid4())
            conn.execute("INSERT INTO bookings (booking_pk, user_id, item_id) VALUES (?, ?, ?)", 
                         (booking_pk, user_id, item_id))
            conn.execute("UPDATE items SET item_booked = 1 WHERE item_pk = ?", (item_id,))
            button_text = "Unbook"

        conn.commit()

        if context == "my_bookings":
            return f"""
            <template mix-target="[id='booking_{item_id}']" mix-replace>
                <!-- Empty template to remove the booking -->
            </template>
            """
        else:
            return f"""
            <template mix-target="[id='frm_book_{item_id}']" mix-replace>
                <form id="frm_book_{item_id}">
                    <input name="item_id" type="hidden" value="{item_id}">
                    <button class="book-button"
                            mix-data="#frm_book_{item_id}"
                            mix-post="/toggle_book"
                            mix-default="{button_text}"
                            mix-await="{button_text}...">
                        {button_text}
                    </button>
                </form>
            </template>
            """
    except Exception as ex:
        return str(ex)
    finally:
        if conn:
            conn.close()


############################# EDIT PROFILE FOR CUSTOMERS - DISPLAY PROFILE
@get("/profile")
def _():
    user_session = request.get_cookie("session", secret=x.COOKIE_SECRET)
    if not user_session:
        redirect("/login")

    user = json.loads(user_session)
    user_id = user['user_id']
    
    conn = x.get_db_connection()
    try:
        user_data = conn.execute("SELECT * FROM users WHERE user_pk = ?", (user_id,)).fetchone()
        return template("profile.html", user=user_data)
    except Exception as ex:
        return str(ex)
    finally:
        if conn:
            conn.close()

############################# EDIT PROFILE FOR CUSTOMERS - EDIT PROFILE
@put("/profile/edit")
def edit_profile():
    try:
        user_session = request.get_cookie("session", secret=x.COOKIE_SECRET)
        if not user_session:
            ic("No user session found")
            return redirect("/login")

        user = json.loads(user_session)
        user_id = user['user_id']
        
        user_name = request.forms.get("user_name").strip()
        user_last_name = request.forms.get("user_last_name").strip()
        user_email = request.forms.get("user_email").strip()

        ic(user_id, user_name, user_last_name, user_email)

        # Validate new inputs
        validated_new_name = x.validate_user_name(user_name)
        validated_new_last_name = x.validate_user_last_name(user_last_name)
        validated_new_email = x.validate_user_email(user_email)
        
        ic(validated_new_name, validated_new_last_name, validated_new_email)

        db = x.get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            UPDATE users
            SET user_name = ?, user_last_name = ?, user_email = ?
            WHERE user_pk = ?
        """, (validated_new_name, validated_new_last_name, validated_new_email, user_id))

        ic("Executed update query")

        db.commit()
        ic("Committed changes")

        return f"""
        <template mix-redirect="/profile">
        </template>
        """

    except Exception as ex:
        ic(ex)
        return str(ex)
    finally:
        if "db" in locals():
            db.close()
            ic("Closed database connection")



############################# SOFT DELETE CUSTOMER PROFILE
@post("/profile/delete")
def delete_profile():
    user_session = request.get_cookie("session", secret=x.COOKIE_SECRET)
    if not user_session:
        redirect("/login")

    user = json.loads(user_session)
    user_id = user['user_id']
    password = request.forms.get("password").strip()
    
    conn = x.get_db_connection()
    try:
        user_data = conn.execute("SELECT * FROM users WHERE user_pk = ?", (user_id,)).fetchone()
        if not bcrypt.checkpw(password.encode(), user_data['user_password']):
            return f"""
            <template mix-target="#delete_profile_message" mix-replace>
                <p>Invalid password</p>
            </template>
            """
        
        deletion_verification_key = str(uuid.uuid4())
        conn.execute("UPDATE users SET user_deletion_verification_key = ? WHERE user_pk = ?", (deletion_verification_key, user_id))
        conn.commit()
        
        # Send email with verification key
        x.send_email(user_data['user_email'], "your-email@example.com", "Confirm Account Deletion", 
                     template('email_confirm_deletion.html', key=deletion_verification_key))
        
        return f"""
        <template mix-target="#delete_profile_message" mix-replace>
            <p>A confirmation email has been sent to your email address.</p>
        </template>
        """
    except Exception as ex:
        return str(ex)
    finally:
        if conn:
            conn.close()

############################## HANDLE THE CONFIRMATION LINK
@get("/profile/confirm-delete/<key>")
def confirm_delete_profile(key):
    ic("Entering confirm_delete_profile with key:", key)
    conn = x.get_db_connection()
    try:
        user_data = conn.execute("SELECT * FROM users WHERE user_deletion_verification_key = ?", (key,)).fetchone()
        ic("User data fetched:", user_data)
        if not user_data:
            ic("Invalid verification key")
            return """
            <template mix-target="body" mix-replace>
                <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
                    <strong class="font-bold">Error!</strong>
                    <span class="block sm:inline">Invalid verification key.</span>
                </div>
            </template>
            """
        
        # Update the user's account to set user_is_deleted to 1
        conn.execute("UPDATE users SET user_is_deleted = 1 WHERE user_pk = ?", (user_data['user_pk'],))
        conn.commit()
        
    except Exception as ex:
        ic(ex)
        return str(ex)
    finally:
        # Render the account deleted message and include the mix-redirect template
        redirect("/logout")
        if conn:
            conn.close()
