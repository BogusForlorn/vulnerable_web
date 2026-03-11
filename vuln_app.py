#!/usr/bin/env python3
# vuln_app.py
from flask import Flask, request, render_template, redirect, session, g, render_template_string
import sqlite3
import os
import requests
import subprocess
import pickle
import base64
import future.standard_library

app = Flask(__name__)
app.secret_key = 'super-secret-key'

DATABASE = 'app.db'

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
        os.remove(DATABASE) # Always reset for this update
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                bio TEXT DEFAULT 'No bio yet.'
            )
        ''')
        c.execute('''
            CREATE TABLE comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE secrets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,
                value TEXT NOT NULL
            )
        ''')
        c.execute("INSERT INTO users (username, password, bio) VALUES ('admin', 'buckaroo', 'The Boss.')")
        c.execute("INSERT INTO secrets (key, value) VALUES ('flag', 'CTF{THIS_IS_A_SECRET_FLAG}')")
        conn.commit()
    print("[+] Database initialized.")

@app.route('/')
def index():
    db = get_db()
    c = db.cursor()
    c.execute("SELECT content FROM comments")
    comments = c.fetchall()
    
    # CSRF Vulnerability: No token, and performs actions on behalf of user
    # Also added links to new vulnerable features
    return render_template('index.html', comments=comments)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # SQL Injection (Original)
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

@app.route('/comment', methods=['POST'])
def comment():
    content = request.form.get('content', '')
    db = get_db()
    c = db.cursor()
    # Stored XSS (Original)
    c.execute("INSERT INTO comments (content) VALUES (?)", (content,))
    db.commit()
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

# OS Command Injection
@app.route('/ping', methods=['GET', 'POST'])
def ping():
    result = ""
    if request.method == 'POST':
        host = request.form.get('host', '')
        # Vulnerable to command injection (e.g., host="8.8.8.8; ls -la")
        command = f"ping -c 1 {host}"
        result = subprocess.getoutput(command)
    return f"""
    <h1>Ping Tool</h1>
    <form method="POST">
        Host: <input type="text" name="host">
        <input type="submit" value="Ping">
    </form>
    <pre>{result}</pre>
    <a href="/">Back</a>
    """

# SSRF
@app.route('/fetch-url', methods=['GET', 'POST'])
def fetch_url():
    content = ""
    if request.method == 'POST':
        url = request.form.get('url', '')
        try:
            # Vulnerable to SSRF
            response = requests.get(url, timeout=5)
            content = response.text
        except Exception as e:
            content = str(e)
    return f"""
    <h1>URL Fetcher</h1>
    <form method="POST">
        URL: <input type="text" name="url">
        <input type="submit" value="Fetch">
    </form>
    <div style="border: 1px solid black; padding: 10px;">
        {content}
    </div>
    <a href="/">Back</a>
    """

# Path Traversal / LFI
@app.route('/view-file')
def view_file():
    filename = request.args.get('file')
    if not filename:
        return "Usage: /view-file?file=filename<br><a href='/'>Back</a>"
    try:
        # Vulnerable to path traversal (e.g., file=../../../../etc/passwd)
        # Note: In a real flask app, this is often done with send_from_directory incorrectly
        with open(filename, 'r') as f:
            content = f.read()
        return f"<h1>Viewing: {filename}</h1><pre>{content}</pre><br><a href='/'>Back</a>"
    except Exception as e:
        return f"Error: {str(e)}<br><a href='/'>Back</a>"

# Insecure Deserialization
@app.route('/debug-pickle', methods=['GET', 'POST'])
def debug_pickle():
    data = request.args.get('data')
    if data:
        try:
            # Vulnerable to insecure deserialization
            decoded_data = base64.b64decode(data)
            obj = pickle.loads(decoded_data)
            return f"Deserialized: {obj}<br><a href='/'>Back</a>"
        except Exception as e:
            return f"Error: {str(e)}<br><a href='/'>Back</a>"
    return "Provide base64 data to deserialize via 'data' parameter.<br><a href='/'>Back</a>"

# CSRF and SQL Injection
@app.route('/update-profile', methods=['POST'])
def update_profile():
    if 'username' not in session:
        return redirect('/login')
    
    # Vulnerable to CSRF (no token)
    # Also vulnerable to SQL Injection in the bio field
    new_bio = request.form.get('bio', '')
    username = session['username']
    
    db = get_db()
    c = db.cursor()
    query = f"UPDATE users SET bio = '{new_bio}' WHERE username = '{username}'"
    print("[DEBUG] Executing:", query)
    c.execute(query)
    db.commit()
    return f"Profile updated to: {new_bio}<br><a href='/'>Back</a>"

# Server-Side Template Injection (SSTI)
@app.route('/hello')
def hello():
    name = request.args.get('name', 'Guest')
    # Vulnerable to SSTI
    template = f'<h1>Hello, {name}!</h1><a href="/">Back</a>'
    return render_template_string(template)

@app.route('/admin-panel')
def admin_panel():
    # Broken Access Control: only checks session, but maybe we can bypass it?
    # Or maybe it's accessible if we know the URL (it is)
    if session.get('username') != 'admin':
        return "Access Denied. Only 'admin' can see this.<br><a href='/'>Back</a>", 403
    
    db = get_db()
    c = db.cursor()
    c.execute("SELECT * FROM secrets")
    secrets = c.fetchall()
    
    return f"""
    <h1>Admin Panel</h1>
    <p>Welcome, admin! Here are the system secrets:</p>
    <ul>
        {"".join([f"<li>{s[1]}: {s[2]}</li>" for s in secrets])}
    </ul>
    <a href="/">Back</a>
    """

@app.route('/hidden-backup')
def hidden_backup():
    return """
    <h1>Backup File</h1>
    <p>Old credentials:</p>
    <pre>
    [backup]
    admin_user=admin
    admin_pass=buckaroo
    db_backup_key=12345
    </pre>
    <a href="/">Back</a>
    """

import importlib

# File Upload (Dangerous: can be used to exploit CVE-2025-50817)
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    message = ""
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            # Dangerous: saves the file in the current directory
            file.save(os.path.join(os.getcwd(), file.filename))
            message = f"File {file.filename} uploaded successfully!"
    return f"""
    <h1>File Uploader</h1>
    <p>{message}</p>
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="file">
        <input type="submit" value="Upload">
    </form>
    <a href="/">Back</a>
    """

@app.route('/reload-future')
def reload_future():
    # To demonstrate CVE-2025-50817, we reload the module
    importlib.reload(future.standard_library)
    return "Reloaded future.standard_library and executed any side-loading payloads (if present)."

if __name__ == '__main__':
    # init_db() # We can uncomment this if we want it to init on run
    app.run(debug=True, host='0.0.0.0', port=5000)

