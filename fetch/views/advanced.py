"""Advanced Analysis page: stop/dwell detection and co-location (proximity) analysis."""
import folium
import pandas
import streamlit as st

from fetch.analysis import cached_compute_colocation, cached_compute_stops, colocation_csv
from fetch.i18n import t
from fetch.maps import MAX_RENDER_POINTS, add_map_basemaps, new_map, render_map
from fetch.utils import csv_bytes, fingerprint, nav_selector, safe_session_get, safe_session_set
from fetch.widgets import optional_radius_filter


def add_colocation_layers(map_obj, events: pandas.DataFrame):
    """One GeoJSON layer for connecting lines and one for midpoint markers (instead of two objects per event)."""
    lines, midpoints = [], []
    for i, (idx, row) in enumerate(events.iterrows()):
        props = {
            'Event': f"Co-Location #{idx+1}",
            'Sources': f"{row['SOURCE_A']} ↔ {row['SOURCE_B']}",
            'Time A': str(row['TIME_A']),
            'Time B': str(row['TIME_B']),
            'Distance (m)': row['DISTANCE_M'],
            'Time Diff (min)': row['TIME_DIFF_MIN'],
            'Summary': f"Co-Location #{idx+1} ({row['DISTANCE_M']}m, {row['TIME_DIFF_MIN']}min)",
        }
        lines.append({'type': 'Feature', 'id': str(i), 'properties': {},
                      'geometry': {'type': 'LineString',
                                   'coordinates': [[row['LON_A'], row['LAT_A']], [row['LON_B'], row['LAT_B']]]}})
        midpoints.append({'type': 'Feature', 'id': str(i), 'properties': props,
                          'geometry': {'type': 'Point', 'coordinates': [row['MIDPOINT_LON'], row['MIDPOINT_LAT']]}})
    if not lines:
        return
    folium.GeoJson({'type': 'FeatureCollection', 'features': lines}, control=False,
                   style_function=lambda f: {'color': 'red', 'weight': 2, 'opacity': 0.8}).add_to(map_obj)
    folium.GeoJson(
        {'type': 'FeatureCollection', 'features': midpoints}, control=False,
        marker=folium.Marker(icon=folium.Icon(color='red', icon='users', prefix='fa')),
        tooltip=folium.GeoJsonTooltip(fields=['Summary'], labels=False),
        popup=folium.GeoJsonPopup(fields=['Event', 'Sources', 'Time A', 'Time B', 'Distance (m)', 'Time Diff (min)']),
    ).add_to(map_obj)


