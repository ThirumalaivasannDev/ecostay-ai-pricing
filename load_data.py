"""One-time import of data.csv (historical bookings) into MySQL."""
import pandas as pd
from pathlib import Path
from db import run
BASE_DIR = Path(__file__).resolve().parent
df = pd.read_csv(BASE_DIR / "data.csv")
rows = [(r.date, int(r.bookings), int(r.price)) for r in df.itertuples()]
run("INSERT INTO daily_bookings (stay_date, rooms_booked, price) VALUES (%s,%s,%s) "
    "ON DUPLICATE KEY UPDATE rooms_booked=VALUES(rooms_booked), price=VALUES(price)", rows, many=True)
print(f"Loaded {len(rows)} rows into daily_bookings")