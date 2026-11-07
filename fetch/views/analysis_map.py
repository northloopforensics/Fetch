"""Analysis Maps page: clustered markers, points & trails, hotspots, heatmaps, and cell sites."""
import folium
import numpy as np
import pandas
import streamlit as st
from folium import plugins
from folium.plugins import HeatMap, TimestampedGeoJson

from fetch.analysis import cached_compute_hotspots, hotspot_input, render_tactical_clock
from fetch.coords import destination_points, filter_valid_coordinates, numeric_like_columns
from fetch.i18n import t
from fetch.maps import (BUDGET_AGGREGATE, BUDGET_SAMPLE, MAX_RENDER_POINTS, add_aggregate_layer, add_color_legend,
                        add_map_basemaps, add_point_layer, add_radius_layer, aggregate_points, fit_to_data, new_map,
                        popup_fields_selector, render_budget, render_map, set_center, thin_evenly)
from fetch.utils import fragment, safe_session_get, safe_session_set, session_memo
from fetch.widgets import filter_map_radius, optional_radius_filter

# Heat layers carry only [lat, lon, weight] per point, so they tolerate a larger display budget.
HEATMAP_MAX_POINTS = 50_000


@fragment
def make_map(in_df, fp):       #bring in pandas dataframe
    # Coordinate cleaning is memoized: this fragment reruns on every widget change.
    valid_records, skipped_count = session_memo(
        "map_valid_records", fp, lambda: filter_valid_coordinates(in_df, 'LATITUDE', 'LONGITUDE'))
    valid_count = len(valid_records)

    # Notify user if records were skipped
    if skipped_count > 0:
        st.warning(f"⚠️ Skipped {skipped_count} record(s) missing valid coordinates. Proceeding with {valid_count}.")

    # Check if we have any valid records left
    if valid_count == 0:
        st.error(t("msg_no_valid_records"))
        return

    gdf = valid_records
    _mt_en = ["Clustered Markers", "Points & Trails", "Hotspots", "Heatmap", "Cell Sites"]
    _mt_tr = [t("map_clustered"), t("map_points_trails"), t("map_hotspots"), t("map_heatmap"), t("map_cell_sites")]
    _mt_sel = st.radio(t("lbl_select_map_type"), options=_mt_tr, horizontal=True)
    map_Type = _mt_en[_mt_tr.index(_mt_sel)]
    if map_Type not in ["Points & Trails", "Cell Sites", "Heatmap"]:
        gdf = optional_radius_filter(gdf, key="map_radius")
        if gdf.empty:
            return
        valid_records = gdf
    Map = new_map()
    # Defer zooming for Hotspots so we can compute a tighter fit later
    if map_Type != "Hotspots":
        fit_to_data(Map, gdf)
    add_map_basemaps(Map)

    if map_Type == "Clustered Markers":
        popup_fields = popup_fields_selector(gdf, key="cluster_popup_fields")
        display_mode = render_budget(gdf, key="cluster_budget")
        if display_mode == BUDGET_AGGREGATE:
            add_aggregate_layer(Map, aggregate_points(gdf, MAX_RENDER_POINTS), name="Aggregated Points")
        else:
            shown = thin_evenly(gdf, MAX_RENDER_POINTS) if display_mode == BUDGET_SAMPLE else gdf
            add_point_layer(Map, shown, name="Clustered Points", cluster=True, fields=popup_fields)
    
    map_rendered = False  # track if we've already sent map to streamlit

    if map_Type == "Hotspots":
        st.markdown("---")
        colh1, colh2, colh3, colh4 = st.columns(4)
        with colh1:
            radius_m = st.number_input(t("lbl_radius_m"), min_value=5, max_value=1000, value=30, step=5)
        with colh2:
            max_hotspots = st.number_input(t("lbl_max_hotspots"), min_value=1, max_value=500, value=3, step=1)
        with colh3:
            possible_time_cols = [c for c in valid_records.columns if 'TIME' in c.upper() or 'DATE' in c.upper()]
            time_col = st.selectbox(t("lbl_time_col_optional"), options=[None]+possible_time_cols, index=0)
        with colh4:
            advanced = st.checkbox(t("chk_advanced"), value=False, help="Show min points parameter")
        if advanced:
            min_samples = st.slider("Min Points (DBSCAN)", min_value=2, max_value=50, value=3, step=1)
        else:
            min_samples = 3
        trim_chaining = st.checkbox(
            t("chk_trim_chaining"), value=True,
            help="If checked, any points farther than the chosen radius from a hotspot's centroid are removed (prevents elongated 'snake' clusters)."
        )
        run_cluster = st.button(t("btn_run_hotspot"))
        param_key = f"r{radius_m}_m{min_samples}_t{time_col}_trim{trim_chaining}"
        clusters_df = pandas.DataFrame(); summary_df = pandas.DataFrame()
        store = safe_session_get('hotspot_store')
        # Results live in st.cache_data; session state only remembers which params were run.
        if run_cluster or (store and store.get('params') == param_key):
            try:
                clean_coords = hotspot_input(valid_records, time_col)
                clusters_df, summary_df = cached_compute_hotspots(clean_coords, radius_m, min_samples, time_col, trim_chaining=trim_chaining)
                safe_session_set('hotspot_store', {'params': param_key})
            except RuntimeError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Hotspot clustering error: {e}")
        elif store:
            st.info(t("msg_params_changed"))

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
                    file_name="Fetch_Hotspots_Top.csv", on_click="ignore",
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
                    file_name="Fetch_Hotspots_All.csv", on_click="ignore",
                )
            if st.button(t("btn_clear_hotspots"), type="secondary"):
                safe_session_set('hotspot_store', None)
                st.rerun()
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
                    set_center(Map, mean_lat, mean_lon, zoom)
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
            show_points = st.checkbox(t("chk_show_points"), value=False, help="Display member points for the shown hotspots (large sets are sampled)")
            if show_points:
                try:
                    pts = clusters_df[clusters_df['HOTSPOT_ID'].isin(limited_summary['HOTSPOT_ID'])]
                    if len(pts) > MAX_RENDER_POINTS:
                        st.caption(f"Showing a random sample of {MAX_RENDER_POINTS:,} of {len(pts):,} member points.")
                        pts = pts.sample(MAX_RENDER_POINTS, random_state=0)
                    for cid, grp in pts.groupby('HOTSPOT_ID'):
                        color = palette[int(id_map.get(cid, cid)) % len(palette)]
                        add_point_layer(Map, grp, color, radius=2, popup=False, fill_opacity=0.9)
                except Exception as e:
                    st.error(f"Failed to render individual points: {e}")
            st.markdown("**Tips:** Increase radius if visits are a few dozen meters apart; decrease radius for tighter grouping.")
            # Render the map here (above clocks) once hotspots & optional points are drawn
            render_map(Map)
            map_rendered = True

            if time_col:
                st.markdown("---")
                t_sub = st.subheader(t("hdr_hotspot_clocks"))
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
                    use_weight = st.checkbox(t("chk_use_weight"))
                weights = None
                weight_series = None
                if use_weight:
                    numeric_cols = [
                        c for c in gdf.columns
                        if c not in ("LATITUDE","LONGITUDE","geometry")
                        and pandas.api.types.is_numeric_dtype(gdf[c])
                    ]
                    if numeric_cols:
                        weight_col = st.selectbox(t("lbl_weight_column"), options=numeric_cols)
                        weight_series = pandas.to_numeric(gdf[weight_col], errors='coerce').fillna(0)
                        weights = weight_series.tolist()
                    else:
                        st.info("No numeric columns available for weights.")
                heat_mode = render_budget(heat_df, key="heat_budget", limit=HEATMAP_MAX_POINTS, what="heatmap points")
                if heat_mode == BUDGET_AGGREGATE:
                    heat_cells = aggregate_points(heat_df, HEATMAP_MAX_POINTS, weight=weight_series)
                    heat_df, weights = heat_cells, heat_cells['WEIGHT'].tolist()
                elif heat_mode == BUDGET_SAMPLE:
                    heat_df = thin_evenly(heat_df, HEATMAP_MAX_POINTS)
                    weights = weight_series.loc[heat_df.index].tolist() if weight_series is not None else None
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
                    fit_to_data(Map, gdf)
                    map_rendered = True
                    # Immediately render to avoid waiting for final fallback (gives user instant feedback)
                    render_map(Map)
                except Exception as e:
                    st.error(f"Heatmap error: {e}")

    if map_Type == "Points & Trails":
            st.markdown("---")
            fit_to_data(Map, gdf) 
            _pp_en = ["Markers", "Show Point Progression", "Vapour Trail"]
            _pp_tr = [t("mode_markers"), t("mode_progression"), t("mode_vapor")]
            _pp_sel = st.radio(label=t("lbl_select_map_activity"), options=_pp_tr, horizontal=True)
            points_or_path = _pp_en[_pp_tr.index(_pp_sel)]
            if points_or_path != "Markers":
                gdf = optional_radius_filter(gdf, key="trail_radius")
                if gdf.empty:
                    return
                valid_records = gdf
                fit_to_data(Map, gdf)
            
            default_color = "#FF0000"
            if points_or_path == "Markers":
                radius_value = None
                if st.checkbox(t("chk_accuracy_radius")):
                    numeric_columns = numeric_like_columns(gdf)
                    if not numeric_columns:
                        st.error("No numeric columns found for radius/accuracy information. Please ensure your data contains numeric columns for radius values.")
                    else:
                        radius_value = st.selectbox(label=t("lbl_radius_meters"), options=numeric_columns)
                        gdf = filter_map_radius(gdf, radius_value, key="marker_max_radius")
                        if gdf.empty:
                            return
                        fit_to_data(Map, gdf)
                popup_fields = popup_fields_selector(gdf, key="markers_popup_fields")
                display_mode = render_budget(gdf, key="markers_budget")
                if display_mode == BUDGET_AGGREGATE:
                    add_aggregate_layer(Map, aggregate_points(gdf, MAX_RENDER_POINTS), default_color)
                else:
                    shown = thin_evenly(gdf, MAX_RENDER_POINTS) if display_mode == BUDGET_SAMPLE else gdf
                    if radius_value is not None:
                        add_radius_layer(Map, shown, radius_value, default_color)
                    if "POINT_COLOR" in shown.columns:
                        for point_color, color_group in shown.groupby("POINT_COLOR", sort=False):
                            add_point_layer(Map, color_group, point_color, fields=popup_fields)
                    else:
                        add_point_layer(Map, shown, default_color, fields=popup_fields)

            if points_or_path == "Show Point Progression":
                popup_fields = popup_fields_selector(gdf, key="progression_popup_fields")
                if render_budget(gdf, key="progression_budget", allow_aggregate=False) == BUDGET_SAMPLE:
                    gdf = thin_evenly(gdf, MAX_RENDER_POINTS)
                groups = gdf.groupby('SOURCE_FILE') if "SOURCE_FILE" in gdf.columns else [(None, gdf)]
                for _, group_df in groups:
                    color = group_df['POINT_COLOR'].iloc[0] if 'POINT_COLOR' in group_df.columns else default_color
                    add_point_layer(Map, group_df, color, fields=popup_fields)
                    plugins.AntPath(
                        locations=group_df[['LATITUDE', 'LONGITUDE']].to_numpy(float).tolist(),
                        color=color, weight=2, opacity=0.8
                    ).add_to(Map)

            if points_or_path == "Vapour Trail":
                choose_datetime_column = st.selectbox(t("lbl_datetime_column"), options=gdf.columns, key="datetime_vapor")
                if render_budget(gdf, key="vapor_budget", allow_aggregate=False) == BUDGET_SAMPLE:
                    gdf = thin_evenly(gdf, MAX_RENDER_POINTS)
                _ti_en = ["Daily", "Hourly", "10 Minutes", "1 Minute"]
                _ti_tr = [t("interval_daily"), t("interval_hourly"), t("interval_10min"), t("interval_1min")]
                _ti_sel = st.radio(t("lbl_time_interval"), options=_ti_tr, horizontal=True)
                time_interval = _ti_en[_ti_tr.index(_ti_sel)]

                if 'SOURCE_FILE' in gdf.columns:
                    groups = gdf.groupby('SOURCE_FILE')
                else:
                    vapor_trail_color = st.selectbox(
                        "Vapour Trail Color",
                        ['DarkRed', 'Yellow', 'Pink', 'Green', 'Teal', 'Blue', 'White'],
                        key="vapor_color"
                    )
                    groups = [(None, gdf)]
                chosen_interval = {'Daily': 'PT24H', 'Hourly': 'PT1H', '10 Minutes': 'PT10M', '1 Minute': 'PT1M'}[time_interval]

                # One LineString per consecutive pair of points that both have a timestamp.
                travel_history = []
                skipped_entries = 0
                for source_file, group_df in groups:
                    color = group_df['POINT_COLOR'].iloc[0] if source_file is not None else vapor_trail_color
                    times = group_df[choose_datetime_column]
                    has_time = times.notna().to_numpy()
                    pair_ok = has_time[:-1] & has_time[1:]
                    skipped_entries += int((~pair_ok).sum())
                    lats = group_df['LATITUDE'].to_numpy(float).tolist()
                    lons = group_df['LONGITUDE'].to_numpy(float).tolist()
                    time_strs = times.astype(str).tolist()
                    for i in np.flatnonzero(pair_ok).tolist():
                        travel_history.append({
                            "type": "Feature",
                            "geometry": {"type": "LineString",
                                         "coordinates": [[lons[i], lats[i]], [lons[i + 1], lats[i + 1]]]},
                            "properties": {"times": [time_strs[i], time_strs[i + 1]],
                                           "style": {"color": color, "weight": 8}},
                        })
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

        
    if map_Type == "Cell Sites":
            # Columns are already uppercased earlier in the pipeline — no need to repeat
            fit_to_data(Map, gdf)

            st.markdown("---")

            # --- Sector color controls ---
            sector_palette = ['Red', 'Blue', 'Green', 'Purple', 'Orange', 'DarkRed', 'Beige',
                              'DarkBlue', 'DarkGreen', 'CadetBlue', 'Pink', 'LightBlue',
                              'LightGreen', 'Gray', 'Black', 'LightGray']

            color_mode = "single"  # default
            wedge_color = sector_palette[0]
            if 'SOURCE_FILE' not in gdf.columns:
                color_mode = st.radio(
                    "Sector Coloring",
                    options=["Single Color", "Cycle Per Sector"],
                    horizontal=True,
                    help="'Cycle Per Sector' auto-assigns a different color to each row so overlapping sectors are distinguishable."
                )
                color_mode = "cycle" if color_mode == "Cycle Per Sector" else "single"
                if color_mode == "single":
                    wedge_color = st.selectbox(t("lbl_sector_color"), options=sector_palette)

            # Sector transparency slider
            sector_opacity = st.slider("Sector Fill Opacity", min_value=0.0, max_value=1.0, value=0.5, step=0.05,
                                       help="Lower values let you see through overlapping sectors.")

            # --- Column selection helpers ---
            all_columns = [col for col in valid_records.columns
                           if col not in ['LATITUDE', 'LONGITUDE', 'SOURCE_FILE', 'POINT_COLOR', 'geometry']]

            if not all_columns:
                st.error("No columns found for azimuth and beam width values. Please ensure your data contains the necessary columns.")
                st.stop()

            # Auto-detect best-match column index for azimuth
            azimuth_keywords = ['AZIMUTH', 'BEARING', 'DIRECTION', 'ANGLE', 'AZ']
            azimuth_default = 0
            for i, col in enumerate(all_columns):
                if any(kw in col.upper() for kw in azimuth_keywords):
                    azimuth_default = i
                    break

            # Auto-detect best-match column index for beam width
            bw_keywords = ['BEAMWIDTH', 'BEAM_WIDTH', 'BW', 'SECTOR_ANGLE', 'BEAM']
            bw_default = 0
            for i, col in enumerate(all_columns):
                if any(kw in col.upper() for kw in bw_keywords):
                    bw_default = i
                    break

            # --- Sector footprint size: presets + "From Column" ---
            numeric_radius_cols = numeric_like_columns(valid_records[all_columns], exclude=())

            radius_options = ["1 KM", "1.5 Mile"]
            if numeric_radius_cols:
                radius_options.append("From Column")
            radii = st.selectbox(t("lbl_sector_footprint"), options=radius_options)

            # Create the radius column based on selection
            if radii == "1.5 Mile":
                valid_records = valid_records.assign(**{"1.5 Mile": 2414})
                gdf = gdf.assign(**{"1.5 Mile": 2414})
                radii = "1.5 Mile"
            elif radii == "1 KM":
                valid_records = valid_records.assign(**{"1 KM": 1000})
                gdf = gdf.assign(**{"1 KM": 1000})
                radii = "1 KM"
            elif radii == "From Column":
                # Auto-detect radius column
                radius_kw = ['RADIUS', 'RANGE', 'DISTANCE', 'RADII']
                radius_default = 0
                for i, col in enumerate(numeric_radius_cols):
                    if any(kw in col.upper() for kw in radius_kw):
                        radius_default = i
                        break
                radii = st.selectbox(t("lbl_radius_col_meters"), options=numeric_radius_cols, index=radius_default)
                gdf = filter_map_radius(gdf, radii, key="sector_max_radius")
                if gdf.empty:
                    return
                fit_to_data(Map, gdf)

            if render_budget(gdf, key="sector_budget", allow_aggregate=False, what="sectors") == BUDGET_SAMPLE:
                gdf = thin_evenly(gdf, MAX_RENDER_POINTS).reset_index(drop=True)
            sector_popup_fields = popup_fields_selector(gdf, key="sector_popup_fields",
                                                        exclude=('geometry', 'POINT_COLOR', 'SOURCE_FILE'))

            # Azimuth and Beam Width dropdowns with auto-detected defaults
            Azimuth = st.selectbox(t("lbl_sector_azimuth"), options=all_columns, index=azimuth_default)
            beam_width = st.selectbox(t("lbl_beam_width"), options=all_columns, index=bw_default,
                                      placeholder='None')

            # --- Sectors and towers: three GeoJSON layers instead of ~5 Leaflet objects per row ---
            sector_fg = folium.FeatureGroup(name="Sector Wedges")
            tower_fg = folium.FeatureGroup(name="Tower Markers")
            azimuth_warnings = 0
            try:
                radius_m = pandas.to_numeric(gdf[radii], errors='coerce').to_numpy(float)
                az_raw = pandas.to_numeric(gdf[Azimuth], errors='coerce').to_numpy(float)
                bw = pandas.to_numeric(gdf[beam_width], errors='coerce').fillna(120.0).to_numpy(float)  # 120° = standard 3-sector site
                has_radius = radius_m > 0
                valid_az = np.isfinite(az_raw)
                azimuth_warnings = int((has_radius & (~valid_az | (az_raw < 0) | (az_raw > 360))).sum())
                idx = np.flatnonzero(has_radius & valid_az)

                fallback = ([sector_palette[i % len(sector_palette)] for i in range(len(gdf))]
                            if color_mode == "cycle" else [wedge_color] * len(gdf))
                if "POINT_COLOR" in gdf.columns:
                    colors = gdf["POINT_COLOR"].where(gdf["POINT_COLOR"].notna(), pandas.Series(fallback, index=gdf.index))
                    colors = colors.astype(str).to_numpy()[idx]
                else:
                    colors = np.asarray(fallback)[idx]

                lat, lon = gdf["LATITUDE"].to_numpy(float)[idx], gdf["LONGITUDE"].to_numpy(float)[idx]
                az, half_bw, r = az_raw[idx] % 360, bw[idx] / 2, radius_m[idx]
                arc_lat, arc_lon = destination_points(lat[:, None], lon[:, None], (r / 2)[:, None],
                                                      az[:, None] + half_bw[:, None] * np.linspace(-1, 1, 17))
                up_lat, up_lon = destination_points(lat, lon, r, az + half_bw)
                dn_lat, dn_lon = destination_points(lat, lon, r, az - half_bw)
                arcs = np.stack([arc_lon, arc_lat], axis=-1).tolist()
                fields = sector_popup_fields
                props = gdf[fields].iloc[idx].astype(str).to_dict('records')

                wedges, edges, towers = [], [], []
                for j, (center, p, color) in enumerate(zip(np.stack([lon, lat], axis=-1).tolist(), props, colors.tolist())):
                    wedges.append({'type': 'Feature', 'id': str(j), 'properties': {**p, '_color': color},
                                   'geometry': {'type': 'Polygon', 'coordinates': [[center] + arcs[j] + [center]]}})
                    edges.append({'type': 'Feature', 'id': str(j), 'properties': {'_color': color},
                                  'geometry': {'type': 'MultiLineString', 'coordinates': [
                                      [center, [up_lon[j], up_lat[j]]], [center, [dn_lon[j], dn_lat[j]]]]}})
                    towers.append({'type': 'Feature', 'id': str(j),
                                   'properties': {**p, '_tower': f"Tower ({center[1]:.5f}, {center[0]:.5f})"},
                                   'geometry': {'type': 'Point', 'coordinates': center}})

                if idx.size:
                    folium.GeoJson(
                        {'type': 'FeatureCollection', 'features': edges}, control=False,
                        style_function=lambda f: {'color': f['properties']['_color'], 'weight': 3},
                    ).add_to(sector_fg)
                    folium.GeoJson(
                        {'type': 'FeatureCollection', 'features': wedges}, control=False,
                        style_function=lambda f: {'color': f['properties']['_color'], 'fillColor': f['properties']['_color'],
                                                  'opacity': 1, 'fillOpacity': sector_opacity, 'weight': 3},
                        popup=folium.GeoJsonPopup(fields=fields),
                    ).add_to(sector_fg)
                    folium.GeoJson(
                        {'type': 'FeatureCollection', 'features': towers}, control=False,
                        marker=folium.CircleMarker(radius=5, color='black', fill=True, fill_color='white',
                                                   fill_opacity=1.0, weight=2),
                        popup=folium.GeoJsonPopup(fields=fields),
                        tooltip=folium.GeoJsonTooltip(fields=['_tower'], labels=False),
                    ).add_to(tower_fg)
            except (TypeError, ValueError) as e:
                st.info("Assign columns for Sector Footprint Size (Radius from Station in Meters), Tower Direction/Azimuth (Degrees), & Beam Width (Degrees)")
                st.error(f"Error: {str(e)}")

            if azimuth_warnings > 0:
                st.warning(f"⚠️ {azimuth_warnings} sector(s) had azimuth values outside 0–360° (corrected via modulo) or non-numeric values (skipped).")

            # Add feature groups and layer control
            sector_fg.add_to(Map)
            tower_fg.add_to(Map)
            folium.LayerControl(collapsed=False).add_to(Map)

    # Add the legend if we have multiple data sources
    if 'SOURCE_FILE' in valid_records.columns and 'POINT_COLOR' in valid_records.columns:
        add_color_legend(Map, valid_records)

    # Final fallback render if not already rendered earlier
    if not map_rendered:
        render_map(Map, download_name="Fetch_Analysis_Map.html", download_key="dl_analysis_map")
