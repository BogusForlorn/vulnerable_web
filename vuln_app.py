#!/usr/bin/env python3
# vuln_app.py
from flask import Flask, request, render_template, redirect, session, g, render_template_string
import sqlite3
import os
import sys
import requests
import subprocess
import pickle
import base64
import importlib
import future.standard_library

# Ensure current directory is in sys.path for CVE-2025-50817 side-loading
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

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
        os.remove(DATABASE)
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
        c.execute('''
            CREATE TABLE burger_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                burger_name TEXT NOT NULL,
                bun_type TEXT NOT NULL,
                patty_style TEXT NOT NULL,
                toppings TEXT NOT NULL,
                secret_sauce TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        c.execute("INSERT INTO users (username, password, bio) VALUES ('admin', 'buckaroo', 'The Boss.')")
        admin_user_id = c.lastrowid
        c.execute(
            """
            INSERT INTO burger_profiles
            (user_id, burger_name, bun_type, patty_style, toppings, secret_sauce)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                admin_user_id,
                "Admin Overdrive",
                "Potato Bun",
                "Smash Patty",
                "Cheddar, Onion Jam, Pickles",
                "Black Pepper Aioli",
            ),
        )
        c.execute("INSERT INTO secrets (key, value) VALUES ('flag', 'CTF{THIS_IS_A_SECRET_FLAG}')")
        conn.commit()
    print("[+] Database initialized.")

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
        # SQL Injection
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        c = get_db().cursor()
        c.execute(query)
        user = c.fetchone()
        if user:
            session['username'] = username
            return redirect('/')
        else:
            error = 'Invalid credentials'
    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        burger_name = request.form.get('burger_name', '').strip()
        bun_type = request.form.get('bun_type', '').strip()
        patty_style = request.form.get('patty_style', '').strip()
        toppings = request.form.get('toppings', '').strip()
        secret_sauce = request.form.get('secret_sauce', '').strip()

        if not username or not password:
            error = 'Username and password are required'
        else:
            burger_name = burger_name or f"{username}'s Signature Stack"
            bun_type = bun_type or 'Sesame Bun'
            patty_style = patty_style or 'Classic Beef Patty'
            toppings = toppings or 'Lettuce, Tomato, Onion'
            secret_sauce = secret_sauce or 'House Sauce'

            db = get_db()
            c = db.cursor()
            try:
                c.execute(
                    "INSERT INTO users (username, password, bio) VALUES (?, ?, ?)",
                    (username, password, "No bio yet.")
                )
                user_id = c.lastrowid
                c.execute(
                    """
                    INSERT INTO burger_profiles
                    (user_id, burger_name, bun_type, patty_style, toppings, secret_sauce)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, burger_name, bun_type, patty_style, toppings, secret_sauce),
                )
                db.commit()
                session['username'] = username
                return redirect('/view-burger-profile')
            except sqlite3.IntegrityError:
                error = 'Username already exists'

    return render_template('register.html', error=error)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

# Stored XSS - Legitimate-looking comment feature
@app.route('/submit-note', methods=['POST'])
def submit_note():
    content = request.form.get('note', '')
    db = get_db()
    c = db.cursor()
    c.execute("INSERT INTO comments (content) VALUES (?)", (content,))
    db.commit()
    return redirect('/')

# Command Injection - Legitimate-looking server health check
@app.route('/ping-service', methods=['GET', 'POST'])
def ping_service():
    result = ""
    if request.method == 'POST':
        endpoint = request.form.get('endpoint', '')
        # Vulnerable to command injection
        command = f"ping -c 1 {endpoint}"
        result = subprocess.getoutput(command)
    return f"""
    <h1>Kitchen Server Diagnostic</h1>
    <form method="POST">
        Internal Node: <input type="text" name="endpoint" placeholder="e.g. 127.0.0.1">
        <input type="submit" value="Check Health">
    </form>
    <pre>{result}</pre>
    <a href="/">Back</a>
    """

# SSRF - Legitimate-looking network test tool
@app.route('/internal-network-test', methods=['GET', 'POST'])
def network_test():
    content = ""
    if request.method == 'POST':
        node_url = request.form.get('node_url', '')
        try:
            # Vulnerable to SSRF
            response = requests.get(node_url, timeout=5)
            content = response.text
        except Exception as e:
            content = str(e)
    return f"""
    <h1>Node Communication Tester</h1>
    <form method="POST">
        Target Node URL: <input type="text" name="node_url" placeholder="http://internal-api:8080/status">
        <input type="submit" value="Test Link">
    </form>
    <div style="border: 1px solid black; padding: 10px;">
        {content}
    </div>
    <a href="/">Back</a>
    """

# Path Traversal / LFI - Legitimate-looking asset explorer
@app.route('/asset-viewer')
def asset_viewer():
    path = request.args.get('path')
    if not path:
        return "Usage: /asset-viewer?path=assets/logo.png<br><a href='/'>Back</a>"
    try:
        # Vulnerable to path traversal
        with open(path, 'r') as f:
            content = f.read()
        return f"<h1>Viewing Kitchen Asset: {path}</h1><pre>{content}</pre><br><a href='/'>Back</a>"
    except Exception as e:
        return f"Error loading asset: {str(e)}<br><a href='/'>Back</a>"

# Insecure Deserialization - Legitimate-looking session monitor
@app.route('/session-debug', methods=['GET', 'POST'])
def session_debug():
    token = request.args.get('token')
    if token:
        try:
            # Vulnerable to insecure deserialization
            decoded_data = base64.b64decode(token)
            # Ensure path includes current dir for CVE-2025-50817 side effect if needed
            obj = pickle.loads(decoded_data)
            return f"Session Context Decoded: {obj}<br><a href='/'>Back</a>"
        except Exception as e:
            return f"Error decoding token: {str(e)}<br><a href='/'>Back</a>"
    return "Provide staff token for debug analysis.<br><a href='/'>Back</a>"

# CSRF and SQL Injection - Legitimate profile update
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        # Vulnerable to CSRF and SQL Injection
        new_bio = request.form.get('bio', '')
        username = session['username']
        db = get_db()
        c = db.cursor()
        query = f"UPDATE users SET bio = '{new_bio}' WHERE username = '{username}'"
        c.execute(query)
        db.commit()
        return f"Kitchen Profile Updated!<br><a href='/'>Back</a>"
    
    return f"""
    <h1>Kitchen Profile</h1>
    <p>Logged in as: {session['username']}</p>
    <form method="POST">
        Update Kitchen Motto: <input type="text" name="bio">
        <button type="submit">Update</button>
    </form>
    <a href="/">Back</a>
    """


@app.route('/view-burger-profile')
def view_burger_profile():
    if 'username' not in session:
        return redirect('/login')

    db = get_db()
    c = db.cursor()
    c.execute("SELECT id, username FROM users WHERE username = ?", (session['username'],))
    current_user = c.fetchone()

    if not current_user:
        return "Session user no longer exists. Please register again.<br><a href='/'>Back</a>", 404

    requested_id = request.args.get('id', type=int)
    if requested_id is None:
        c.execute("SELECT id FROM burger_profiles WHERE user_id = ?", (current_user[0],))
        own_profile = c.fetchone()
        if not own_profile:
            return "No burger profile found for this account.<br><a href='/'>Back</a>", 404
        return redirect(f"/view-burger-profile?id={own_profile[0]}")

    # Intentional IDOR vulnerability: no check that profile belongs to current_user.
    c.execute(
        """
        SELECT bp.id, u.username, bp.burger_name, bp.bun_type, bp.patty_style, bp.toppings, bp.secret_sauce
        FROM burger_profiles bp
        JOIN users u ON u.id = bp.user_id
        WHERE bp.id = ?
        """,
        (requested_id,),
    )
    profile = c.fetchone()
    if not profile:
        return "Burger profile not found.<br><a href='/'>Back</a>", 404

    return render_template(
        'burger_profile.html',
        profile=profile,
        current_username=current_user[1],
    )

# SSTI - Legitimate personalized greeting
@app.route('/say-hello')
def say_hello():
    user = request.args.get('user', 'Chef')
    # Vulnerable to SSTI
    template = f'<h1>Greetings, {user}!</h1><p>Welcome to the grill room.</p><a href="/">Back</a>'
    return render_template_string(template)

# Broken Access Control - Legitimate-looking admin vault
@app.route('/kitchen-secrets')
def kitchen_secrets():
    if session.get('username') != 'admin':
        return "Access Denied. Only Senior Grill Architects can access the vault.<br><a href='/'>Back</a>", 403
    db = get_db()
    c = db.cursor()
    c.execute("SELECT * FROM secrets")
    secrets = c.fetchall()
    return f"""
    <h1>Kitchen Secrets Vault</h1>
    <ul>{"".join([f"<li>{s[1]}: {s[2]}</li>" for s in secrets])}</ul>
    <a href="/">Back</a>
    """

# File Upload - Legitimate-looking recipe upload (Used for CVE-2025-50817)
@app.route('/upload-recipe', methods=['GET', 'POST'])
def upload_recipe():
    message = ""
    if request.method == 'POST':
        recipe_file = request.files.get('recipe')
        if recipe_file:
            # DANGEROUS: Saves in CWD, enables CVE-2025-50817
            recipe_file.save(os.path.join(os.getcwd(), recipe_file.filename))
            message = f"Recipe {recipe_file.filename} uploaded to kitchen storage!"
    return f"""
    <h1>Recipe Image Uploader</h1>
    <p style="color: green;">{message}</p>
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="recipe">
        <input type="submit" value="Upload to Storage">
    </form>
    <a href="/">Back</a>
    """

# Trigger for CVE-2025-50817 - Legitimate-looking ingredient sync

@app.route('/sync-ingredients')

def sync_ingredients():

    # To demonstrate CVE-2025-50817 side-loading

    if 'test' in sys.modules:

        del sys.modules['test']

    

    # In vulnerable future==1.0.0, this import triggers 'import test'

    # if it's in the CWD (since Flask adds CWD to sys.path)

    importlib.reload(future.standard_library)

    

    if 'test' in sys.modules:

        return "Ingredient database synchronized. (Side-loaded module detected!)"

    else:

        return "Ingredient database synchronized. (Standard library reloaded)."



if __name__ == '__main__':

    # init_db() # We can uncomment this if we want it to init on run

    app.run(debug=True, host='0.0.0.0', port=5000)
