"""Hotspot, co-location, and stop/dwell analysis plus tactical clock charts."""
from typing import Optional

import numpy as np
import pandas
import streamlit as st

from fetch.coords import haversine_distance_m

def compute_hotspots(df: pandas.DataFrame, radius_m: float, min_samples: int, time_col: Optional[str], trim_chaining: bool = True):
    """Run DBSCAN (haversine) on LATITUDE/LONGITUDE columns (meters radius) and return
    (clusters_df, summary_df).

    Notes
    -----
    DBSCAN's notion of a cluster allows *chaining*: points can be connected via a series
    of <= eps links even if the overall diameter is >> eps. That can yield MAX_DISTANCE_M
    much larger than the user-selected radius. When trim_chaining is True we post-filter
    each cluster to retain only points within radius_m of the cluster centroid; any points
    outside are re-labelled as noise. Clusters falling below min_samples after trimming
    are discarded. This makes MAX_DISTANCE_M always <= radius_m (or very close due to
    floating error) and matches an intuitive "circular hotspot" expectation.
    """
    try:
        from sklearn.cluster import DBSCAN  # dynamic import in case installed after first run
    except Exception as e:
        raise RuntimeError("scikit-learn not available: install scikit-learn") from e

    earth_radius_m = 6371000.0
    eps = radius_m / earth_radius_m
    coords_rad = np.radians(df[['LATITUDE','LONGITUDE']].to_numpy())
    model = DBSCAN(eps=eps, min_samples=min_samples, metric='haversine')
    labels = model.fit_predict(coords_rad)
    df = df.copy()
    df['HOTSPOT_ID'] = labels
    clusters = df[df['HOTSPOT_ID'] != -1].copy()
    if clusters.empty:
        return df, pandas.DataFrame(columns=['HOTSPOT_ID','COUNT','CENTER_LAT','CENTER_LON','MAX_DISTANCE_M','RADIUS_INPUT_M','FIRST_OBS','LAST_OBS'])

    earth_r = earth_radius_m
    summary_rows = []
    groupby = clusters.groupby('HOTSPOT_ID')
    # We may need to relabel after trimming; collect relabel operations
    relabel_noise_indices: list[int] = []
    for cid, grp in groupby:
        lat_mean = grp['LATITUDE'].mean(); lon_mean = grp['LONGITUDE'].mean()
        lat_mean_r, lon_mean_r = np.radians(lat_mean), np.radians(lon_mean)
        lat_vals = grp['LATITUDE'].to_numpy(); lon_vals = grp['LONGITUDE'].to_numpy()
        lat_r = np.radians(lat_vals); lon_r = np.radians(lon_vals)
        dlat = lat_r - lat_mean_r; dlon = lon_r - lon_mean_r
        a = np.sin(dlat/2)**2 + np.cos(lat_mean_r) * np.cos(lat_r) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        dists = earth_r * c  # meters from centroid
        if trim_chaining:
            keep_mask = dists <= radius_m * 1.0005  # small tolerance
            if not np.all(keep_mask):
                # mark dropped points (by original index) to become noise
                dropped = grp.loc[~keep_mask]
                relabel_noise_indices.extend(dropped.index.tolist())
                grp = grp.loc[keep_mask]
                dists = dists[keep_mask]
        # After optional trimming, maybe cluster too small
        if len(grp) < min_samples:
            # whole cluster becomes noise
            relabel_noise_indices.extend(grp.index.tolist())
            continue
        max_dist = float(dists.max()) if len(dists) else 0.0
        first_time = last_time = None
        if time_col and time_col in grp.columns:
            times = pandas.to_datetime(grp[time_col], errors='coerce').dropna()
            if not times.empty:
                first_time, last_time = times.min(), times.max()
        summary_rows.append({
            'HOTSPOT_ID': cid,
            'COUNT': len(grp),
            'CENTER_LAT': lat_mean,
            'CENTER_LON': lon_mean,
            'MAX_DISTANCE_M': round(max_dist,2),
            'RADIUS_INPUT_M': radius_m,
            'FIRST_OBS': first_time,
            'LAST_OBS': last_time
        })
    # Apply relabeling (set to noise)
    if relabel_noise_indices:
        df.loc[relabel_noise_indices, 'HOTSPOT_ID'] = -1
        clusters = df[df['HOTSPOT_ID'] != -1].copy()
        # Rebuild summary_df if we trimmed any clusters away entirely
        if relabel_noise_indices:
            # regenerate summary from summary_rows already filtered
            pass
    summary_df = pandas.DataFrame(summary_rows).sort_values(by='COUNT', ascending=False).reset_index(drop=True)
    return df, summary_df


