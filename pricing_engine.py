import joblib, numpy as np, pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from curve_model import CurveModel
from generate_data import ROOMS, true_demand, calendar
BASE_DIR = Path(__file__).resolve().parent
FEATURES = ["dow","month","is_weekend","is_festival","is_event","price"]
GRID = np.arange(2000, 9001, 100)            # price bounds: Rs.2000 - Rs.9000
FIXED_PRICE = 3500

def _m(name, y, p):
    return dict(model=name, MAE=round(mean_absolute_error(y,p),2), RMSE=round(mean_squared_error(y,p)**.5,2), R2=round(r2_score(y,p),3))

def train():
    df = pd.read_csv(BASE_DIR / "data.csv", parse_dates=["date"])
    tr, te = df[df.date < "2025-01-01"], df[df.date >= "2025-01-01"]
    base = tr.groupby(["month","is_weekend"]).bookings.mean()
    res = [_m("Baseline (month+weekend average)", te.bookings, te.apply(lambda r: base[(r.month,r.is_weekend)], axis=1))]
    rf = RandomForestRegressor(200, min_samples_leaf=3, random_state=1).fit(tr[FEATURES], tr.bookings)
    gb = HistGradientBoostingRegressor(monotonic_cst=[0,0,0,0,0,-1], random_state=1).fit(tr[FEATURES], tr.bookings)
    res += [_m("Random Forest", te.bookings, rf.predict(te[FEATURES])), _m("Gradient Boosting (price-monotonic)", te.bookings, gb.predict(te[FEATURES]))]
    curve = CurveModel().fit(tr[FEATURES], tr.bookings)
    res.append(_m("Demand curve (used for pricing)", te.bookings, np.minimum(ROOMS, curve.predict(te[FEATURES]))))
    joblib.dump(curve, BASE_DIR / "model.pkl")   # smooth price response -> varied, explainable prices
    return res

def recommend(model, cal):
    out = []
    for _, r in cal.iterrows():
        X = pd.DataFrame({f: [r[f]]*len(GRID) for f in FEATURES[:-1]}); X["price"] = GRID
        b = np.minimum(ROOMS, model.predict(X)); rev = GRID * b; i = rev.argmax()
        out.append(dict(date=str(r.date.date()), price=int(GRID[i]), occupancy=round(b[i]/ROOMS*100,1), revenue=int(rev[i])))
    return out

def simulate(model):
    """Dynamic vs fixed pricing on 2025, revenue evaluated with the true demand rules."""
    cal = calendar(pd.date_range("2025-01-01", "2025-12-31")); rec = recommend(model, cal)
    dyn = sum(p["price"] * min(ROOMS, true_demand(cal.iloc[[i]], p["price"]).iloc[0]) for i, p in enumerate(rec))
    fix = sum(FIXED_PRICE * min(ROOMS, true_demand(cal.iloc[[i]], FIXED_PRICE).iloc[0]) for i in range(len(cal)))
    return dict(dynamic=int(dyn), fixed=int(fix), uplift_pct=float(round((dyn/fix-1)*100, 1)))

def whatif(model, date, price):
    r = calendar([date]).iloc[0]; X = pd.DataFrame([{**{f: r[f] for f in FEATURES[:-1]}, "price": price}])
    b = float(min(ROOMS, model.predict(X)[0])); return dict(bookings=round(b,1), occupancy=round(b/ROOMS*100,1), revenue=int(b*price))

if __name__ == "__main__":
    import json; res = train(); m = joblib.load(BASE_DIR / "model.pkl"); s = simulate(m)
    json.dump(dict(models=res, simulation=s), open(BASE_DIR / "results.json","w"), indent=1); print(res, s)