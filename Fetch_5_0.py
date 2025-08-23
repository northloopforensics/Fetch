#Python3

# fixed an issue where submitted data had empty or null lat or long values. those records are now skipped and user notified

import simplekml #the library used to map longitudes and latitudes on google earth
import pandas #used to read spreadsheet data
import re
# import operator
import streamlit as st
import chardet      #   used to check file encodings
import os
from polycircles import polycircles     #   creates kml polygons
import leafmap.foliumap as leafmap      #   maps 
from leafmap.foliumap import plugins    #   maps
import geopandas                        
import folium                           #   maps
from math import asin, atan2, cos, degrees, radians, sin    #   calculates shapes and polygons on sphere
from folium.plugins import Draw, Geocoder, TimestampedGeoJson, HeatMap      
from streamlit_folium import st_folium          #   used to create geofences
import datetime
import geocoder                         #   search bar for geofence, api calls for address and ip lookups
import gpxpy
import numpy as np
from dateutil import parser
import xml.etree.ElementTree as ET
import zipfile
from functools import lru_cache
from typing import Optional
try:
    import pytz
except ImportError:
    pytz = None
import hashlib

# -------------------------------------------------------------
# Performance/Stability Helpers (added v5 PERF)
# -------------------------------------------------------------
# Centralize expensive regex compilation so they aren't recompiled each call
IPV4_REGEX = re.compile(r'(?:\d{1,3}\.){3}\d{1,3}\b')
IPV6_REGEX = re.compile(r'(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))')

def filter_valid_coordinates(df: pandas.DataFrame, lat_col: str = 'LATITUDE', lon_col: str = 'LONGITUDE'):
    """Return a cleaned copy of df with only valid numeric finite coordinates.

    This consolidates previously duplicated logic (numeric coercion, NaN/inf removal)
    and returns (clean_df, skipped_count).
    """
    if df is None or df.empty:
        return pandas.DataFrame(columns=df.columns if df is not None else []), 0
    working = df.copy()
    if lat_col not in working.columns or lon_col not in working.columns:
        return pandas.DataFrame(columns=working.columns), len(working)

    original = len(working)
    # Drop obvious nulls first
    working = working.dropna(subset=[lat_col, lon_col])
    # Coerce numeric
    working[lat_col] = pandas.to_numeric(working[lat_col], errors='coerce')
    working[lon_col] = pandas.to_numeric(working[lon_col], errors='coerce')
    # Remove NaN / inf
    working = working[
        working[lat_col].notna() & working[lon_col].notna() &
        np.isfinite(working[lat_col]) & np.isfinite(working[lon_col])
    ]
    clean = working.dropna(subset=[lat_col, lon_col]).reset_index(drop=True)
    return clean, (original - len(clean))

@st.cache_data(show_spinner=False)
def cached_ip_lookup(ip: str):
    """Cache individual IP lookups to avoid repeated API calls during a session."""
    try:
        return geocoder.ipinfo(ip).json
    except Exception:
        return None

now = datetime.datetime.now()
st.set_page_config(
   page_title="Fetch v5.0",
   #page_icon="🔴",
   layout="wide",
   initial_sidebar_state="expanded",
    menu_items={}
)
logo = ("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")
header_html = "<img src='data:image/png;base64,{}' class='img-fluid'>".format(logo)
st.markdown(
    header_html, unsafe_allow_html=True,
)
#Custom button color to bring prominence to executable actions

m = st.markdown("""
        <style>
        div.stButton > button:first-child {
            background-color: #ff0000;
            color:#ffffff;
        }
        div.stButton > button:hover {
            background-color: #8b0000;
            color:#ff0000;
            }
        </style>""", unsafe_allow_html=True)
#This removes Streamlit default settings icons
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: visible;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Top-level Kepler export button removed. Use the Kepler download button shown below the embedded map.

### Global Variables ###
get_headings = ""
selected_encoding = ""
icon_options = ["Yellow Paddle", "Green Paddle", "Blue Paddle", "White Paddle", "Teal Paddle", "Red Paddle", "Yellow Pushpin", "White Pushpin", "Red Pushpin", "Square"]
selected_icon = {'Square' :'http://maps.google.com/mapfiles/kml/shapes/placemark_square.png','Yellow Pushpin' : "http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png",'Red Pushpin' : "http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png",'White Pushpin' : "http://maps.google.com/mapfiles/kml/pushpin/wht-pushpin.png",'Red Paddle' : "http://maps.google.com/mapfiles/kml/paddle/red-circle.png",'Green Paddle' : "http://maps.google.com/mapfiles/kml/paddle/grn-circle.png",'Blue Paddle' : "http://maps.google.com/mapfiles/kml/paddle/blu-circle.png",'Teal Paddle' : "http://maps.google.com/mapfiles/kml/paddle/ltblu-circle.png",'Yellow Paddle' : "http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png",'White Paddle' : "http://maps.google.com/mapfiles/kml/paddle/wht-circle.png"}
invalid_ips = ['0', '10.', '127.0.0.1','172.16', '172.17', '172.18', '172.19', '172.2',  '172.21', '172.22', '172.23', '172.24', '172.25',
            '172.26', '172.27', '172.28', '172.29', '172.30',  '172.31', '192.168', '169.254', "255.255" ,"fc00"]
geo_list = []

# ---------------- Hotspot / Clustering Helpers ----------------
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

# Cached wrapper so repeated UI reruns don't recompute unnecessarily
@st.cache_data(show_spinner=False)
def cached_compute_hotspots(df: pandas.DataFrame, radius_m: float, min_samples: int, time_col: Optional[str], trim_chaining: bool = True):
    return compute_hotspots(df, radius_m, min_samples, time_col, trim_chaining=trim_chaining)

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
    for d, h in zip(day_idx, hours):
        counts[d, h] += 1
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
        use_container_width=True,
        config={
            'displaylogo': False,
            'modeBarButtonsToRemove': remove_buttons,
            'responsive': True
        }
    )

####    Functions Live Here     ######

