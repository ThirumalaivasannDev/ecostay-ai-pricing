"""MySQL / TiDB helper. Credentials are read from the .env file (never hard-coded)."""
import os
from pathlib import Path
import mysql.connector
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

port_val = os.getenv("DB_PORT", "3306")
try:
    port = int(port_val)
except ValueError:
    port = 3306

CFG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": port,
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME", "projectDB"),
}

ssl_mode = os.getenv("DB_SSL", "true").lower() in ("true", "1", "yes")
ssl_ca = os.getenv("DB_SSL_CA")

if ssl_ca and os.path.exists(ssl_ca):
    CFG["ssl_ca"] = ssl_ca
    CFG["ssl_verify_cert"] = True
elif ssl_mode:
    CFG["ssl_disabled"] = False
    CFG["ssl_verify_cert"] = False

if not CFG["password"]:
    raise RuntimeError("DB_PASSWORD missing. Copy .env.example to .env and fill in your database password.")

def run(sql, params=None, many=False, fetch=False):
    con = mysql.connector.connect(**CFG)
    cur = con.cursor(dictionary=True)
    try:
        (cur.executemany if many else cur.execute)(sql, params or ())
        rows = cur.fetchall() if fetch else None
        con.commit()
        return rows
    finally:
        cur.close()
        con.close()
