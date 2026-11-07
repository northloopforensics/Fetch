"""Reusable Streamlit input widgets shared across pages."""
import numpy as np
import pandas
import streamlit as st

from fetch.coords import numeric_like_columns
from fetch.i18n import t


def filter_map_radius(df: pandas.DataFrame, radius_col: str, key: str):
    """Select a maximum radius and return eligible records without changing the input."""
    max_radius = st.number_input(
        "Maximum Radius (meters)", min_value=0.0, value=50.0, step=1.0, key=key,
        help="Filters out entire records whose radius value is larger than this maximum (in meters), including their map markers and radius shapes. Missing, non-numeric, and non-positive radii are also excluded."
    )
    radius = pandas.to_numeric(df[radius_col], errors='coerce')
    keep = np.isfinite(radius) & (radius > 0) & (radius <= max_radius)
    filtered = df.loc[keep].copy().reset_index(drop=True)
    filtered[radius_col] = radius.loc[keep].to_numpy()
    excluded = len(df) - len(filtered)
    if excluded:
        st.caption(f"Radius filter: excluded {excluded:,} record(s); {len(filtered):,} remain.")
    if filtered.empty:
        st.warning("No records match the maximum radius. Increase the limit or select another radius column.")
    return filtered


def optional_radius_filter(df: pandas.DataFrame, key: str):
    """Optionally filter input records by their accuracy/radius column."""
    if not st.checkbox(t("chk_accuracy_radius"), key=f"{key}_enabled"):
        return df
    numeric_columns = numeric_like_columns(df)
    if not numeric_columns:
        st.error("No numeric columns found for radius/accuracy information. Please ensure your data contains numeric columns for radius values.")
        return df.iloc[0:0].copy()
    default_index = next(
        (index for index, col in enumerate(numeric_columns)
         if any(word in str(col).upper() for word in ['RADIUS', 'ACCURACY', 'RANGE', 'DISTANCE', 'RADII'])),
        0
    )
    radius_col = st.selectbox(
        t("lbl_radius_meters"), options=numeric_columns, index=default_index, key=f"{key}_column"
    )
    return filter_map_radius(df, radius_col, key=f"{key}_maximum")
