"""Run once to create the owner login (password is stored hashed)."""
import getpass
from werkzeug.security import generate_password_hash
from db import run
u = input("Owner username: ").strip(); p = getpass.getpass("Password (min 8 chars): ")
if not u or len(p) < 8: raise SystemExit("Username required and password must be at least 8 characters")
run("INSERT INTO users (username, password_hash, role) VALUES (%s,%s,'owner') "
    "ON DUPLICATE KEY UPDATE password_hash=VALUES(password_hash)", (u, generate_password_hash(p)))
print("Owner account saved.")