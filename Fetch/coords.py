"""Coordinate parsing, validation, conversion, and spherical geometry helpers."""
import re
from math import atan2, cos, degrees, radians, sin
from typing import Optional

import numpy as np
import pandas

def filter_valid_coordinates(df: pandas.DataFrame, lat_col: str = 'LATITUDE', lon_col: str = 'LONGITUDE'):
    """Return (clean_copy, skipped_count) keeping only rows with numeric, finite, in-range coordinates.

    Latitude must be within [-90, 90] and longitude within [-180, 180].
    """
    if df is None or df.empty:
        return pandas.DataFrame(columns=df.columns if df is not None else []), 0
    if lat_col not in df.columns or lon_col not in df.columns:
        return pandas.DataFrame(columns=df.columns), len(df)

    lat = pandas.to_numeric(df[lat_col], errors='coerce').to_numpy(dtype=float, na_value=np.nan)
    lon = pandas.to_numeric(df[lon_col], errors='coerce').to_numpy(dtype=float, na_value=np.nan)
    with np.errstate(invalid='ignore'):
        keep = (np.isfinite(lat) & np.isfinite(lon)
                & (np.abs(lat) <= 90.0) & (np.abs(lon) <= 180.0))
    clean = df.loc[keep].reset_index(drop=True)
    clean[lat_col] = lat[keep]
    clean[lon_col] = lon[keep]
    return clean, int(len(df) - len(clean))


def coordinate_bounds(df: pandas.DataFrame, lat_col: str = 'LATITUDE', lon_col: str = 'LONGITUDE'):
    """[[south, west], [north, east]] for valid coordinates in df, or None when there are none."""
    lat = pandas.to_numeric(df[lat_col], errors='coerce')
    lon = pandas.to_numeric(df[lon_col], errors='coerce')
    if lat.notna().sum() == 0 or lon.notna().sum() == 0:
        return None
    return [[float(lat.min()), float(lon.min())], [float(lat.max()), float(lon.max())]]


def numeric_like_columns(df: pandas.DataFrame, exclude=('LATITUDE', 'LONGITUDE', 'geometry')) -> list:
    """Columns with at least one value coercible to a number (handles numeric strings)."""
    result = []
    for c in df.columns:
        if c in exclude:
            continue
        col = df[c]
        if pandas.api.types.is_numeric_dtype(col):
            if col.notna().any():
                result.append(c)
            continue
        # Scan text columns in growing chunks so typical columns resolve after a few values.
        values = col.dropna()
        start, size = 0, 256
        while start < len(values):
            if pandas.to_numeric(values.iloc[start:start + size], errors='coerce').notna().any():
                result.append(c)
                break
            start, size = start + size, size * 4
    return result


def dms_to_decimal(deg: float, minutes: float, seconds: float, direction: str = '') -> float:
    """Convert DMS (Degrees, Minutes, Seconds) to decimal degrees."""
    decimal = abs(deg) + minutes / 60.0 + seconds / 3600.0
    if direction.upper() in ('S', 'W') or deg < 0:
        decimal = -decimal
    return decimal


def ddm_to_decimal(deg: float, minutes: float, direction: str = '') -> float:
    """Convert DDM (Degrees Decimal Minutes) to decimal degrees."""
    decimal = abs(deg) + minutes / 60.0
    if direction.upper() in ('S', 'W') or deg < 0:
        decimal = -decimal
    return decimal


DMS_PATTERN = re.compile(
    r'^\s*(?P<deg>-?\d{1,3})\s*[\xb0dD\-]\s*'
    r'(?P<min>\d{1,2})\s*[\'\u2018\u2019mM\-]\s*'
    r'(?P<sec>\d{1,2}(?:\.\d+)?)\s*["\u201c\u201dsS]?\s*'
    r'(?P<dir>[NSEWnsew])?\s*$',
    re.VERBOSE
)


DDM_PATTERN = re.compile(
    r'^\s*(?P<deg>-?\d{1,3})\s*[\xb0dD\-]\s*'
    r'(?P<min>\d{1,2}(?:\.\d+)?)\s*[\'\u2018\u2019mM]?\s*'
    r'(?P<dir>[NSEWnsew])?\s*$',
    re.VERBOSE
)


def parse_coordinate_value(value) -> Optional[float]:
    """Try to parse a coordinate value from various formats.
    Supports: decimal degrees, DMS, DDM.
    Returns float (decimal degrees) or None if unparseable.
    """
    if value is None:
        return None
    # Already numeric
    if isinstance(value, (int, float)):
        if np.isfinite(value):
            return float(value)
        return None
    s = str(value).strip()
    if not s:
        return None
    # Try plain float first
    try:
        v = float(s)
        if np.isfinite(v):
            return v
        return None
    except ValueError:
        pass
    # Try DMS
    m = DMS_PATTERN.match(s)
    if m:
        return dms_to_decimal(
            float(m.group('deg')),
            float(m.group('min')),
            float(m.group('sec')),
            m.group('dir') or ''
        )
    # Try DDM
    m = DDM_PATTERN.match(s)
    if m:
        return ddm_to_decimal(
            float(m.group('deg')),
            float(m.group('min')),
            m.group('dir') or ''
        )
    return None


