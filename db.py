"""MySQL / TiDB helper. Credentials are read from the .env file (never hard-coded)."""
import os
import ssl
from pathlib import Path
import mysql.connector
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

port_val = os.getenv("DB_PORT", "4000")
try:
    port = int(port_val)
except ValueError:
    port = 4000

CFG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": port,
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME", "projectDB"),
    "autocommit": True,
    "use_pure": True,
}

ssl_mode = os.getenv("DB_SSL", "true").lower() in ("true", "1", "yes")
ssl_ca = os.getenv("DB_SSL_CA")

# Find system CA bundle if not explicitly configured (e.g. /etc/ssl/certs/ca-certificates.crt on Render Linux)
if not ssl_ca:
    default_ca = ssl.get_default_verify_paths().cafile
    if default_ca and os.path.exists(default_ca):
        ssl_ca = default_ca
    else:
        for candidate in [
            "/etc/ssl/certs/ca-certificates.crt",
            "/etc/pki/tls/certs/ca-bundle.crt",
            "/etc/ssl/cert.pem",
        ]:
            if os.path.exists(candidate):
                ssl_ca = candidate
                break

if ssl_ca and os.path.exists(ssl_ca):
    CFG["ssl_ca"] = ssl_ca
    CFG["ssl_verify_cert"] = True
    CFG["ssl_verify_identity"] = True
elif ssl_mode:
    CFG["ssl_disabled"] = False
    CFG["ssl_verify_cert"] = False

if not CFG["password"]:
    raise RuntimeError("DB_PASSWORD missing. Fill in your database password in the environment.")

def run(sql, params=None, many=False, fetch=False):
    try:
        con = mysql.connector.connect(**CFG)
    except Exception as err:
        print(f"[DB ERROR] Failed connecting to {CFG.get('host')}:{CFG.get('port')}: {err}")
        raise
    cur = con.cursor(dictionary=True)
    try:
        (cur.executemany if many else cur.execute)(sql, params or ())
        rows = cur.fetchall() if fetch else None
        con.commit()
        return rows
    finally:
        cur.close()
        con.close()
