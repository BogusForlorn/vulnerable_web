# PenAI Vulnerable Web Application

This is a sample web application designed with various intentional vulnerabilities to test and evaluate automated security frameworks like PenAI.

## Existing Vulnerabilities

- **SQL Injection (SQLi):** Present in the login form and profile update bio field.
- **Cross-Site Scripting (XSS):** Stored XSS in the comments section.
- **OS Command Injection:** Exploitable via the Ping Tool (`/ping`).
- **Server-Side Request Forgery (SSRF):** Exploitable via the URL Fetcher (`/fetch-url`).
- **Path Traversal / Local File Inclusion (LFI):** Exploitable via the File Viewer (`/view-file`).
- **Insecure Deserialization:** Exploitable via the Pickle Debugger (`/debug-pickle`).
- **Server-Side Template Injection (SSTI):** Exploitable via the Hello Page (`/hello`).
- **Broken Access Control:** Insecure admin panel at `/admin-panel` and hidden backups at `/hidden-backup`.
- **Cross-Site Request Forgery (CSRF):** Profile updates and comments lack CSRF protection.

## Setup and Running

### Installation
```bash
pip install -r requirements.txt --break-system-packages # Remove --break-system-packages if not needed
python3 setup.py # Initializes the database with the new schema
```

### Running with Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:5000 vuln_app:app
```

### Resetting the Database
To clean up the database after testing:
```bash
python3 reset.py
gunicorn -w 4 -b 0.0.0.0:5000 vuln_app:app
```

## Security Warning
**WARNING:** This application is intentionally vulnerable and contains dangerous features (like RCE via deserialization). **NEVER** run this on a public-facing server or any untrusted network. Use only in a controlled, isolated testing environment.