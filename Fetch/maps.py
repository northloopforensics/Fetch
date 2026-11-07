"""Folium map construction, rendering, and display-size budgeting."""
import re
from typing import Optional

import folium
import numpy as np
import pandas
import streamlit as st
from folium import plugins

from fetch.coords import coordinate_bounds
from fetch.utils import safe_session_set

# Default cap on individually drawn map features; above it users choose how to display the data.
MAX_RENDER_POINTS = 5000
MAX_POPUP_FIELDS = 10
INTERNAL_COLUMNS = ('geometry', 'POINT_COLOR')


def new_map(location=None, zoom: int = 2, **kwargs) -> folium.Map:
    """Folium map with the controls the app previously got from leafmap.foliumap.Map."""
    m = folium.Map(location=location or [20, 0], zoom_start=zoom, tiles=None, max_zoom=24,
                   control_scale=True, **kwargs)
    plugins.Fullscreen().add_to(m)
    return m


def fit_to_data(map_obj, df: pandas.DataFrame, lat_col: str = 'LATITUDE', lon_col: str = 'LONGITUDE'):
    bounds = coordinate_bounds(df, lat_col, lon_col)
    if bounds:
        map_obj.fit_bounds(bounds)


def set_center(map_obj, lat: float, lon: float, zoom: int):
    map_obj.fit_bounds([[lat, lon], [lat, lon]], max_zoom=zoom)


def add_layer_control(map_obj, **kwargs):
    """Add a LayerControl unless the map already has one."""
    if not any(isinstance(child, folium.LayerControl) for child in map_obj._children.values()):
        folium.LayerControl(**kwargs).add_to(map_obj)


def popup_fields_selector(df: pandas.DataFrame, key: str, exclude=INTERNAL_COLUMNS) -> list:
    """Let users pick popup columns; large popups dominate map size, so the default is capped."""
    columns = [c for c in df.columns if c not in exclude]
    default = columns[:MAX_POPUP_FIELDS]
    if len(columns) <= MAX_POPUP_FIELDS:
        return columns
    return st.multiselect(
        "Map popup fields", options=columns, default=default, key=key,
        help=f"Fields shown when clicking a point. Fewer fields make maps load faster. "
             f"The first {MAX_POPUP_FIELDS} are selected by default; exports always contain every column.",
    )


def _point_feature_collection(df: pandas.DataFrame, properties: list) -> dict:
    lats = df['LATITUDE'].to_numpy(float).tolist()
    lons = df['LONGITUDE'].to_numpy(float).tolist()
    return {'type': 'FeatureCollection', 'features': [
        {'type': 'Feature', 'id': str(i), 'geometry': {'type': 'Point', 'coordinates': [lon, lat]}, 'properties': p}
        for i, (lat, lon, p) in enumerate(zip(lats, lons, properties))
    ]}


def add_point_layer(map_obj, df: pandas.DataFrame, color: Optional[str] = None, radius: int = 5,
                    name: Optional[str] = None, popup: bool = True, cluster: bool = False,
                    fields: Optional[list] = None, **marker_kwargs):
    if df.empty:
        return
    if fields is None:
        fields = [c for c in df.columns if c != 'geometry']
    popup = popup and bool(fields)
    props = df[fields].astype(str).to_dict('records') if popup else [{}] * len(df)
    if cluster:
        target = plugins.MarkerCluster(name=name).add_to(map_obj)
        marker = folium.Marker()
    else:
        target = map_obj
        marker = folium.CircleMarker(**{'radius': radius, 'color': color, 'fill_color': color, **marker_kwargs})
    folium.GeoJson(
        _point_feature_collection(df, props), marker=marker, name=name, control=bool(name) and not cluster,
        popup=folium.GeoJsonPopup(fields=fields) if popup else None,
    ).add_to(target)


