"""Number and value formatting utilities."""

import pandas as pd


def fmt_markup(v: float) -> str:
    """Format markup percentage value."""
    if v == 0.0:
        return "0"
    return f"{v:.4f}".rstrip("0").rstrip(".")


def fmt_num(v: float) -> str:
    """Format numeric values safely, handling None/NaN."""
    if v is None or pd.isna(v):
        return "N/D"
    if isinstance(v, (int, float)):
        return f"{v:.2f}"
    return str(v)