def advanced_page(preview_data, fp):
    st.header(t("hdr_advanced_analysis"))
    _adv_opts = [t("tab_stop_dwell"), t("tab_colocation")]
    _adv_sel = nav_selector("Analysis", _adv_opts, key="nav_adv")
    analysis_data = optional_radius_filter(preview_data, key="analysis_radius")
    analysis_input = fingerprint(fp, *(safe_session_get(f"analysis_radius_{part}")
                                       for part in ("enabled", "column", "maximum")))
    if safe_session_get('analysis_radius_input') != analysis_input:
        safe_session_set('stop_results', None)
        safe_session_set('coloc_results', None)
        safe_session_set('analysis_radius_input', analysis_input)

    if _adv_sel == _adv_opts[0]:
        # --- Stop / Dwell Detection (Feature #7) ---
        st.subheader(t("hdr_stop_dwell"))
        st.caption("Detect locations where a subject remained stationary for a configurable duration.")

        # Time column detection
        stop_time_cols = [c for c in preview_data.columns if 'TIME' in c.upper() or 'DATE' in c.upper()]
        if not stop_time_cols:
            st.warning(t("msg_stops_no_time"))
        else:
            stop_col1, stop_col2, stop_col3 = st.columns(3)
            with stop_col1:
                stop_time_col = st.selectbox(t("lbl_time_column"), options=stop_time_cols, key="stop_time_col")
            with stop_col2:
                stop_radius = st.number_input(t("lbl_radius_m"), min_value=5, max_value=2000, value=50, step=5, key="stop_radius",
                                              help="Maximum distance from centroid to be considered the same stop")
            with stop_col3:
                stop_min_duration = st.number_input(t("lbl_min_duration"), min_value=1, max_value=1440, value=5, step=1, key="stop_min_dur",
                                                    help="Minimum time at a location to qualify as a stop")

            # Per-source or combined
            run_stops_per_source = False
            if 'SOURCE_FILE' in analysis_data.columns and analysis_data['SOURCE_FILE'].nunique() > 1:
                run_stops_per_source = st.checkbox(t("chk_per_source"), value=True, key="stop_per_src")

            if st.button(t("btn_detect_stops"), key="run_stops", disabled=analysis_data.empty):
                with st.spinner("Analyzing stops..."):
                    all_stops = []
                    if run_stops_per_source:
                        for src in analysis_data['SOURCE_FILE'].unique():
                            src_df = analysis_data[analysis_data['SOURCE_FILE'] == src]
                            stops_df = cached_compute_stops(src_df, stop_time_col, stop_radius, stop_min_duration, src)
                            if not stops_df.empty:
                                all_stops.append(stops_df)
                        if all_stops:
                            stops_result = pandas.concat(all_stops, ignore_index=True)
                        else:
                            stops_result = pandas.DataFrame()
                    else:
                        stops_result = cached_compute_stops(analysis_data, stop_time_col, stop_radius, stop_min_duration)

                    safe_session_set('stop_results', stops_result)
                    if stops_result.empty:
                        st.warning("No stops detected with current parameters. Try increasing the radius or decreasing the minimum duration.")

            # Display results
            stops_result = safe_session_get('stop_results')
            if stops_result is not None and isinstance(stops_result, pandas.DataFrame) and not stops_result.empty:
                st.markdown(f"### Found {len(stops_result)} Stop(s)")

                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    st.metric("Total Stops", len(stops_result))
                with col_m2:
                    avg_dur = stops_result['DURATION_MIN'].mean()
                    st.metric("Avg Duration", f"{avg_dur:.1f} min")
                with col_m3:
                    total_dwell = stops_result['DURATION_MIN'].sum()
                    if total_dwell > 60:
                        st.metric("Total Dwell Time", f"{total_dwell/60:.1f} hrs")
                    else:
                        st.metric("Total Dwell Time", f"{total_dwell:.1f} min")

                st.dataframe(stops_result, width="stretch")
                st.download_button("Download Stops CSV", data=csv_bytes(stops_result, index=False),
                                   file_name="Fetch_Stops.csv", key="dl_stops", mime="text/csv", on_click="ignore")

                # Map the stops
                st.markdown("### Stop Locations Map")
                stop_map = new_map()
                add_map_basemaps(stop_map)

                stop_palette = ["red","blue","green","orange","purple","teal","pink","yellow"]
                for idx, row in stops_result.iterrows():
                    color = stop_palette[idx % len(stop_palette)]
                    dur_str = f"{row['DURATION_MIN']:.0f} min" if row['DURATION_MIN'] < 60 else f"{row['DURATION_MIN']/60:.1f} hrs"
                    popup_text = (f"Stop #{row['STOP_ID']+1}<br>"
                                  f"Arrive: {row['ARRIVAL']}<br>"
                                  f"Depart: {row['DEPARTURE']}<br>"
                                  f"Duration: {dur_str}<br>"
                                  f"Points: {row['POINT_COUNT']}")
                    if row.get('SOURCE_FILE'):
                        popup_text += f"<br>Source: {row['SOURCE_FILE']}"
                    folium.Circle(
                        location=[row['CENTER_LAT'], row['CENTER_LON']],
                        radius=stop_radius if 'stop_radius' in dir() else 50,
                        color=color, fill=True, fill_color=color, fill_opacity=0.3,
                        popup=popup_text
                    ).add_to(stop_map)
                    folium.Marker(
                        [row['CENTER_LAT'], row['CENTER_LON']],
                        tooltip=f"Stop #{row['STOP_ID']+1} ({dur_str})",
                        icon=folium.Icon(color=color if color in ['red','blue','green','orange','purple'] else 'red', icon='pause', prefix='fa')
                    ).add_to(stop_map)

                # Fit bounds
                if len(stops_result) > 0:
                    stop_lats = stops_result['CENTER_LAT'].tolist()
                    stop_lons = stops_result['CENTER_LON'].tolist()
                    sw = [min(stop_lats)-0.001, min(stop_lons)-0.001]
                    ne = [max(stop_lats)+0.001, max(stop_lons)+0.001]
                    stop_map.fit_bounds([sw, ne])

                render_map(stop_map)

    elif _adv_sel == _adv_opts[1]:
        # --- Co-Location / Proximity Analysis (Feature #3) ---
        st.subheader(t("hdr_colocation"))
        st.caption("Detect when and where two subjects (from different source files) were at the same place at the same time.")

        if 'SOURCE_FILE' not in analysis_data.columns or analysis_data['SOURCE_FILE'].nunique() < 2:
            st.info("Co-location analysis requires **2 or more source files** loaded simultaneously. Upload multiple files to use this feature.")
        else:
            sources = sorted(analysis_data['SOURCE_FILE'].unique())
            st.write(f"**{len(sources)} source files loaded:** {', '.join(sources)}")

            coloc_time_cols = [c for c in analysis_data.columns if 'TIME' in c.upper() or 'DATE' in c.upper()]
            if not coloc_time_cols:
                st.warning(t("msg_coloc_no_time"))
            else:
                coloc_c1, coloc_c2, coloc_c3 = st.columns(3)
                with coloc_c1:
                    coloc_time_col = st.selectbox(t("lbl_time_column"), options=coloc_time_cols, key="coloc_time_col")
                with coloc_c2:
                    coloc_radius = st.number_input(t("lbl_proximity_radius"), min_value=5, max_value=5000, value=50, step=5, key="coloc_radius",
                                                   help="Maximum distance between two subjects to be considered co-located")
                with coloc_c3:
                    coloc_time_window = st.number_input(t("lbl_time_window"), min_value=1, max_value=1440, value=10, step=1, key="coloc_window",
                                                        help="Maximum time difference between observations")

                if st.button(t("btn_run_colocation"), key="run_coloc", disabled=analysis_data.empty):
                    with st.spinner("Analyzing co-location events... This may take a moment for large datasets."):
                        coloc_result, coloc_total = cached_compute_colocation(analysis_data, coloc_time_col, coloc_radius, coloc_time_window)
                        safe_session_set('coloc_results', coloc_result)
                        safe_session_set('coloc_meta', {'total': coloc_total, 'params': (coloc_time_col, coloc_radius, coloc_time_window)})

                coloc_result = safe_session_get('coloc_results')
                coloc_meta = safe_session_get('coloc_meta') or {}
                if coloc_result is not None and isinstance(coloc_result, pandas.DataFrame) and not coloc_result.empty:
                    coloc_total = coloc_meta.get('total', len(coloc_result))
                    truncated = coloc_total > len(coloc_result)
                    st.markdown(f"### {coloc_total:,} Co-Location Event(s) Detected")
                    if truncated:
                        st.warning(f"Showing the {len(coloc_result):,} closest of {coloc_total:,} events to keep the app responsive. "
                                   "Narrow the radius or time window, or download every event below.")

                    col_m1, col_m2, col_m3 = st.columns(3)
                    with col_m1:
                        st.metric("Total Events", f"{coloc_total:,}")
                    with col_m2:
                        avg_dist = coloc_result['DISTANCE_M'].mean()
                        st.metric("Avg Distance (shown)" if truncated else "Avg Distance", f"{avg_dist:.1f} m")
                    with col_m3:
                        pairs = coloc_result.groupby(['SOURCE_A','SOURCE_B']).size().reset_index(name='count')
                        st.metric("Subject Pairs", len(pairs))

                    # Show pair breakdown
                    if len(pairs) > 1:
                        st.markdown("**Shown events per subject pair:**" if truncated else "**Events per subject pair:**")
                        for _, pair_row in pairs.iterrows():
                            st.write(f"- {pair_row['SOURCE_A']} ↔ {pair_row['SOURCE_B']}: **{pair_row['count']}** events")

                    st.dataframe(coloc_result, width="stretch")
                    st.download_button("Download Shown Events CSV" if truncated else "Download Co-Location CSV",
                                       data=csv_bytes(coloc_result, index=False),
                                       file_name="Fetch_CoLocation.csv", key="dl_coloc", mime="text/csv", on_click="ignore")
                    if truncated and 'params' in coloc_meta:
                        time_col_used, radius_used, window_used = coloc_meta['params']
                        st.download_button(
                            f"Download All {coloc_total:,} Events CSV", key="dl_coloc_all", mime="text/csv", on_click="ignore",
                            file_name="Fetch_CoLocation_All.csv",
                            data=lambda: colocation_csv(analysis_data, time_col_used, radius_used, window_used),
                            help="Recomputed when clicked and written straight to CSV (grouped by subject pair).")

                    # Map co-location events
                    st.markdown("### Co-Location Map")
                    coloc_map = new_map()
                    add_map_basemaps(coloc_map)

                    coloc_map_df = coloc_result
                    if len(coloc_result) > MAX_RENDER_POINTS:
                        st.caption(f"Map shows the {MAX_RENDER_POINTS:,} closest of {len(coloc_result):,} listed events; the table and CSV include all of them.")
                        coloc_map_df = coloc_result.nsmallest(MAX_RENDER_POINTS, 'DISTANCE_M')
                    add_colocation_layers(coloc_map, coloc_map_df)

                    # Fit bounds
                    all_lats = coloc_result['MIDPOINT_LAT'].tolist()
                    all_lons = coloc_result['MIDPOINT_LON'].tolist()
                    if all_lats:
                        sw = [min(all_lats)-0.001, min(all_lons)-0.001]
                        ne = [max(all_lats)+0.001, max(all_lons)+0.001]
                        coloc_map.fit_bounds([sw, ne])

                    render_map(coloc_map)

                elif coloc_result is not None and isinstance(coloc_result, pandas.DataFrame) and coloc_result.empty:
                    if safe_session_get('coloc_results') is not None:
                        st.info("No co-location events found with the current parameters. Try increasing the radius or time window.")
