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
    reset_token             TEXT,
    PRIMARY KEY(user_pk)
) WITHOUT ROWID;

SELECT * FROM users;
-- DELETE FROM users WHERE user_pk = "6f5acc09-2136-44d7-b7d9-adb229071df1" OR user_pk = "26d25c65-83bb-49b1-b415-d0a42c71b7bb" OR user_pk = "251ee0fe-3c25-4427-9927-79ab01c74f19" OR user_pk = "1f56ce48-3e15-4540-9bb3-e65092cb2265" OR user_pk = "082629e1-eecf-4b33-b10a-0a76071d5954";

--------------------------------------------- ITEMS
DROP TABLE IF EXISTS items;

CREATE TABLE items(
    item_pk                 TEXT,
    item_name               TEXT,
    item_splash_image       TEXT,
    item_lat                TEXT,
    item_lon                TEXT,
    item_stars              REAL,
    item_price_per_night    REAL,
    item_created_at         INTEGER,
    item_updated_at         INTEGER,
    item_owner_fk           TEXT,
    PRIMARY KEY(item_pk)          
)WITHOUT ROWID;

INSERT INTO items VALUES
("62f2ec02b59043ac9492087feb9dfb611", "Martofte", "8c6b03c866d641ff8096f840bbfe68a1.webp", "55.676098", "12.568337", 4.0, 2344, 1, 0, "c403b9ce-d363-47c2-aeff-0715f1dceeb1"),
("62f2ec02b59043ac9492087feb9dfb612", "Assens", "8c6b03c866d641ff8096f840bbfe68a2.webp", "55.676070", "12.568334", 3.0, 2344, 2, 0, "c403b9ce-d363-47c2-aeff-0715f1dceeb1"),
("62f2ec02b59043ac9492087feb9dfb613", "Otterup", "8c6b03c866d641ff8096f840bbfe68a3.webp", "55.676010", "12.56834", 5.0, 2344, 3, 0, "c403b9ce-d363-47c2-aeff-0715f1dceeb1"),
("62f2ec02b59043ac9492087feb9dfb614", "Kalundborg", "8c6b03c866d641ff8096f840bbfe68a4.webp", "55.676028", "12.568437", 2.0, 2344, 4, 0, "c403b9ce-d363-47c2-aeff-0715f1dceeb1"),
("62f2ec02b59043ac9492087feb9dfb615", "Slagelse", "8c6b03c866d641ff8096f840bbfe68a5.webp", "55.676099", "12.568339", 3.0, 2344, 5, 0, "c403b9ce-d363-47c2-aeff-0715f1dceeb1"),
("62f2ec02b59043ac9492087feb9dfb616", "Aarhus", "8c6b03c866d641ff8096f840bbfe68a6.webp", "55.676198", "12.568331", 1.0, 2344, 6, 0, "c403b9ce-d363-47c2-aeff-0715f1dceeb1"),
("62f2ec02b59043ac9492087feb9dfb617", "Gørlev", "8c6b03c866d641ff8096f840bbfe68a7.webp", "55.676298", "12.568311", 3.0, 2344, 7, 0, "c403b9ce-d363-47c2-aeff-0715f1dceeb1"),
("62f2ec02b59043ac9492087feb9dfb618", "Haderslev", "8c6b03c866d641ff8096f840bbfe68a8.webp", "55.676598", "12.568322", 2.0, 2344, 8, 0, "c403b9ce-d363-47c2-aeff-0715f1dceeb1"),
("62f2ec02b59043ac9492087feb9dfb619", "Faxe", "8c6b03c866d641ff8096f840bbfe68a9.webp", "55.676398", "12.568312", 2.0, 2344, 9, 0, "c403b9ce-d363-47c2-aeff-0715f1dceeb1"),
("62f2ec02b59043ac9492087feb9dfb6110", "Vejl", "8c6b03c866d641ff8096f840bbfe68a10.webp", "55.676098", "12.568323", 2.0, 2344, 10, 0, "c403b9ce-d363-47c2-aeff-0715f1dceeb1");

SELECT * FROM items ORDER BY item_created_at DESC;