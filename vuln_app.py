#!/usr/bin/env python3
# vuln_app.py
from flask import Flask, request, render_template, redirect, session, g
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'super-secret-key'

DATABASE = 'app.db'

# -----------------------------
# DB Setup
# -----------------------------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    if os.path.exists(DATABASE):
        return
    with sqlite3.connect(DATABASE) as conn:
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
        c.execute("INSERT INTO users (username, password) VALUES ('admin', 'admin123')")
        conn.commit()
    print("[+] Database initialized.")

# -----------------------------
# Routes
# -----------------------------

@app.route('/')
def index():
    db = get_db()
    c = db.cursor()
    c.execute("SELECT content FROM comments")
    comments = c.fetchall()
    return render_template('index.html', comments=comments)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        print("[DEBUG] Executing:", query)
        c = get_db().cursor()
        c.execute(query)
        user = c.fetchone()
        
        if user:
            session['username'] = username
            return redirect('/')
        else:
            error = 'Invalid credentials'
    return render_template('login.html', error=error)

@app.route('/comment', methods=['GET', 'POST'])
def comment():
    if request.method == 'POST':
        content = request.form['content']  # No sanitization
        db = get_db()
        c = db.cursor()
        c.execute("INSERT INTO comments (content) VALUES (?)", (content,))
        db.commit()
        return redirect('/')
    return render_template('comment.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

# -----------------------------
# New vulnerable directories
# -----------------------------
@app.route('/admin-panel')
def admin_panel():
    return """
    <h1>Admin Panel</h1>
    <p>This is a fake admin panel. You should not have found this!</p>
    <p>Only admin should see this.</p>
    """

@app.route('/hidden-backup')
def hidden_backup():
    return """
    <h1>Backup File</h1>
    <p>Old credentials:</p>
    <pre>
    [backup]
    admin_user=admin
    admin_pass=admin123
    db_backup_key=12345
    </pre>
    """

# -----------------------------
# Main
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

