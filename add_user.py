import sqlite3
from werkzeug.security import generate_password_hash

def create_user(username, password):
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    with sqlite3.connect('database1.db') as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            print('User created successfully')
        except sqlite3.IntegrityError:
            print('Username already exists')

create_user('Nina', '123')
