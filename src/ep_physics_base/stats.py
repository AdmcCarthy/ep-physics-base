"""Statistics shared by the hypothesis tests of the knowledge store and by analyses that need the same decision language (pure): a cluster bootstrap over wellbores (tests in one well are not independent), the wells needed for a given precision, the scientific verdict of an interval against thresholds, and the decision status of a departure against a tolerance.  Moved out of `src/knowledge/verify.py` so that analysis code can use it without importing the knowledge store (docs/architecture_boundaries.md)."""
from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd


LEVEL = 0.90
B = 1000
SEED = 7


def cluster_bootstrap(values: pd.Series, groups: pd.Series, stat: Callable[[np.ndarray], float], b: int = B, seed: int = SEED, level: float = LEVEL) -> tuple[float, float, float]:
    """(estimate, low, high) of `stat`, resampling whole groups (wellbores) with replacement."""
    v = np.asarray(values, dtype=float)
    g = np.asarray(groups)
    keys, inv = np.unique(g, return_inverse=True)
    idx = [np.flatnonzero(inv == k) for k in range(len(keys))]
    rng = np.random.default_rng(seed)
    est = float(stat(v))
    sims = np.empty(b)
    for i in range(b):
        pick = rng.integers(0, len(keys), len(keys))
        sims[i] = stat(v[np.concatenate([idx[j] for j in pick])])
    a = (1 - level) / 2
    return est, float(np.quantile(sims, a)), float(np.quantile(sims, 1 - a))


def wells_needed(n_wells: int, ci_low: float, ci_high: float, separation: float) -> float:
    """Wells needed for a 90 % interval half as wide as the gap between the 'holds' and 'does not hold' thresholds (the interval width falls with 1/sqrt(n))."""
    half = (ci_high - ci_low) / 2.0
    target = separation / 2.0
    if n_wells <= 0 or not np.isfinite(half) or target <= 0:
        return np.nan
    return float(np.ceil(n_wells * (half / target) ** 2)) if half > target else float(n_wells)


def scientific_verdict(low: float, high: float, holds: tuple[float, float], fails_below: float | None, fails_above: float | None, point: float | None = None,
                       precise: bool = False) -> str:
    """`holds` = the interval of the statistic in which the relation holds; outside `fails_below` / `fails_above` it does not.  Uses the whole interval; when the interval is already as
    narrow as the thresholds need (`precise`) but still touches a threshold, the result lies ON the boundary and the point value decides."""
    lo_h, hi_h = holds
    if precise and point is not None and np.isfinite(point):
        low = high = point
    if lo_h <= low and high <= hi_h:
        return "confirmed"
    if (fails_above is not None and low > fails_above) or (fails_below is not None and high < fails_below):
        return "contradicted"
    inside_middle = ((fails_below is None or low >= fails_below) and (fails_above is None or high <= fails_above)) and not (lo_h <= low and high <= hi_h)
    straddles = (low < lo_h <= high) or (low <= hi_h < high)
    if straddles:
        return "inconclusive"
    return "partly" if inside_middle else "inconclusive"


def decision_status(effect: float, low: float, high: float, tol: float) -> str:
    """Status in decision units (0 = the relation holds); uses the absolute departure at the point estimate and at the two edges of the interval."""
    if not np.isfinite(effect):
        return "no_data"
    near = 0.0 if low <= 0 <= high else min(abs(low), abs(high))
    far = max(abs(low), abs(high))
    if near > tol:
        return "act"
    if abs(effect) > tol:
        return "caution"
    if far > tol:
        return "watch"
    return "fine"
