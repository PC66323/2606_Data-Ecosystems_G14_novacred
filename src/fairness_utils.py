"""
Reusable fairness metric helpers for credit / lending bias analysis.
Used by notebooks/02-bias-analysis.ipynb and for governance monitoring.
"""

import pandas as pd
import numpy as np

# Four-fifths rule (EEOC): DI below this threshold indicates potential disparate impact
DI_THRESHOLD = 0.80


def _ensure_numeric(y):
    """Convert boolean or object outcome to numeric (0/1) for rate calculations."""
    y = pd.Series(y)
    if y.dtype == bool:
        return y.astype(int)
    if y.dtype == "object" or not np.issubdtype(y.dtype, np.number):
        return pd.to_numeric(y, errors="coerce")
    return y


def disparate_impact_ratio(y_true, group_series, privileged_val, unprivileged_val):
    """
    Compute the disparate impact ratio: unprivileged_approval_rate / privileged_approval_rate.

    Four-fifths rule: ratio < 0.8 indicates potential disparate impact.

    Parameters
    ----------
    y_true : array-like or Series
        Binary outcome (1 = positive/approved, 0 = negative/rejected).
    group_series : array-like or Series
        Protected attribute (e.g. gender).
    privileged_val : scalar
        Value denoting the privileged group (e.g. "Male").
    unprivileged_val : scalar
        Value denoting the unprivileged group (e.g. "Female").

    Returns
    -------
    tuple of (di_ratio, rate_privileged, rate_unprivileged)
        di_ratio is np.nan if rate_privileged is 0.
    """
    y = _ensure_numeric(y_true)
    g = pd.Series(group_series)
    df = pd.DataFrame({"y": y, "g": g}).dropna()
    if len(df) == 0:
        return np.nan, np.nan, np.nan
    rate_priv = df.loc[df["g"] == privileged_val, "y"].mean()
    rate_unpriv = df.loc[df["g"] == unprivileged_val, "y"].mean()
    if rate_priv == 0:
        di_ratio = np.nan
    else:
        di_ratio = float(rate_unpriv / rate_priv)
    return di_ratio, float(rate_priv), float(rate_unpriv)


def demographic_parity_difference(y_true, group_series):
    """
    Demographic parity difference: max group approval rate minus min group approval rate.
    0 = parity; larger values indicate greater disparity (e.g. fairlearn-style metric).

    Parameters
    ----------
    y_true : array-like or Series
        Binary outcome (1 = approved, 0 = rejected).
    group_series : array-like or Series
        Protected attribute (e.g. gender).

    Returns
    -------
    tuple of (parity_difference, rates_series)
        rates_series is a pandas Series index by group with approval rate per group.
    """
    y = _ensure_numeric(y_true)
    g = pd.Series(group_series)
    df = pd.DataFrame({"y": y, "g": g}).dropna()
    if len(df) == 0:
        return np.nan, pd.Series(dtype=float)
    rates = df.groupby("g")["y"].mean()
    diff = float(rates.max() - rates.min())
    return diff, rates