def convert_coordinate_column(series: pandas.Series) -> pandas.Series:
    """Convert a column of coordinates from any supported format to decimal degrees.
    Handles: decimal degrees, DMS, DDM. Non-convertible values become NaN.
    """
    return series.apply(parse_coordinate_value).astype(float)


def detect_coordinate_format(series: pandas.Series) -> str:
    """Detect the coordinate format of a pandas Series.
    Returns one of: 'decimal', 'dms', 'ddm', 'mixed', 'unknown'
    """
    sample = series.dropna().head(20)
    formats_found = set()
    for val in sample:
        s = str(val).strip()
        try:
            float(s)
            formats_found.add('decimal')
            continue
        except ValueError:
            pass
        if DMS_PATTERN.match(s):
            formats_found.add('dms')
        elif DDM_PATTERN.match(s):
            formats_found.add('ddm')
        else:
            formats_found.add('unknown')
    if len(formats_found) == 1:
        return formats_found.pop()
    elif len(formats_found) > 1 and 'unknown' not in formats_found:
        return 'mixed'
    elif 'unknown' in formats_found and len(formats_found) > 1:
        return 'mixed'
    return 'unknown'


def utm_to_latlon(easting: float, northing: float, zone_number: int, zone_letter: str = 'N') -> tuple:
    """Convert UTM coordinates to latitude/longitude (WGS84).
    Simple implementation without external UTM library dependency.
    """
    # WGS84 parameters
    a = 6378137.0
    f = 1 / 298.257223563
    e = (2 * f - f ** 2) ** 0.5
    e_prime_sq = e ** 2 / (1 - e ** 2)

    # Determine hemisphere
    northern = zone_letter.upper() >= 'N'

    x = easting - 500000.0
    y = northing
    if not northern:
        y = y - 10000000.0

    lon0 = radians((zone_number - 1) * 6 - 180 + 3)

    M = y / 0.9996
    mu = M / (a * (1 - e**2/4 - 3*e**4/64 - 5*e**6/256))

    e1 = (1 - (1 - e**2)**0.5) / (1 + (1 - e**2)**0.5)
    phi1 = mu + (3*e1/2 - 27*e1**3/32) * sin(2*mu)
    phi1 += (21*e1**2/16 - 55*e1**4/32) * sin(4*mu)
    phi1 += (151*e1**3/96) * sin(6*mu)
    phi1 += (1097*e1**4/512) * sin(8*mu)

    N1 = a / (1 - e**2 * sin(phi1)**2)**0.5
    T1 = (sin(phi1) / cos(phi1))**2
    C1 = e_prime_sq * cos(phi1)**2
    R1 = a * (1 - e**2) / (1 - e**2 * sin(phi1)**2)**1.5
    D = x / (N1 * 0.9996)

    lat = phi1 - (N1 * (sin(phi1) / cos(phi1)) / R1) * (
        D**2/2 - (5 + 3*T1 + 10*C1 - 4*C1**2 - 9*e_prime_sq) * D**4/24
        + (61 + 90*T1 + 298*C1 + 45*T1**2 - 252*e_prime_sq - 3*C1**2) * D**6/720
    )
    lon = lon0 + (D - (1 + 2*T1 + C1) * D**3/6
                  + (5 - 2*C1 + 28*T1 - 3*C1**2 + 8*e_prime_sq + 24*T1**2) * D**5/120) / cos(phi1)

    return (degrees(lat), degrees(lon))


UTM_PATTERN = re.compile(
    r'^\s*(?P<zone>\d{1,2})\s*(?P<letter>[A-Za-z])\s+'
    r'(?P<easting>\d+(?:\.\d+)?)\s*[mM]?\s*[Ee]?\s+'
    r'(?P<northing>\d+(?:\.\d+)?)\s*[mM]?\s*[Nn]?\s*$'
)


def parse_utm_string(s: str) -> Optional[tuple]:
    """Parse a UTM string like '17T 630000 4833000' into (lat, lon) or None."""
    m = UTM_PATTERN.match(str(s).strip())
    if not m:
        return None
    try:
        zone = int(m.group('zone'))
        letter = m.group('letter')
        easting = float(m.group('easting'))
        northing = float(m.group('northing'))
        if 1 <= zone <= 60:
            return utm_to_latlon(easting, northing, zone, letter)
    except Exception:
        pass
    return None


def haversine_distance_m(lat1, lon1, lat2, lon2):
    """Calculate haversine distance in meters between two points."""
    R = 6371000.0
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlam = radians(lon2 - lon1)
    a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlam/2)**2
    return 2 * R * atan2(a**0.5, (1-a)**0.5)


def destination_points(lat, lon, dist_m, bearing_deg, R=6371000.0):
    """Vectorized great-circle destination: (lat, lon) in degrees after travelling dist_m along bearing_deg."""
    lat1, lon1, a = np.radians(lat), np.radians(lon), np.radians(bearing_deg)
    d = np.asarray(dist_m, dtype=float) / R
    lat2 = np.arcsin(np.sin(lat1) * np.cos(d) + np.cos(lat1) * np.sin(d) * np.cos(a))
    lon2 = lon1 + np.arctan2(np.sin(a) * np.sin(d) * np.cos(lat1), np.cos(d) - np.sin(lat1) * np.sin(lat2))
    return np.degrees(lat2), np.degrees(lon2)
