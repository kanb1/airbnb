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
        response.status = 401
        redirect("/login")

    user = json.loads(user_session)
    user_id = user['user_id']
    
    conn = x.get_db_connection()
    try:
        # SELECT all columns from the items table, with all the details such as item_pk, item_name lat long and so on

        # GROUPCONCAT, concatenates values from multiple rows into a single string, here it does it with image_url values from the items_images table associated with each item
        # items_images.image_url: Refers to the image_url column in the items_images table.
        # as item_images: Renames the concatenated result to item_images. This makes it easier to reference in the code.

        # CASE WHEN: This is a conditional expression that returns a specific value based on whether a condition is true.
        # bookings.item_id IS NOT NULL: Checks if there is a booking for the item. If bookings.item_id is not NULL, it means the item is booked.
        # THEN 1 ELSE 0: It will be 1 if the item is booked, otherwise it will be 0.
        # AS item_booked: Renames the result of the CASE expression to item_booked. This indicates whether the item is booked or not.

        # JOIN bookings: Performs an inner join with the bookings table.
        # ON items.item_pk = bookings.item_id: Specifies the join condition. It matches the primary key of the items table (items.item_pk) with the item ID in the bookings table (bookings.item_id). This means only rows that have matching values in both tables will be included in the result.
        # JOIN bookings ON items.item_pk = bookings.item_id: Combines rows from the items table and the bookings table where items.item_pk matches bookings.item_id. This ensures only items that have been booked are included.

        # LEFT JOIN
        # Combines rows from the items table and the items_images table where items.item_pk matches items_images.item_fk.
        # A LEFT JOIN includes all rows from the items table, and the matching rows from the items_images table. If there is no match, the result is NULL for columns from the items_images table.
        # This is used to get all images associated with each item.

        # WHERE
        # Filters the results to include only those items that have been booked by a specific user, where user_id matches the given parameter (?)

        # GROUP BY
        # Groups the results by the primary key of the items (items.item_pk), ensuring each item appears only once in the result set.
        # This is necessary because we are using aggregate functions like GROUP_CONCAT and we want to combine all images related to an item into a single row.

        # Executes an SQL query to fetch the booked items for the user.
        # The query joins the items, bookings, and items_images tables.
        # JOIN: Finds which items has been booked, the condition is item.pk(items) skal matche item.id(bookings). If an item exists in the items table but not in the bookings table, it will be excluded.
        # LEFT JOIN: To get the images associated with each item. the item_pk (items) must match item_fk (items_images)
        # WHERE: filter the bookings to only include the bookings from the user
        # GROUP BY: Groups the results by item_pk to ensure each item appears once in the result set, with its images concatenated
        q = conn.execute("""
            SELECT items.*, 
                   GROUP_CONCAT(items_images.image_url) as item_images,
                   CASE WHEN bookings.item_id IS NOT NULL THEN 1 ELSE 0 END AS item_booked
            FROM items
            JOIN bookings ON items.item_pk = bookings.item_id
            LEFT JOIN items_images ON items.item_pk = items_images.item_fk
            WHERE bookings.user_id = ?
            GROUP BY items.item_pk
        """, (user_id,))
        
        # Fetch all the results of the query
        booked_items = q.fetchall()
        
        
        # [dict(item) for item in booked_items] converts each row from the query result into a dictionary.
        # For each item, if item['item_images'] is not empty, split the concatenated string of image URLs into a list.
        booked_items_dict = [dict(item) for item in booked_items]
        for item in booked_items_dict:
            if item['item_images']:
                item['item_images'] = item['item_images'].split(',')
        
        response.status = 200
        return template("my_bookings.html", items=booked_items_dict)
    except Exception as ex:
        response.status = 500
        return str(ex)
    finally:
        if conn:
            conn.close()

 

