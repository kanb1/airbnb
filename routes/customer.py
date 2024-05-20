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
                   CASE WHEN bookings.item_id IS NOT NULL THEN 1 ELSE 0 END AS booked
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
            button_text = "Book"
        else:
            # If not booked, create a new booking with UUID
            booking_pk = str(uuid.uuid4())
            conn.execute("INSERT INTO bookings (booking_pk, user_id, item_id) VALUES (?, ?, ?)", 
                         (booking_pk, user_id, item_id))
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

############################# EDIT PROFILE
############################# DELETE PROFILE
