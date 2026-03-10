#!/usr/bin/env python3
# reset.py
from vuln_app import init_db
import os

DATABASE = 'app.db'

if __name__ == '__main__':
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
        print(f"[+] Deleted old {DATABASE}")
    init_db()
    print(f"[+] New database initialized.")

