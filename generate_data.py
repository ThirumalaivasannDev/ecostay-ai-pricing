"""Synthetic booking data for a 20-room eco-lodge (2023-2025). Demand rules are realistic assumptions."""
import numpy as np, pandas as pd
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
ROOMS = 20
SEASON = {1:1.3,2:1.2,3:1.0,4:1.15,5:1.1,6:0.7,7:0.6,8:0.65,9:0.8,10:1.1,11:1.25,12:1.4}
FESTIVALS = pd.to_datetime(["2023-01-14","2023-01-15","2023-01-16","2023-11-12","2024-01-14","2024-01-15",
  "2024-01-16","2024-11-01","2025-01-14","2025-01-15","2025-01-16","2025-10-20","2026-01-14","2026-01-15",
  "2026-01-16","2026-11-08","2026-12-25"])

def calendar(dates):
    d = pd.DataFrame({"date": pd.to_datetime(list(dates))})
    d["dow"], d["month"] = d.date.dt.dayofweek, d.date.dt.month
    d["is_weekend"] = (d.dow >= 4).astype(int)                      # Fri-Sun
    d["is_festival"] = d.date.isin(FESTIVALS).astype(int)
    d["is_event"] = ((d.date.map(lambda x: x.toordinal()) * 2654435761) % 100 < 6).astype(int)  # local events
    return d

def true_demand(df, price):
    """Linear demand D = D0 * (1 - p/Pmax); both D0 and Pmax rise in peak periods."""
    m = df.month.map(SEASON) * (1 + .25*df.is_weekend) * (1 + .3*df.is_festival) * (1 + .1*df.is_event)
    return 12 * m * np.clip(1 - price / (6000 * m), 0, 1)

if __name__ == "__main__":
    rng = np.random.default_rng(42)
    df = calendar(pd.date_range("2023-01-01", "2025-12-31"))
    # owner's historical rule-of-thumb price with wide price experimentation (so the model sees the full 2000-9000 range)
    df["price"] = (3500 * (1 + .2*df.is_weekend) * (1 + .1*(df.month.map(SEASON) > 1.1)) * rng.uniform(.6, 2.2, len(df))).clip(2000, 9000).round(-2)
    df["bookings"] = np.minimum(ROOMS, rng.poisson(true_demand(df, df.price)))
    df["occupancy"] = df.bookings / ROOMS * 100
    df["revenue"] = df.bookings * df.price
    df.to_csv(BASE_DIR / "data.csv", index=False); print(df.describe().round(1))