def add_radius_layer(map_obj, df: pandas.DataFrame, radius_col: str, color: str = "#FF0000"):
    """Draw accuracy circles (meters) for rows with a positive radius, colored by POINT_COLOR when present."""
    radii = pandas.to_numeric(df[radius_col], errors='coerce')
    keep = radii > 0
    rows = df.loc[keep]
    colors = rows['POINT_COLOR'].fillna(color).astype(str) if 'POINT_COLOR' in rows.columns else pandas.Series(color, index=rows.index)
    props = [{'r': r, 'c': c} for r, c in zip(radii[keep].astype(float).tolist(), colors.tolist())]
    if not props:
        return
    folium.GeoJson(
        _point_feature_collection(rows, props), control=False,
        marker=folium.Circle(fill=True, fill_opacity=0.5),
        style_function=lambda f: {'radius': f['properties']['r'], 'color': f['properties']['c'],
                                  'fillColor': f['properties']['c']},
    ).add_to(map_obj)


# ---------------------------------------------------------------------------------------------
# Display budget: what to do when a dataset is too large to draw point-by-point
# ---------------------------------------------------------------------------------------------
BUDGET_SAMPLE = "sample"
BUDGET_AGGREGATE = "aggregate"
BUDGET_ALL = "all"


def thin_evenly(df: pandas.DataFrame, limit: int) -> pandas.DataFrame:
    """Keep `limit` evenly spaced rows, preserving order (so trails and progressions stay sequential)."""
    if len(df) <= limit:
        return df
    positions = np.unique(np.linspace(0, len(df) - 1, limit).round().astype(int))
    return df.iloc[positions]


def aggregate_points(df: pandas.DataFrame, limit: int, weight: Optional[pandas.Series] = None) -> pandas.DataFrame:
    """Bin points into a lat/lon grid of at most ~`limit` cells per color.

    Returns one row per occupied cell (and POINT_COLOR, when present) with the mean
    position, the number of points (COUNT), and the summed WEIGHT.
    """
    lat = df['LATITUDE'].to_numpy(float)
    lon = df['LONGITUDE'].to_numpy(float)
    has_color = 'POINT_COLOR' in df.columns
    n_colors = max(1, df['POINT_COLOR'].nunique()) if has_color else 1
    side = max(1, int(np.sqrt(limit / n_colors)))

    def bins(values):
        lo, hi = values.min(), values.max()
        if hi <= lo:
            return np.zeros(len(values), dtype=np.int64)
        return np.minimum(((values - lo) / (hi - lo) * side).astype(np.int64), side - 1)

    work = pandas.DataFrame({
        'LATITUDE': lat, 'LONGITUDE': lon,
        'CELL': bins(lat) * side + bins(lon),
        'WEIGHT': 1.0 if weight is None else pandas.to_numeric(weight, errors='coerce').fillna(0).to_numpy(float),
    })
    keys = ['CELL']
    if has_color:
        work['POINT_COLOR'] = df['POINT_COLOR'].astype(str).to_numpy()
        keys.append('POINT_COLOR')
    agg = {'LATITUDE': ('LATITUDE', 'mean'), 'LONGITUDE': ('LONGITUDE', 'mean'),
           'COUNT': ('LATITUDE', 'size'), 'WEIGHT': ('WEIGHT', 'sum')}
    if 'SOURCE_FILE' in df.columns:
        work['SOURCE_FILE'] = df['SOURCE_FILE'].astype(str).to_numpy()
        agg['SOURCE_FILE'] = ('SOURCE_FILE', 'first')
    return work.groupby(keys, sort=False).agg(**agg).reset_index().drop(columns='CELL')


