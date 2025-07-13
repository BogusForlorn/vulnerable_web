#!/usr/bin/env python3
# reset_db.py

import os
import sqlite3

DATABASE = 'app.db'

def reset_db():
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
        print(f"[+] Deleted old {DATABASE}")

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL
        )
    ''')
    # Insert known good admin creds
    c.execute("INSERT INTO users (username, password) VALUES ('admin', 'admin123')")
    conn.commit()
    conn.close()
    print(f"[+] New database initialized with default admin account.")

if __name__ == '__main__':
    reset_db()

