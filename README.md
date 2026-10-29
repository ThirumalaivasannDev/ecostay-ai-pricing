# AI-Based Dynamic Pricing and Revenue Management for Eco-Tourism Hospitality

A full stack web system that predicts room demand for an eco-lodge and recommends the revenue-maximizing price for every day. Built as a Semester 5 mini project (Full Stack Web Development).

## Problem
Eco-tourism lodges (jungle stays, homestays, farm stays) have few rooms and strongly seasonal demand, yet most charge fixed or gut-feel prices. They underprice on peak days (festivals, winter weekends) and leave rooms empty on slow days (monsoon weekdays).

## Solution
The system learns demand patterns, forecasts occupancy, and tests every price between Rs. 2,000 and Rs. 9,000 for each date to pick the one with the highest expected revenue (price x predicted bookings). The owner reviews the prices on a dashboard; customers see only the final nightly price.

## Features
**Owner dashboard (login required)**
- Revenue KPIs: AI pricing vs fixed pricing (2025 simulation)
- 60-day chart of recommended price and predicted occupancy
- What-if simulator: choose a date and a price, see predicted bookings, occupancy and revenue
- Record daily bookings (saved to MySQL)
- Model comparison table

**Customer page (public, `/book`)**
- Pick a date and see the price per room per night. No occupancy, revenue or other business data is exposed.

**Backend and data**
- MySQL storage for bookings, recommended prices and hashed user accounts
- Password hashing, session login, secrets kept in `.env`

## Tech stack
Python, Flask, MySQL, scikit-learn, SciPy, pandas, NumPy, HTML/CSS/JavaScript, Chart.js

## Project structure
```
eco_pricing/
├── .env                  # your real credentials (never commit)
├── .env.example          # template with placeholder values
├── .gitignore            # keeps .env, venv and generated files out of Git
├── generate_data.py      # builds the synthetic dataset (data.csv)
├── curve_model.py        # smooth demand-curve model used for pricing
├── pricing_engine.py     # model training, optimizer, what-if, simulation
├── db.py                 # MySQL connection (reads .env)
├── load_data.py          # imports data.csv into MySQL
├── schema.sql            # creates the database and tables
├── create_owner.py       # creates the owner login (hashed password)
├── app.py                # Flask backend, routes, authentication
├── requirements.txt
├── README.md
└── templates/
    ├── index.html        # owner dashboard
    ├── login.html        # owner login
    └── customer.html     # public price page

# generated when you run the scripts
├── data.csv
├── model.pkl
└── results.json
```

## How it works
1. `generate_data.py` creates 3 years (2023-2025) of daily bookings for a 20-room lodge using demand rules for season, weekends, festivals and local events.
2. `pricing_engine.py` trains on 2023-24 and tests on 2025. Four models are compared: baseline, Random Forest, Gradient Boosting (price-monotonic) and a smooth demand-curve model.
3. The demand-curve model (`demand = 12*m*(1 - price/(P0*m))`) is used for pricing because it responds smoothly to price and produces explainable, varied prices.
4. For each date the optimizer tries every price from Rs. 2,000 to Rs. 9,000 (step 100), caps bookings at 20 rooms, and picks the price with the highest revenue.
5. A 2025 simulation compares AI pricing against a fixed Rs. 3,500 rate.

## Setup (Windows)

**1. Database**
Open MySQL Workbench, open `schema.sql`, and run it (lightning bolt). This creates the `eco_pricing` database and the `daily_bookings`, `price_recommendations` and `users` tables.

**2. Virtual environment and packages**
```
cd path\to\eco_pricing
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**3. Environment file**
Create a file named `.env` in the project folder:
```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=eco_pricing
SECRET_KEY=your_long_random_string
```
Generate a secret key with:
```
python -c "import secrets; print(secrets.token_hex(32))"
```

**4. Generate data, train, and load the database**
```
python generate_data.py
python pricing_engine.py
python load_data.py
```

**5. Create the owner account (once)**
```
python create_owner.py
```
The password prompt does not show characters while you type. This is normal.

**6. Run the app**
```
python app.py
```
- Owner dashboard: http://127.0.0.1:5000 (redirects to login)
- Customer price page: http://127.0.0.1:5000/book

The link works only on the computer running the app.

## API routes
| Route | Access | Purpose |
|---|---|---|
| `/` | Owner | Dashboard |
| `/login`, `/logout` | Public | Authentication |
| `/book` | Public | Customer price page |
| `/api/public-price?date=YYYY-MM-DD` | Public | Price per night only (next 180 days) |
| `/api/forecast?start=YYYY-MM-DD&days=60` | Owner | Recommended prices and occupancy (also saved to MySQL) |
| `/api/whatif?date=YYYY-MM-DD&price=4000` | Owner | Predicted bookings, occupancy, revenue |
| `/api/results` | Owner | Model comparison and revenue simulation |
| `/api/bookings` (GET, POST) | Owner | List or record daily bookings |

## Results (test year 2025)
| Model | MAE | RMSE | R2 |
|---|---|---|---|
| Baseline (month + weekend average) | 2.77 | 3.64 | 0.205 |
| Random Forest | 1.38 | 2.10 | 0.736 |
| Gradient Boosting (price-monotonic) | 1.51 | 2.04 | 0.750 |
| Demand curve (used for pricing) | 1.18 | 1.86 | 0.793 |

AI pricing earned about **7.9% more revenue** than a fixed Rs. 3,500 rate in the 2025 simulation.

## Limitations
- The data is **synthetic**, generated from assumed demand rules. The revenue gain shows the method works under those assumptions, not a guaranteed real-world result. The demand-curve fit is also helped by the data being generated with a similar shape.
- Festival dates are hard-coded and run only up to 25 Dec 2026.
- The model is trained from `data.csv` and is not retrained automatically from bookings saved in MySQL.
- Customers can view prices but cannot book rooms. The owner cannot yet override a recommended price.
- No login attempt limit or HTTPS, and Flask runs in debug mode. This is suitable for a prototype, not a live deployment.

## Future work
- Train on a real lodge's booking history and retrain from MySQL
- Local event scraping and weather as demand features
- Owner price overrides, availability checks and an actual booking flow
- Limits on day-to-day price swings, and customer loyalty or satisfaction in the objective
- Production deployment with HTTPS and login rate limiting