############################# BOOK/UNBOOK
@post("/toggle_book")
def toggle_book():
    user_session = request.get_cookie("session", secret=x.COOKIE_SECRET)
    if not user_session:
        response.status = 401
        redirect("/login")

    user = json.loads(user_session)
    user_id = user['user_id']
    # Get Item ID: request.forms.get("item_id") retrieves the item ID from the form data.
    # Get Context: request.forms.get("context", "default") retrieves the context of the request from the form data. If not provided, it defaults to "default".
    item_id = request.forms.get("item_id")
    # The toggle_book route reads the context value from the form data:
    context = request.forms.get("context", "default")  #it is used later on with the mix replacement. This line retrieves the value of the context input. If the input is not present, it defaults to "default".

    
    conn = x.get_db_connection()
    try:
        #  The query checks if there is an existing booking for the user and item (checking in the bookings table)
        q = conn.execute("SELECT * FROM bookings WHERE user_id = ? AND item_id = ?", (user_id, item_id))
        booking = q.fetchone()

        # TOGGLE
        # Tjekker hvis bookingen allerede eksisterer, hvis den eksisterer så:
        if booking:
            # hvis booket, unbook:
            conn.execute("DELETE FROM bookings WHERE user_id = ? AND item_id = ?", (user_id, item_id))
            conn.execute("UPDATE items SET item_booked = 0 WHERE item_pk = ?", (item_id,))
            # Sæt buttontext til book for næste handling
            button_text = "Book"
        else:
            # hvis ikke booket, book:
            # create a new booking with UUID
            booking_pk = str(uuid.uuid4())
            # inserts a new booking record.
            conn.execute("INSERT INTO bookings (booking_pk, user_id, item_id) VALUES (?, ?, ?)", 
                         (booking_pk, user_id, item_id))
            # updates the item_booked status in the items table to 1.
            conn.execute("UPDATE items SET item_booked = 1 WHERE item_pk = ?", (item_id,))
            # sets the button text to unbook
            button_text = "Unbook"

        conn.commit()
        
        response.status = 200

        # Ram den specifikke booking_item (my_bookings.html har øverst en div med en booking) og fjern den, ellers
        # Lidt længere oppe har vi en context = request.forms.get("context", "default"), som læser context-værdien fra den formdata der blev submittet
        # hvis context == my_bookings, som er værdien på context inputfelt i my_bookings.html, så kører den denne her mix-replace hvor den fjerner. Det bliver triggered hvad end context er, når en af de der to forms fra _item.html eller my_bookings klikker og mix-post trigger toggle-routen - men hvilken af de her to html template ting der skal køres er ud fra konteksten, fordi en user kan både unbook fra my_bookings.html men book/unbook fra item.html
        if context == "my_bookings":
            return f"""
            <template mix-target="[id='booking_{item_id}']" mix-replace>
                <!-- Empty template to remove the booking -->
            </template>
            """
        # ellers er den default, hvilket vil sige den kører denne her under, hvor den ændrer i _item.html
        else:

            # Ændrer dynmamisk knapperne for book or unbook (lidt længere oppe defineret) baseret på item'ets nuværende status, (inde i _item.html)
            # replacer book-button class fra item og ændrer buttontext efter om den er booket eller ej som defineres længere oppe i denne her route
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
        response.status = 500
        return str(ex)
    finally:
        if conn:
            conn.close()


############################# EDIT PROFILE FOR CUSTOMERS - DISPLAY PROFILE
@get("/profile")
def _():
    user_session = request.get_cookie("session", secret=x.COOKIE_SECRET)
    if not user_session:
        response.status = 401
        redirect("/login")

    user = json.loads(user_session)
    user_id = user['user_id']
    
    conn = x.get_db_connection()
    try:
        user_data = conn.execute("SELECT * FROM users WHERE user_pk = ?", (user_id,)).fetchone()
        response.status = 200
        return template("profile.html", user=user_data)
    except Exception as ex:
        response.status = 500
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
            response.status = 401
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

        response.status = 200
        return f"""
        <template mix-redirect="/profile">
        </template>
        """

    except Exception as ex:
        ic(ex)
        response.status = 500
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
        response.status = 401
        redirect("/login")

    user = json.loads(user_session)
    user_id = user['user_id']
    password = request.forms.get("password").strip()
    
    conn = x.get_db_connection()
    try:
        # fetches the userdata from the database
        user_data = conn.execute("SELECT * FROM users WHERE user_pk = ?", (user_id,)).fetchone()
        # verifies the password using bcrypt.
        if not bcrypt.checkpw(password.encode(), user_data['user_password']):
            response.status = 400
            return f"""
            <template mix-target="#delete_profile_message" mix-replace>
                <p>Invalid password</p>
            </template>
            """
        
        # generates a unique verification key
        deletion_verification_key = str(uuid.uuid4())
        # updates the user's record in the database with this key
        conn.execute("UPDATE users SET user_deletion_verification_key = ? WHERE user_pk = ?", (deletion_verification_key, user_id))
        conn.commit()
        
        # Send email with deletion verification key
        x.send_email(user_data['user_email'], "your-email@example.com", "Confirm Account Deletion", 
                     template('email_confirm_deletion.html', key=deletion_verification_key))
        
        response.status = 200

        return f"""
        <template mix-target="#delete_profile_message" mix-replace>
            <p>A confirmation email has been sent to your email address.</p>
        </template>
        """
    except Exception as ex:
        response.status = 500
        return str(ex)
    finally:
        if conn:
            conn.close()

############################## HANDLE THE CONFIRMATION LINK
# finalizes the deletion proces by verifying the deletion key and setting the user's account to a deleted state
@get("/profile/confirm-delete/<key>")
def confirm_delete_profile(key):
    ic("Entering confirm_delete_profile with key:", key)
    conn = x.get_db_connection()
    try:
        # retrieves the user's data using the deletion verification key
        # if the key is invalid it returns an error emssage 
        user_data = conn.execute("SELECT * FROM users WHERE user_deletion_verification_key = ?", (key,)).fetchone()
        ic("User data fetched:", user_data)
        if not user_data:
            ic("Invalid verification key")
            response.status = 400
            return """
            <template mix-target="body" mix-replace>
                <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
                    <strong class="font-bold">Error!</strong>
                    <span class="block sm:inline">Invalid verification key.</span>
                </div>
            </template>
            """
        
        # Update the user's account to set user_is_deleted to 1, indicating it's deleted
        conn.execute("UPDATE users SET user_is_deleted = 1 WHERE user_pk = ?", (user_data['user_pk'],))
        conn.commit()
        response.status = 200

        
    except Exception as ex:
        ic(ex)
        response.status = 500
        return str(ex)
    finally:
        # Render the account deleted message and include the mix-redirect template
        redirect("/logout")
        if conn:
            conn.close()
