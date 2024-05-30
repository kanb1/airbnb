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


############################# GET ADD PROPERTY PAGE
@get("/add-property")
def add_property():
    try:
        ic("Rendering add_property.html")
        return template("add_property.html")
    except Exception as ex:
        ic(ex)
        return "Problems rendering add_property.html"
    finally:
        pass

############################# ADD PROPERTY 
@post("/create_property")
def create_property():
    try:
        ic("Entering create_property route")
        user_session = request.get_cookie("session", secret=x.COOKIE_SECRET)
        if not user_session:
            ic("No user session found, redirecting to login")
            return redirect("/login")

        user = json.loads(user_session)
        if user.get('role') != 'partner':
            ic("User is not a partner, unauthorized")
            return "Unauthorized"

        item_pk = str(uuid.uuid4())
        item_name = request.forms.get('item_name').strip()
        item_price_per_night = request.forms.get('item_price_per_night').strip()

        # Validate the inputs
        validated_item_name = x.validate_item_name(item_name)
        validated_item_price = x.validate_item_price(item_price_per_night)

        # Define latitude and longitude within Denmark
        item_lat = random.uniform(54.5, 57.75)
        item_lon = random.uniform(8.0, 12.75)
        item_stars = 5  # Default value for stars
        item_created_at = int(time.time())
        item_updated_at = 0
        item_owner_fk = user['user_id']

        db = x.get_db_connection()

        # Handle images
        try:
            item_images = request.files.getall('item_images')
            x.validate_item_images(item_images)
        except ValueError as ve:
            return f"""
            <template mix-target="#file_container" mix-replace>
                <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
                    <p class="text-red-700">{ve}</p>
                    <input name="item_images" id="item_images" class="w-full border" type="file" accept=".png, .jpg, .jpeg, .webp" multiple required max="5" min="1">
                </div>
            </template>
            """

        for index, image in enumerate(item_images, start=1):
            image_pk = str(uuid.uuid4())
            image_created_at = int(time.time())
            filename = f"{item_pk}_{index}.{image.filename.split('.')[-1]}"
            path = f"images/{filename}"
            ic(f"Saving image to {path}")
            image.save(path)  # Save the image with the new filename

            # Insert the image filename into the items_images table (without path)
            db.execute("INSERT INTO items_images (image_pk, image_url, item_fk, image_created_at) VALUES (?, ?, ?, ?)",
                       (image_pk, filename, item_pk, image_created_at))
            db.commit()

        db.execute("INSERT INTO items (item_pk, item_name, item_lat, item_lon, item_stars, item_price_per_night, item_created_at, item_updated_at, item_owner_fk) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   (item_pk, validated_item_name, item_lat, item_lon, item_stars, validated_item_price, item_created_at, item_updated_at, item_owner_fk))
        db.commit()

        return """
        <template mix-redirect="/">
            <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative" role="alert">
                <strong class="font-bold">Success!</strong>
                <span class="block sm:inline">Property has been successfully added.</span>
            </div>
        </template>
        """
    except Exception as ex:
        ic("########################### create property exception:")
        ic(ex)
    finally:
        if "db" in locals():
            db.close()



            
############################# GET MY PROPERTIES PAGE
# @get("/my-properties")
# def my_properties():
#     conn = None
#     try:
#         if not x.validate_partner_logged():
#             return redirect("/login")
        
#         user = json.loads(request.get_cookie("session", secret=x.COOKIE_SECRET))
#         user_id = user['user_id']
        
#         conn = x.get_db_connection()
#         properties = conn.execute("SELECT * FROM items WHERE item_owner_fk = ?", (user_id,)).fetchall()
#         return template("my_properties.html", properties=properties)
#     except Exception as ex:
#         ic(ex)
#         return str(ex)
#     finally:
#         if conn:
#             conn.close()

############################# HANDLE NEXT AND PREVIOUS BUTTONS WITH MIXHTML 
#NEXTX
# @post("/nextImage")
# def next_image():
#     try:
#         data = json.loads(request.forms.get("data"))
#         images = data['images']
#         current_index = data['current_index']
#         next_index = (current_index + 1) % len(images)
#         next_image_url = images[next_index]

#         return f"""
#         <template mix-target="#current-image-{data['item_pk']}" mix-replace>
#             <img src="/images/{next_image_url}" class="w-full h-48 aspect-square object-cover rounded-lg">
#         </template>
#         <template mix-target="[mix-data*='current_index']" mix-replace>
#             <input type="hidden" name="current_index" value="{next_index}">
#         </template>
#         """
#     except Exception as ex:
#         ic(ex)
#         return str(ex)



#PREVIOUS
# @post("/previousImage")
# def previous_image():
#     try:
#         data = json.loads(request.forms.get("data"))
#         images = data['images']
#         current_index = data['current_index']
#         previous_index = (current_index - 1) % len(images)
#         previous_image_url = images[previous_index]

#         return f"""
#         <template mix-target="#current-image-{data['item_pk']}" mix-replace>
#             <img src="/images/{previous_image_url}" class="w-full h-48 aspect-square object-cover rounded-lg">
#         </template>
#         <template mix-target="[mix-data*='current_index']" mix-replace>
#             <input type="hidden" name="current_index" value="{previous_index}">
#         </template>
#         """
#     except Exception as ex:
#         ic(ex)
#         return str(ex)


############################# EDIT PROPERTY
@put("/edit_property/<item_pk>")
def edit_property(item_pk):
    try:
        user_session = request.get_cookie("session", secret=x.COOKIE_SECRET)
        if not user_session:
            return redirect("/login")

        user = json.loads(user_session)
        if user.get('role') != 'partner':
            return "Unauthorized"

        item_name = request.forms.get('item_name').strip()
        item_price_per_night = request.forms.get('item_price_per_night').strip()

        validated_item_name = x.validate_item_name(item_name)
        validated_item_price = x.validate_item_price(item_price_per_night)

        conn = x.get_db_connection()

        # Handle new images
        new_images = request.files.getall('new_images') # Get's all images from input field
        # However, .getAll() always returns a file called 'empty' if there is no new files uploaded
        if(new_images[0].filename == 'empty'): # This checks if the 'empty' file
            new_images = [] #If it's there, it will reset the array to nothing to not interrupt the edit flow.

        current_images = conn.execute("SELECT image_url FROM items_images WHERE item_fk = ?", (item_pk,)).fetchall()
        current_images = [img['image_url'] for img in current_images]

        try:
            x.validate_item_images(current_images, new_images)
        except ValueError as ve:
            return f"""
            <template mix-target="#file_container" mix-replace>
                <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
                    <p class="text-red-700">{ve}</p>
                    <input type="file" name="new_images" accept=".png, .jpg, .jpeg, .webp" multiple class="mt-2 w-full border">
                </div>
            </template>
            """

        for image in new_images:
            image_pk = str(uuid.uuid4())
            image_created_at = int(time.time())
            filename = f"{item_pk}_{uuid.uuid4()}.{image.filename.split('.')[-1]}"
            path = f"images/{filename}"
            ic(f"Saving new image to {path}")
            image.save(path)  # Save the new image with the new filename

            # Insert the new image filename into the items_images table (without path)
            conn.execute("INSERT INTO items_images (image_pk, image_url, item_fk, image_created_at) VALUES (?, ?, ?, ?)",
                         (image_pk, filename, item_pk, image_created_at))
            conn.commit()

        conn.execute("""
            UPDATE items
            SET item_name = ?, item_price_per_night = ?, item_updated_at = ?
            WHERE item_pk = ? AND item_owner_fk = ?
        """, (validated_item_name, validated_item_price, int(time.time()), item_pk, user['user_id']))
        conn.commit()

        return """
        <template mix-redirect="/">
            <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative" role="alert">
                <strong class="font-bold">Success!</strong>
                <span class="block sm:inline">Property has been successfully updated.</span>
            </div>
        </template>
        """
    except Exception as ex:
        ic(ex)
    finally:
        if conn:
            conn.close()

#EDIT PROPERTY DIALOG
@get("/edit_property_dialog/<item_pk>")
def edit_property_dialog(item_pk):
    try:
        user_session = request.get_cookie("session", secret=x.COOKIE_SECRET)
        if not user_session:
            return redirect("/login")

        user = json.loads(user_session)
        if user.get('role') != 'partner':
            return "Unauthorized"

        conn = x.get_db_connection()
        item = conn.execute("SELECT * FROM items WHERE item_pk = ? AND item_owner_fk = ?", (item_pk, user['user_id'])).fetchone()
        if not item:
            return "Item not found or unauthorized"

        return template("edit_property_dialog.html", item=item)
    except Exception as ex:
        ic(ex)
        return str(ex)
    finally:
        if conn:
            conn.close()




############################# DELETE PROPERTY
@delete("/delete_property/<item_pk>")
def delete_property(item_pk):
    try:
        user_session = request.get_cookie("session", secret=x.COOKIE_SECRET)
        if not user_session:
            return redirect("/login")

        user = json.loads(user_session)
        if user.get('role') != 'partner':
            return "Unauthorized"

        conn = x.get_db_connection()
        conn.execute("DELETE FROM items WHERE item_pk = ? AND item_owner_fk = ?", (item_pk, user['user_id']))
        conn.execute("DELETE FROM items_images WHERE item_fk = ?", (item_pk,))
        conn.commit()

        return f"""
        <template mix-redirect="/">
            <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative" role="alert">
                <strong class="font-bold">Success!</strong>
                <span class="block sm:inline">Property has been successfully deleted.</span>
            </div>
        </template>
        """
    except Exception as ex:
        ic(ex)
        return str(ex)
    finally:
        if conn:
            conn.close()


############################# DELETE PROPERTY IMAGES FOR EDITING
@delete("/remove_image/<item_pk>/<image_url>")
def remove_image(item_pk, image_url):
    try:
        user_session = request.get_cookie("session", secret=x.COOKIE_SECRET)
        if not user_session:
            return redirect("/login")

        user = json.loads(user_session)
        if user.get('role') != 'partner':
            return "Unauthorized"

        conn = x.get_db_connection()
        conn.execute("DELETE FROM items_images WHERE item_fk = ? AND image_url = ?", (item_pk, image_url))
        conn.commit()

        # Remove the image file from the filesystem
        image_path = os.path.join("images", image_url)
        if os.path.exists(image_path):
            os.remove(image_path)

        return f"""
        <template mix-redirect="/">
            <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative" role="alert">
                <strong class="font-bold">Success!</strong>
                <span class="block sm:inline">Image has been successfully deleted.</span>
            </div>
        </template>
        """
    except Exception as ex:
        ic(ex)
        return str(ex)
    finally:
        if conn:
            conn.close()