# Borgor Science: Professional Grill Architect Portal

This is a professional-themed web application designed with various intentional vulnerabilities to test and evaluate automated security frameworks like **PenAI and other similar security frameworks**.

## Platform Features & Hidden Vulnerabilities

To simulate a real-world environment, vulnerabilities are integrated into seemingly legitimate functional modules:

- **SQL Injection (SQLi):**
  - **Staff Login:** Standard SQLi in the authentication module.
  - **Kitchen Profile:** SQLi in the "Kitchen Motto" update field.
- **Weak JWT Session Authentication:**
  - **Kitchen Session Cookie:** Authentication trusts a client-side JWT-like cookie (`kitchen_token`) with `alg: none`, no signature, and reversible no-key payload obfuscation.
- **Stored Cross-Site Scripting (XSS):**
  - **Community Kitchen Notes:** Malicious scripts can be stored in the public culinary tips section.
- **OS Command Injection:**
  - **Kitchen Server Diagnostic:** Exploitable via the "Server Heartbeat" tool (`/ping-service`).
- **Server-Side Request Forgery (SSRF):**
  - **Node Communication Tester:** Exploitable via the internal network diagnostic tool (`/internal-network-test`).
- **Path Traversal / Local File Inclusion (LFI):**
  - **Asset Explorer:** Access sensitive files via the `/asset-viewer` module.
- **Insecure Deserialization:**
  - **Session Monitor:** Exploitable via the staff debug token decoder (`/session-debug`).
- **Server-Side Template Injection (SSTI):**
  - **Personalized Greetings:** Exploitable via the guest greeting generator (`/say-hello`).
- **Broken Access Control:**
  - **Kitchen Secrets Vault:** Insecure access to the Senior Grill Architect vault (`/kitchen-secrets`).
- **Insecure Direct Object Reference (IDOR):**
  - **View Burger Profile:** Authenticated users are redirected to their own tokenized profile URL, but swapping the `token` in `/view-burger-profile?token=<token>` can expose other users' burger profiles.
- **CVE-2025-50817 (Side-Loading):**
  - **Ingredient Sync:** Triggered via the `/sync-ingredients` route after uploading a malicious `test.py` through the Recipe Image Uploader.
- **Cross-Site Request Forgery (CSRF):** Profile updates and kitchen notes lack CSRF protection.

## Setup and Running

### Installation
```bash
pip install -r requirements.txt
python3 setup.py # Initializes the database with the Borgor Science schema
```

### Running the Portal
```bash
python3 vuln_app.py
```

### Create Test Accounts
- Register at `/register` to create a user with a personalized burger profile.
- Use `/view-burger-profile` while logged in to see your own profile first, then replace the `token` in the URL to validate IDOR behavior.

### Testing CVE-2025-50817
A dedicated Proof of Concept script is provided:
```bash
python3 poc_cve_2025_50817.py
```

## Security Warning
**WARNING:** This application is intentionally vulnerable and contains dangerous features (like RCE via side-loading and deserialization). **NEVER** run this on a public-facing server or any untrusted network. Use only in a controlled, isolated testing environment.
