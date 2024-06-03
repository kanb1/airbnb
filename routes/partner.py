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
        response.status = 200
        return template("add_property.html")
    except Exception as ex:
        ic(ex)
        response.status = 500
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
            response.status = 401
            return redirect("/login")

        # Load User Data: Parses the JSON session data to get user details, converting the session string back into a Python dictionary.
        user = json.loads(user_session)
        # Checks if the userrole is not a partner
        if user.get('role') != 'partner':
            ic("User is not a partner, unauthorized")
            response.status = 403
            return "Unauthorized"

        # generates a unique primary key for the new property with uuid
        item_pk = str(uuid.uuid4())
        # Get Item Name: Retrieves the property name from the form data and removes leading/trailing whitespace with .strip()
        item_name = request.forms.get('item_name').strip()
        item_price_per_night = request.forms.get('item_price_per_night').strip()

        # Validate the inputs
        validated_item_name = x.validate_item_name(item_name)
        validated_item_price = x.validate_item_price(item_price_per_night)

        # Define latitude and longitude within Denmark
        # Latitude: Generates a random latitude within Denmark's geographic range.
        item_lat = random.uniform(54.5, 57.75)
        item_lon = random.uniform(8.0, 12.75)
        item_stars = 5  # Default value for stars
        # Created At: Sets the current timestamp as the creation time.
        item_created_at = int(time.time())
        item_updated_at = 0
        # Owner Foreign Key: Sets the owner foreign key to the current user's ID from the session data.
        item_owner_fk = user['user_id']

        db = x.get_db_connection()

        # Handle images
        # Retrieve Images: Gets all uploaded images from the form using request.files.getall('item_images').
        # validate the images
        try:
            item_images = request.files.getall('item_images')
            x.validate_item_images(item_images)
        except ValueError as ve:
            response.status = 400
            # Returns an HTML template displaying the error message.
            return f"""
            <template mix-target="#file_container" mix-replace>
                <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
                    <p class="text-red-700">{ve}</p>
                    <input name="item_images" id="item_images" class="w-full border" type="file" accept=".png, .jpg, .jpeg, .webp" multiple required max="5" min="1">
                </div>
            </template>
            """
        # Loop Through Images: Iterates through each image, starting the index at 1.
        for index, image in enumerate(item_images, start=1):
            # generates a unique primary key for each image using uuid
            image_pk = str(uuid.uuid4())
            # sets the current timestamp
            image_created_at = int(time.time())
            # Create Filename: Constructs a new filename using the property ID and index, preserving the original file extension.
            # The index in the code refers to the position of each image in the list of uploaded images. When you upload multiple images, they are handled in a list, and the enumerate function is used to keep track of the position (or index) of each image in that list. This helps in creating unique filenames for each image associated with a property.
            # -1 the last element of the list --> filename extension
            filename = f"{item_pk}_{index}.{image.filename.split('.')[-1]}"
            # Set Path: Defines the path where the image will be saved. Here under my images folder
            path = f"images/{filename}"
            ic(f"Saving image to {path}")
            image.save(path)  # Save the image with the new filename

            # Insert the image filename into the items_images table (without path)
            db.execute("INSERT INTO items_images (image_pk, image_url, item_fk, image_created_at) VALUES (?, ?, ?, ?)",
                       (image_pk, filename, item_pk, image_created_at))
            # commit: save changes
            db.commit()

        # Inserts the property details into the items table in the database.
        db.execute("INSERT INTO items (item_pk, item_name, item_lat, item_lon, item_stars, item_price_per_night, item_created_at, item_updated_at, item_owner_fk) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   (item_pk, validated_item_name, item_lat, item_lon, item_stars, validated_item_price, item_created_at, item_updated_at, item_owner_fk))
        db.commit()

        response.status = 201

        # success response
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
        response.status = 500

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
            response.status = 401
            return redirect("/login")

        user = json.loads(user_session)
        if user.get('role') != 'partner':
            response.status = 403
            return "Unauthorized"
        
        # Extracts and trims the item_name from the form.
        item_name = request.forms.get('item_name').strip()
        item_price_per_night = request.forms.get('item_price_per_night').strip()

        # Validates the item name
        validated_item_name = x.validate_item_name(item_name)
        validated_item_price = x.validate_item_price(item_price_per_night)

        conn = x.get_db_connection()

        # Handle new images
        # request.files.getall('new_images'): Retrieves all new image files from the form.
        new_images = request.files.getall('new_images') 
        # However, .getAll() always returns a file called 'empty' if there is no new files uploaded
        if(new_images[0].filename == 'empty'): # This checks if the 'empty' file
            new_images = [] #If it's there, it will reset the array to nothing to not interrupt the edit flow.

        # Fetches the current images associated with the property from the database.
        current_images = conn.execute("SELECT image_url FROM items_images WHERE item_fk = ?", (item_pk,)).fetchall()
        # Converts the list of rows into a list of image URLs.
        current_images = [img['image_url'] for img in current_images]

        
        try:
            # Validates the combined list of current and new images.
            x.validate_item_images(current_images, new_images)
        except ValueError as ve:
            response.status = 400
            return f"""
            <template mix-target="#file_container" mix-replace>
                <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
                    <p class="text-red-700">{ve}</p>
                    <input type="file" name="new_images" accept=".png, .jpg, .jpeg, .webp" multiple class="mt-2 w-full border">
                </div>
            </template>
            """
        # Iterates over each new image.
        for image in new_images:
            # Generates a unique ID for each image.
            image_pk = str(uuid.uuid4())
            image_created_at = int(time.time())
            # Constructs a new filename using the property ID and a UUID.
            # the -1: For example, if image.filename is "example.image.jpg", split('.') would return ["example", "image", "jpg"].This is a list indexing operation. In Python, negative indices are used to access elements from the end of the list. -1 refers to the last element in the list.
            # Continuing the example, ["example", "image", "jpg"][-1] would return "jpg".
            # {item_pk}: The property ID.
            # {uuid.uuid4()}: A new unique identifier.
            # {image.filename.split('.')[-1]}: The file extension extracted from the original filename.
            # This ensures that each image file is uniquely named while preserving its original file extension.
            filename = f"{item_pk}_{uuid.uuid4()}.{image.filename.split('.')[-1]}"
            path = f"images/{filename}"
            ic(f"Saving new image to {path}")
            image.save(path)  # Save the new image with the new filename

            # Insert the new image filename into the items_images table (without path)
            conn.execute("INSERT INTO items_images (image_pk, image_url, item_fk, image_created_at) VALUES (?, ?, ?, ?)",
                         (image_pk, filename, item_pk, image_created_at))
            conn.commit()

        # Updates the property record in the items table.
        conn.execute("""
            UPDATE items
            SET item_name = ?, item_price_per_night = ?, item_updated_at = ?
            WHERE item_pk = ? AND item_owner_fk = ?
        """, (validated_item_name, validated_item_price, int(time.time()), item_pk, user['user_id']))
        conn.commit()

        response.status = 200

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
        response.status = 500

    finally:
        if conn:
            conn.close()

#EDIT PROPERTY DIALOG
#The <item_pk> part is a dynamic segment that captures the property ID (item_pk) from the URL and passes it as an argument to the edit_property_dialog function
@get("/edit_property_dialog/<item_pk>")
def edit_property_dialog(item_pk):
    try:
        user_session = request.get_cookie("session", secret=x.COOKIE_SECRET)
        if not user_session:
            response.status = 401
            return redirect("/login")

        user = json.loads(user_session)
        if user.get('role') != 'partner':
            response.status = 403
            return "Unauthorized"

        conn = x.get_db_connection()
        # retrieve the item details from the items table where the item_pk matches the provided item_pk and item_owner_fk matches the user's ID.
        item = conn.execute("SELECT * FROM items WHERE item_pk = ? AND item_owner_fk = ?", (item_pk, user['user_id'])).fetchone()
        if not item:
            response.status = 404
            return "Item not found or unauthorized"
        
        response.status = 200
        # edit_property_dialog.html template, passing the retrieved item details as a context variable.
        return template("edit_property_dialog.html", item=item)
    except Exception as ex:
        ic(ex)
        response.status = 500
        return str(ex)
    finally:
        if conn:
            conn.close()




############################# DELETE PROPERTY
# It takes one parameter from the URL: item_pk, which is the primary key of the property to be deleted.
@delete("/delete_property/<item_pk>")
def delete_property(item_pk):
    try:
        user_session = request.get_cookie("session", secret=x.COOKIE_SECRET)
        if not user_session:
            response.status = 401
            return redirect("/login")

        user = json.loads(user_session)
        if user.get('role') != 'partner':
            response.status = 403
            return "Unauthorized"

        conn = x.get_db_connection()
        # Delete Property Record: Execute an SQL command to delete the property record from the items table where item_pk matches item_pk and item_owner_fk matches the user's ID.
        conn.execute("DELETE FROM items WHERE item_pk = ? AND item_owner_fk = ?", (item_pk, user['user_id']))
        # Delete Related Images: Execute an SQL command to delete all image records from the items_images table where item_fk matches item_pk.
        conn.execute("DELETE FROM items_images WHERE item_fk = ?", (item_pk,))
        conn.commit()
        
        response.status = 200

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
        response.status = 500
        return str(ex)
    finally:
        if conn:
            conn.close()


############################# DELETE PROPERTY IMAGES FOR EDITING
# It takes two parameters from the URL: item_pk (the primary key of the item) and image_url (the URL of the image to be removed).
@delete("/remove_image/<item_pk>/<image_url>")
def remove_image(item_pk, image_url):
    try:
        user_session = request.get_cookie("session", secret=x.COOKIE_SECRET)
        if not user_session:
            response.status = 401
            return redirect("/login")

        user = json.loads(user_session)
        if user.get('role') != 'partner':
            response.status = 403
            return "Unauthorized"

        conn = x.get_db_connection()
        # Execute an SQL command to delete the image record from the items_images table where item_fk matches item_pk and image_url matches image_url.
        conn.execute("DELETE FROM items_images WHERE item_fk = ? AND image_url = ?", (item_pk, image_url))
        conn.commit()

        # Remove the image file from the filesystem
        # Construct the full file path of the image using os.path.join("images", image_url).
        image_path = os.path.join("images", image_url)
        if os.path.exists(image_path):
            # Delete File: If the file exists, delete it using os.remove(image_path).
            os.remove(image_path)
        
        response.status = 200

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
        response.status = 500
        return str(ex)
    finally:
        if conn:
            conn.close()