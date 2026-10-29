import os, json, joblib, pandas as pd
from pathlib import Path
from functools import wraps
from flask import Flask, jsonify, request, render_template, session, redirect, url_for
from werkzeug.security import check_password_hash
from dotenv import load_dotenv
from generate_data import calendar
import pricing_engine as pe
from db import run

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
app = Flask(__name__); app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key: raise RuntimeError("SECRET_KEY missing in .env (see .env.example)")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

# Ensure AI model and results exist before loading (for fresh cloud deploys)
model_file = BASE_DIR / "model.pkl"
results_file = BASE_DIR / "results.json"
data_file = BASE_DIR / "data.csv"

if not model_file.exists() or not results_file.exists():
    import subprocess, sys
    print("Model or results missing. Generating dataset and training model...")
    if not data_file.exists():
        subprocess.run([sys.executable, str(BASE_DIR / "generate_data.py")], check=True)
    subprocess.run([sys.executable, str(BASE_DIR / "pricing_engine.py")], check=True)

model = joblib.load(model_file)

def owner_only(f):
    @wraps(f)
    def wrap(*a, **k):
        if session.get("role") != "owner":
            if request.path.startswith("/api/"): return jsonify(error="login required"), 401
            return redirect(url_for("login"))
        return f(*a, **k)
    return wrap

# ---------- authentication ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    err = None
    if request.method == "POST":
        u = run("SELECT * FROM users WHERE username=%s", (request.form["username"].strip(),), fetch=True)
        if u and check_password_hash(u[0]["password_hash"], request.form["password"]):
            session.clear(); session["role"] = u[0]["role"]; session["user"] = u[0]["username"]
            return redirect(url_for("home"))
        err = "Invalid username or password"
    return render_template("login.html", error=err)

@app.route("/logout")
def logout(): session.clear(); return redirect(url_for("login"))

# ---------- customer side (public: price only) ----------
@app.route("/book")
def book(): return render_template("customer.html")

@app.route("/api/public-price")
def public_price():
    try: d = pd.Timestamp(request.args["date"]).normalize()
    except Exception: return jsonify(error="Invalid date"), 400
    today = pd.Timestamp.today().normalize()
    if not (today <= d <= today + pd.Timedelta(days=180)): return jsonify(error="Choose a date within the next 180 days"), 400
    r = pe.recommend(model, calendar([d]))[0]
    return jsonify(date=r["date"], price_per_night=r["price"])

# ---------- owner side (login required) ----------
@app.route("/")
@owner_only
def home(): return render_template("index.html")

@app.route("/api/forecast")
@owner_only
def forecast():
    start = request.args.get("start", str(pd.Timestamp.today().date())); days = int(request.args.get("days", 60))
    rec = pe.recommend(model, calendar(pd.date_range(start, periods=days)))
    try:
        run("INSERT INTO price_recommendations (stay_date, recommended_price, occupancy_pct, expected_revenue) VALUES (%s,%s,%s,%s) "
            "ON DUPLICATE KEY UPDATE recommended_price=VALUES(recommended_price), occupancy_pct=VALUES(occupancy_pct), expected_revenue=VALUES(expected_revenue)",
            [(r["date"], r["price"], float(r["occupancy"]), r["revenue"]) for r in rec], many=True)
    except Exception as e: print("DB save failed:", e)
    return jsonify(rec)

@app.route("/api/whatif")
@owner_only
def whatif(): return jsonify(pe.whatif(model, request.args["date"], float(request.args["price"])))

@app.route("/api/results")
@owner_only
def results(): return jsonify(json.load(open(BASE_DIR / "results.json")))

@app.route("/api/bookings", methods=["GET", "POST"])
@owner_only
def bookings():
    if request.method == "POST":
        d = request.get_json(); rooms = int(d["rooms"]); price = int(d["price"])
        if not (0 <= rooms <= pe.ROOMS and 2000 <= price <= 9000): return jsonify(error="rooms 0-20, price 2000-9000"), 400
        run("INSERT INTO daily_bookings (stay_date, rooms_booked, price) VALUES (%s,%s,%s) "
            "ON DUPLICATE KEY UPDATE rooms_booked=VALUES(rooms_booked), price=VALUES(price)", (d["date"], rooms, price))
        return jsonify(ok=True)
    return jsonify(run("SELECT DATE_FORMAT(stay_date,'%Y-%m-%d') AS date, rooms_booked, price, revenue FROM daily_bookings ORDER BY stay_date DESC LIMIT 10", fetch=True))

if __name__ == "__main__": app.run(debug=True)