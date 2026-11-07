"""Create Geofence page: draw shapes, search addresses/IPs, and export coordinates."""
import json as _json
import re

import folium
import streamlit as st
from folium.plugins import Draw
from streamlit_folium import st_folium

from fetch.geo_lookup import cached_arcgis_result, cached_ipinfo_result
from fetch.i18n import t
from fetch.maps import add_map_basemaps
from fetch.utils import fragment, safe_session_get, safe_session_set


@fragment
def make_geofence_map():
    # --- Geofence Manager State ---
    if safe_session_get('geofences') is None:
        safe_session_set('geofences', [])  # list of dicts: id,name,color,geometry(type,wkt),created,updated,active,notes
    if safe_session_get('geofence_counter') is None:
        safe_session_set('geofence_counter', 1)

    help_Box = st.expander(label="Help")
    with help_Box:
        st.markdown("""
        Welcome to Fetch! This area is used to create geofences. To upload location data use the input area above.
        - Use the draw toolbar on the map (polygon/rectangle). 
        - Search for a street address or get the map of an IP address. See the IP address mapping tab to carry out bulk searches.
        """)

    # Search / locate
    with st.form("geoform"):
        user_geo_input = st.text_input(t("lbl_search_addr_ip"), placeholder="123 Main St or 8.8.8.8")
        search = st.form_submit_button("Locate")

    # Initialize session state for caching geocoding results
    if safe_session_get('cached_geocode_result') is None:
        safe_session_set('cached_geocode_result', None)
    if safe_session_get('cached_search_term') is None:
        safe_session_set('cached_search_term', None)

    # Initialize with neutral continental US view; we'll optionally recenter below
    geomap = folium.Map(zoom_start=4, location=[39,-98], tiles=None)
    add_map_basemaps(geomap)
    Draw(export=True, draw_options={'circle': False,'circlemarker':False, 'marker':False}).add_to(geomap)
    folium.LayerControl(position="topright", collapsed=True).add_to(geomap)

    # Geocode/IP locate - Only run when search button is clicked
    if search and user_geo_input:
        ipv4_ipv6_regex = r"(^\s*((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))\s*$)|(^\s*((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\s*$)"

        # Check if we need to make a new API call
        # Use safe_session_get to avoid KeyError if cached_search_term is missing between reruns
        if user_geo_input != safe_session_get('cached_search_term'):
            if re.search(ipv4_ipv6_regex, user_geo_input):
                try:
                    ip_res = cached_ipinfo_result(user_geo_input.strip())
                    if ip_res and ip_res.latlng:
                        # Cache the successful result
                        safe_session_set('cached_geocode_result', {
                            'type': 'ip',
                            'data': ip_res,
                            'input': user_geo_input
                        })
                        safe_session_set('cached_search_term', user_geo_input)
                        st.success("✅ IP address located successfully!")
                    else:
                        st.error("❌ Could not locate IP address")
                        safe_session_set('cached_geocode_result', None)
                        safe_session_set('cached_search_term', None)
                except Exception as e:
                    st.error(f"❌ IP lookup failed: {str(e)}")
                    safe_session_set('cached_geocode_result', None)
                    safe_session_set('cached_search_term', None)
            else:
                try:
                    geo_res = cached_arcgis_result(user_geo_input.strip())
                    if geo_res and geo_res.latlng:
                        # Cache the successful result
                        safe_session_set('cached_geocode_result', {
                            'type': 'address',
                            'data': geo_res,
                            'input': user_geo_input
                        })
                        safe_session_set('cached_search_term', user_geo_input)
                        st.success("✅ Address located successfully!")
                    else:
                        st.error("❌ Could not locate address")
                        safe_session_set('cached_geocode_result', None)
                        safe_session_set('cached_search_term', None)
                except Exception as e:
                    st.error(f"❌ Address lookup failed: {str(e)}")
                    safe_session_set('cached_geocode_result', None)
                    safe_session_set('cached_search_term', None)
        else:
            st.info("📋 Using cached result (no API call needed)")

    # Display cached results if available (use .get() to avoid KeyError)
    if safe_session_get('cached_geocode_result'):
        cached_result = safe_session_get('cached_geocode_result')
        
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
            with st.expander("🔧 Raw Lookup Data (Debug)"):
                st.json(ip_res.json)
            
            # Rebuild map centered on result
            geomap = folium.Map(location=ip_res.latlng, zoom_start=11, tiles=None)
            add_map_basemaps(geomap)
            Draw(export=True, draw_options={'circle': False,'circlemarker':False, 'marker':False}).add_to(geomap)
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
                    "Match Score": getattr(geo_res, 'score', 'Not available'),
                    "Provider": geo_res.provider if hasattr(geo_res, 'provider') else 'ArcGIS',
                    "Status": getattr(geo_res, 'status', 'Unknown')
                }
                for key, value in accuracy_info.items():
                    st.write(f"• **{key}:** {value}")
            
            # Show raw data in an expandable section
            with st.expander("🔧 Raw Lookup Data (Debug)"):
                st.json(geo_res.json)
            
            geomap = folium.Map(location=geo_res.latlng, zoom_start=16, tiles=None)
            add_map_basemaps(geomap)
            Draw(export=True, draw_options={'circle': False,'circlemarker':False, 'marker':False}).add_to(geomap)
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
                    <tr><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">Match Score:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{getattr(geo_res, 'score', 'Unknown')}</td></tr>
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
    geofences_list = safe_session_get('geofences') or []
    if geofences_list:
        for g in geofences_list:
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
        last_geojson_temp = safe_session_get('last_drawn_raw')
    except Exception:
        last_geojson_temp = None

    # Fallback: attempt to get from current output later; we will set after outputmap if needed.
    
    # Try to render interactive folium via streamlit_folium; if the component fails to load
    # (common on deployments where the frontend component isn't available), fall back to
    # embedding the map HTML. This avoids the "component failed to load" reset loop.
    outputmap = None
    try:
        try:
            # Only drawing changes trigger a rerun; panning/zooming no longer reruns the app.
            outputmap = st_folium(geomap, width=1100, height=600, key="geofence_map",
                                  returned_objects=["last_active_drawing"])
        except TypeError:
            outputmap = st_folium(geomap, width=1100, height=600, key="geofence_map")
    except Exception as e:
        # Log the error for debugging but don't crash the app; render HTML fallback.
        try:
            st.warning("streamlit_folium component failed to load; falling back to static HTML rendering.")
        except Exception:
            pass
        try:
            # Render map HTML as a safe fallback. This won't provide the drawing callbacks
            # that st_folium exposes, so we attempt to preserve the last drawn geometry
            # from session_state instead of relying on the component.
            html = geomap._repr_html_()
            st.iframe(html, height=600, scrolling=True)
        except Exception:
            # If even HTML rendering fails, show a placeholder message.
            try:
                st.error("Unable to render the map via streamlit_folium or HTML fallback.")
            except Exception:
                pass

    # Capture last drawn geometry. If we used the HTML fallback, prefer the last stored drawing
    # from session_state because the fallback doesn't provide live drawing callbacks.
    last_geojson = None
    try:
        if isinstance(outputmap, dict):
            last_geojson = outputmap.get('last_active_drawing')
        if not last_geojson:
            # fallback to any previously stored drawing
            last_geojson = safe_session_get('last_drawn_raw')
    except Exception:
        last_geojson = safe_session_get('last_drawn_raw')
    if last_geojson:
        safe_session_set('last_drawn_raw', last_geojson)
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
            st.download_button("Download TXT", data=coords_text, file_name="geofence_coordinates.txt", on_click="ignore")
        with colx2:
            # Quick GeoJSON export of just this drawing

            feature = {
                "type":"FeatureCollection",
                "features":[{"type":"Feature","geometry":{"type":g_type,"coordinates":last_geojson['geometry']['coordinates']},"properties":{}}]
            }
            st.download_button("Download GeoJSON", data=_json.dumps(feature), file_name="geofence.geojson", on_click="ignore")
        with colx3:
            # KML (very simple) if polygon
            if g_type == 'Polygon':
                kml_coords = " ".join(f"{lon},{lat},0" for lat, lon in coord_list)
                kml = f"""<?xml version='1.0' encoding='UTF-8'?>\n<kml xmlns='http://www.opengis.net/kml/2.2'>\n<Document><Placemark><Polygon><outerBoundaryIs><LinearRing><coordinates>{kml_coords}</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark></Document></kml>"""
                st.download_button("Download KML", data=kml, file_name="geofence.kml", on_click="ignore")
            else:
                st.write(" ")
    else:
        st.info("Draw a shape (polygon/rectangle) to see coordinates below the map instantly.")
