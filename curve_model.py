"""Smooth demand-curve model used for pricing.
demand = 12*m*(1 - price/(P0*m)),  m = exp(theta . features)
The context (month, weekend, festival, event) scales both the volume (m) and the guests' willingness to pay (P0*m),
so the revenue-maximising price moves smoothly with demand instead of jumping between a few tiers."""
import numpy as np
from scipy.optimize import least_squares
ROOMS = 20

def _x(X):
    M = np.zeros((len(X), 15)); M[np.arange(len(X)), X["month"].to_numpy() - 1] = 1   # 12 month effects
    M[:, 12], M[:, 13], M[:, 14] = X["is_weekend"], X["is_festival"], X["is_event"]; return M

class CurveModel:
    def fit(self, X, y):
        A, p, y = _x(X), X["price"].to_numpy(float), np.asarray(y, float)
        def resid(w):
            m = np.exp(A @ w[:15]); return np.minimum(ROOMS, 12*m*np.clip(1 - p/(w[15]*m), 0, 1)) - y
        self.w = least_squares(resid, np.r_[np.zeros(15), 6000.]).x; return self

    def predict(self, X):                      # uncapped demand (rooms); callers apply the ROOMS cap
        m = np.exp(_x(X) @ self.w[:15]); p = X["price"].to_numpy(float)
        return 12*m*np.clip(1 - p/(self.w[15]*m), 0, 1)