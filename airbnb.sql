DROP TABLE IF EXISTS users;

CREATE TABLE users(
    user_pk                 TEXT,
    user_username           TEXT,
    user_name               TEXT,
    user_last_name          TEXT,
    -- email should be unique, I am testing the email verification so I removed it temporarily. Remember to put it back to unique afterwards, or argue on it to the exam
    user_email              TEXT,
    user_password           TEXT,
    user_role               TEXT,
    user_created_at         INTEGER,
    user_updated_at         INTEGER,
    user_is_verified        INTEGER,
    user_is_blocked         INTEGER,
    user_verification_key   TEXT,
    user_deletion_verification_key TEXT,
    user_is_deleted         INTEGER DEFAULT 0,
    reset_token             TEXT,
    PRIMARY KEY(user_pk)
) WITHOUT ROWID;

SELECT * FROM users;
DELETE FROM users WHERE user_pk = "admin-user-id" OR user_pk = "90a4c5d5-79e4-4ea6-9a16-4e3064632240" OR user_pk = "d208f72b-8c72-41e7-b54e-4ad358873aff";
DELETE FROM users WHERE user_pk = "admin-user-id";

-- Make the admin-user already
INSERT INTO users (
    user_pk, user_username, user_name, user_last_name, user_email,
    user_password, user_role, user_created_at, user_updated_at,
    user_is_verified, user_is_blocked, user_verification_key
) VALUES (
    '7c2d1a1f-c38a-41e5-a70e-0341df6b0c30', 'admin', 'Admin', 'User', 'admin@example.com',
    '$2b$12$N8VhBZo.zd7CZqz/WlGQO.Yc5QeU4cvjOiWg.4Z7cCgKSwx10zUoO',  -- this is "adminpassword" hashed with bcrypt
    'admin', strftime('%s', 'now'), strftime('%s', 'now'), 1, 0, NULL
);





--------------------------------------------- ITEMS
DROP TABLE IF EXISTS items;

CREATE TABLE items (
    item_pk                 TEXT PRIMARY KEY,
    item_name               TEXT,
    item_splash_image       TEXT,
    item_lat                TEXT,
    item_lon                TEXT,
    item_stars              REAL,
    item_price_per_night    REAL,
    item_booked             INT DEFAULT 0,
    item_created_at         INTEGER,
    item_updated_at         INTEGER,
    item_owner_fk           TEXT,
    item_is_blocked         INT DEFAULT 0,
    FOREIGN KEY(item_owner_fk) REFERENCES users(user_pk)
) WITHOUT ROWID;

INSERT INTO items VALUES
("62f2ec02b59043ac9492087feb9dfb611", "Martofte", "8c6b03c866d641ff8096f840bbfe68a1.webp", "55.676098", "12.568337", 4.0, 2344, 0, 1, 0, "c403b9ce-d363-47c2-aeff-0715f1dceeb1", 0),
("62f2ec02b59043ac9492087feb9dfb612", "Assens", "8c6b03c866d641ff8096f840bbfe68a2.webp", "55.676070", "12.568334", 3.0, 2344, 0, 2, 0, "c403b9ce-d363-47c2-aeff-0715f1dceeb1", 0),
("62f2ec02b59043ac9492087feb9dfb613", "Otterup", "8c6b03c866d641ff8096f840bbfe68a3.webp", "55.676010", "12.56834", 5.0, 2344, 0, 3, 0, "c403b9ce-d363-47c2-aeff-0715f1dceeb1", 0),
("62f2ec02b59043ac9492087feb9dfb614", "Kalundborg", "8c6b03c866d641ff8096f840bbfe68a4.webp", "55.676028", "12.568437", 2.0, 2344, 0, 4, 0, "c403b9ce-d363-47c2-aeff-0715f1dceeb1", 0),
("62f2ec02b59043ac9492087feb9dfb615", "Slagelse", "8c6b03c866d641ff8096f840bbfe68a5.webp", "55.676099", "12.568339", 3.0, 2344, 0, 5, 0, "c403b9ce-d363-47c2-aeff-0715f1dceeb1", 0),
("62f2ec02b59043ac9492087feb9dfb616", "Aarhus", "8c6b03c866d641ff8096f840bbfe68a6.webp", "55.676198", "12.568331", 1.0, 2344, 0, 6, 0, "c403b9ce-d363-47c2-aeff-0715f1dceeb1", 0),
("62f2ec02b59043ac9492087feb9dfb617", "Gørlev", "8c6b03c866d641ff8096f840bbfe68a7.webp", "55.676298", "12.568311", 3.0, 2344, 0, 7, 0, "c403b9ce-d363-47c2-aeff-0715f1dceeb1", 0),
("62f2ec02b59043ac9492087feb9dfb618", "Haderslev", "8c6b03c866d641ff8096f840bbfe68a8.webp", "55.676598", "12.568322", 2.0, 2344, 0, 8, 0, "c403b9ce-d363-47c2-aeff-0715f1dceeb1", 0),
("62f2ec02b59043ac9492087feb9dfb619", "Faxe", "8c6b03c866d641ff8096f840bbfe68a9.webp", "55.676398", "12.568312", 2.0, 2344, 0, 9, 0, "c403b9ce-d363-47c2-aeff-0715f1dceeb1", 0),
("62f2ec02b59043ac9492087feb9dfb6110", "Vejl", "8c6b03c866d641ff8096f840bbfe68a10.webp", "55.676098", "12.568323", 2.0, 2344, 0, 10, 0, "c403b9ce-d363-47c2-aeff-0715f1dceeb1", 0);

SELECT * FROM items ORDER BY item_created_at DESC;
-- DELETE FROM items WHERE item_pk = "4f07f353-d01b-4483-8403-c216dcbe22ff";




--------------------------------------------- BOOKINGS

DROP TABLE IF EXISTS bookings;
CREATE TABLE bookings(
    booking_pk      TEXT,
    user_id         TEXT,
    item_id         TEXT,
    FOREIGN KEY(user_id) REFERENCES users(user_pk),
    FOREIGN KEY(item_id) REFERENCES items(item_pk)
    PRIMARY KEY(booking_pk)
)WITHOUT ROWID;

SELECT * FROM bookings;

--------------------------------------------- STORE THE IMAGES RELATED TO EACH PROPERTY



DROP TABLE IF EXISTS items_images;
CREATE TABLE items_images(
    image_pk                TEXT,
    image_url               TEXT,
    item_fk                 TEXT,
    image_created_at        INTEGER,
    PRIMARY KEY(image_pk),
    FOREIGN KEY(item_fk) REFERENCES items(item_pk)
) WITHOUT ROWID;

SELECT * FROM items_images