def add_aggregate_layer(map_obj, agg_df: pandas.DataFrame, default_color: str = "#FF0000", name: Optional[str] = None):
    """Proportional circles for aggregated grid cells; popups show how many points each represents."""
    if agg_df.empty:
        return
    colors = agg_df['POINT_COLOR'] if 'POINT_COLOR' in agg_df.columns else pandas.Series(default_color, index=agg_df.index)
    counts = agg_df['COUNT'].to_numpy(int)
    radii = (3 + 2 * np.log2(np.maximum(counts, 1))).round(1)
    sources = agg_df['SOURCE_FILE'].tolist() if 'SOURCE_FILE' in agg_df.columns else None
    props = []
    for i, (count, lat, lon, radius, color) in enumerate(
            zip(counts.tolist(), agg_df['LATITUDE'].tolist(), agg_df['LONGITUDE'].tolist(), radii.tolist(), colors.tolist())):
        prop = {'Points': count, 'Latitude': round(lat, 6), 'Longitude': round(lon, 6), 'r': radius, 'c': str(color)}
        if sources is not None:
            prop['Source'] = sources[i]
        props.append(prop)
    fields = ['Points', 'Latitude', 'Longitude'] + (['Source'] if sources is not None else [])
    folium.GeoJson(
        _point_feature_collection(agg_df, props), name=name, control=bool(name),
        marker=folium.CircleMarker(fill=True, fill_opacity=0.6, weight=1),
        style_function=lambda f: {'radius': f['properties']['r'], 'color': f['properties']['c'],
                                  'fillColor': f['properties']['c']},
        popup=folium.GeoJsonPopup(fields=fields),
    ).add_to(map_obj)


def render_budget(df: pandas.DataFrame, key: str, allow_aggregate: bool = True,
                  limit: int = MAX_RENDER_POINTS, what: str = "points") -> str:
    """Ask the user how to display a dataset larger than `limit`; returns BUDGET_* (BUDGET_ALL when within limit).

    Only the map display is affected; analysis, tables, and exports always use every record.
    """
    if len(df) <= limit:
        return BUDGET_ALL
    options = {BUDGET_SAMPLE: f"Show {limit:,} evenly spaced {what}"}
    if allow_aggregate:
        options[BUDGET_AGGREGATE] = "Aggregate into a grid (each circle shows its point count)"
    options[BUDGET_ALL] = f"Draw all {len(df):,} {what} (slow; may freeze the browser)"
    st.warning(f"⚠️ {len(df):,} {what} exceed the {limit:,}-point map display limit. "
               "Choose how to display them — analysis, tables, and downloads still use every record.")
    choice = st.radio("Large dataset display", options=list(options), format_func=options.get,
                      key=key, horizontal=False)
    return choice or BUDGET_SAMPLE


# ---------------------------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------------------------
def _iter_elements(root):
    stack, seen = [root], set()
    while stack:
        element = stack.pop()
        if id(element) in seen:
            continue
        seen.add(id(element))
        yield element
        children = list(getattr(element, '_children', {}).values())
        for attr in ('header', 'html', 'script'):
            child = getattr(element, attr, None)
            if child is not None and hasattr(child, '_children'):
                children.append(child)
        stack.extend(reversed(children))


_UUID_ID = re.compile(r'(?<=_)[0-9a-f]{32}(?![0-9a-f])')


def map_html(map_obj) -> str:
    """Render map HTML deterministically.

    Folium names every element with a random UUID, so rebuilding an unchanged map produced
    different HTML on each rerun and the browser reloaded the whole map iframe. Replacing
    those ids with sequential ones keeps identical maps byte-identical, so they don't reload.
    """
    root = map_obj.get_root()
    element_ids = {}
    for element in _iter_elements(root):
        element_id = getattr(element, '_id', None)
        if isinstance(element_id, str) and element_id not in element_ids:
            element_ids[element_id] = f"{len(element_ids):032x}"
            element._id = element_ids[element_id]
    html = root.render()
    # Elements created during rendering get ids after the walk above; normalize any leftovers.
    leftovers = {}
    known = set(element_ids.values())

    def _replace(match):
        value = match.group(0)
        if value in known:
            return value
        if value not in leftovers:
            leftovers[value] = f"f{len(leftovers):031x}"
        return leftovers[value]

    return _UUID_ID.sub(_replace, html)


def render_map(map_obj, height: int = 600, download_name: Optional[str] = None,
               download_key: Optional[str] = None):
    """Display a Folium map; the optional HTML download is generated only when clicked."""
    add_layer_control(map_obj)
    html = map_html(map_obj)
    st.iframe(html, height=height)
    safe_session_set('last_map_type', 'leaflet')
    if download_name:
        st.download_button(label="Download Map HTML", data=lambda: fix_osm_tiles_for_export(html),
                           file_name=download_name, mime="text/html", key=download_key, on_click="ignore")