@st.cache_data(show_spinner=False, max_entries=4, ttl=3600)
def cached_compute_hotspots(df: pandas.DataFrame, radius_m: float, min_samples: int, time_col: Optional[str], trim_chaining: bool = True):
    return compute_hotspots(df, radius_m, min_samples, time_col, trim_chaining=trim_chaining)


def hotspot_input(df: pandas.DataFrame, time_col: Optional[str] = None) -> pandas.DataFrame:
    """Only the columns hotspot analysis uses, so cache hashing and cached results stay small."""
    cols = ['LATITUDE', 'LONGITUDE'] + ([time_col] if time_col and time_col in df.columns else [])
    return pandas.DataFrame(df[cols]).reset_index(drop=True)


def compute_colocation(df: pandas.DataFrame, time_col: str,
                       radius_m: float = 50.0, time_window_min: float = 10.0,
                       max_events: Optional[int] = None, csv_sink=None):
    """Detect co-location events between different source files.

    For each pair of source files, find records where two subjects were within
    `radius_m` meters of each other within `time_window_min` minutes.

    Returns (events, total_events). `events` has columns:
    SOURCE_A, SOURCE_B, TIME_A, TIME_B, LAT_A, LON_A, LAT_B, LON_B,
    DISTANCE_M, TIME_DIFF_MIN, MIDPOINT_LAT, MIDPOINT_LON
    and, when `max_events` is set, holds only the `max_events` closest events so memory
    stays bounded however many matches exist. If `csv_sink` (a text stream) is given,
    every event is also written to it as CSV as soon as it is found.
    """
    if 'SOURCE_FILE' not in df.columns:
        return pandas.DataFrame(), 0

    sources = df['SOURCE_FILE'].unique()
    if len(sources) < 2:
        return pandas.DataFrame(), 0

    # Pre-parse datetimes (only the columns the analysis needs, to limit memory)
    working = df[['SOURCE_FILE', 'LATITUDE', 'LONGITUDE']].copy()
    working['_PARSED_DT'] = pandas.to_datetime(df[time_col], errors='coerce')
    working = working.dropna(subset=['_PARSED_DT', 'LATITUDE', 'LONGITUDE'])
    working['LATITUDE'] = pandas.to_numeric(working['LATITUDE'], errors='coerce')
    working['LONGITUDE'] = pandas.to_numeric(working['LONGITUDE'], errors='coerce')
    working = working.dropna(subset=['LATITUDE', 'LONGITUDE'])
    working = working.sort_values('_PARSED_DT').reset_index(drop=True)

    time_delta = pandas.Timedelta(minutes=time_window_min)
    events = []
    kept = total = 0
    header_written = False

    def _keep_closest(frames, limit):
        merged = pandas.concat(frames, ignore_index=True)
        return merged.nsmallest(limit, 'DISTANCE_M', keep='first') if len(merged) > limit else merged

    source_list = sorted(sources)
    for i in range(len(source_list)):
        for j in range(i+1, len(source_list)):
            src_a = source_list[i]
            src_b = source_list[j]
            df_a = working[working['SOURCE_FILE'] == src_a].reset_index(drop=True)
            df_b = working[working['SOURCE_FILE'] == src_b].reset_index(drop=True)

            if df_a.empty or df_b.empty:
                continue

            # Vectorized: binary-search each A time into B's sorted times, then compute distances in bulk.
            def _to_ns(s):
                return ((s - pandas.Timestamp(0, tz=s.dt.tz)) // pandas.Timedelta(1, 'ns')).to_numpy(np.int64)
            ta = _to_ns(df_a['_PARSED_DT'])
            tb = _to_ns(df_b['_PARSED_DT'])
            delta_ns = int(time_delta.value)
            lo = np.searchsorted(tb, ta - delta_ns, side='left')
            hi = np.searchsorted(tb, ta + delta_ns, side='right')
            counts = hi - lo
            lat_a_all = np.radians(df_a['LATITUDE'].to_numpy(float)); lon_a_all = np.radians(df_a['LONGITUDE'].to_numpy(float))
            lat_b_all = np.radians(df_b['LATITUDE'].to_numpy(float)); lon_b_all = np.radians(df_b['LONGITUDE'].to_numpy(float))

            # Chunk A rows so candidate pair arrays stay bounded in memory.
            max_pairs = 2_000_000
            start = 0
            n_a = len(df_a)
            while start < n_a:
                end = start
                pairs = 0
                while end < n_a and (pairs + counts[end] <= max_pairs or end == start):
                    pairs += counts[end]
                    end += 1
                c = counts[start:end]
                if pairs:
                    ia = np.repeat(np.arange(start, end), c)
                    offsets = np.repeat(np.cumsum(c) - c, c)
                    ib = np.repeat(lo[start:end], c) + (np.arange(pairs) - offsets)
                    dphi = lat_b_all[ib] - lat_a_all[ia]
                    dlam = lon_b_all[ib] - lon_a_all[ia]
                    a = np.sin(dphi / 2) ** 2 + np.cos(lat_a_all[ia]) * np.cos(lat_b_all[ib]) * np.sin(dlam / 2) ** 2
                    dist = 2 * 6371000.0 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
                    hit = dist <= radius_m
                    if hit.any():
                        ia_h, ib_h, d_h = ia[hit], ib[hit], dist[hit]
                        t_a = df_a['_PARSED_DT'].iloc[ia_h].reset_index(drop=True)
                        t_b = df_b['_PARSED_DT'].iloc[ib_h].reset_index(drop=True)
                        lat_a = df_a['LATITUDE'].to_numpy(float)[ia_h]; lon_a = df_a['LONGITUDE'].to_numpy(float)[ia_h]
                        lat_b = df_b['LATITUDE'].to_numpy(float)[ib_h]; lon_b = df_b['LONGITUDE'].to_numpy(float)[ib_h]
                        chunk = pandas.DataFrame({
                            'SOURCE_A': src_a,
                            'SOURCE_B': src_b,
                            'TIME_A': t_a,
                            'TIME_B': t_b,
                            'LAT_A': lat_a,
                            'LON_A': lon_a,
                            'LAT_B': lat_b,
                            'LON_B': lon_b,
                            'DISTANCE_M': np.round(d_h, 2),
                            'TIME_DIFF_MIN': np.round(np.abs((ta[ia_h] - tb[ib_h]) / 6e10), 2),
                            'MIDPOINT_LAT': (lat_a + lat_b) / 2,
                            'MIDPOINT_LON': (lon_a + lon_b) / 2,
                        })
                        total += len(chunk)
                        if csv_sink is not None:
                            chunk.to_csv(csv_sink, header=not header_written, index=False)
                            header_written = True
                        events.append(chunk)
                        kept += len(chunk)
                        if max_events is not None and kept > 2 * max_events:
                            events = [_keep_closest(events, max_events)]
                            kept = len(events[0])
                start = end

    result = pandas.concat(events, ignore_index=True) if events else pandas.DataFrame()
    if max_events is not None and len(result) > max_events:
        result = result.nsmallest(max_events, 'DISTANCE_M', keep='first')
    if not result.empty:
        result = result.sort_values('TIME_A', kind='stable').reset_index(drop=True)
    return result, total


# Events retained for display; beyond this only the closest are kept (each event row is ~170 bytes).
COLOC_MAX_EVENTS = 50_000


@st.cache_data(show_spinner=False, max_entries=3, ttl=3600)
def cached_compute_colocation(df: pandas.DataFrame, time_col: str, radius_m: float, time_window_min: float,
                              max_events: Optional[int] = COLOC_MAX_EVENTS):
    return compute_colocation(df, time_col, radius_m, time_window_min, max_events=max_events)


def colocation_csv(df: pandas.DataFrame, time_col: str, radius_m: float, time_window_min: float) -> bytes:
    """Every co-location event as CSV, streamed while computing (no full DataFrame is built)."""
    import io
    sink = io.StringIO()
    compute_colocation(df, time_col, radius_m, time_window_min, max_events=1, csv_sink=sink)
    return sink.getvalue().encode('utf-8')


def compute_stops(df: pandas.DataFrame, time_col: str, radius_m: float = 50.0,
                  min_duration_min: float = 5.0, source_file: Optional[str] = None) -> pandas.DataFrame:
    """Detect stationary periods (stops/dwells) in location data.

    Groups consecutive points that stay within `radius_m` of their running centroid
    for at least `min_duration_min` minutes.

    Returns a DataFrame with columns:
    STOP_ID, CENTER_LAT, CENTER_LON, ARRIVAL, DEPARTURE, DURATION_MIN, POINT_COUNT, SOURCE_FILE
    """
    working = df.copy()
    working['_PARSED_DT'] = pandas.to_datetime(working[time_col], errors='coerce')
    working['LATITUDE'] = pandas.to_numeric(working['LATITUDE'], errors='coerce')
    working['LONGITUDE'] = pandas.to_numeric(working['LONGITUDE'], errors='coerce')
    working = working.dropna(subset=['_PARSED_DT', 'LATITUDE', 'LONGITUDE'])
    working = working.sort_values('_PARSED_DT').reset_index(drop=True)

    if working.empty:
        return pandas.DataFrame(columns=['STOP_ID','CENTER_LAT','CENTER_LON','ARRIVAL','DEPARTURE','DURATION_MIN','POINT_COUNT','SOURCE_FILE'])

    stops = []
    stop_id = 0
    i = 0
    n = len(working)
    lats = working['LATITUDE'].to_numpy(float)
    lons = working['LONGITUDE'].to_numpy(float)
    times = working['_PARSED_DT']

    while i < n:
        # Running sums keep the centroid O(1) per point instead of re-averaging the whole cluster.
        sum_lat, sum_lon, k = lats[i], lons[i], 1
        j = i + 1

        while j < n:
            dist = haversine_distance_m(sum_lat / k, sum_lon / k, lats[j], lons[j])
            if dist <= radius_m:
                sum_lat += lats[j]
                sum_lon += lons[j]
                k += 1
                j += 1
            else:
                break

        cluster_start = times.iat[i]
        cluster_end = times.iat[j - 1]
        duration = (cluster_end - cluster_start).total_seconds() / 60.0
        point_count = j - i

        if duration >= min_duration_min and point_count >= 2:
            stops.append({
                'STOP_ID': stop_id,
                'CENTER_LAT': round(sum_lat / k, 6),
                'CENTER_LON': round(sum_lon / k, 6),
                'ARRIVAL': cluster_start,
                'DEPARTURE': cluster_end,
                'DURATION_MIN': round(duration, 2),
                'POINT_COUNT': point_count,
                'SOURCE_FILE': source_file or (working.at[i, 'SOURCE_FILE'] if 'SOURCE_FILE' in working.columns else '')
            })
            stop_id += 1

        i = j if j > i else i + 1

    return pandas.DataFrame(stops)


@st.cache_data(show_spinner=False, max_entries=20, ttl=3600)
def cached_compute_stops(df: pandas.DataFrame, time_col: str, radius_m: float,
                         min_duration_min: float, source_file: Optional[str] = None):
    return compute_stops(df, time_col, radius_m, min_duration_min, source_file)


def render_tactical_clock(points_df: pandas.DataFrame, time_col: str, title: str = "Tactical Clock", height: int = 520,
                          center_lat: Optional[float] = None, center_lon: Optional[float] = None, radius_m: Optional[float] = None,
                          visits: Optional[int] = None, max_distance_m: Optional[float] = None,
                          first_obs: Optional[pandas.Timestamp] = None, last_obs: Optional[pandas.Timestamp] = None):
    """Polar day/time chart with equal day wedges and radial hours.
    - Angular: 7 equal wedges (Mon..Sun clockwise)
    - Radial: hour (0 center -> 24 outer)
    - Color: count of observations for (day, hour)
    """
    if time_col not in points_df.columns:
        return
    times = pandas.to_datetime(points_df[time_col], errors='coerce').dropna()
    if times.empty:
        return
    day_idx = times.dt.dayofweek.to_numpy()  # 0=Mon
    hours = times.dt.hour.to_numpy()
    counts = np.zeros((7,24), dtype=int)
    np.add.at(counts, (day_idx, hours), 1)
    max_count = counts.max()
    if max_count == 0:
        return
    try:
        import plotly.graph_objects as go
    except Exception:
        st.warning("Plotly not installed; tactical clock unavailable.")
        return
    day_names = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
    day_wedge = 360/7
    thetas = []
    rs = []
    bases = []
    widths = []
    colors = []
    texts = []
    for d in range(7):
        theta_center = d*day_wedge + day_wedge/2
        for h in range(24):
            c = counts[d, h]
            thetas.append(theta_center)
            bases.append(h)
            rs.append(1)  # 1 hour thickness
            widths.append(day_wedge * 0.90)  # a touch more gap to reduce visual crowding
            colors.append(c)
            texts.append(f"Day: {day_names[d]}<br>Hour: {h:02d}:00<br>Count: {c}")
    fig = go.Figure()
    fig.add_trace(go.Barpolar(
        theta=thetas,
        r=rs,
        base=bases,
        width=widths,
        marker=dict(
            color=colors,
            colorscale='Viridis',
            cmin=0,
            cmax=max_count if max_count>0 else 1,
            line=dict(color='#222', width=0.3),
            colorbar=dict(
                title='Count',
                orientation='h',
                x=0.5,
                y=-0.18,
                xanchor='center',
                yanchor='top',
                len=0.55,
                thickness=12
            )
        ),
        hovertemplate="%{text}<extra></extra>",
        text=texts
    ))
    day_tick_vals = [d*day_wedge + day_wedge/2 for d in range(7)]
    radial_ticks = list(range(0,25,3))
    # Build info block (embedded into title for PNG export completeness)
    info_lines = []
    if center_lat is not None and center_lon is not None:
        info_lines.append(f"Center {center_lat:.5f}, {center_lon:.5f}")
    if radius_m is not None:
        info_lines.append(f"Radius {int(radius_m)}m")
    if visits is not None:
        info_lines.append(f"Visits {visits}")
    if max_distance_m is not None:
        info_lines.append(f"MaxDist {max_distance_m}m")
    # Time window
    if first_obs is not None and last_obs is not None:
        try:
            fstr = pandas.to_datetime(first_obs).strftime('%Y-%m-%d %H:%M')
            lstr = pandas.to_datetime(last_obs).strftime('%Y-%m-%d %H:%M')
            info_lines.append(f"Span {fstr} → {lstr}")
        except Exception:
            pass
    info_html = " | ".join(info_lines)
    title_html = title if not info_html else f"{title}<br><span style='font-size:12px;color:#bbb'>{info_html}</span>"
    fig.update_layout(
        title={'text': title_html, 'x':0.5, 'xanchor':'center'},
        polar=dict(
            bgcolor='#0d0d0d',
            angularaxis=dict(
                direction='clockwise',
                rotation=90,
                tickmode='array',
                tickvals=day_tick_vals,
                ticktext=day_names,
                gridcolor='#222',
                tickfont=dict(size=13, color='#ddd')
            ),
            radialaxis=dict(
                range=[0,24.8],  # extend slightly to give day labels breathing room
                tickmode='array',
                tickvals=radial_ticks,
                ticktext=[str(t) for t in radial_ticks],
                tickfont=dict(size=10, color='#aaa'),
                angle=0,
                gridcolor='#222'
            )
        ),
    margin=dict(l=25, r=25, t=90 if info_html else 60, b=70),
        template='plotly_dark',
        height=height,
    annotations=[]
    )
    # Remove unusable zoom/pan controls while retaining image download & fullscreen
    remove_buttons = [
        'zoom2d','pan2d','select2d','lasso2d','zoomIn2d','zoomOut2d','autoScale2d','resetScale2d'
    ]
    st.plotly_chart(
        fig,
        width="stretch",
        config={
            'displaylogo': False,
            'modeBarButtonsToRemove': remove_buttons,
            'responsive': True
        }
    )