def add_color_legend(Map, df):
    """
    Adds a color legend to the map for multiple data sources
    """
    if 'SOURCE_FILE' in df.columns and 'POINT_COLOR' in df.columns:
        # Get unique combinations of source files and colors
        legend_items = df[['SOURCE_FILE', 'POINT_COLOR']].drop_duplicates()
        
        # Create HTML for the legend
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 10px; 
                    right: 10px; 
                    z-index: 1000;
                    background-color: #333333;
                    color: white;
                    padding: 5px;
                    border-radius: 5px;
                    border: 2px solid grey;
                    ">
        <h5>Data Sources</h5>
        '''
        
        # Add each source file and its color to the legend
        for _, row in legend_items.iterrows():
            legend_html += f'''
            <div style="display: flex; align-items: center; margin: 5px;">
                <div style="width: 15px; 
                           height: 15px; 
                           background-color: {row['POINT_COLOR']}; 
                           border-radius: 50%;
                           margin-right: 5px;">
                </div>
                <span>{row['SOURCE_FILE']}</span>
            </div>
            '''
        
        legend_html += '</div>'
        
        # Add the legend to the map
        Map.get_root().html.add_child(folium.Element(legend_html))

def get_bounds(feature_collection):
    """Calculate bounds from feature collection"""
    lats = []
    lngs = []
    
    for feature in feature_collection['features']:
        coords = feature['geometry']['coordinates']
        for coord in coords:
            lats.append(coord[1])
            lngs.append(coord[0])
            
    return [[min(lats), min(lngs)], [max(lats), max(lngs)]]


def hex_to_rgb(hex_color: str):
    """Convert #RRGGBB hex to [r,g,b] list of ints for kepler color ranges."""
    if not isinstance(hex_color, str):
        return [255, 0, 0]
    h = hex_color.lstrip('#')
    if len(h) != 6:
        # fallback to red
        return [255, 0, 0]
    try:
        return [int(h[i:i+2], 16) for i in (0, 2, 4)]
    except Exception:
        return [255, 0, 0]

def convert_to_datetime_and_string(timestamp_string):  # function takes a timestamp string and converts to datetime and a uniform string output
    # parses the timestamp string into a datetime object
    datetime_value = parser.parse(timestamp_string)

    # Formats the datetime object into the desired string format
    formatted_string = datetime_value.strftime("%Y-%m-%dT%H:%M:%S")

    return datetime_value, formatted_string

def get_point_at_distance(lat1, lon1, d, bearing, R=6371):  # used to draw tower wedges
    """
    lat: initial latitude, in degrees
    lon: initial longitude, in degrees
    d: target distance from initial
    bearing: (true) heading in degrees
    R: optional radius of sphere, defaults to mean radius of earth

    Returns new lat/lon coordinate {d}km from initial, in degrees
    """
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    a = radians(bearing)
    lat2 = asin(sin(lat1) * cos(d/R) + cos(lat1) * sin(d/R) * cos(a))
    lon2 = lon1 + atan2(
        sin(a) * sin(d/R) * cos(lat1),
        cos(d/R) - sin(lat1) * sin(lat2)
    )
    return (degrees(lat2), degrees(lon2),)

def make_geofence_map():
    # --- Geofence Manager State ---
    if 'geofences' not in st.session_state:
        st.session_state['geofences'] = []  # list of dicts: id,name,color,geometry(type,wkt),created,updated,active,notes
    if 'geofence_counter' not in st.session_state:
        st.session_state['geofence_counter'] = 1

    help_Box = st.expander(label="Help")
    with help_Box:
        st.markdown("""
        Draw, name, save, import, and export geofences. Each geofence can have rules (dwell threshold coming soon).
        - Use the draw toolbar on the map (polygon/rectangle). Circles can be added after saving via buffer.
        - Click 'Capture Drawing' to load the last drawn shape into the metadata form.
        - Export all as GeoJSON or import an existing GeoJSON.
        - Convert hotspots to geofences from the hotspot panel (integration point pending).
        """)

    # Search / locate
    with st.form("geoform"):
        user_geo_input = st.text_input("Search (Address/IP)", placeholder="123 Main St or 8.8.8.8")
        search = st.form_submit_button("Locate")

    # Initialize session state for caching geocoding results
    if 'cached_geocode_result' not in st.session_state:
        st.session_state['cached_geocode_result'] = None
    if 'cached_search_term' not in st.session_state:
        st.session_state['cached_search_term'] = None

    global geomap
    # Initialize with neutral continental US view; we'll optionally recenter below
    geomap = folium.Map(zoom_start=4, location=[39,-98])
    Draw(export=True, draw_options={'circle': False,'circlemarker':False, 'marker':False}).add_to(geomap)
    folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                     attr='Esri', name='Esri Satellite', overlay=False, control=True).add_to(geomap)
    folium.LayerControl(position="topright", collapsed=True).add_to(geomap)

    # Geocode/IP locate - Only run when search button is clicked
    if search and user_geo_input:
        ipv4_ipv6_regex = "(^\s*((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))\s*$)|(^\s*((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\s*$)"
        
        # Check if we need to make a new API call
        if user_geo_input != st.session_state['cached_search_term']:
            if re.search(ipv4_ipv6_regex, user_geo_input):
                try:
                    st.info("🔍 Looking up IP address... (API call)")
                    ip_res = geocoder.ipinfo(user_geo_input)
                    if ip_res and ip_res.latlng:
                        # Cache the successful result
                        st.session_state['cached_geocode_result'] = {
                            'type': 'ip',
                            'data': ip_res,
                            'input': user_geo_input
                        }
                        st.session_state['cached_search_term'] = user_geo_input
                        st.success("✅ IP address located successfully!")
                    else:
                        st.error("❌ Could not locate IP address")
                        st.session_state['cached_geocode_result'] = None
                        st.session_state['cached_search_term'] = None
                except Exception as e:
                    st.error(f"❌ IP lookup failed: {str(e)}")
                    st.session_state['cached_geocode_result'] = None
                    st.session_state['cached_search_term'] = None
            else:
                try:
                    st.info("🔍 Looking up address... (API call)")
                    geo_res = geocoder.arcgis(user_geo_input)
                    if geo_res and geo_res.latlng:
                        # Cache the successful result
                        st.session_state['cached_geocode_result'] = {
                            'type': 'address',
                            'data': geo_res,
                            'input': user_geo_input
                        }
                        st.session_state['cached_search_term'] = user_geo_input
                        st.success("✅ Address located successfully!")
                    else:
                        st.error("❌ Could not locate address")
                        st.session_state['cached_geocode_result'] = None
                        st.session_state['cached_search_term'] = None
                except Exception as e:
                    st.error(f"❌ Address lookup failed: {str(e)}")
                    st.session_state['cached_geocode_result'] = None
                    st.session_state['cached_search_term'] = None
        else:
            st.info("📋 Using cached result (no API call needed)")

    # Display cached results if available
    if st.session_state['cached_geocode_result']:
        cached_result = st.session_state['cached_geocode_result']
        
        if cached_result['type'] == 'ip':
            ip_res = cached_result['data']
            user_geo_input = cached_result['input']
            
            # Format geocoder response for better readability
            st.write("**IP Geolocation Results - Location represents an estimated geographic area and does not indicate the point of usage.**")
            
            # Create organized display of key information
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Location Information:**")
                location_info = {
                    "IP Address": getattr(ip_res, 'ip', user_geo_input),
                    "City": getattr(ip_res, 'city', 'Not available'),
                    "State/Region": getattr(ip_res, 'state', 'Not available'), 
                    "Country": getattr(ip_res, 'country', 'Not available'),
                    "Postal Code": getattr(ip_res, 'postal', 'Not available'),
                    "Coordinates": f"{ip_res.latlng[0]:.6f}, {ip_res.latlng[1]:.6f}",
                    "Timezone": getattr(ip_res, 'timezone', 'Not available')
                }
                for key, value in location_info.items():
                    st.write(f"• **{key}:** {value}")
            
            with col2:
                st.write("**🌐 Network Information:**")
                network_info = {
                    "Organization": getattr(ip_res, 'org', 'Not available'),
                    "Status": getattr(ip_res, 'status', 'Unknown'),
                    "Provider": ip_res.provider if hasattr(ip_res, 'provider') else 'ipinfo.io'
                }
                for key, value in network_info.items():
                    st.write(f"• **{key}:** {value}")
            
            # Show raw data in an expandable section
            with st.expander("🔧 Raw Geocoder Data (Debug)"):
                # Show all available attributes in a more organized way
                all_attrs = {}
                for attr in dir(ip_res):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(ip_res, attr)
                            if not callable(value):
                                all_attrs[attr] = value
                        except:
                            pass
                st.json(all_attrs)
            
            # Rebuild map centered on result
            geomap = folium.Map(location=ip_res.latlng, zoom_start=11)
            Draw(export=True, draw_options={'circle': False,'circlemarker':False, 'marker':False}).add_to(geomap)
            folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                             attr='Esri', name='Esri Satellite', overlay=False, control=True).add_to(geomap)
            folium.LayerControl(position="topright", collapsed=True).add_to(geomap)
            
            # Create enhanced popup with correct field names
            popup_content = f"""
            <div style="width: 350px; font-family: Arial, sans-serif;">
                <h4 style="margin: 0 0 10px 0; color: #2c3e50;">🌐 IP Geolocation Details</h4>
                <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                    <tr style="background-color: #f8f9fa;"><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">IP Address:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{getattr(ip_res, 'ip', user_geo_input)}</td></tr>
                    <tr><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">Location:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{getattr(ip_res, 'city', 'Unknown')}, {getattr(ip_res, 'state', 'Unknown')}</td></tr>
                    <tr style="background-color: #f8f9fa;"><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">Country:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{getattr(ip_res, 'country', 'Unknown')}</td></tr>
                    <tr><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">Postal Code:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{getattr(ip_res, 'postal', 'N/A')}</td></tr>
                    <tr style="background-color: #f8f9fa;"><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">Coordinates:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{ip_res.latlng[0]:.6f}, {ip_res.latlng[1]:.6f}</td></tr>
                    <tr><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">Organization:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{getattr(ip_res, 'org', 'Unknown')}</td></tr>
                    <tr style="background-color: #f8f9fa;"><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">Timezone:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{getattr(ip_res, 'timezone', 'Unknown')}</td></tr>
                </table>
                <div style="margin-top: 8px; font-size: 11px; color: #6c757d; text-align: center;">
                    Data provided by {getattr(ip_res, 'provider', 'ipinfo.io')}
                </div>
            </div>
            """
            
            # Add enhanced marker
            folium.Marker(
                location=ip_res.latlng, 
                tooltip=f"🌐 {getattr(ip_res, 'ip', user_geo_input)} - {getattr(ip_res, 'city', 'Unknown')}, {getattr(ip_res, 'state', 'Unknown')}",
                popup=folium.Popup(popup_content, max_width=400),
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(geomap)

            
        elif cached_result['type'] == 'address':
            geo_res = cached_result['data']
            user_geo_input = cached_result['input']
            
            # Format geocoder response for better readability
            st.write("**🔍 Address Geolocation Results:**")
            
            # Create organized display of key information
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**📍 Location Information:**")
                location_info = {
                    "Search Term": user_geo_input,
                    "Full Address": getattr(geo_res, 'address', 'Not available'),
                    "City": getattr(geo_res, 'city', 'Not available'),
                    "State": getattr(geo_res, 'state', 'Not available'),
                    "Country": getattr(geo_res, 'country', 'Not available'),
                    "Postal Code": getattr(geo_res, 'postal', 'Not available'),
                    "Coordinates": f"{geo_res.latlng[0]:.6f}, {geo_res.latlng[1]:.6f}"
                }
                for key, value in location_info.items():
                    st.write(f"• **{key}:** {value}")
            
            with col2:
                st.write("**🎯 Accuracy Information:**")
                accuracy_info = {
                    "Confidence": getattr(geo_res, 'confidence', 'Not available'),
                    "Provider": geo_res.provider if hasattr(geo_res, 'provider') else 'ArcGIS',
                    "Status": getattr(geo_res, 'status', 'Unknown')
                }
                for key, value in accuracy_info.items():
                    st.write(f"• **{key}:** {value}")
            
            # Show raw data in an expandable section
            with st.expander("🔧 Raw Geocoder Data (Debug)"):
                all_attrs = {}
                for attr in dir(geo_res):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(geo_res, attr)
                            if not callable(value):
                                all_attrs[attr] = value
                        except:
                            pass
                st.json(all_attrs)
            
            geomap = folium.Map(location=geo_res.latlng, zoom_start=16)
            Draw(export=True, draw_options={'circle': False,'circlemarker':False, 'marker':False}).add_to(geomap)
            folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                             attr='Esri', name='Esri Satellite', overlay=False, control=True).add_to(geomap)
            folium.LayerControl(position="topright", collapsed=True).add_to(geomap)
            
            # Create enhanced popup for address
            popup_content = f"""
            <div style="width: 350px; font-family: Arial, sans-serif;">
                <h4 style="margin: 0 0 10px 0; color: #2c3e50;">📍 Address Details</h4>
                <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                    <tr style="background-color: #f8f9fa;"><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">Search Term:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{user_geo_input}</td></tr>
                    <tr><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">Full Address:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{getattr(geo_res, 'address', 'Not available')}</td></tr>
                    <tr style="background-color: #f8f9fa;"><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">City:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{getattr(geo_res, 'city', 'Unknown')}</td></tr>
                    <tr><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">State:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{getattr(geo_res, 'state', 'Unknown')}</td></tr>
                    <tr style="background-color: #f8f9fa;"><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">Country:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{getattr(geo_res, 'country', 'Unknown')}</td></tr>
                    <tr><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">Postal Code:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{getattr(geo_res, 'postal', 'N/A')}</td></tr>
                    <tr style="background-color: #f8f9fa;"><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">Coordinates:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{geo_res.latlng[0]:.6f}, {geo_res.latlng[1]:.6f}</td></tr>
                    <tr><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">Confidence:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{getattr(geo_res, 'confidence', 'Unknown')}</td></tr>
                </table>
                <div style="margin-top: 8px; font-size: 11px; color: #6c757d; text-align: center;">
                    Data provided by {getattr(geo_res, 'provider', 'ArcGIS')}
                </div>
            </div>
            """
            
            # Add enhanced marker
            folium.Marker(
                location=geo_res.latlng, 
                tooltip=f"📍 {getattr(geo_res, 'address', user_geo_input)}",
                popup=folium.Popup(popup_content, max_width=400),
                icon=folium.Icon(color='red', icon='map-marker')
            ).add_to(geomap)
            
        
    # Render existing saved geofences
    bounds_points = []
    if st.session_state.get('geofences'):
        for g in st.session_state['geofences']:
            if not g.get('active'):  # skip inactive
                continue
            try:
                feature = {
                    'type': 'Feature',
                    'geometry': {'type': g['type'], 'coordinates': g['coordinates']},
                    'properties': {'name': g['name']}
                }
                folium.GeoJson(
                    feature,
                    name=g['name'],
                    tooltip=g['name'],
                    style_function=lambda feat, col=g['color']: {
                        'color': col,
                        'weight': 2,
                        'fillColor': col,
                        'fillOpacity': 0.15
                    }
                ).add_to(geomap)
                # Collect bounds points for recentering
                geom_type = g['type']
                coords = g['coordinates']
                if geom_type == 'Polygon':
                    for lon, lat in coords[0]:
                        bounds_points.append((lat, lon))
                elif geom_type == 'LineString':
                    for lon, lat in coords:
                        bounds_points.append((lat, lon))
                elif geom_type == 'Point':
                    lon, lat = coords
                    bounds_points.append((lat, lon))
            except Exception:
                continue

    # Include current drawing in bounds
    last_geojson_temp = None
    try:
        last_geojson_temp = st.session_state.get('last_drawn_raw')
    except Exception:
        pass

    # Fallback: attempt to get from current output later; we will set after outputmap if needed.
    
    outputmap = st_folium(geomap, width=1100, height=600, key="geofence_map")

    # Capture last drawn geometry
    last_geojson = outputmap.get('last_active_drawing') if outputmap else None
    if last_geojson:
        st.session_state['last_drawn_raw'] = last_geojson
        # Update bounds with current drawing
        try:
            g_t = last_geojson.get('geometry', {}).get('type')
            g_c = last_geojson.get('geometry', {}).get('coordinates')
            if g_t == 'Polygon':
                for lon, lat in g_c[0]:
                    bounds_points.append((lat, lon))
            elif g_t == 'LineString':
                for lon, lat in g_c:
                    bounds_points.append((lat, lon))
            elif g_t == 'Point':
                lon, lat = g_c
                bounds_points.append((lat, lon))
        except Exception:
            pass

    # Fit bounds if we have enough points and map still default
    if bounds_points:
        try:
            lats = [p[0] for p in bounds_points]
            lons = [p[1] for p in bounds_points]
            sw = (min(lats), min(lons))
            ne = (max(lats), max(lons))
            # Add a slight padding
            pad_lat = (ne[0]-sw[0]) * 0.05 if ne[0]!=sw[0] else 0.01
            pad_lon = (ne[1]-sw[1]) * 0.05 if ne[1]!=sw[1] else 0.01
            geomap.fit_bounds([[sw[0]-pad_lat, sw[1]-pad_lon], [ne[0]+pad_lat, ne[1]+pad_lon]])
        except Exception:
            pass

    st.markdown("### Current Drawing (Instant Coordinates)")
    coord_list = []
    g_type = None
    if last_geojson:
        geom_obj = last_geojson.get('geometry', {})
        g_type = geom_obj.get('type')
        raw_coords = geom_obj.get('coordinates')
        try:
            if g_type == 'Polygon' and raw_coords:
                for lon, lat in raw_coords[0]:
                    coord_list.append((lat, lon))
            elif g_type == 'LineString' and raw_coords:
                for lon, lat in raw_coords:
                    coord_list.append((lat, lon))
            elif g_type == 'Point' and raw_coords:
                lon, lat = raw_coords
                coord_list.append((lat, lon))
        except Exception:
            coord_list = []

    if coord_list:
        coords_text = "Latitude, Longitude\n" + "\n".join(f"{lat}, {lon}" for lat, lon in coord_list)
        st.caption(f"Geometry: {g_type} | Vertices: {len(coord_list)}")
        st.text_area("Coordinates", value=coords_text, height=160, key="coord_display", help="Copy / paste ready")
        colx1, colx2, colx3 = st.columns(3)
        with colx1:
            st.download_button("Download TXT", data=coords_text, file_name="geofence_coordinates.txt")
        with colx2:
            # Quick GeoJSON export of just this drawing
            import json as _json
            feature = {
                "type":"FeatureCollection",
                "features":[{"type":"Feature","geometry":{"type":g_type,"coordinates":last_geojson['geometry']['coordinates']},"properties":{}}]
            }
            st.download_button("Download GeoJSON", data=_json.dumps(feature), file_name="geofence.geojson")
        with colx3:
            # KML (very simple) if polygon
            if g_type == 'Polygon':
                kml_coords = " ".join(f"{lon},{lat},0" for lat, lon in coord_list)
                kml = f"""<?xml version='1.0' encoding='UTF-8'?>\n<kml xmlns='http://www.opengis.net/kml/2.2'>\n<Document><Placemark><Polygon><outerBoundaryIs><LinearRing><coordinates>{kml_coords}</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark></Document></kml>"""
                st.download_button("Download KML", data=kml, file_name="geofence.kml")
            else:
                st.write(" ")
    else:
        st.info("Draw a shape (polygon/rectangle) to see coordinates below the map instantly.")

    # Advanced save/manage block removed per user request.

    # (Removed list management per user request)

    # Removed planned feature caption to declutter UI.


def parse_text_for_IPs(text):  #used to map ips
    # Use precompiled regex objects for performance
    ipv4_addresses = IPV4_REGEX.findall(text)
    ipv6_addresses = IPV6_REGEX.findall(text)
    
    ipv6_list = []
    ip_list = list(set(ipv4_addresses))

    for address in ipv6_addresses:
        clean_ipv6 = [item for item in address if len(item) > 16]
        if clean_ipv6:      # checks for empty lists
            ipv6_list.append(clean_ipv6)
    unique_ip6_list = [str(inner_list[0]) for inner_list in ipv6_list]
    unique_ip6_list = list(set(unique_ip6_list))
    ip_list.extend(unique_ip6_list)
    return ip_list

def get_IP_locale(invalidList, IPs):
    """Used to map IPs with better handling of API limits"""
    valid_only = [address for address in IPs if not any(address.startswith(inval) for inval in invalidList)]
    
    # Counter for successful lookups
    lookup_count = 0
    api_limit = 1000  # Daily limit for free tier
    results = []
    for ip in valid_only:
        try:
            data = cached_ip_lookup(ip)
            if not data:
                continue
            # Check for rate limit hint
            if isinstance(data, dict) and data.get('status_code') == 429:
                st.error(f"🚫 IP lookup limit reached (Error 429). Daily free limit ~{api_limit}. Try later or consider sponsored expansion.")
                break
            results.append(data)
            lookup_count += 1
            if lookup_count % 25 == 0:
                st.info(f"Processed {lookup_count} IPs...")
        except Exception as e:
            st.warning(f"⚠️ Error processing IP {ip}: {e}")
    # mutate global geo_list only once (reduces re-render churn)
    geo_list.extend(results)
    return results

def geo_ip_to_Dataframe(geo_list):  #used to map ips
    df = pandas.json_normalize(geo_list)
    df = df.dropna(how='all') #removes entirely empty rows
    columns = df.columns
    columnnamelist = []
    for name in columns:
        columnnamelist.append(name.upper())
    df.columns = columnnamelist
    df.rename(columns={"IP": 'IP ADDRESS','LAT': 'LATITUDE', 'LNG': "LONGITUDE", 'ORG': "SERVICE PROVIDER"}, inplace=True)
    return (df)

def convert_df(df):
    return df.to_csv().encode('utf-8')
def make_IPaddress_Map():   #used to map ips
    # help_Box = st.expander(label="Help")
    user_location = st.text_input("Place Name or Address - Use to Add a Relevant Location to the Map (Place e-mail received, point of comparison, etc)")
    ipdata = st.text_area("Input Data with IP Addresses or an E-Mail Header",height=200)
    ip_geo_button = st.button("Search")
    

    if ip_geo_button == True:
        
        search_geo_results = geocoder.arcgis(user_location)
        search_latlng = search_geo_results.json
        # print(search_latlng)
        
        try:
            parsed_IPs = parse_text_for_IPs(ipdata) # Parses text for IP addresses
            get_IP_locale(invalid_ips, parsed_IPs)  # Filters out local ip and keeps valid public ips
            datfram = geo_ip_to_Dataframe(geo_list=geo_list)  
            if datfram.empty:
                st.warning("Warning: No values resembling public IP addresses were found. Check the submitted data.")
              
            show_these = ('IP ADDRESS', 'STATUS','SERVICE PROVIDER', 'CITY', 'STATE', 'COUNTRY','LATITUDE', 'LONGITUDE')
            # show_these = None
            st.dataframe(data=datfram,hide_index=True,column_order=show_these) 
            csv = convert_df(datfram)
            st.download_button(label="Download as CSV",
                            data=csv,
                            file_name='Fetch_IP_Lookup.csv',
                            mime='text/csv',
                            )   
        
            cleandf, skipped_count = filter_valid_coordinates(datfram, 'LATITUDE', 'LONGITUDE')
            valid_count = len(cleandf)
            cleandf = cleandf.reset_index(drop=True)
            
            if skipped_count > 0:
                st.warning(f"⚠️ Skipped {skipped_count} IP record(s) that were missing latitude or longitude values. {valid_count} valid records will be processed.")
            
            if valid_count == 0:
                st.error("No valid IP records found with location data.")
                return
            
            gdf = geopandas.GeoDataFrame(cleandf, geometry=geopandas.points_from_xy(cleandf.LONGITUDE, cleandf.LATITUDE))
        except KeyError:
            print("key error in makeipaddressmap")
            pass
        
        try:
            user_gdf = pandas.json_normalize(search_latlng)
        except NotImplementedError:
            # st.info("No Place Name or Address provided. Attempting to Map IPs.")
            pass
        try:
            user_gdf = geopandas.GeoDataFrame(user_gdf, geometry=geopandas.points_from_xy(user_gdf.lng, user_gdf.lat))
        except UnboundLocalError:
            pass
        ipmap = leafmap.Map(zoom=2)    
        ipmap.add_basemap(basemap='ROADMAP')
        ipmap.add_basemap(basemap='TERRAIN')
        ipmap.add_basemap(basemap='HYBRID')
        ipmap.add_basemap(basemap="CartoDB.DarkMatter") 
        # ipmap.zoom_to_gdf(gdf) 
        try:
            user_spot = ipmap.add_circle_markers_from_xy(data=user_gdf, x="lng", y="lat",color='Red',fill_color="White")
        except UnboundLocalError:
            pass
        try:
            circle_Points = ipmap.add_circle_markers_from_xy(data=gdf, x="LONGITUDE", y="LATITUDE",color="Yellow",fill_color="Yellow", radius=5)
            ipmap.to_streamlit()
            # Record the last rendered map type so the unified download button can choose the correct exporter
            try:
                st.session_state['last_map_type'] = 'leaflet'
            except Exception:
                pass
            downloadfile = ipmap.to_html()               # for downloads
            download_test = st.download_button(label="Download HTML Map", data=downloadfile,file_name="Fetch_Analysis_Map.html")
        except UnboundLocalError:
            pass
        #     st.error("Input Data is required OR No location data was located from the provided data.")


def make_map(in_df):       #bring in pandas dataframe
    mapbox_token = "pk.eyJ1Ijoibm9ydGhsb29wY29uc3VsdGluZyIsImEiOiJjbTIyMng3ZmYwMnRyMmtvaGx6NnJvdnFpIn0.ixLwI99ZfD6vtsM_hoxDtA"
    valid_records, skipped_count = filter_valid_coordinates(in_df, 'LATITUDE', 'LONGITUDE')
    valid_count = len(valid_records)

    # Notify user if records were skipped
    if skipped_count > 0:
        st.warning(f"⚠️ Skipped {skipped_count} record(s) missing valid coordinates. Proceeding with {valid_count}.")

    # Check if we have any valid records left
    if valid_count == 0:
        st.error("No valid records with coordinates.")
        return

    gdf = geopandas.GeoDataFrame(valid_records, geometry=geopandas.points_from_xy(valid_records.LONGITUDE, valid_records.LATITUDE))
    # Reset index to ensure sequential indexing for iloc operations
    gdf = gdf.reset_index(drop=True)
    map_Type = st.radio(
        "Select Map Type",
        options=["Clustered Markers", "Points & Trails", "Hotspots", "Heatmap", "Cell Sites"],
        horizontal=True
    )
    Map = leafmap.Map()
    # Defer zooming for Hotspots so we can compute a tighter fit later
    if map_Type != "Hotspots":
        Map.zoom_to_gdf(gdf) 
    Map.add_basemap(basemap='ROADMAP')
    # Map.add_basemap(basemap='SATELLITE')
    Map.add_basemap(basemap='TERRAIN')
    Map.add_basemap(basemap='HYBRID')
    Map.add_basemap(basemap="CartoDB.DarkMatter") 

    if map_Type == "Clustered Markers":
        grouped_Points = Map.add_points_from_xy(gdf, x="LONGITUDE", y="LATITUDE", min_width=10,max_width=250,layer_name="Clustered Points", add_legend=False)
    
    map_rendered = False  # track if we've already sent map to streamlit

    if map_Type == "Hotspots":
        st.markdown("---")
        clean_coords = valid_records.copy()
        colh1, colh2, colh3, colh4 = st.columns(4)
        with colh1:
            radius_m = st.number_input("Radius (m)", min_value=5, max_value=1000, value=30, step=5)
        with colh2:
            max_hotspots = st.number_input("Max Hotspots", min_value=1, max_value=500, value=3, step=1)
        with colh3:
            possible_time_cols = [c for c in clean_coords.columns if 'TIME' in c.upper() or 'DATE' in c.upper()]
            time_col = st.selectbox("Time Column (optional -select for tactical clock)", options=[None]+possible_time_cols, index=0)
        with colh4:
            advanced = st.checkbox("Advanced", value=False, help="Show min points parameter")
        if advanced:
            min_samples = st.slider("Min Points (DBSCAN)", min_value=2, max_value=50, value=3, step=1)
        else:
            min_samples = 3
        trim_chaining = st.checkbox(
            "Trim Chaining (enforce radius)", value=True,
            help="If checked, any points farther than the chosen radius from a hotspot's centroid are removed (prevents elongated 'snake' clusters)."
        )
        run_cluster = st.button("Run Hotspot Analysis")
        if 'hotspot_store' not in st.session_state:
            st.session_state['hotspot_store'] = None
        param_key = f"r{radius_m}_m{min_samples}_t{time_col}_max{max_hotspots}_trim{trim_chaining}"
        clusters_df = pandas.DataFrame(); summary_df = pandas.DataFrame()
        if run_cluster:
            try:
                clusters_df, summary_df = cached_compute_hotspots(clean_coords, radius_m, min_samples, time_col, trim_chaining=trim_chaining)
            except RuntimeError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Hotspot clustering error: {e}")
            st.session_state['hotspot_store'] = {
                'params': param_key,
                'clusters': clusters_df,
                'summary': summary_df,
                'radius_m': radius_m,
                'min_samples': min_samples,
                'time_col': time_col,
                'max_hotspots': max_hotspots,
                'trim_chaining': trim_chaining
            }
        else:
            store = st.session_state.get('hotspot_store')
            if store and store.get('params') == param_key:
                clusters_df = store.get('clusters', pandas.DataFrame())
                summary_df = store.get('summary', pandas.DataFrame())
            elif store and store.get('params') != param_key and store.get('summary') is not None:
                st.info("Parameters changed — press 'Run Hotspot Analysis' to recompute.")

        if not summary_df.empty:
            st.markdown("### Hotspot Summary")
            # Ensure deterministic ordering (highest visit count first) then create sequential display IDs
            summary_df = summary_df.sort_values('COUNT', ascending=False).reset_index(drop=True)
            summary_df['DISPLAY_ID'] = summary_df.index + 1  # 1-based numbering for user-friendly display
            total_clusters = len(summary_df)
            limited_summary = summary_df.head(max_hotspots)
            id_map = dict(zip(summary_df['HOTSPOT_ID'], summary_df['DISPLAY_ID']))
            if total_clusters > max_hotspots:
                st.caption(f"Showing top {max_hotspots} of {total_clusters} hotspots (by visits).")
            # Prepare a user-facing table with contiguous hotspot numbers
            limited_display = limited_summary.copy()
            # Rename DISPLAY_ID column for clarity and place first
            cols_order = ['DISPLAY_ID'] + [c for c in limited_display.columns if c != 'DISPLAY_ID']
            limited_display = limited_display[cols_order].rename(columns={'DISPLAY_ID': 'HOTSPOT'})
            # Remove internal HOTSPOT_ID from user-facing table
            if 'HOTSPOT_ID' in limited_display.columns:
                limited_display = limited_display.drop(columns=['HOTSPOT_ID'])
            # Hide the implicit 0,1,2... index column from the user-facing table
            try:
                st.dataframe(limited_display.style.hide(axis='index'))
            except Exception:
                # Fallback if Styler.hide not available
                st.dataframe(limited_display.set_index(limited_display.columns[0], drop=True))
            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                st.download_button(
                    "Download Shown CSV",
                    data=limited_display.to_csv(index=False),
                    file_name="Fetch_Hotspots_Top.csv"
                )
            with col_dl2:
                # Provide full summary with both IDs so user can reconcile if needed
                full_display = summary_df.copy()
                full_display = full_display[['DISPLAY_ID'] + [c for c in full_display.columns if c != 'DISPLAY_ID']]
                full_display = full_display.rename(columns={'DISPLAY_ID': 'HOTSPOT'})
                if 'HOTSPOT_ID' in full_display.columns:
                    full_display = full_display.drop(columns=['HOTSPOT_ID'])
                st.download_button(
                    "Download All CSV",
                    data=full_display.to_csv(index=False),
                    file_name="Fetch_Hotspots_All.csv"
                )
            if st.button("Clear Hotspots", type="secondary"):
                st.session_state['hotspot_store'] = None
                st.experimental_rerun()
            palette = ["red","blue","green","orange","purple","teal","pink","yellow","white","gray","cadetblue","darkred","darkblue","darkgreen"]
            # --- Center & zoom based on hotspot CENTERS (ignoring any outlier member points) ---
            try:
                if not limited_summary.empty:
                    # Compute center-of-centers
                    mean_lat = float(limited_summary['CENTER_LAT'].mean())
                    mean_lon = float(limited_summary['CENTER_LON'].mean())
                    # Compute max pairwise center distance (approx haversine) to scale zoom
                    import math
                    def hav(lat1, lon1, lat2, lon2):
                        R = 6371000.0
                        phi1, phi2 = math.radians(lat1), math.radians(lat2)
                        dphi = math.radians(lat2-lat1)
                        dl = math.radians(lon2-lon1)
                        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dl/2)**2
                        return 2*R*math.atan2(math.sqrt(a), math.sqrt(1-a))
                    centers = limited_summary[['CENTER_LAT','CENTER_LON']].to_numpy()
                    max_dist = 0.0
                    for i in range(len(centers)):
                        for j in range(i+1, len(centers)):
                            d = hav(centers[i][0], centers[i][1], centers[j][0], centers[j][1])
                            if d > max_dist:
                                max_dist = d
                    # Map distance span (meters) to an approximate Leaflet zoom level
                    # Values chosen empirically for typical mid-latitude scale
                    if max_dist <= 60: zoom = 18
                    elif max_dist <= 120: zoom = 17
                    elif max_dist <= 300: zoom = 16
                    elif max_dist <= 600: zoom = 15
                    elif max_dist <= 1200: zoom = 14
                    elif max_dist <= 2500: zoom = 13
                    elif max_dist <= 5000: zoom = 12
                    elif max_dist <= 10000: zoom = 11
                    elif max_dist <= 20000: zoom = 10
                    elif max_dist <= 40000: zoom = 9
                    else: zoom = 8
                    # Slightly tighten if only a single hotspot
                    if len(limited_summary) == 1:
                        zoom = max(zoom, 17)
                    Map.set_center(mean_lon, mean_lat, zoom=zoom)
            except Exception:
                pass
            for idx, row in limited_summary.iterrows():
                color = palette[idx % len(palette)]
                display_id = row.DISPLAY_ID
                folium.Circle(
                    location=[row.CENTER_LAT, row.CENTER_LON],
                    radius=radius_m,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.35,
                    popup=f"Hotspot {display_id}<br>Visits: {row.COUNT}<br>Max Dist: {row.MAX_DISTANCE_M} m"
                ).add_to(Map)
                folium.Marker(
                    [row.CENTER_LAT, row.CENTER_LON],
                    tooltip=f"#{display_id} ({row.COUNT})"
                ).add_to(Map)
            show_points = st.checkbox("Show Individual Points", value=True, help="Display all member points for the shown hotspots (may slow large datasets)")
            if show_points:
                try:
                    pts = clusters_df[clusters_df['HOTSPOT_ID'].isin(limited_summary['HOTSPOT_ID'])]
                    if len(pts) > 25000:
                        st.warning("Showing individual points for very large hotspot sets may slow the browser.")
                    for cid, grp in pts.groupby('HOTSPOT_ID'):
                        color = palette[int(id_map.get(cid, cid)) % len(palette)]
                        for lat, lon in zip(grp['LATITUDE'], grp['LONGITUDE']):
                            folium.CircleMarker(location=[lat, lon], radius=2, color=color, fill=True, fill_color=color, fill_opacity=0.9).add_to(Map)
                except Exception as e:
                    st.error(f"Failed to render individual points: {e}")
            st.markdown("**Tips:** Increase radius if visits are a few dozen meters apart; decrease radius for tighter grouping.")
            # Render the map here (above clocks) once hotspots & optional points are drawn
            Map.to_streamlit()
            try:
                st.session_state['last_map_type'] = 'leaflet'
            except Exception:
                pass
            map_rendered = True

            if time_col:
                st.markdown("---")
                st.subheader("Hotspot Tactical Clocks")
                # Show one clock per hotspot (limited set only)
                for idx, row in limited_summary.iterrows():
                    hid = row.HOTSPOT_ID
                    display_id = row.DISPLAY_ID
                    subset = clusters_df[(clusters_df['HOTSPOT_ID']==hid)]
                    with st.expander(f"Hotspot {display_id} — {row.COUNT} visits", expanded=len(limited_summary)<=3):
                        render_tactical_clock(
                            subset,
                            time_col,
                            title=f"Hotspot {display_id} Activity",
                            height=560,
                            center_lat=row.CENTER_LAT,
                            center_lon=row.CENTER_LON,
                            radius_m=radius_m,
                            visits=int(row.COUNT),
                            max_distance_m=row.MAX_DISTANCE_M,
                            first_obs=row.FIRST_OBS,
                            last_obs=row.LAST_OBS
                        )
                # Overall clock
                with st.expander("All Hotspots Combined", expanded=False):
                    combined = clusters_df[clusters_df['HOTSPOT_ID']!=-1]
                    # Aggregate span and stats
                    agg_visits = int(combined.shape[0]) if not combined.empty else None
                    try:
                        first_obs_all = pandas.to_datetime(combined[time_col], errors='coerce').min()
                        last_obs_all = pandas.to_datetime(combined[time_col], errors='coerce').max()
                    except Exception:
                        first_obs_all = last_obs_all = None
                    render_tactical_clock(
                        combined,
                        time_col,
                        title="All Hotspots Combined",
                        height=560,
                        radius_m=radius_m,
                        visits=agg_visits,
                        first_obs=first_obs_all,
                        last_obs=last_obs_all
                    )
        else:
            if run_cluster:
                st.warning("No hotspots found with current parameters.")

    # (Single final Map.to_streamlit() call occurs later; removed interim render to avoid duplicate maps.)


    if map_Type == "Heatmap":
            st.markdown("---")
            heat_df = gdf[["LATITUDE","LONGITUDE"]].dropna()
            if heat_df.empty:
                st.error("No valid points for heatmap.")
            else:
                col_h1, col_h2, col_h3 = st.columns(3)
                with col_h1:
                    heat_radius = st.slider("Point Radius (px)", 2, 50, 12)
                with col_h2:
                    heat_blur = st.slider("Blur", 2, 40, 18)
                with col_h3:
                    use_weight = st.checkbox("Use Weight Column")
                weights = None
                if use_weight:
                    numeric_cols = [
                        c for c in gdf.columns
                        if c not in ("LATITUDE","LONGITUDE","geometry")
                        and pandas.api.types.is_numeric_dtype(gdf[c])
                    ]
                    if numeric_cols:
                        weight_col = st.selectbox("Weight Column", options=numeric_cols)
                        weights = pandas.to_numeric(gdf[weight_col], errors='coerce').fillna(0).tolist()
                    else:
                        st.info("No numeric columns available for weights.")
                try:
                    heat_data = list(zip(heat_df['LATITUDE'], heat_df['LONGITUDE'], weights if weights else [1]*len(heat_df)))
                    HeatMap(
                        data=[(lat, lon, w) for lat, lon, w in heat_data],
                        name="Heatmap",
                        radius=heat_radius,
                        blur=heat_blur,
                        max_zoom=18
                    ).add_to(Map)
                    folium.LayerControl().add_to(Map)
                    Map.zoom_to_gdf(gdf)
                    map_rendered = True
                    # Immediately render to avoid waiting for final fallback (gives user instant feedback)
                    Map.to_streamlit()
                    try:
                        st.session_state['last_map_type'] = 'leaflet'
                    except Exception:
                        pass
                except Exception as e:
                    st.error(f"Heatmap error: {e}")

    if map_Type == "Points & Trails":
            st.markdown("---")
            Map.zoom_to_gdf(gdf) 
            points_or_path = st.radio(label="Select map activity", options=["Markers", "Show Point Progression", "Vapour Trail", "Kepler 3D"], horizontal=True)
            
            if points_or_path == "Markers":     #Shows markers only
                if "POINT_COLOR" in valid_records.columns:
                    # First add the accuracy circles with lower z-index
                    if st.checkbox("Data has Accuracy or Radius Information"):
                        # Filter to only show numeric columns for radius selection
                        numeric_columns = []
                        for col in gdf.columns:
                            if gdf[col].dtype in ['int64', 'float64', 'int32', 'float32']:
                                numeric_columns.append(col)
                        
                        if not numeric_columns:
                            st.error("No numeric columns found for radius/accuracy information. Please ensure your data contains numeric columns for radius values.")
                        else:
                            radius_value = st.selectbox(label="Radius/Footprint in Meters", options=numeric_columns)
                            try:
                                for idx, row in gdf.iterrows():
                                    rad_value = row[radius_value]
                                    # Only create circle if radius value exists and is valid
                                    if pandas.notna(rad_value) and float(rad_value) > 0:                        
                                        circle = folium.Circle(
                                            location=[row['LATITUDE'], row['LONGITUDE']],
                                            radius=rad_value,
                                            color=row["POINT_COLOR"],
                                            fill_color=row["POINT_COLOR"],                                
                                            fill=True,
                                            fill_opacity=0.5,
                                        ).add_to(Map)
                            except (KeyError, ValueError) as e:
                                st.error(f"Error processing radius information: {str(e)}. Please select a column with positive numeric values.")
                    
                    # Then add the markers with higher z-index
                    for idx, row in gdf.iterrows():
                        # Create a single-row dataframe for this point
                        single_point_df = pandas.DataFrame([row]).reset_index(drop=True)
                        circle_Points = Map.add_circle_markers_from_xy(
                            data=single_point_df, 
                            x="LONGITUDE", 
                            y="LATITUDE",
                            color=row["POINT_COLOR"],
                            fill_color=row["POINT_COLOR"],
                            radius=5,
                        )
                    # per-map legacy download suppressed here; a single download button
                    # will be shown below the final rendered map instead.
                    try:
                        import tempfile, os, hashlib
                        btn_col_left, _ = st.columns([1, 4])
                        with btn_col_left:
                            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
                            tmp_name = tmp.name
                            tmp.close()
                            try:
                                try:
                                    Map.save(tmp_name)
                                except Exception:
                                    try:
                                        with open(tmp_name, 'w', encoding='utf-8') as fh:
                                            fh.write(Map.get_root().render())
                                    except Exception:
                                        pass

                                # per-map markers_all download suppressed; final download button placed below the rendered map
                            finally:
                                try:
                                    if os.path.exists(tmp_name):
                                        os.unlink(tmp_name)
                                except Exception:
                                    pass
                    except Exception:
                        pass

                else:
                    # Use color from color picker (stored in POINT_COLOR column)
                    color = gdf['POINT_COLOR'].iloc[0] if 'POINT_COLOR' in gdf.columns and len(gdf) > 0 else "#FF0000"
                    
                    if st.checkbox("Data has Accuracy or Radius Information"):
                        # Filter to only show numeric columns for radius selection
                        numeric_columns = []
                        for col in gdf.columns:
                            if gdf[col].dtype in ['int64', 'float64', 'int32', 'float32']:
                                numeric_columns.append(col)
                        
                        if not numeric_columns:
                            st.error("No numeric columns found for radius/accuracy information. Please ensure your data contains numeric columns for radius values.")
                        else:
                            radius_value = st.selectbox(label="Radius/Footprint in Meters", options=numeric_columns)
                            try:
                                for idx, row in gdf.iterrows():
                                    rad_value = row[radius_value]
                                    if pandas.notna(rad_value) and float(rad_value) > 0:
                                        circle = folium.Circle(
                                            location=[row['LATITUDE'], row['LONGITUDE']],
                                            radius=rad_value,
                                            color=color,
                                            fill_color=color,                                
                                            fill=True,
                                            fill_opacity=0.5,
                                            weight=1,
                                            z_index=1,  # Lower z-index for circles
                                        ).add_to(Map)
                            except (KeyError, ValueError) as e:
                                st.error(f"Error processing radius information: {str(e)}. Please select a column with positive numeric values.")
                    
                    # Add markers with higher z-index
                    circle_Points = Map.add_circle_markers_from_xy(
                        data=gdf, 
                        x="LONGITUDE", 
                        y="LATITUDE",
                        color=color,
                        fill_color=color, 
                        radius=5,
                        z_index_offset=1000  # Higher z-index for markers
                    )
                    # Per-map download button for this legacy Map render (Markers)
                    try:
                        import tempfile, os, hashlib
                        btn_col_left, _ = st.columns([1, 4])
                        with btn_col_left:
                            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
                            tmp_name = tmp.name
                            tmp.close()
                            try:
                                try:
                                    Map.save(tmp_name)
                                except Exception:
                                    try:
                                        with open(tmp_name, 'w', encoding='utf-8') as fh:
                                            fh.write(Map.get_root().render())
                                    except Exception:
                                        pass

                                # legacy markers_all download suppressed (single download button shown after loop)
                            finally:
                                try:
                                    if os.path.exists(tmp_name):
                                        os.unlink(tmp_name)
                                except Exception:
                                    pass
                    except Exception:
                        pass
            # Kepler 3D option: interactive 3D map via keplergl
            if points_or_path == "Kepler 3D":
                st.markdown("---")
                # Try to import keplergl and pandas to_geojson helper
                try:
                    from keplergl import KeplerGl
                    import json
                except Exception:
                    st.error("keplergl is not installed in the environment. Install keplergl to use the 3D map option.")
                    st.stop()

                # Controls
                with st.expander("Kepler 3D Settings"):
                    col1, col2 = st.columns(2)
                    with col1:
                        map_style_mode = st.radio("Map Style", options=["light", "dark", "satellite"], index=0, horizontal=False)
                        # Add radius circles controls directly in the settings
                        enable_radius_circles = st.checkbox("Create flat radius circles from point locations", value=False)
                        if enable_radius_circles:
                            # Let user select radius column from dataframe
                            numeric_cols = [c for c in gdf.columns if pandas.api.types.is_numeric_dtype(gdf[c]) and c not in ['LATITUDE', 'LONGITUDE']]
                            if numeric_cols:
                                radius_col = st.selectbox("Select radius column (meters)", options=numeric_cols)
                            else:
                                st.warning("No numeric columns found for radius values.")
                                enable_radius_circles = False
                    with col2:
                        enable_3d_buildings = st.checkbox("Show 3D Buildings (basemap)", value=True)
                        cam_tilt = st.slider("Camera Tilt (deg)", min_value=0, max_value=85, value=45)
                    
                    cam_zoom = st.slider("Camera Zoom (0-20)", min_value=0, max_value=20, value=12)
                    # Debug toggle to inspect persisted kepler payload in-session
                    show_kepler_debug = st.checkbox("Show Kepler payload debug", value=False)

                # Prepare dataframe for kepler
                try:
                    kdf = gdf.copy()
                    # Ensure numeric
                    kdf['LATITUDE'] = pandas.to_numeric(kdf['LATITUDE'], errors='coerce')
                    kdf['LONGITUDE'] = pandas.to_numeric(kdf['LONGITUDE'], errors='coerce')
                    kdf = kdf.dropna(subset=['LATITUDE','LONGITUDE'])
                except Exception as e:
                    st.error(f"Failed to prepare data for kepler.gl: {e}")
                    kdf = None

                if kdf is None or kdf.empty:
                    st.warning("No valid points for Kepler 3D map.")
                else:
                    # Build dataset
                    dataset_name = 'points'
                    
                    # Add elevation for all points (3 meters above ground)
                    kdf['point_elevation'] = 3.0
                    
                    # Convert POINT_COLOR hex to rgb arrays for kepler
                    if 'POINT_COLOR' in kdf.columns:
                        kdf = kdf.reset_index(drop=True)
                        kdf['__color_rgb'] = kdf['POINT_COLOR'].apply(lambda hx: hex_to_rgb(hx))
                        # kepler expects color as list of four ints [r,g,b,a] sometimes; we'll add alpha 255
                        kdf['__color_rgba'] = kdf['__color_rgb'].apply(lambda rgb: [rgb[0], rgb[1], rgb[2], 255])
                        
                        # Create lighter versions for point fills
                        def lighten_color(rgb, factor=0.4):
                            """Make color lighter by blending with white"""
                            return [min(255, int(c + (255 - c) * factor)) for c in rgb]
                        
                        kdf['__color_light'] = kdf['__color_rgb'].apply(lambda rgb: lighten_color(rgb))
                        kdf['__color_light_hex'] = kdf['__color_light'].apply(lambda rgb: f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}")

                    # Set building color based on map style
                    if map_style_mode == "light":
                        building_color = [180, 180, 180]  # Light gray for light mode
                    elif map_style_mode == "dark":
                        building_color = [160, 130, 100]  # Darker tan for dark mode
                        # building_color = [9.665468314072013, 17.18305478057247, 31.1442867897876]  # Dark blue-gray for dark mode
                    else:  # satellite
                        building_color = [120, 120, 120]  # Medium gray for satellite mode

                    # Create a simple Kepler config to set 3D extrusion
                    kepler_config = {
                        "version": "v1",
                        "config": {
                            "visState": {
                                "filters": [],
                                "layers": []
                            },
                            "mapState": {
                                "latitude": float(kdf['LATITUDE'].mean()),
                                "longitude": float(kdf['LONGITUDE'].mean()),
                                "zoom": cam_zoom,
                                "bearing": 0,
                                "pitch": cam_tilt
                            },
                            "mapStyle": {
                                "styleType": "{style}".format(style=map_style_mode),
                                "topLayerGroups": {},
                                "visibleLayerGroups": {
                                    "label": True,
                                    "road": True,
                                    "border": False,
                                    "building": enable_3d_buildings,
                                    "water": True,
                                    "land": True,
                                    "3d building": enable_3d_buildings
                                },
                                "threeDBuildingColor": building_color,
                                "mapStyles": {}
                            }
                        }
                    }

                    # Build a point layer config
                    point_layer = {
                        "id": "point_layer",
                        "type": "point",
                        "config": {
                            "dataId": dataset_name,
                            "label": "Points",
                            "color": [255, 99, 71],
                            "columns": {"lat": "LATITUDE", "lng": "LONGITUDE"},
                            "isVisible": True,
                            "visConfig": {
                                # radius is in pixels for kepler point layers
                                "radius": 25,
                                "radiusRange": [1, 100],
                                "opacity": 0.9,
                                "colorRange": {"name": "Custom","type": "custom","category": "Custom","colors": ["#FF0000","#00FF00","#0000FF"]},
                                "elevationScale": 1,
                                "enable3d": True
                            }
                        },
                        "visualChannels": {
                            "colorField": None,
                            "colorScale": "quantile",
                            "sizeField": None,
                            "sizeScale": "linear",
                            "heightField": {
                                "name": "point_elevation",
                                "type": "real"
                            },
                            "heightScale": "linear"
                        }
                    }

                    # If user provided colors per source, use the color field as color
                    # Kepler can map color by a column; we'll provide a numeric fallback but encode rgba in the dataset for styling
                    if 'POINT_COLOR' in kdf.columns:
                        # Add color column as strings (kepler can parse hex in some versions), also create numeric index
                        kdf['__color_hex'] = kdf['POINT_COLOR']
                        # Use lighter color for point fills
                        point_layer['config']['color'] = [255, 255, 255]
                        point_layer['config']['colorField'] = {"name": "__color_light_hex", "type": "string"}
                        point_layer['visualChannels']['colorField'] = {"name": "__color_light_hex", "type": "string"}
                        point_layer['config']['visConfig'].update({
                            "colorRange": {"name": "Custom","type": "custom","category": "Custom","colors": list(kdf['__color_light_hex'].unique())},
                            "strokeColor": kdf['POINT_COLOR'].iloc[0] if len(kdf) > 0 else "#FF0000",
                            "strokeColorRange": {"name": "Custom","type": "custom","category": "Custom","colors": list(kdf['POINT_COLOR'].unique())},
                            "stroked": True,
                            "strokeWidth": 2
                        })

                    kepler_config['config']['visState']['layers'].append(point_layer)

                    # If radius circles enabled, add flat circles using radius values from data
                    if enable_radius_circles:
                        building_layer = {
                            "id": "radius_circles",
                            "type": "geojson",
                            "config": {
                                "dataId": dataset_name,
                                "label": "Radius Circles",
                                "color": [200, 200, 200],
                                "highlightColor": [252, 242, 26, 255],
                                "columns": {
                                    "geojson": "_geojson"
                                },
                                "isVisible": True,
                                "visConfig": {
                                    "opacity": 0.3,
                                    "strokeOpacity": 0.6,
                                    "thickness": 0.5,
                                    "strokeColor": [200, 200, 200],
                                    "colorRange": {
                                        "name": "Global Warming",
                                        "type": "sequential",
                                        "category": "Uber",
                                        "colors": ["#5A1846", "#900C3F", "#C70039", "#E3611C", "#F1920E", "#FFC300"]
                                    },
                                    "strokeColorRange": {
                                        "name": "Global Warming",
                                        "type": "sequential", 
                                        "category": "Uber",
                                        "colors": ["#5A1846", "#900C3F", "#C70039", "#E3611C", "#F1920E", "#FFC300"]
                                    },
                                    "radius": 10,
                                    "sizeRange": [0, 10],
                                    "radiusRange": [0, 50],
                                    "heightRange": [0, 1],
                                    "elevationScale": 0.01,
                                    "stroked": True,
                                    "filled": True,
                                    "enable3d": True,
                                    "wireframe": False
                                },
                                "hidden": False,
                                "textLabel": [
                                    {
                                        "field": None,
                                        "color": [255, 255, 255],
                                        "size": 18,
                                        "offset": [0, 0],
                                        "anchor": "start",
                                        "alignment": "center"
                                    }
                                ]
                            },
                            "visualChannels": {
                                "colorField": None,
                                "colorScale": "quantile",
                                "sizeField": None,
                                "sizeScale": "linear",
                                "strokeColorField": None,
                                "strokeColorScale": "quantile",
                                "heightField": {
                                    "name": "building_height",
                                    "type": "real"
                                },
                                "heightScale": "linear",
                                "radiusField": None,
                                "radiusScale": "linear"
                            }
                        }
                        # Only add if geometry column exists (we'll replace dataId later if we build a separate 'buildings' dataset)
                        if 'geometry' in kdf.columns:
                            kepler_config['config']['visState']['layers'].append(building_layer)

                    # Prepare Kepler data payloads carefully:
                    # - Points dataset must NOT contain shapely geometry objects (convert/drop geometry)
                    # - Buildings (if requested) must be passed as a GeoJSON dict (only when polygon geometries present)
                    try:
                        data_payload = {}
                        # Points DataFrame: drop geometry column if present to avoid shapely serialization issues
                        points_df = kdf.copy()
                        if 'geometry' in points_df.columns:
                            try:
                                # If geometry is present, drop it for the points dataset (we use LAT/LONG columns instead)
                                points_df = points_df.drop(columns=['geometry'])
                            except Exception:
                                # ensure we still have a usable points dataframe
                                points_df = points_df.loc[:, [c for c in points_df.columns if c != 'geometry']]

                        # Sanitize object columns to avoid passing non-serializable types into keplergl
                        try:
                            import json as _json
                            import numpy as _np
                            for col in list(points_df.columns):
                                if points_df[col].dtype == object:
                                    # Inspect a sample
                                    sample = None
                                    try:
                                        sample = points_df[col].dropna().iloc[0]
                                    except Exception:
                                        sample = None

                                    # If sample is shapely geometry, drop the column
                                    try:
                                        from shapely.geometry.base import BaseGeometry
                                        if isinstance(sample, BaseGeometry):
                                            points_df = points_df.drop(columns=[col])
                                            continue
                                    except Exception:
                                        pass

                                    # If sample is a string that looks like a JSON/list/dict, try to parse it into a Python object
                                    if isinstance(sample, str):
                                        s = sample.strip()
                                        if s and (s[0] in '[{('):
                                            try:
                                                parsed = _json.loads(s)
                                                sample = parsed
                                            except Exception:
                                                try:
                                                    import ast as _ast
                                                    parsed = _ast.literal_eval(s)
                                                    sample = parsed
                                                except Exception:
                                                    # leave as original string if parsing fails
                                                    pass

                                    # If sample is a list/tuple/ndarray of primitives (e.g. color arrays), keep as Python list
                                    if isinstance(sample, (list, tuple, _np.ndarray)):
                                        def _normalize_list(v):
                                            if v is None:
                                                return None
                                            # If v is a stringified list, try to parse it first
                                            if isinstance(v, str):
                                                s2 = v.strip()
                                                if s2 and (s2[0] in '[{('):
                                                    try:
                                                        v = _json.loads(s2)
                                                    except Exception:
                                                        try:
                                                            import ast as _ast2
                                                            v = _ast2.literal_eval(s2)
                                                        except Exception:
                                                            # leave as string and fall through to JSON-dump fallback
                                                            pass

                                            # convert numpy arrays to list
                                            if isinstance(v, _np.ndarray):
                                                try:
                                                    v = v.tolist()
                                                except Exception:
                                                    return _json.dumps(v)
                                            # If all items are primitives, return as list (keplergl wants lists for color arrays)
                                            try:
                                                if all(isinstance(x, (int, float, str, bool, type(None))) for x in v):
                                                    return list(v)
                                            except Exception:
                                                pass
                                            # Fallback: JSON-serialize complex nested structures
                                            return _json.dumps(v)

                                        points_df[col] = points_df[col].apply(_normalize_list)
                                    elif isinstance(sample, dict):
                                        # JSON-serialize dicts
                                        points_df[col] = points_df[col].apply(lambda v: _json.dumps(v) if v is not None else None)
                                    else:
                                        # Fallback: coerce to primitive/string for safe serialization
                                        points_df[col] = points_df[col].apply(lambda v: v if v is None or isinstance(v, (str, int, float, bool)) else str(v))
                        except Exception:
                            # If sanitization fails, proceed with original points_df (we already dropped geometry)
                            pass

                        data_payload[dataset_name] = points_df

                        # Prepare radius circles dataset only if user enabled. We support:
                        # - polygon/multipolygon geometries already in a 'geometry' column  
                        # - WKT polygon strings in an object column
                        # - flat circles generated from point locations using radius column values
                        buildings_added = False
                        if enable_radius_circles:
                            try:
                                valid_poly_types = {'Polygon', 'MultiPolygon'}
                                gdf_buildings = None

                                # 1) If there's a geometry column, check for polygon types
                                if 'geometry' in kdf.columns:
                                    try:
                                        geom_series = kdf['geometry']
                                        if hasattr(geom_series, 'geom_type'):
                                            geom_types = set(geom_series.geom_type.dropna().unique())
                                        else:
                                            geom_types = set()
                                    except Exception:
                                        geom_types = set()

                                    if geom_types & valid_poly_types:
                                        gdf_buildings = geopandas.GeoDataFrame(kdf.loc[kdf['geometry'].geom_type.isin(list(valid_poly_types))].copy())
                                        gdf_buildings = gdf_buildings.set_geometry('geometry')

                                # 2) If no polygon geometries found, look for WKT-like columns containing POLYGON text
                                if gdf_buildings is None or gdf_buildings.empty:
                                    wkt_col = None
                                    for c in kdf.columns:
                                        if kdf[c].dtype == object:
                                            sample_vals = kdf[c].dropna().astype(str).head(5).str.upper().tolist()
                                            if any(s.startswith('POLYGON') or s.startswith('MULTIPOLYGON') for s in sample_vals):
                                                wkt_col = c
                                                break
                                    if wkt_col:
                                        try:
                                            import shapely.wkt as wkt
                                            parsed = kdf[wkt_col].astype(str).apply(lambda x: wkt.loads(x) if x and x.strip() else None)
                                            tmp = kdf.copy()
                                            tmp['geometry'] = parsed
                                            tmp = tmp[tmp['geometry'].notna()].copy()
                                            if not tmp.empty:
                                                gdf_buildings = geopandas.GeoDataFrame(tmp, geometry='geometry')
                                        except Exception:
                                            gdf_buildings = None

                                # 3) If still nothing and radius circles are enabled, create flat circular polygons using radius from data
                                if (gdf_buildings is None or gdf_buildings.empty) and ('LATITUDE' in kdf.columns and 'LONGITUDE' in kdf.columns) and enable_radius_circles:
                                    try:
                                        pts = geopandas.GeoDataFrame(kdf.copy(), geometry=geopandas.points_from_xy(kdf.LONGITUDE, kdf.LATITUDE), crs="EPSG:4326")
                                        pts_proj = pts.to_crs(epsg=3857)
                                        
                                        # Use individual radius values from the selected column
                                        radius_values = pandas.to_numeric(pts[radius_col], errors='coerce').fillna(10)  # fallback to 10m
                                        
                                        # Buffer each point with its individual radius
                                        polys_proj = pts_proj.geometry.buffer(radius_values)
                                        polys = polys_proj.to_crs(epsg=4326)
                                        
                                        tmp = pts.copy()
                                        tmp['geometry'] = polys
                                        gdf_buildings = geopandas.GeoDataFrame(tmp, geometry='geometry', crs="EPSG:4326")
                                    except Exception as e:
                                        st.error(f"Failed to create radius circles: {e}")
                                        gdf_buildings = None

                                # If we managed to build polygon features, inject heights and convert to GeoJSON
                                if gdf_buildings is not None and not gdf_buildings.empty:
                                    # For radius circles, make them flat (height = 0.01 for visibility)
                                    # Set minimal height for flat appearance
                                    gdf_buildings['building_height'] = 0.01

                                    try:
                                        buildings_geojson = json.loads(gdf_buildings.to_json())
                                        for feat_idx, feat in enumerate(buildings_geojson.get('features', [])):
                                            props = feat.setdefault('properties', {})
                                            props['building_height'] = 0.01
                                            
                                            # Add color information from POINT_COLOR column if available
                                            if 'POINT_COLOR' in gdf_buildings.columns:
                                                try:
                                                    point_color = gdf_buildings.iloc[feat_idx]['POINT_COLOR']
                                                    props['point_color'] = point_color
                                                    # Convert hex to RGB for kepler
                                                    rgb = hex_to_rgb(point_color)
                                                    props['color_r'] = rgb[0]
                                                    props['color_g'] = rgb[1] 
                                                    props['color_b'] = rgb[2]
                                                except Exception:
                                                    pass
                                        
                                        data_payload['buildings'] = buildings_geojson
                                        buildings_added = True
                                    except Exception:
                                        buildings_added = False
                                else:
                                    st.info("3D buildings skipped: geometry column contains no Polygon/MultiPolygon features and no footprints were created.")
                                    buildings_added = False
                            except Exception:
                                buildings_added = False

                        # Update building layer config to reference a separate dataset if created
                        if buildings_added:
                            # Reference the 'buildings' dataset (geojson dict)
                            building_layer['config']['dataId'] = 'buildings'
                            # Update building layer to use color from POINT_COLOR if available
                            if 'POINT_COLOR' in kdf.columns:
                                building_layer['visualChannels']['colorField'] = {
                                    "name": "point_color", 
                                    "type": "string"
                                }
                                building_layer['visualChannels']['strokeColorField'] = {
                                    "name": "point_color",
                                    "type": "string"
                                }
                                building_layer['config']['visConfig']['colorRange'] = {
                                    "name": "Custom",
                                    "type": "custom", 
                                    "category": "Custom",
                                    "colors": list(kdf['POINT_COLOR'].unique())
                                }
                                building_layer['config']['visConfig']['strokeColorRange'] = {
                                    "name": "Custom",
                                    "type": "custom",
                                    "category": "Custom", 
                                    "colors": list(kdf['POINT_COLOR'].unique())
                                }
                        else:
                            # Remove attempted building layer if we couldn't construct valid building geojson
                            # (safely ignore -- keep only point layers)
                            kepler_config['config']['visState']['layers'] = [lay for lay in kepler_config['config']['visState']['layers'] if lay.get('id') != 'buildings']

                        # Instantiate Kepler with prepared payload
                        # If debug enabled, inspect the 'points' DataFrame for problematic dtypes/values
                        if show_kepler_debug:
                            try:
                                preview_df = data_payload.get(dataset_name) if isinstance(data_payload, dict) else None
                                st.write('[Kepler debug] top-level payload type:', type(data_payload))
                                if isinstance(preview_df, pandas.DataFrame):
                                    st.write('[Kepler debug] points DataFrame shape:', preview_df.shape)
                                    for col in preview_df.columns:
                                        try:
                                            col_dtype = str(preview_df[col].dtype)
                                            nonnull = preview_df[col].dropna()
                                            sample = nonnull.iloc[0] if len(nonnull) > 0 else None
                                            sample_type = type(sample)
                                            sample_repr = repr(sample)
                                            st.write(f" - {col}: dtype={col_dtype}, sample_type={sample_type}, sample_repr={sample_repr[:200]}")
                                            # detect shapely geometries or nested structures
                                            try:
                                                from shapely.geometry.base import BaseGeometry
                                                if isinstance(sample, BaseGeometry):
                                                    st.write(f"   -> column {col} contains shapely geometry objects; these should be removed or converted.")
                                            except Exception:
                                                pass
                                        except Exception as e_ins:
                                            st.write(f" - {col}: inspection error: {e_ins}")
                                else:
                                    st.write('[Kepler debug] points payload not a DataFrame:', type(preview_df))
                            except Exception:
                                pass
                        kepler_map = KeplerGl(height=600, data=data_payload, config=kepler_config)
                        # Persist payload and config so we can rebuild KeplerGl later
                        try:
                            if isinstance(data_payload, dict) and isinstance(kepler_config, dict):
                                st.session_state['kepler_data_payload'] = data_payload
                                st.session_state['kepler_config'] = kepler_config
                            else:
                                # Avoid storing malformed payloads (e.g., strings) into session
                                st.warning("Kepler payload/config not persisted because structure is unexpected.")
                        except Exception:
                            pass
                        # Optional debug output: show session payload type/summary
                        try:
                            if show_kepler_debug:
                                preview = st.session_state.get('kepler_data_payload', data_payload if 'data_payload' in locals() else None)
                                st.write("Kepler payload type:", type(preview))
                                if isinstance(preview, dict):
                                    st.write("Kepler payload keys:", list(preview.keys()))
                                    for k, v in preview.items():
                                        try:
                                            if hasattr(v, 'shape'):
                                                st.write(f" - {k}: DataFrame shape={v.shape}")
                                            else:
                                                st.write(f" - {k}: {type(v)}")
                                        except Exception:
                                            st.write(f" - {k}: {type(v)}")
                                elif isinstance(preview, str):
                                    st.write(f"Kepler payload is a string (len={len(preview)}) -> exists on disk: {os.path.exists(preview)}")
                                else:
                                    st.write(repr(preview))
                        except Exception:
                            pass
                        # Render via HTML representation
                        html = kepler_map._repr_html_()
                        st.components.v1.html(html, height=650, scrolling=True)
                        # Record that the last rendered map was a Kepler map
                        try:
                            st.session_state['last_map_type'] = 'kepler'
                        except Exception:
                            pass
                        # Per-map download button for this Kepler render: build an HTML file from
                        # the persisted kepler payload/config (preferred) or fall back to the
                        # current kepler_map object, then offer it via st.download_button.
                        try:
                            import tempfile, os

                            # Create a small two-column area so the button sits under the map on the left
                            btn_col_left, _ = st.columns([1, 4])
                            with btn_col_left:
                                try:
                                    # Build a temporary file and write the Kepler HTML into it.
                                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
                                    tmp_name = tmp.name
                                    tmp.close()

                                    # Prefer persisted payload/config from session state
                                    kp_payload = st.session_state.get('kepler_data_payload') if 'kepler_data_payload' in st.session_state else (data_payload if 'data_payload' in locals() else None)
                                    kp_config = st.session_state.get('kepler_config') if 'kepler_config' in st.session_state else (kepler_config if 'kepler_config' in locals() else None)

                                    wrote_ok = False
                                    try:
                                        # If we have a valid persisted payload+config, recreate and save
                                        if isinstance(kp_payload, dict) and isinstance(kp_config, dict):
                                            try:
                                                tmp_map = KeplerGl(height=600, data=kp_payload, config=kp_config)
                                                tmp_map.save_to_html(file_name=tmp_name)
                                                wrote_ok = True
                                            except Exception:
                                                wrote_ok = False

                                        # If that failed, try saving the in-memory kepler_map object
                                        if not wrote_ok:
                                            try:
                                                kepler_map.save_to_html(file_name=tmp_name)
                                                wrote_ok = True
                                            except Exception:
                                                wrote_ok = False

                                        if wrote_ok:
                                            with open(tmp_name, 'rb') as fh:
                                                html_bytes = fh.read()
                                            st.download_button(
                                                label='Download Kepler HTML',
                                                data=html_bytes,
                                                file_name='kepler_map.html',
                                                mime='text/html',
                                                key='download_kepler_html'
                                            )
                                        else:
                                            st.warning('Unable to build Kepler HTML for download at this time.')
                                    finally:
                                        try:
                                            if os.path.exists(tmp_name):
                                                os.unlink(tmp_name)
                                        except Exception:
                                            pass
                                except Exception:
                                    # Non-fatal: show nothing if download assembly fails
                                    pass
                        except Exception:
                            pass

                        map_rendered = True

                    except Exception as e:
                        # Fallback: try saving to file and embedding
                        try:
                            tmpfile = 'kepler_map.html'
                            # If kepler_map exists use it, otherwise try to construct minimal map
                            try:
                                kepler_map.save_to_html(file_name=tmpfile)
                            except Exception:
                                # Try instantiating with a validated payload
                                safe_payload = None
                                if 'data_payload' in locals() and isinstance(data_payload, dict):
                                    safe_payload = data_payload
                                elif 'kdf' in locals() and kdf is not None:
                                    safe_payload = {dataset_name: kdf}

                                if isinstance(safe_payload, dict) and isinstance(kepler_config, dict):
                                    kepler_map = KeplerGl(height=600, data=safe_payload, config=kepler_config)
                                    kepler_map.save_to_html(file_name=tmpfile)
                                else:
                                    raise RuntimeError('No valid kepler data payload available for fallback rendering.')

                            with open(tmpfile, 'r', encoding='utf-8') as fh:
                                kepler_html = fh.read()
                            st.components.v1.html(kepler_html, height=650, scrolling=True)
                            try:
                                st.session_state['last_map_type'] = 'kepler'
                            except Exception:
                                pass
                            map_rendered = True
                        except Exception as e2:
                            st.error(f"Failed to render kepler map: {e} / {e2}")
            
           
            if points_or_path == "Show Point Progression":      #Shows the moving path between markers
                list_of_path_points = []    #stores coordinates from dataframe, but in long/lat format
                pathpointforreal = []       #stores corrected coordinates in lat/long form to be used by the Antpath tool
                
                if "SOURCE_FILE" in valid_records.columns and "POINT_COLOR" in valid_records.columns:
                    # Group data by source file
                    grouped = valid_records.groupby('SOURCE_FILE')
                    
                    # Create markers and paths for each source file
                    for source_file, group_df in grouped:
                        # Reset index to avoid iloc issues
                        group_df = group_df.reset_index(drop=True)
                        # Convert group DataFrame to GeoDataFrame
                        group_gdf = geopandas.GeoDataFrame(
                            group_df, 
                            geometry=geopandas.points_from_xy(group_df.LONGITUDE, group_df.LATITUDE)
                        )
                        # Reset index for the geodataframe too
                        group_gdf = group_gdf.reset_index(drop=True)
                        
                        # Add markers using the file's selected color
                        color = group_df['POINT_COLOR'].iloc[0]  # Get color for this file
                        circle_Points = Map.add_circle_markers_from_xy(
                            data=group_gdf, 
                            x="LONGITUDE", 
                            y="LATITUDE",
                            color=color,
                            fill_color=color, 
                            radius=5
                        )
                        
                        # Create path points for this group
                        group_path_points = []
                        for index, row in group_gdf.iterrows():
                            for pt in list(row['geometry'].coords):
                                group_path_points.append(pt)
                        
                        # Convert coordinates for this group
                        group_pathpoints = []
                        for ting in group_path_points:
                            [longy, laty] = ting
                            ltlng = (str(laty) + "," + str(longy))
                            ltlng2list = [float(value) for value in ltlng.split(",")]
                            group_pathpoints.append(ltlng2list)
                        
                        # Add AntPath for this group with its color
                        plugins.AntPath(
                            locations=group_pathpoints,
                            color=color,
                            weight=2,
                            opacity=0.8
                        ).add_to(Map)
                        
                else:
                    # Use color from color picker (stored in POINT_COLOR column)
                    color = gdf['POINT_COLOR'].iloc[0] if 'POINT_COLOR' in gdf.columns and len(gdf) > 0 else "#FF0000"
                        
                    try:
                        circle_Points = Map.add_circle_markers_from_xy(
                            data=gdf, 
                            x="LONGITUDE", 
                            y="LATITUDE",
                            color=color,
                            fill_color=color, 
                            radius=5
                        )
                    except ValueError:
                        st.error("Select")
                        
                    for index, row in gdf.iterrows():
                        for pt in list(row['geometry'].coords):
                            list_of_path_points.append(pt)
                    
                    for ting in list_of_path_points:
                        [longy, laty] = ting
                        ltlng = (str(laty) + "," + str(longy))
                        ltlng2list = [float(value) for value in ltlng.split(",")]
                        pathpointforreal.append(ltlng2list)
                    plugins.AntPath(locations=pathpointforreal,color=color).add_to(Map)

                # Per-map download button for the progression map
                try:
                    import tempfile, os, hashlib
                    btn_col_left, _ = st.columns([1, 4])
                    with btn_col_left:
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
                        tmp_name = tmp.name
                        tmp.close()
                        try:
                            try:
                                Map.save(tmp_name)
                            except Exception:
                                try:
                                    with open(tmp_name, 'w', encoding='utf-8') as fh:
                                        fh.write(Map.get_root().render())
                                except Exception:
                                    pass

                            # per-map progression download suppressed; final download button will appear below the rendered map
                        finally:
                            try:
                                if os.path.exists(tmp_name):
                                    os.unlink(tmp_name)
                            except Exception:
                                pass
                except Exception:
                    pass

            #   GOTTA ORDER THE DATAFRAME BY TIME AND DATE THEN ADD THE POINTS IN ORDER TO A LIST TO BE READ BY THE ANTPATH


            if points_or_path == "Vapour Trail":
                choose_datetime_column = st.selectbox("Date / Time Column", options=gdf.columns, key="datetime_vapor")
                time_interval = st.radio("Time Interval to Display", options=['Daily', 'Hourly', '10 Minutes', '1 Minute'], horizontal=True)
                
                # Only show color selector if there's no SOURCE_FILE column
                if 'SOURCE_FILE' not in gdf.columns:
                    vapor_trail_color = st.selectbox(
                        "Vapour Trail Color",
                        ['DarkRed', 'Yellow', 'Pink', 'Green', 'Teal', 'Blue', 'White'],
                        key="vapor_color"
                    )
                
                # Set time intervals
                if time_interval == 'Daily': chosen_interval = 'PT24H'
                if time_interval == 'Hourly': chosen_interval = 'PT1H'
                if time_interval == '10 Minutes': chosen_interval = 'PT10M'  
                if time_interval == '1 Minute': chosen_interval = 'PT1M'   

                # Create a FeatureGroup for the vapor trail
                vapor_trail = folium.FeatureGroup(name='Vapor Trail')
                vapor_trail.add_to(Map)

                travel_history = []
                skipped_entries = 0

                # If we have multiple source files
                if 'SOURCE_FILE' in gdf.columns:
                    # Group by source file
                    for source_file, group_df in gdf.groupby('SOURCE_FILE'):
                        # Reset index to avoid iloc issues
                        group_df = group_df.reset_index(drop=True)
                        color = group_df['POINT_COLOR'].iloc[0]  # Get color for this file
                        
                        # Process each group separately
                        for i in range(len(group_df) - 1):
                            row1 = group_df.iloc[i]
                            row2 = group_df.iloc[i + 1]
                            
                            # Skip if any coordinate or timestamp is NaN
                            if (pandas.isna(row1['LONGITUDE']) or pandas.isna(row1['LATITUDE']) or 
                                pandas.isna(row2['LONGITUDE']) or pandas.isna(row2['LATITUDE']) or 
                                pandas.isna(row1[choose_datetime_column]) or pandas.isna(row2[choose_datetime_column])):
                                skipped_entries += 1
                                continue

                            try:
                                if 'datetime.datetime' in str(type(row1[choose_datetime_column])):
                                    row1_timestampstr = (row1[choose_datetime_column]).strftime("%Y-%m-%dT%H:%M:%S")
                                    row2_timestampstr = (row2[choose_datetime_column]).strftime("%Y-%m-%dT%H:%M:%S")
                                else:
                                    row1_timestampstr = str(row1[choose_datetime_column])
                                    row2_timestampstr = str(row2[choose_datetime_column])
                                            
                                coord = [[float(row1["LONGITUDE"]), float(row1["LATITUDE"])],
                                        [float(row2["LONGITUDE"]), float(row2["LATITUDE"])]]
                                
                                entry = {
                                    "type": "Feature",
                                    "geometry": {
                                        "type": "LineString",
                                        "coordinates": coord
                                    },
                                    "properties": {
                                        "times": [row1_timestampstr, row2_timestampstr],
                                        "style": {
                                            "color": color,  # Use the color from the source file
                                            "weight": 8
                                        },
                                        "source": source_file  # Add source file info to properties
                                    }
                                }
                                travel_history.append(entry)
                            except (ValueError, TypeError) as e:
                                skipped_entries += 1
                                st.warning(f"Skipping invalid data point: {e}")
                                continue
                else:
                    # Original single-color processing for single files
                    for i in range(len(gdf) - 1):
                        row1 = gdf.iloc[i]
                        row2 = gdf.iloc[i + 1]
                        
                        if (pandas.isna(row1['LONGITUDE']) or pandas.isna(row1['LATITUDE']) or 
                            pandas.isna(row2['LONGITUDE']) or pandas.isna(row2['LATITUDE']) or 
                            pandas.isna(row1[choose_datetime_column]) or pandas.isna(row2[choose_datetime_column])):
                            skipped_entries += 1
                            continue

                        try:
                            if 'datetime.datetime' in str(type(row1[choose_datetime_column])):
                                row1_timestampstr = (row1[choose_datetime_column]).strftime("%Y-%m-%dT%H:%M:%S")
                                row2_timestampstr = (row2[choose_datetime_column]).strftime("%Y-%m-%dT%H:%M:%S")
                            else:
                                row1_timestampstr = str(row1[choose_datetime_column])
                                row2_timestampstr = str(row2[choose_datetime_column])
                                        
                            coord = [[float(row1["LONGITUDE"]), float(row1["LATITUDE"])],
                                    [float(row2["LONGITUDE"]), float(row2["LATITUDE"])]]
                            
                            entry = {
                                "type": "Feature",
                                "geometry": {
                                    "type": "LineString",
                                    "coordinates": coord
                                },
                                "properties": {
                                    "times": [row1_timestampstr, row2_timestampstr],
                                    "style": {
                                        "color": vapor_trail_color,
                                        "weight": 8
                                    }
                                }
                            }
                            travel_history.append(entry)
                        except (ValueError, TypeError) as e:
                            skipped_entries += 1
                            st.warning(f"Skipping invalid data point: {e}")
                            continue

                # Show skipped entries warning
                if skipped_entries > 0:
                    st.warning(f"⚠️ Skipped {skipped_entries} entries due to missing timestamps or invalid data")

                if travel_history:
                    # Create feature collection
                    feature_collection = {
                        "type": "FeatureCollection",
                        "features": travel_history
                    }

                    try:
                        # Create a TimestampedGeoJson layer
                        vapor_trail_layer = TimestampedGeoJson(
                            feature_collection,
                            period=chosen_interval,
                            auto_play=True,
                            loop=True,
                            date_options="YYYY-MM-DD HH:mm:ss",
                            add_last_point=False,
                            transition_time=1000,
                            duration=None
                        )

                        # Add the vapor trail layer to the map
                        vapor_trail_layer.add_to(Map)            

                        # Add LayerControl
                        folium.LayerControl().add_to(Map)
                    except Exception as e:
                        st.error(f"Error creating vapor trail: {e}")
                else:
                    st.warning("No valid data points found for creating vapor trail")

                # Per-map download button for the Vapour Trail map
                try:
                    import tempfile, os, hashlib
                    btn_col_left, _ = st.columns([1, 4])
                    with btn_col_left:
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
                        tmp_name = tmp.name
                        tmp.close()
                        try:
                            try:
                                Map.save(tmp_name)
                            except Exception:
                                try:
                                    with open(tmp_name, 'w', encoding='utf-8') as fh:
                                        fh.write(Map.get_root().render())
                                except Exception:
                                    pass

                            # per-map vapour_trail download suppressed; final download button will appear below the rendered map
                        finally:
                            try:
                                if os.path.exists(tmp_name):
                                    os.unlink(tmp_name)
                            except Exception:
                                pass
                except Exception:
                    pass
            
        
    if map_Type == "Cell Sites":
            towermastpoint = Map.add_circle_markers_from_xy(data=gdf, x="LONGITUDE", y="LATITUDE",color='white',fill_color='white', radius=1)

            gdf.columns = gdf.columns.str.upper()
            gdf.geometry = gdf["GEOMETRY"]
            Map.zoom_to_gdf(gdf) 
            
            st.markdown("---")

            # Only show color selector if there's no SOURCE_FILE column
            if 'SOURCE_FILE' not in gdf.columns:
                wedge_color = st.selectbox("Sector Color", options=['Red', 'Blue', 'Green', 'Purple', 'Orange', 'DarkRed', 'Beige', 'DarkBlue', 'DarkGreen', 'CadetBlue', 'Pink', 'LightBlue', 'LightGreen', 'Gray', 'Black', 'LightGray'])

            # Create radius column based on selection before using it
            radii_list = ["1.5 Miles", "1 Kilometer"]
            for oto in valid_records.columns:
                radii_list.append(oto)
            radii = st.selectbox("Sector Footprint Size", options=radii_list)
            
            # Create the radius column based on selection
            if radii == "1.5 Miles":
                valid_records = valid_records.copy()
                valid_records["1.5 Miles"] = 2414
                gdf["1.5 Miles"] = 2414
            elif radii == "1 Kilometer":
                valid_records = valid_records.copy()
                valid_records["1 Kilometer"] = 1000
                gdf["1 Kilometer"] = 1000
            
            # Add any existing column data if not using preset distances
            if radii not in ["1.5 Miles", "1 Kilometer"]:
                if radii in valid_records.columns:
                    gdf[radii] = valid_records[radii]

            # Filter columns for numeric-only selections
            numeric_columns = []
            for col in valid_records.columns:
                if valid_records[col].dtype in ['int64', 'float64', 'int32', 'float32']:
                    numeric_columns.append(col)

            if not numeric_columns:
                st.error("No numeric columns found for azimuth and beam width values. Please ensure your data contains numeric columns.")
                st.stop()

            Azimuth = st.selectbox("Sector Azimuth", options=numeric_columns)   
            beam_width = st.selectbox("Sector Beam Width", options=numeric_columns, placeholder='None')
            
            try:
                for index, row in gdf.iterrows():
                    if radii in row:
                        length = float(row[radii])/1000  # Convert to km
                        half_beamwidth = float(row[beam_width]) / 2
                        upside = (float(row[Azimuth]) + half_beamwidth) % 360
                        downside = (float(row[Azimuth]) - half_beamwidth) % 360
                        
                        # Get color from POINT_COLOR if available, otherwise use selected wedge_color
                        current_color = row["POINT_COLOR"] if "POINT_COLOR" in row else wedge_color
                        
                        up_lat, up_lon = get_point_at_distance(row["LATITUDE"], row["LONGITUDE"], d=length, bearing=upside)
                        dwn_lat, dwn_lon = get_point_at_distance(row["LATITUDE"], row["LONGITUDE"], d=length, bearing=downside)
                        
                        leafmap.folium.PolyLine([[row["LATITUDE"],row["LONGITUDE"]], [up_lat,up_lon]], color=current_color).add_to(Map)
                        leafmap.folium.PolyLine([[row["LATITUDE"],row["LONGITUDE"]], [dwn_lat,dwn_lon]], color=current_color).add_to(Map)
                        
                        plugins.SemiCircle(
                            (row["LATITUDE"],row["LONGITUDE"]),
                            radius=float(row[radii])/2,
                            direction=float(row[Azimuth]),
                            arc=float(row[beam_width]),
                            color=current_color,
                            fill_color=current_color,
                            opacity=1,
                            fill_opacity=.5,
                            popup=('<br>'.join(f'{k}: {v}' for k, v in row.items()))
                        ).add_to(Map)
                        
            except (TypeError, ValueError) as e:
                st.info("Assign columns for Sector Footprint Size (Radius from Station in Meters), Tower Direction/Azimuth (Degrees), & Beam Width (Degrees)")
                st.error(f"Error: {str(e)}")

    # Add the legend if we have multiple data sources
    if 'SOURCE_FILE' in valid_records.columns and 'POINT_COLOR' in valid_records.columns:
        add_color_legend(Map, valid_records)

    # Final fallback render if not already rendered earlier
    if not map_rendered:
        Map.to_streamlit()
        # After rendering the final map, provide a single download button beneath it
        try:
            try:
                downloadfile = Map.to_html()
            except Exception:
                # Some Map objects provide get_root().render(); try that
                try:
                    downloadfile = Map.get_root().render()
                except Exception:
                    downloadfile = None

            if downloadfile is not None:
                st.download_button(label="Download Map HTML", data=downloadfile, file_name="Fetch_Analysis_Map.html")
        except Exception:
            pass
        
def get_footprint_color(icon_Color):
    if "Yellow" in icon_Color:
        footprint_color = simplekml.Color.changealphaint(50, simplekml.Color.yellow)
    if "Red" in icon_Color:
        footprint_color = simplekml.Color.changealphaint(100, simplekml.Color.red)
    if "Blue" in icon_Color:
        footprint_color = simplekml.Color.changealphaint(100, simplekml.Color.blue)
    if "White" in icon_Color:
        footprint_color = simplekml.Color.changealphaint(100, simplekml.Color.white)
    if "Green" in icon_Color:
        footprint_color = simplekml.Color.changealphaint(100, simplekml.Color.green)
    if "Teal" in icon_Color:
        footprint_color = simplekml.Color.changealphaint(100, simplekml.Color.lightblue)
    if "Square" in icon_Color:
        footprint_color = simplekml.Color.changealphaint(200, simplekml.Color.white)
    return footprint_color

def HTML_output_file(name_for_file):
    try:
        name_for_file = name_for_file + ".html"
    except Exception:
        st.error("Provide map name above")
    out_folder = os.path.expanduser('~\\Documents\\Fetch_Maps\\')
    if os.path.exists(out_folder) == False:
        os.makedirs(out_folder)
    else:
        pass
    out_file = os.path.expanduser(out_folder+name_for_file)
    return out_file

def KML_output_file(name_for_file):
    name_for_file = name_for_file + ".kml"
    out_folder = os.path.expanduser('~\\Documents\\Fetch_Maps\\')
    if os.path.exists(out_folder) == False:
        os.makedirs(out_folder)
    else:
        pass
    out_file = os.path.expanduser(out_folder+name_for_file)
    return out_file

def get_file_encoding(infile):      #checks file encoding
    return (chardet.detect(infile.read()))
 
# 

def create_kml_tour(df, output_file, altitude, tilt, linger, time_column, icon, footprint, radii):
    """
    Creates a KML file with a Google Earth tour from a DataFrame.

    Parameters:
    df (DataFrame): A DataFrame with 'longitude', 'latitude', and 'time' columns.
    output_file (str): Path to the output KML file.
    altitude (int): Camera height in meters.
    tilt (int): Camera tilt.
    linger (float): Seconds to rest on each point.
    time_column (str): Column name for time data.
    icon (str): Icon style for map points.
    footprint (bool): Indicates if the data includes radius/area information.
    radii (str): Column name for radius data.
    """
    try:
        altitude = int(altitude)
        tilt = int(tilt)
        linger = float(linger)
        kml = simplekml.Kml()
        tour = kml.newgxtour(name="Fetch Tour")
        playlist = tour.newgxplaylist()

        # Ensure that 'longitude', 'latitude', and 'time' columns are present
        if 'LONGITUDE' not in df.columns or 'LATITUDE' not in df.columns:
            raise ValueError("DataFrame must contain 'LONGITUDE' and 'LATITUDE' columns.")
        
        # Filter out records without valid latitude or longitude FIRST
        original_count = len(df)
        valid_df = df.dropna(subset=['LATITUDE', 'LONGITUDE']).copy()
        
        # Additional validation to ensure numeric values
        valid_df = valid_df[
            pandas.to_numeric(valid_df['LATITUDE'], errors='coerce').notna() &
            pandas.to_numeric(valid_df['LONGITUDE'], errors='coerce').notna()
        ].copy()
        
        # Convert to numeric and remove infinite values
        valid_df['LATITUDE'] = pandas.to_numeric(valid_df['LATITUDE'], errors='coerce')
        valid_df['LONGITUDE'] = pandas.to_numeric(valid_df['LONGITUDE'], errors='coerce')
        
        valid_df = valid_df[
            pandas.notna(valid_df['LATITUDE']) & 
            pandas.notna(valid_df['LONGITUDE']) &
            np.isfinite(valid_df['LATITUDE']) &
            np.isfinite(valid_df['LONGITUDE'])
        ]
        
        # Final cleanup
        valid_df = valid_df.dropna(subset=['LATITUDE', 'LONGITUDE'])
        
        valid_count = len(valid_df)
        skipped_count = original_count - valid_count
        
        # Notify user if records were skipped
        if skipped_count > 0:
            print(f"Skipped {skipped_count} record(s) that were missing latitude or longitude values for KML tour.")
        
        # Check if we have any valid records left
        if valid_count == 0:
            print("No valid records found for KML tour generation.")
            return
        
        # Convert the 'TIME' column to datetime objects if present
        if time_column is not None:
            try:
                valid_df[time_column] = pandas.to_datetime(valid_df[time_column])
            except ValueError:
                valid_df[time_column] = pandas.to_datetime(valid_df[time_column], utc=True)
                valid_df[time_column] = valid_df[time_column].dt.tz_convert('UTC')
        
        # Iterate through the points in the DataFrame
        for idx, row in valid_df.iterrows():
            try:
                lon, lat = row['LONGITUDE'], row['LATITUDE']
                description_lines = [f"{key}: {value}" for key, value in row.items()]
                description = "\n".join(description_lines)
                
                placemark = kml.newpoint(name=f"{row[time_column]}" if time_column else f"{row['LATITUDE']}, {row['LONGITUDE']}", coords=[(lon, lat)], description=description)
                placemark.style.iconstyle.icon.href = selected_icon[icon]

                if footprint and radii:
                    rad = row[radii]
                    polycircle = polycircles.Polycircle(latitude=float(lat),
                                                        longitude=float(lon),
                                                        radius=float(rad),
                                                        number_of_vertices=72)
                    pol = kml.newpolygon(name=f"{lat}, {lon}, {rad}", outerboundaryis=polycircle.to_kml())
                    pol.style.polystyle.color = get_footprint_color(icon_Color=icon)
                
                # Add a camera or look-at point for the tour
                flyto = playlist.newgxflyto(gxduration=3.0)
                flyto.camera.longitude = lon
                flyto.camera.latitude = lat
                flyto.camera.altitude = altitude
                flyto.camera.heading = 0
                flyto.camera.tilt = tilt
                flyto.camera.roll = 0
                
                # Add the time and date
                if time_column is not None:
                    flyto.when = row[time_column].isoformat() # Convert datetime to ISO format
            
                # Optionally, you can add a wait period between points
                playlist.newgxwait(gxduration=linger)  # Wait for the specified linger duration
            
            except AttributeError as e:
                print(f"Error at index {idx}: {e}")
            except TypeError as e:
                print(f"Error at index {idx}: {e}")

        # Save the KML to the specified output file
        kml.save(output_file)
        print(f"KML file saved as {output_file}")
    except TypeError:
        st.error("Error creating KML tour. Check for errors in the data set.")

def create_kml(df_in, outfile):
    try:
        headers = df_in.columns.to_list()

        # Streamlit UI for selecting columns
        st.subheader("Design Your KML Map")
        
        # Only show color selector if there's no POINT_COLOR column
        if 'POINT_COLOR' not in df_in.columns:
            icon = st.selectbox("Select Map Point Icon Style", options=icon_options)
        else:
            icon = "Yellow Paddle"  # Default icon style
            st.info("Using colors selected during file upload")

        label_for_icons = st.selectbox("Map Icon Labels", options=headers)
        
        footprint = st.checkbox("Data set includes radius/area information", value=False)
        radii = None
        if footprint:
            radii = st.selectbox("Radius/Distance-from-Point in Meters", options=headers)
        
        tour = st.checkbox("Include KML Tour", value=False)
        if tour:     # Tour Settings
            st.subheader("Design Tour Settings")
            there_are_dates = st.checkbox("Data set includes date/time information", value=False)
            if there_are_dates:
                time_column = st.selectbox("Date/Time Column", options=headers)
            else:
                time_column = None
            tour_altitude = st.selectbox("Tour Altitude (Meters)", options=['50','150', '250', '300', '750', '1500', '10000'], index=2)
            tour_linger_time = st.selectbox("Tour Linger Time (Seconds)", options=['1', '2', '3', '4', '5', '10', '15'], index=3)
            tour_tilt = st.selectbox("Tour Tilt", options=['0', '5', '10', '20'], index=1)

    except AttributeError:
        print("Attribute error on variable headers in createkml")
        st.error("Check for errors in column selection.")

    if st.button("Generate KML"):
        filename = "MITE_KML_Map" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        if not filename:
            st.error("Map Name Required")
        else:
            try:
                # Filter out records without valid latitude or longitude FIRST
                original_count = len(df_in)
                valid_df = df_in.dropna(subset=['LATITUDE', 'LONGITUDE']).copy()
                
                # Additional validation to ensure numeric values
                valid_df = valid_df[
                    pandas.to_numeric(valid_df['LATITUDE'], errors='coerce').notna() &
                    pandas.to_numeric(valid_df['LONGITUDE'], errors='coerce').notna()
                ].copy()
                
                # Convert to numeric and remove infinite values
                valid_df['LATITUDE'] = pandas.to_numeric(valid_df['LATITUDE'], errors='coerce')
                valid_df['LONGITUDE'] = pandas.to_numeric(valid_df['LONGITUDE'], errors='coerce')
                
                valid_df = valid_df[
                    pandas.notna(valid_df['LATITUDE']) & 
                    pandas.notna(valid_df['LONGITUDE']) &
                    np.isfinite(valid_df['LATITUDE']) &
                    np.isfinite(valid_df['LONGITUDE'])
                ]
                
                # Final cleanup
                valid_df = valid_df.dropna(subset=['LATITUDE', 'LONGITUDE'])
                
                valid_count = len(valid_df)
                skipped_count = original_count - valid_count
                
                # Notify user if records were skipped
                if skipped_count > 0:
                    st.warning(f"⚠️ Skipped {skipped_count} record(s) that were missing latitude or longitude values. {valid_count} valid records will be processed in KML.")
                
                # Check if we have any valid records left
                if valid_count == 0:
                    st.error("No valid records found for KML generation. All records are missing latitude or longitude values.")
                    return
                
                kml = simplekml.Kml()
                Label = label_for_icons
                
                for idx, row in valid_df.iterrows():
                    lon, lat = row['LONGITUDE'], row['LATITUDE']
                    description_lines = [f"{key}: {value}" for key, value in row.items()]
                    descript = "\n".join(description_lines)      
                    lab = row[Label]
                    long = re.findall(r'([0-9.-]+)', str(lon))[0]
                    lati = re.findall(r'([0-9.-]+)', str(lat))[0]

                    point = kml.newpoint(name=lab, coords=[(float(long), float(lati))], description=descript)
                    # Use point color from dataframe if available, otherwise use selected icon
                    if 'POINT_COLOR' in row:
                        # Convert hex color to KML color format (aabbggrr)
                        hex_color = row['POINT_COLOR'].lstrip('#')
                        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                        kml_color = simplekml.Color.rgb(*rgb)
                        
                        point.style.iconstyle.icon.href = selected_icon[icon]
                        point.style.iconstyle.color = kml_color
                    else:
                        point.style.iconstyle.icon.href = selected_icon[icon]

                    if footprint and radii:
                        rad = row[radii]
                        polycircle = polycircles.Polycircle(
                            latitude=float(lati),
                            longitude=float(long),
                            radius=float(rad),
                            number_of_vertices=72
                        )

                        pol = kml.newpolygon(name=f"{lati}, {long}, {rad}", outerboundaryis=polycircle.to_kml())
                        # Use point color for footprint if available
                        if 'POINT_COLOR' in row:
                            pol.style.polystyle.color = kml_color
                        else:
                            pol.style.polystyle.color = get_footprint_color(icon_Color=icon)
                            
            except Exception as e:
                st.error(f"Error generating KML: {e}")
                return

            if not tour:
                # Generate normal KML file
                kml.save(outfile)
                with open(outfile, 'rb') as f:
                    kml_data = f.read()

                st.download_button("Download KML", data=kml_data, file_name="Fetch_KML_Download.kml")

            if tour:
                # Generate the KML tour file
                tourfile = 'tour.kml'
                create_kml_tour(df=valid_df, output_file=tourfile, altitude=tour_altitude, 
                              tilt=tour_tilt, linger=tour_linger_time, time_column=time_column, 
                              icon=icon, footprint=footprint, radii=radii)
                with open(tourfile, 'rb') as f:
                    tour_data = f.read()

                st.download_button("Download KML Tour", data=tour_data, file_name="Fetch_KML_Tour.kml")

            st.success(f"KML file has been stored to: {outfile}")


@st.cache_data
def prepare_datetime_column(df, date_column):
    """Prepare datetime column with proper conversion and caching for performance"""
    df_copy = df.copy()
    try:
        df_copy[date_column] = pandas.to_datetime(df_copy[date_column])
    except ValueError:
        # Handle GPX UTC inputs
        df_copy[date_column] = pandas.to_datetime(df_copy[date_column], utc=True)
        df_copy[date_column] = df_copy[date_column].dt.tz_convert('UTC')
    except Exception:
        # Coerce errors to NaT for invalid dates
        df_copy[date_column] = pandas.to_datetime(df_copy[date_column], errors='coerce')
    
    # Remove rows with invalid dates
    df_copy = df_copy.dropna(subset=[date_column])
    return df_copy

def detect_datetime_columns_by_source(df):
    """Detect potential datetime columns for each source file"""
    datetime_mapping = {}
    
    if 'SOURCE_FILE' in df.columns:
        for source_file in df['SOURCE_FILE'].unique():
            source_data = df[df['SOURCE_FILE'] == source_file]
            
            # Look for datetime-like column names
            datetime_candidates = []
            for col in source_data.columns:
                if col in ['SOURCE_FILE', 'POINT_COLOR', 'LATITUDE', 'LONGITUDE']:
                    continue
                col_upper = col.upper()
                if any(keyword in col_upper for keyword in ['TIME', 'DATE', 'TIMESTAMP', 'DATETIME']):
                    datetime_candidates.append(col)
            
            # Test each candidate for actual datetime data
            valid_datetime_cols = []
            for col in datetime_candidates:
                try:
                    test_data = source_data[col].dropna().head(10)
                    if len(test_data) > 0:
                        pandas.to_datetime(test_data)
                        valid_datetime_cols.append(col)
                except:
                    continue
            
            datetime_mapping[source_file] = {
                'candidates': datetime_candidates,
                'valid': valid_datetime_cols
            }
    
    return datetime_mapping

def create_unified_datetime_column(df, datetime_mapping):
    """Create a unified UNIFIED_DATETIME column from multiple source columns"""
    df_copy = df.copy()
    df_copy['UNIFIED_DATETIME'] = pandas.NaT
    processed_files = []
    
    for source_file, datetime_col in datetime_mapping.items():
        if datetime_col and datetime_col != 'Skip this file':
            source_mask = df_copy['SOURCE_FILE'] == source_file
            source_data = df_copy.loc[source_mask, datetime_col]
            
            # Try multiple parsing strategies
            converted_dates = None
            strategy_used = None
            
            strategies = [
                ('Standard parsing', lambda x: pandas.to_datetime(x)),
                ('UTC parsing', lambda x: pandas.to_datetime(x, utc=True)),
                ('Inferred format', lambda x: pandas.to_datetime(x, infer_datetime_format=True)),
                ('Standard format', lambda x: pandas.to_datetime(x, format='%Y-%m-%d %H:%M:%S')),
                ('US format', lambda x: pandas.to_datetime(x, format='%m/%d/%Y %H:%M:%S')),
                ('ISO format', lambda x: pandas.to_datetime(x, format='%Y-%m-%dT%H:%M:%S')),
            ]
            
            for strategy_name, strategy_func in strategies:
                try:
                    converted_dates = strategy_func(source_data)
                    strategy_used = strategy_name
                    break
                except:
                    continue
            
            if converted_dates is not None:
                df_copy.loc[source_mask, 'UNIFIED_DATETIME'] = converted_dates
                processed_files.append(f"{source_file} ({strategy_used})")
            else:
                st.error(f"Could not parse datetime data from {source_file} column {datetime_col}")
    
    if processed_files:
        st.success(f"Successfully processed datetime data from: {', '.join(processed_files)}")
    
    return df_copy

def multi_source_time_filter_config(df):
    """Configure datetime columns for multiple source files"""
    if 'SOURCE_FILE' not in df.columns:
        return None
    
    source_files = df['SOURCE_FILE'].unique()
    st.subheader("Multi-Source Time Configuration")
    st.info(f"You have {len(source_files)} source files. Configure datetime columns for each file:")
    
    datetime_mapping_detected = detect_datetime_columns_by_source(df)
    datetime_column_mapping = {}
    
    for i, source_file in enumerate(source_files):
        st.markdown(f"**File: {source_file}**")
        source_data = df[df['SOURCE_FILE'] == source_file]
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Show sample data
            st.write("Sample data:")
            display_cols = [col for col in source_data.columns if col not in ['POINT_COLOR']][:6]
            st.dataframe(source_data[display_cols].head(2), use_container_width=True)
        
        with col2:
            # Show detected datetime candidates
            detected_info = datetime_mapping_detected.get(source_file, {})
            if detected_info.get('valid'):
                st.write("Detected datetime columns:")
                for col in detected_info['valid']:
                    st.write(f"✓ {col}")
            elif detected_info.get('candidates'):
                st.write("Potential datetime columns:")
                for col in detected_info['candidates']:
                    st.write(f"? {col}")
            else:
                st.write("No datetime columns detected")
        
        # Column selection
        all_columns = ['Skip this file'] + [col for col in source_data.columns if col not in ['SOURCE_FILE', 'POINT_COLOR']]
        
        # Pre-select the best candidate if available
        default_index = 0
        if detected_info.get('valid'):
            best_candidate = detected_info['valid'][0]
            if best_candidate in all_columns:
                default_index = all_columns.index(best_candidate)
        
        datetime_col = st.selectbox(
            f"Select datetime column for {source_file}",
            options=all_columns,
            index=default_index,
            key=f"datetime_col_{source_file}_{i}"
        )
        
        if datetime_col != 'Skip this file':
            datetime_column_mapping[source_file] = datetime_col
            
            # Test the column
            try:
                test_data = source_data[datetime_col].dropna().head(5)
                if len(test_data) > 0:
                    test_conversion = pandas.to_datetime(test_data)
                    st.success(f"✓ Valid datetime format detected")
                    st.write(f"Sample: {test_conversion.iloc[0]}")
                else:
                    st.warning("No data found in this column")
            except Exception as e:
                st.warning(f"Potential parsing issue: {str(e)[:100]}")
        else:
            st.info("This file will be skipped during time filtering")
        
        st.markdown("---")
    
    return datetime_column_mapping

def display_filter_results(filtered_df, original_df):
    """Display filter results with metrics and sample data"""
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Filtered Records", len(filtered_df))
    with col2:
        st.metric("Original Records", len(original_df))
    with col3:
        if len(original_df) > 0:
            percentage = (len(filtered_df) / len(original_df)) * 100
            st.metric("✅ Retained", f"{percentage:.1f}%")
        else:
            st.metric("✅ Retained", "0%")
    
    # Show sample of results instead of full table
    if len(filtered_df) > 0:
        st.subheader("Sample of Filtered Data")
        # Show first 10 rows with better formatting
        sample_df = filtered_df.head(10)
        st.dataframe(sample_df, use_container_width=True)
        
        if len(filtered_df) > 10:
            st.info(f"ℹShowing first 10 of {len(filtered_df):,} records")
        
        # Add download option for filtered data
        if st.button("Download Filtered Data as CSV"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"filtered_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.warning("⚠️ No records match the selected time range")

def time_filter(in_df, date_column_or_mapping):
    """Improved time filter with support for single and multi-source data"""
    st.subheader("Time Filter")
    
    try:
        # Handle multi-source vs single-source scenarios
        if isinstance(date_column_or_mapping, dict):
            # Multi-source: create unified datetime column
            st.info("Processing multi-source data with unified datetime column...")
            df_with_datetime = create_unified_datetime_column(in_df, date_column_or_mapping)
            
            # Check if any data was successfully processed
            valid_datetime_count = df_with_datetime['UNIFIED_DATETIME'].notna().sum()
            if valid_datetime_count == 0:
                st.error("No valid datetime records found across all source files")
                return in_df
            
            date_column = 'UNIFIED_DATETIME'
            st.success(f"Created unified datetime column with {valid_datetime_count:,} valid records")
            
        else:
            # Single source: use existing logic
            df_with_datetime = prepare_datetime_column(in_df, date_column_or_mapping)
            date_column = date_column_or_mapping
            
            if len(df_with_datetime) == 0:
                st.error("No valid datetime records found in the selected column")
                return in_df
        
        # Data range info
        min_date = df_with_datetime[date_column].min()
        max_date = df_with_datetime[date_column].max()
        total_span = max_date - min_date
        
        # Info panel
        st.subheader("Data Time Range Information")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Earliest Record", min_date.strftime("%Y-%m-%d %H:%M"))
        with col2:
            st.metric("Latest Record", max_date.strftime("%Y-%m-%d %H:%M"))
        with col3:
            st.metric("Total Span", f"{total_span.days} days")
        
        # Quick filters
        st.subheader("Quick Filters")
        st.info(f"Preset ranges are calculated from your data's latest record: {max_date.strftime('%Y-%m-%d %H:%M')}")
        
        quick_filter = st.radio(
            "Choose a preset or custom range:",
            ["All Data", "Last 24 Hours", "Last Week", "Last Month", "Custom Range"],
            horizontal=True,
            key="time_filter_quick"
        )
        
        # Set date range based on selection (relative to dataset's max_date)
        if quick_filter == "All Data":
            start_dt, end_dt = min_date, max_date
        elif quick_filter == "Last 24 Hours":
            end_dt = max_date
            start_dt = max_date - pandas.Timedelta(days=1)
            start_dt = max(start_dt, min_date)  # Don't go before dataset start
        elif quick_filter == "Last Week":
            end_dt = max_date
            start_dt = max_date - pandas.Timedelta(weeks=1)
            start_dt = max(start_dt, min_date)  # Don't go before dataset start
        elif quick_filter == "Last Month":
            end_dt = max_date
            start_dt = max_date - pandas.Timedelta(days=30)
            start_dt = max(start_dt, min_date)  # Don't go before dataset start
        
        # Show selected date range for preset filters
        if quick_filter != "Custom Range":
            st.success(f"Selected range: {start_dt.strftime('%Y-%m-%d %H:%M')} to {end_dt.strftime('%Y-%m-%d %H:%M')}")
            if start_dt == min_date and quick_filter != "All Data":
                st.info("Note: Range limited to dataset start date")
        
        else:  # Custom Range
            st.subheader("Custom Date Range")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Start Date & Time**")
                start_date = st.date_input(
                    "Start Date", 
                    value=min_date.date(),
                    min_value=min_date.date(),
                    max_value=max_date.date(),
                    key="time_filter_start_date"
                )
                start_time = st.time_input(
                    "Start Time",
                    value=min_date.time(),
                    key="time_filter_start_time"
                )
                start_dt = pandas.Timestamp.combine(start_date, start_time)
            with col2:
                st.write("**End Date & Time**")
                end_date = st.date_input(
                    "End Date", 
                    value=max_date.date(),
                    min_value=min_date.date(),
                    max_value=max_date.date(),
                    key="time_filter_end_date"
                )
                end_time = st.time_input(
                    "End Time",
                    value=max_date.time(),
                    key="time_filter_end_time"
                )
                end_dt = pandas.Timestamp.combine(end_date, end_time)
            
            # Validation for custom range
            if start_dt >= end_dt:
                st.error("❌ Start date must be before end date")
                return in_df
        
        # Apply filter
        filtered_df = df_with_datetime[
            (df_with_datetime[date_column] >= start_dt) & 
            (df_with_datetime[date_column] <= end_dt)
        ].copy()
        
        # Display results
        st.subheader("Filter Results")
        display_filter_results(filtered_df, df_with_datetime)
        
        return filtered_df
        
    except Exception as e:
        st.error(f"❌ Error processing time filter: {str(e)}")
        st.error("Please ensure the selected column contains valid date/time data.")
        return in_df

def declutterer(in_df, date_column):
    """Improved declutterer with better UI and error handling"""
    st.subheader("🎯 Declutter Settings")
    
    try:
        # Convert to datetime
        df_copy = in_df.copy()
        df_copy[date_column] = pandas.to_datetime(df_copy[date_column])
        
        # Show data info
        total_records = len(df_copy)
        st.info(f"Processing {total_records:,} records for decluttering")
        
        # Time interval settings with better layout
        Time_intervals = {
            "🟢 Minute": "T", 
            "🔵 Hour": "H", 
            "🟡 Day": "D", 
            "🟠 Week": "W", 
            "🔴 Month": "M", 
            "🟤 Year": "A"
        }
        
        col1, col2 = st.columns([1, 2])
        with col1:
            count_of_time = st.number_input(
                "Interval Count", 
                min_value=1, 
                max_value=60, 
                value=1,
                help="Number of time units to group together"
            )
        with col2:
            choose_interval = st.selectbox(
                "Time Unit", 
                options=list(Time_intervals.keys()),
                help="Time period for grouping locations"
            )
        
        # Build resample rate
        interval_code = Time_intervals[choose_interval]
        resample_Rate = str(count_of_time) + interval_code
        
        # Show what this means
        interval_name = choose_interval.split(" ", 1)[1]  # Remove emoji
        st.info(f"Grouping locations every **{count_of_time} {interval_name.lower()}{'s' if count_of_time > 1 else ''}**")
        
        # Process the data
        with st.spinner("Processing declutter operation..."):
            declutter_data = df_copy.set_index(date_column)
            
            # Check if we have required columns
            if 'LATITUDE' not in declutter_data.columns or 'LONGITUDE' not in declutter_data.columns:
                st.error("❌ LATITUDE and LONGITUDE columns are required for decluttering")
                return in_df
            
            # Perform resampling
            declutter_data = declutter_data.resample(resample_Rate).agg({
                'LATITUDE': 'mean', 
                'LONGITUDE': 'mean'
            })
            
            # Remove rows with NaN values
            declutter_data = declutter_data[declutter_data['LATITUDE'].notna()]
            
            # Reset index to get datetime back as column
            declutter_data = declutter_data.reset_index()
        
        # Show results
        final_count = len(declutter_data)
        reduction_pct = ((total_records - final_count) / total_records) * 100 if total_records > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Original Records", f"{total_records:,}")
        with col2:
            st.metric("Averaged Locations", f"{final_count:,}")
        with col3:
            st.metric("Reduction", f"{reduction_pct:.1f}%")
        
        if final_count > 0:
            st.success(f"✅ Successfully consolidated {total_records:,} records into {final_count:,} averaged locations")
        else:
            st.warning("⚠️ No data remains after decluttering. Try a larger time interval.")
            return in_df
            
        return declutter_data
        
    except Exception as e:
        st.error(f"❌ Error during decluttering: {str(e)}")
        st.error("Please ensure the selected column contains valid date/time data.")
        return in_df

def convert_kml_2_DF(kml_file):
    if type(kml_file) == str:   # used for parsing kml collected from kmz
        tree = ET.ElementTree(ET.fromstring(kml_file))
    else:                    # used for parsing a direct kml submission
        tree = ET.parse(kml_file)
    root = tree.getroot()

    # Namespace dictionary to handle namespaces in the KML file
    ns = {
        'kml': 'http://www.opengis.net/kml/2.2'
    }

    # Extract placemarks
    placemarks = root.findall('.//kml:Placemark', ns)

    # Initialize a list to hold dictionaries of each placemark's data
    placemark_data = []

    # Iterate through each placemark
    for placemark in placemarks:
        # Initialize a dictionary to hold the current placemark's data
        data = {}
        keys_seen = set()  # To track keys in a case-insensitive manner, also used to avoid duplicate keys (getting dup lat and long columns from kml descriptions)
        
        # Extract standard fields (name and coordinates)
        name = placemark.find('kml:name', ns)
        coordinates = placemark.find('.//kml:coordinates', ns)
        
        if name is not None:
            data['name'] = name.text
            keys_seen.add('name'.lower())
        if coordinates is not None:
            # Split coordinates into individual coordinate sets
            coord_sets = coordinates.text.strip().split()
            if len(coord_sets) == 1:  # Only consider placemarks with a single set of coordinates
                coord_values = re.split(r'[,\s]+', coord_sets[0])
                if len(coord_values) >= 2:
                    data['longitude'] = float(coord_values[0])
                    data['latitude'] = float(coord_values[1])
                    keys_seen.update(['longitude', 'latitude'])
                if len(coord_values) == 3:
                    data['altitude'] = float(coord_values[2])
                    keys_seen.add('altitude')

        # Extract all extended data fields
        extended_data = placemark.findall('.//kml:ExtendedData/kml:Data', ns)
        for ed in extended_data:
            key = ed.attrib.get('name')
            if key and key.lower() not in keys_seen:
                value = ed.find('kml:value', ns).text if ed.find('kml:value', ns) is not None else ''
                data[key] = value
                keys_seen.add(key.lower())

        # Extract all extended data fields (both Data and SchemaData/SimpleData)
        # Handle Data elements
        extended_data = placemark.findall('.//kml:ExtendedData/kml:Data', ns)
        for ed in extended_data:
            key = ed.attrib.get('name')
            if key and key.lower() not in keys_seen:
                value = ed.find('kml:value', ns).text if ed.find('kml:value', ns) is not None else ''
                data[key] = value
                keys_seen.add(key.lower())

        # Handle SchemaData elements
        schema_data = placemark.findall('.//kml:ExtendedData/kml:SchemaData/kml:SimpleData', ns)
        for sd in schema_data:
            key = sd.attrib.get('name')
            value = sd.text if sd is not None else ''
            if key and key.lower() not in keys_seen:
                data[key] = value
                keys_seen.add(key.lower())

        # Add the placemark data to the list
        placemark_data.append(data)

    # Create a DataFrame from the extracted data
    df = pandas.DataFrame(placemark_data)

    # Ensure all coordinates are numeric
    df['latitude'] = pandas.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pandas.to_numeric(df['longitude'], errors='coerce')

    # Drop rows with missing latitude or longitude
    df = df.dropna(subset=['latitude', 'longitude'])
    # print(df)
    return df


def ingest_multiple_files():
    uploaded_files = st.file_uploader("Choose files to analyze", 
                                    type=["csv", "txt", "tsv", "xlsx", "xls", "gpx", "kmz", "kml"],
                                    accept_multiple_files=True)
    if not uploaded_files:
        return None

    # Set how many columns per row
    num_cols = 3  
    color_selections = {}
    
    # Create color selector grid
    for i in range(0, len(uploaded_files), num_cols):
        cols = st.columns(num_cols)
        for j, file in enumerate(uploaded_files[i:i+num_cols]):
            with cols[j]:
                st.markdown(f"**{file.name}**")
                # Use a deterministic, compact key derived from the filename to avoid Streamlit duplicate-key errors
                _digest = hashlib.md5(file.name.encode()).hexdigest()
                _cp_key = f"color_picker_{_digest}"
                color_selections[file.name] = st.color_picker(
                    f"Select color for points in {file.name}", 
                    value="#FF0000", 
                    key=_cp_key
                )    
    
    df_list = []
    for file in uploaded_files:
        try:
            # Reset file pointer
            file.seek(0)
            filename_lower = file.name.lower()
            # Excel files
            if any(ext in file.name.lower() for ext in [".xls", ".xlsx"]):
                df = pandas.read_excel(file)
            
            # CSV/TXT files  
            elif any(ext in file.name.lower() for ext in [".csv", ".txt"]):
                enc = selected_encoding if selected_encoding else "utf-8"
                df = pandas.read_csv(file, encoding=enc)
            
            # TSV files
            elif ".tsv" in file.name.lower():
                enc = selected_encoding if selected_encoding else "utf-8"
                df = pandas.read_csv(file, encoding=enc, sep="\t")
            
            # GPX files
            elif ".gpx" in file.name.lower():
                gpx = gpxpy.parse(file)
                points_data = []
                for track in gpx.tracks:
                    for segment in track.segments:
                        for point in segment.points:
                            points_data.append({
                                'LATITUDE': point.latitude,
                                'LONGITUDE': point.longitude,
                                'ELEVATION': point.elevation,
                                'DATETIME': point.time
                            })
                df = pandas.DataFrame.from_records(points_data)
            
            # KML files
            elif ".kml" in file.name.lower():
                df = convert_kml_2_DF(file)
                # Ensure column names are standardized
                df.columns = df.columns.str.upper()
                # Rename lat/long columns if needed
                if 'LAT' in df.columns and 'LATITUDE' not in df.columns:
                    df = df.rename(columns={'LAT': 'LATITUDE'})
                if 'LON' in df.columns and 'LONGITUDE' not in df.columns:
                    df = df.rename(columns={'LON': 'LONGITUDE'})
            
            # KMZ files  
            elif ".kmz" in file.name.lower():
                with zipfile.ZipFile(file, 'r') as kmz:
                    kml_file_name = next(
                        (name for name in kmz.namelist() if name.endswith('.kml')), 
                        None
                    )
                    if kml_file_name:
                        kml_content = kmz.read(kml_file_name).decode('utf-8')
                        df = convert_kml_2_DF(kml_content)
                    else:
                        st.error(f"No KML file found in {file.name}")
                        continue

            # Clean up DataFrame
            # Create a copy to avoid SettingWithCopyWarning
            # Reset index and drop old index
            if not df.empty:
                df = df.copy().reset_index(drop=True)
            else:
                st.warning(f"File {file.name} contains no data")
                continue
            
            # Standardize column names and remove duplicates
            df.columns = df.columns.str.upper()
            
            # Check if dataframe is empty after processing
            if df.empty:
                st.warning(f"File {file.name} resulted in empty dataframe after processing")
                continue
                
            # Remove duplicate columns safely
            if len(df.columns) > 0:
                df = df.loc[:, ~df.columns.duplicated()]
            else:
                st.error(f"File {file.name} has no valid columns")
                continue
            
            # Add source tracking
            try:
                df["SOURCE_FILE"] = file.name
                df["POINT_COLOR"] = color_selections.get(file.name, "#FF0000")
            except Exception as assign_error:
                st.error(f"Error adding tracking columns to {file.name}: {str(assign_error)}")
                continue
            
            # Validate required columns
            if "LATITUDE" not in df.columns or "LONGITUDE" not in df.columns:
                st.error(f"File {file.name} missing required latitude/longitude columns")
                continue
                
            df_list.append(df)

        except Exception as e:
            st.error(f"Error processing {file.name}: {str(e)}")
            continue

    if df_list:
        try:
            # Combine all dataframes with clean indexes
            combined_df = pandas.concat(df_list, ignore_index=True, sort=False)
            
            # Ensure unique columns and reset index one final time
            combined_df = combined_df.loc[:, ~combined_df.columns.duplicated()]
            combined_df = combined_df.reset_index(drop=True)
            
            return combined_df
        except Exception as e:
            st.error(f"Error combining data: {str(e)}")
            return None
    else:
        st.error("No valid dataframes were ingested.") 
        return None


########################################
#### In Progress ####


########################################

####    Main Page   ####

uploaded_file = None
preview_data = None
notices = st.empty()            #   Places notifications at the top of the screen


# else:
combined_df = ingest_multiple_files()
if combined_df is not None:
    combined_df.rename(columns=lambda x: x.lower(), inplace=True)
    combined_df.columns = combined_df.columns.str.upper()  # standardize columns to uppercase
    
    # Update point colors if color pickers have changed
    if 'SOURCE_FILE' in combined_df.columns and 'POINT_COLOR' in combined_df.columns:
        # Get current color picker values for each file
        unique_files = combined_df['SOURCE_FILE'].unique()
        
        for file_name in unique_files:
            # Derive the same deterministic key used when the uploader created the picker
            _digest = hashlib.md5(file_name.encode()).hexdigest()
            color_picker_key = f"color_picker_{_digest}"
            if color_picker_key in st.session_state:
                current_color = st.session_state[color_picker_key]
                # Update the color for this file in the dataframe
                file_mask = combined_df['SOURCE_FILE'] == file_name
                combined_df.loc[file_mask, 'POINT_COLOR'] = current_color
    
    preview_data = combined_df
        

if preview_data is not None:
    with st.expander("Manage Ingested Data"):
        tabi, tabii, tabiii, tabiv = st.tabs(["Review Ingest Data","Time Filter","Declutter","Timezone Conversion"])
        with tabi:
            st.subheader("Review Ingested Data")
            
            # Show data overview
            if preview_data is not None:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Records", f"{len(preview_data):,}")
                with col2:
                    st.metric("Columns", len(preview_data.columns))
                with col3:
                    if 'SOURCE_FILE' in preview_data.columns:
                        unique_files = preview_data['SOURCE_FILE'].nunique()
                        st.metric("Source Files", unique_files)
                    else:
                        st.metric("Source Files", 1)
            
            # Row removal option
            st.subheader("Header Cleaning")
            lines_t0_remove = st.slider(
                label="Number of Rows to Remove from Start",
                min_value=0, 
                max_value=10,
                value=0,
                help="Remove header rows or unwanted data from the beginning of your dataset. First remaining row should contain 'Latitude' and 'Longitude' data."
            )
            
            if lines_t0_remove > 0:
                st.info(f"ℹRemoving the first {lines_t0_remove} row{'s' if lines_t0_remove > 1 else ''} from the dataset")
                
            # Show sample of current data
            st.subheader("Data Preview")
            if preview_data is not None and len(preview_data) > 0:
                # Apply row removal if specified
                display_data = preview_data.iloc[lines_t0_remove:] if lines_t0_remove > 0 else preview_data
                
                # Show first few rows
                st.dataframe(display_data.head(10), use_container_width=True)
                
                if len(display_data) > 10:
                    st.info(f"ℹShowing first 10 rows of {len(display_data):,} total records")
                    
                # Column information
                show_column_info = st.checkbox("Show Column Information", value=False)
                if show_column_info:
                    col_info = []
                    for col in display_data.columns:
                        col_type = str(display_data[col].dtype)
                        non_null = display_data[col].count()
                        null_count = len(display_data) - non_null
                        col_info.append({
                            "Column": col,
                            "Data Type": col_type,
                            "Non-Null Values": f"{non_null:,}",
                            "Null Values": f"{null_count:,}"
                        })
                    
                    col_df = pandas.DataFrame(col_info)
                    st.dataframe(col_df, use_container_width=True)
            else:
                st.warning("⚠️ No data available to preview")
                
            # Apply row removal to actual data if specified
            if lines_t0_remove > 0 and preview_data is not None:
                preview_data = preview_data.iloc[lines_t0_remove:].copy()
                st.success(f"✅ Applied row removal: {lines_t0_remove} rows removed from dataset")            

           
        with tabii:
            st.subheader("Date/Time Filtering")
            filterbytime = st.checkbox("Enable Time Filtering", help="Filter data to a specific date/time range")
            if filterbytime:
                # Check if we have multiple source files
                if 'SOURCE_FILE' in preview_data.columns and preview_data['SOURCE_FILE'].nunique() > 1:
                    st.info("Multiple source files detected. Configure datetime columns for each file:")
                    
                    # Multi-source configuration
                    datetime_mapping = multi_source_time_filter_config(preview_data)
                    
                    if datetime_mapping:
                        st.subheader("Apply Time Filter")
                        if st.button("Apply Multi-Source Time Filter"):
                            preview_data = time_filter(preview_data, datetime_mapping)
                    else:
                        st.warning("No files configured for time filtering")
                        
                else:
                    # Single source configuration
                    st.info("Select the column containing your date/time data, then choose your filtering options below.")
                    datetime_Column = st.selectbox(
                        "Select Date/Time Column", 
                        options=preview_data.columns,
                        help="Choose the column that contains date/time information"
                    )
                    preview_data = time_filter(preview_data, datetime_Column)
                
        with tabiii:
            st.subheader("Data Decluttering")
            declutter_dis = st.checkbox(
                "Consolidate Location Points", 
                help="Average multiple location points over specified time intervals to reduce data density"
            )
            if declutter_dis:
                st.info("💡 This feature combines nearby points taken within the same time interval into a single averaged location.")
                try:
                    datetim_Column = st.selectbox(
                        "Choose Date/Time Column", 
                        options=preview_data.columns,
                        help="Select the column containing date/time data for grouping"
                    )
                except AttributeError:
                    st.error("❌ No date/time columns available. Please ensure your data contains date/time information.")
                try:
                    preview_data = declutterer(preview_data, date_column=datetim_Column)
                except Exception as e:
                    st.error(f"❌ Error processing declutter: {str(e)}")
                    st.error("Please select a valid date/time column")

        with tabiv:
            st.subheader("Timezone Conversion")
            
            # Detect datetime columns
            datetime_columns = []
            if preview_data is not None:
                for col in preview_data.columns:
                    # Check if column contains datetime-like data
                    if preview_data[col].dtype == 'object':
                        # Try to convert a sample to see if it's datetime-like
                        try:
                            sample_values = preview_data[col].dropna().head(5)
                            if len(sample_values) > 0:
                                pandas.to_datetime(sample_values.iloc[0])
                                datetime_columns.append(col)
                        except:
                            pass
                    elif 'datetime' in str(preview_data[col].dtype).lower():
                        datetime_columns.append(col)
            
            if datetime_columns:
                st.info("Convert datetime columns using timezone names (with daylight savings) or simple hourly offsets.")
                
                # Column selection
                tz_column = st.selectbox(
                    "Select DateTime Column to Convert",
                    options=datetime_columns,
                    help="Choose the datetime column you want to convert to a different timezone"
                )
                
                # Conversion method selection
                conversion_method = st.radio(
                    "Conversion Method",
                    options=["Timezone Conversion", "Hourly Offset"],
                    help="Choose between timezone-aware conversion (handles DST) or simple hourly offset"
                )
                
                if conversion_method == "Timezone Conversion":
                    # Timezone selection with common timezones
                    common_timezones = [
                        'UTC',
                        'US/Eastern',
                        'US/Central', 
                        'US/Mountain',
                        'US/Pacific',
                        'US/Alaska',
                        'US/Hawaii',
                        'Europe/London',
                        'Europe/Paris',
                        'Europe/Berlin',
                        'Asia/Tokyo',
                        'Asia/Shanghai',
                        'Australia/Sydney',
                        'Australia/Melbourne'
                    ]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        source_tz = st.selectbox(
                            "Source Timezone",
                            options=['Auto-detect'] + common_timezones,
                            help="Current timezone of the data. Auto-detect will try to determine automatically."
                        )
                    
                    with col2:
                        target_tz = st.selectbox(
                            "Convert to Timezone",
                            options=common_timezones,
                            index=1,  # Default to US/Eastern
                            help="Target timezone for conversion"
                        )
                
                else:  # Hourly Offset
                    st.info("💡 Positive values add hours (e.g., +3 for 3 hours ahead), negative values subtract hours (e.g., -5 for 5 hours behind)")
                    
                    hour_offset = st.number_input(
                        "Hour Offset",
                        min_value=-12.0,
                        max_value=14.0,
                        value=0.0,
                        step=0.5,
                        help="Number of hours to add (+) or subtract (-) from the datetime. Supports half-hour increments."
                    )
                
                # Show sample conversion
                if st.button("Preview Conversion"):
                    try:
                        # Get sample data
                        sample_data = preview_data[tz_column].dropna().head(3)
                        
                        if len(sample_data) > 0:
                            st.write("**Sample Conversion Preview:**")
                            
                            preview_results = []
                            for idx, original_value in sample_data.items():
                                try:
                                    # Convert to datetime if not already
                                    if not pandas.api.types.is_datetime64_any_dtype(type(original_value)):
                                        dt_value = pandas.to_datetime(original_value)
                                    else:
                                        dt_value = original_value
                                    
                                    if conversion_method == "Timezone Conversion":
                                        # Timezone conversion logic
                                        if pytz is None:
                                            raise ImportError("pytz library required for timezone conversion")
                                        
                                        # Handle source timezone
                                        if source_tz == 'Auto-detect':
                                            # Try to detect if already timezone-aware
                                            if dt_value.tz is None:
                                                # Assume UTC if no timezone info
                                                dt_value = dt_value.tz_localize('UTC')
                                        else:
                                            # Localize or convert based on current timezone info
                                            if dt_value.tz is None:
                                                dt_value = dt_value.tz_localize(source_tz)
                                            else:
                                                dt_value = dt_value.tz_convert('UTC').tz_convert(source_tz)
                                        
                                        # Convert to target timezone
                                        converted_value = dt_value.tz_convert(target_tz)
                                        
                                        preview_results.append({
                                            'Original': str(original_value),
                                            'Source TZ': str(dt_value),
                                            'Converted': str(converted_value)
                                        })
                                    
                                    else:  # Hourly Offset
                                        # Simple hour offset logic
                                        from datetime import timedelta
                                        
                                        # Remove timezone info for offset calculation
                                        if hasattr(dt_value, 'tz') and dt_value.tz is not None:
                                            dt_naive = dt_value.tz_localize(None)
                                        else:
                                            dt_naive = dt_value
                                        
                                        # Apply hour offset
                                        converted_value = dt_naive + timedelta(hours=hour_offset)
                                        
                                        preview_results.append({
                                            'Original': str(original_value),
                                            'Hour Offset': f"{hour_offset:+.1f} hours",
                                            'Converted': str(converted_value)
                                        })
                                    
                                except Exception as e:
                                    preview_results.append({
                                        'Original': str(original_value),
                                        'Error': str(e),
                                        'Converted': 'Error'
                                    })
                            
                            preview_df = pandas.DataFrame(preview_results)
                            st.dataframe(preview_df, use_container_width=True)
                        else:
                            st.warning("No valid datetime values found in selected column")
                            
                    except Exception as e:
                        st.error(f"Error during conversion preview: {str(e)}")
                
                # Apply conversion
                if st.button("Apply Conversion", type="primary"):
                    try:
                        with st.spinner("Converting datetime..."):
                            # Create a copy of the data
                            converted_data = preview_data.copy()
                            
                            # Convert the datetime column
                            dt_series = pandas.to_datetime(converted_data[tz_column])
                            
                            if conversion_method == "Timezone Conversion":
                                if pytz is None:
                                    st.error("pytz library required for timezone conversion. Please install with: pip install pytz")
                                    st.stop()
                                
                                # Handle source timezone
                                if source_tz == 'Auto-detect':
                                    # If no timezone info, assume UTC
                                    if dt_series.dt.tz is None:
                                        dt_series = dt_series.dt.tz_localize('UTC')
                                else:
                                    if dt_series.dt.tz is None:
                                        dt_series = dt_series.dt.tz_localize(source_tz)
                                    else:
                                        dt_series = dt_series.dt.tz_convert(source_tz)
                                
                                # Convert to target timezone
                                converted_series = dt_series.dt.tz_convert(target_tz)
                                
                                success_message = f"✅ Successfully converted {tz_column} from {source_tz} to {target_tz}"
                            
                            else:  # Hourly Offset
                                from datetime import timedelta
                                
                                # Remove timezone info for offset calculation
                                if dt_series.dt.tz is not None:
                                    dt_series = dt_series.dt.tz_localize(None)
                                
                                # Apply hour offset
                                converted_series = dt_series + pandas.Timedelta(hours=hour_offset)
                                
                                success_message = f"✅ Successfully applied {hour_offset:+.1f} hour offset to {tz_column}"
                            
                            # Update the dataframe
                            converted_data[tz_column] = converted_series
                            preview_data = converted_data
                            
                            st.success(success_message)
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"Error during conversion: {str(e)}")
            else:
                st.info("No datetime columns detected in the data. Upload data with datetime information to use timezone conversion.")

if preview_data is None:
    tabA, tabB = st.tabs(["Create Geofence", "IP Address Mapping"])
    with tabA:
        make_geofence_map()
    with tabB:
        make_IPaddress_Map()
        

if preview_data is not None:
    # Simple filter status display
    declutter_active = 'declutter_dis' in locals() and declutter_dis
    timefilter_active = 'filterbytime' in locals() and filterbytime
    
    if declutter_active or timefilter_active:
        st.markdown(":orange[Filters are active]")
        
    tab1, tab2, tab3 = st.tabs(["Preview/KML Map", "Analysis Maps", "Create Geofence"])    
    with tab1:
        try:
            # Clean preview_data before passing to st.map to avoid null value errors
            if 'LATITUDE' in preview_data.columns and 'LONGITUDE' in preview_data.columns:
                # Count original records
                original_count = len(preview_data)
                
                # Clean the data for st.map
                clean_preview = preview_data.dropna(subset=['LATITUDE', 'LONGITUDE']).copy()
                
                # Additional validation to ensure numeric values
                clean_preview = clean_preview[
                    pandas.to_numeric(clean_preview['LATITUDE'], errors='coerce').notna() &
                    pandas.to_numeric(clean_preview['LONGITUDE'], errors='coerce').notna()
                ].copy()
                
                # Convert to numeric and remove infinite values
                clean_preview['LATITUDE'] = pandas.to_numeric(clean_preview['LATITUDE'], errors='coerce')
                clean_preview['LONGITUDE'] = pandas.to_numeric(clean_preview['LONGITUDE'], errors='coerce')
                
                clean_preview = clean_preview[
                    pandas.notna(clean_preview['LATITUDE']) & 
                    pandas.notna(clean_preview['LONGITUDE']) &
                    np.isfinite(clean_preview['LATITUDE']) &
                    np.isfinite(clean_preview['LONGITUDE'])
                ]
                
                # Final cleanup
                clean_preview = clean_preview.dropna(subset=['LATITUDE', 'LONGITUDE'])
                
                # Check if we have valid data for mapping
                valid_count = len(clean_preview)
                skipped_count = original_count - valid_count
                
                if skipped_count > 0:
                    st.info(f"ℹ️ Preview map: Showing {valid_count} valid records. {skipped_count} records with missing coordinates were excluded from the map display.")
                
                if valid_count > 0:
                    st.map(clean_preview)
                else:
                    st.error("No valid coordinate data available for preview map.")
            else:
                st.map(preview_data)
                
            st.download_button("Download as CSV", data=preview_data.to_csv(), file_name="Fetch_CSV_Export.csv")
        except TypeError:
            st.error("Ensure you have correct settings in Manage Ingested Data and Date/Time Filtering. Remove any non-numeric characters from your Lat/Long columns.")          
        except NameError:
            st.error("preview data not defined")
        # KML = st.button("GENERATE KML")
        st.markdown("---")
        try:
            outFile = KML_output_file("Fetch_KML_Map"+str(now))
            create_kml(df_in=preview_data,outfile=outFile)
        except Exception as e:
            st.error(f"Error generating KML: {e}")
        
    with tab2:
        try:
            make_map(preview_data)
        except AttributeError:
            st.error("Check that your data has Latitude and Longitude columns")
    with tab3:
        make_geofence_map()
    
# add a button to open a popup window that will contain hyperlinks
st.markdown("---")

with st.expander("Privacy Statement and API Use"):
    st.write("""
    ## Data Privacy Statement and API Usage Information
    
    We take your privacy seriously. North Loop Consulting will only have temporary access to small portions of data that may be involved in error reporting.  
    This data will not be stored for any period longer than needed to identify and correct any issues, if at all.
                
    We make use of a third party company, Streamlit, to provide hosting for Fetch.  
    For more information about Streamlit and their handling of user data, please refer to their [Privacy Policy](https://streamlit.io/privacy-policy).
    
    For specific information about how Streamlit handles data sets you have uploaded as files, please refer to their 
    [documents on file uploads](https://docs.streamlit.io/knowledge-base/using-streamlit/where-file-uploader-store-when-deleted).
    
    It is always best to avoid uploading sensitive data to any online service. Please do not upload any data that may contain personal identifiable information or sensitive data.

    Fetch is intended to be a free tool available to everyone.  To do this, free resources are used to return information like IP address data.  There are caps on this free usage.  You may run into periods where that cap has been met and these resources are not available. If you would like to explore financial support for the tool to expand these capabilities, I am open to the conversation. Just reach out via the Contact Page on our site.   
    """)
st.markdown(":orange[© 2025 North Loop Consulting - Fetch_v5.0]")
