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