def add_map_basemaps(map_obj):
    esri_attr = "Esri, Maxar, Earthstar Geographics, and the GIS User Community"
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        name="Satellite + Labels (Esri)", attr=esri_attr, max_zoom=19,
        overlay=False, control=True, show=True,
    ).add_to(map_obj)
    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        name="OpenStreetMap", attr="© OpenStreetMap contributors", max_zoom=19,
        overlay=False, control=True, show=False,
    ).add_to(map_obj)
    for service, name in (
        ("World_Street_Map", "Esri World Street Map"),
        ("World_Topo_Map", "Esri World Topographic Map"),
        ("World_Gray_Canvas", "Esri World Gray Canvas"),
        ("World_Terrain_Base", "Esri World Terrain"),
    ):
        folium.TileLayer(
            tiles=f"https://server.arcgisonline.com/ArcGIS/rest/services/{service}/MapServer/tile/{{z}}/{{y}}/{{x}}",
            name=name, attr=esri_attr, max_zoom=19,
            overlay=False, control=True, show=False,
        ).add_to(map_obj)
    for service in ("Reference/World_Transportation", "Reference/World_Boundaries_and_Places"):
        folium.TileLayer(
            tiles=f"https://server.arcgisonline.com/ArcGIS/rest/services/{service}/MapServer/tile/{{z}}/{{y}}/{{x}}",
            name=f"Esri {service.rsplit('/', 1)[-1].replace('_', ' ')}",
            attr=esri_attr, max_zoom=19, overlay=True, control=False, show=True,
        ).add_to(map_obj)


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


def fix_osm_tiles_for_export(html: str) -> str:
    """Patch exported map HTML so OpenStreetMap tiles load when opened locally (file://).

    OSM's tile servers require either a Referer header or an identifying
    X-Requested-With header (see osm.wiki/Blocked_tiles). Browsers never send a
    Referer for file:// pages, which is why Chrome shows "Access blocked" tiles
    when the exported HTML is double-clicked (Safari happens to leak the local
    Referer, which is why it doesn't show the block). This injects a small
    Leaflet layer that fetches OSM tiles with a custom X-Requested-With header,
    satisfying the tile usage policy without touching non-OSM basemaps.
    """
    patch_script = """
<script>
(function(){
  async function fetchOsmTile(url, callback) {
    try {
      var resp = await fetch(url, {headers: {'X-Requested-With': 'Fetch-Analysis-Tool/5.4'}, mode: 'cors'});
      var blob = await resp.blob();
      var reader = new FileReader();
      reader.onload = function () { callback(reader.result); };
      reader.readAsDataURL(blob);
    } catch (e) {
      callback(null);
    }
  }
  L.TileLayer.OsmHeaderTileLayer = L.TileLayer.extend({
    createTile: function (coords, done) {
      var img = document.createElement('img');
      img.setAttribute('role', 'presentation');
      fetchOsmTile(this.getTileUrl(coords), function (dataUrl) {
        if (dataUrl) { img.src = dataUrl; }
        done(null, img);
      });
      return img;
    }
  });
  L.osmHeaderTileLayer = function (url, options) {
    return new L.TileLayer.OsmHeaderTileLayer(url, options);
  };
})();
</script>
"""
    leaflet_script_re = re.compile(r'(<script src="[^"]*/leaflet(?:@[^"/]+)?/dist/leaflet\.js"></script>)')
    if leaflet_script_re.search(html):
        html = leaflet_script_re.sub(lambda m: m.group(1) + patch_script, html, count=1)
    else:
        html = html.replace('</head>', patch_script + '</head>', 1)

    osm_tilelayer_re = re.compile(r'L\.tileLayer\(\s*("https?://(?:\{s\}\.)?tile\.openstreetmap\.org/\{z\}/\{x\}/\{y\}\.png")')
    html = osm_tilelayer_re.sub(r'L.osmHeaderTileLayer(\1', html)
    return html
