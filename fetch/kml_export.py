"""KML/KMZ map generation (placemarks, footprints, path lines, and Google Earth tours)."""
import io
import zipfile
from math import asin, atan2, cos, degrees, radians, sin

import pandas
import simplekml
import streamlit as st
from polycircles import polycircles

from fetch.coords import filter_valid_coordinates
from fetch.i18n import t
from fetch.utils import fragment
from fetch.widgets import filter_map_radius


def kml_to_kmz_bytes(kml: simplekml.Kml) -> bytes:
    """Zip a KML document as doc.kml (what simplekml's savekmz writes) without touching disk."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as kmz:
        kmz.writestr("doc.kml", kml.kml())
    return buffer.getvalue()


icon_options = ["Yellow Paddle", "Green Paddle", "Blue Paddle", "White Paddle", "Teal Paddle", "Red Paddle", "Yellow Pushpin", "White Pushpin", "Red Pushpin", "Square"]


selected_icon = {'Square' :'http://maps.google.com/mapfiles/kml/shapes/placemark_square.png','Yellow Pushpin' : "http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png",'Red Pushpin' : "http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png",'White Pushpin' : "http://maps.google.com/mapfiles/kml/pushpin/wht-pushpin.png",'Red Paddle' : "http://maps.google.com/mapfiles/kml/paddle/red-circle.png",'Green Paddle' : "http://maps.google.com/mapfiles/kml/paddle/grn-circle.png",'Blue Paddle' : "http://maps.google.com/mapfiles/kml/paddle/blu-circle.png",'Teal Paddle' : "http://maps.google.com/mapfiles/kml/paddle/ltblu-circle.png",'Yellow Paddle' : "http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png",'White Paddle' : "http://maps.google.com/mapfiles/kml/paddle/wht-circle.png"}


def get_footprint_color(icon_Color):
    if "Yellow" in icon_Color:
        footprint_color = simplekml.Color.changealphaint(50, simplekml.Color.yellow)
    elif "Red" in icon_Color:
        footprint_color = simplekml.Color.changealphaint(100, simplekml.Color.red)
    elif "Blue" in icon_Color:
        footprint_color = simplekml.Color.changealphaint(100, simplekml.Color.blue)
    elif "White" in icon_Color:
        footprint_color = simplekml.Color.changealphaint(100, simplekml.Color.white)
    elif "Green" in icon_Color:
        footprint_color = simplekml.Color.changealphaint(100, simplekml.Color.green)
    elif "Teal" in icon_Color:
        footprint_color = simplekml.Color.changealphaint(100, simplekml.Color.lightblue)
    elif "Square" in icon_Color:
        footprint_color = simplekml.Color.changealphaint(200, simplekml.Color.white)
    else:
        footprint_color = simplekml.Color.changealphaint(100, simplekml.Color.white)
    return footprint_color


def _compute_bearing(lat1, lon1, lat2, lon2):
    """Compute initial bearing (degrees 0-360) from point 1 to point 2."""
    lat1, lon1, lat2, lon2 = radians(lat1), radians(lon1), radians(lat2), radians(lon2)
    dlon = lon2 - lon1
    x = sin(dlon) * cos(lat2)
    y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
    bearing = atan2(x, y)
    return (degrees(bearing) + 360) % 360


def _haversine_km(lat1, lon1, lat2, lon2):
    """Return distance in km between two lat/lon points."""
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * asin(a ** 0.5)


def create_kml_tour(df, altitude, tilt, linger, time_column, icon, footprint, radii,
                    fly_mode="smooth", kml_obj=None):
    """
    Creates a KML tour (and placemarks + path line) either into a new KML or
    into an existing *kml_obj* so tour + placemarks live in one file.

    Parameters:
        df: DataFrame with LATITUDE / LONGITUDE columns.
        altitude: Camera height in meters (int).
        tilt: Camera tilt in degrees (int).
        linger: Seconds to linger at each point (float).
        time_column: Column name for timestamps, or None.
        icon: Icon style key into selected_icon dict.
        footprint: Whether to draw radius polygons.
        radii: Column name for radius data.
        fly_mode: 'smooth' for cinematic flight, 'bounce' for default Google Earth hop.
        kml_obj: Optional existing simplekml.Kml to append tour into.

    Returns the simplekml.Kml containing the tour.
    """
    try:
        altitude = int(altitude)
        tilt = int(tilt)
        linger = float(linger)

        kml = kml_obj if kml_obj is not None else simplekml.Kml()
        tour = kml.newgxtour(name="Fetch Tour")
        playlist = tour.newgxplaylist()

        if 'LONGITUDE' not in df.columns or 'LATITUDE' not in df.columns:
            raise ValueError("DataFrame must contain 'LONGITUDE' and 'LATITUDE' columns.")

        # Coordinate cleaning
        valid_df, skipped_count = filter_valid_coordinates(df, 'LATITUDE', 'LONGITUDE')
        valid_count = len(valid_df)

        if skipped_count > 0:
            st.warning(f"⚠️ Skipped {skipped_count} record(s) missing coordinates for KML tour.")

        if valid_count == 0:
            st.warning("No valid records found for KML tour generation.")
            return

        # Convert time column
        if time_column is not None:
            try:
                valid_df[time_column] = pandas.to_datetime(valid_df[time_column])
            except ValueError:
                valid_df[time_column] = pandas.to_datetime(valid_df[time_column], utc=True)
                valid_df[time_column] = valid_df[time_column].dt.tz_convert('UTC')

        # Determine fly-to mode
        gx_flyto_mode = simplekml.GxFlyToMode.smooth if fly_mode == "smooth" else simplekml.GxFlyToMode.bounce

        # Collect coords for path LineString
        path_coords = []
        rows_list = list(valid_df.iterrows())

        for i, (idx, row) in enumerate(rows_list):
            try:
                lon, lat = float(row['LONGITUDE']), float(row['LATITUDE'])
                path_coords.append((lon, lat))

                description_lines = [f"{key}: {value}" for key, value in row.items()]
                description = "\n".join(description_lines)

                placemark = kml.newpoint(
                    name=f"{row[time_column]}" if time_column else f"{lat}, {lon}",
                    coords=[(lon, lat)],
                    description=description
                )
                placemark.style.iconstyle.icon.href = selected_icon[icon]

                if footprint and radii:
                    rad = row[radii]
                    polycircle = polycircles.Polycircle(
                        latitude=lat, longitude=lon,
                        radius=float(rad), number_of_vertices=72
                    )
                    pol = kml.newpolygon(
                        name=f"{lat}, {lon}, {rad}",
                        outerboundaryis=polycircle.to_kml()
                    )
                    pol.style.polystyle.color = get_footprint_color(icon_Color=icon)

                # --- Compute smart heading (bearing toward next point) ---
                if i + 1 < len(rows_list):
                    next_row = rows_list[i + 1][1]
                    next_lat, next_lon = float(next_row['LATITUDE']), float(next_row['LONGITUDE'])
                    heading = _compute_bearing(lat, lon, next_lat, next_lon)
                    dist_km = _haversine_km(lat, lon, next_lat, next_lon)
                else:
                    # Last point: keep heading from previous leg (or 0)
                    heading = heading if i > 0 else 0  # noqa: F821 — heading set in prior iteration
                    dist_km = 0

                # --- Scale fly duration by distance (1s min, 8s max) ---
                fly_duration = max(1.0, min(8.0, dist_km * 0.5 + 1.0))

                flyto = playlist.newgxflyto(gxduration=fly_duration)
                flyto.gxflytomode = gx_flyto_mode
                flyto.camera.longitude = lon
                flyto.camera.latitude = lat
                flyto.camera.altitude = altitude
                flyto.camera.altitudemode = simplekml.AltitudeMode.relativetoground
                flyto.camera.heading = heading
                flyto.camera.tilt = tilt
                flyto.camera.roll = 0

                if time_column is not None:
                    flyto.when = row[time_column].isoformat()

                playlist.newgxwait(gxduration=linger)

            except (AttributeError, TypeError) as e:
                st.warning(f"Tour: skipping point {idx}: {e}")

        # Add a LineString showing the full travel path
        if len(path_coords) >= 2:
            line = kml.newlinestring(name="Travel Path")
            line.coords = path_coords
            line.style.linestyle.color = simplekml.Color.changealphaint(180, simplekml.Color.cyan)
            line.style.linestyle.width = 3
            line.altitudemode = simplekml.AltitudeMode.clamptoground

        return kml

    except TypeError as e:
        st.error(f"Error creating KML tour. Check for errors in the data set. ({e})")


@fragment
def create_kml(df_in):
    try:
        headers = df_in.columns.to_list()

        # Streamlit UI for selecting columns
        st.subheader(t("hdr_design_kml"))

        # Only show color selector if there's no POINT_COLOR column
        if 'POINT_COLOR' not in df_in.columns:
            icon = st.selectbox(t("lbl_icon_style"), options=icon_options)
        else:
            icon = "Yellow Paddle"  # Default icon style
            st.info("Using colors selected during file upload")

        label_for_icons = st.selectbox(t("lbl_icon_labels"), options=headers)

        footprint = st.checkbox(t("chk_footprint"), value=False)
        radii = None
        if footprint:
            radii = st.selectbox(t("lbl_radius_distance"), options=headers)
            df_in = filter_map_radius(df_in, radii, key="kml_max_radius")
            if df_in.empty:
                return

        # --- Path line option ---
        add_path_line = st.checkbox(t("chk_path_line"), value=False,
                                    help="Draws a LineString connecting all points in order.")

        # --- Output format ---
        output_format = st.radio(t("lbl_output_format"), options=["KML", "KMZ"], horizontal=True,
                                 help="KMZ is a compressed KML — smaller file size.")

        tour = st.checkbox(t("chk_kml_tour"), value=False)
        if tour:
            st.subheader(t("hdr_tour_settings"))
            there_are_dates = st.checkbox(t("chk_has_dates"), value=False)
            if there_are_dates:
                time_column = st.selectbox(t("lbl_date_time_col"), options=headers)
            else:
                time_column = None
            tour_altitude = st.selectbox(t("lbl_tour_altitude"), options=[50, 150, 250, 300, 750, 1500, 10000], index=2)
            tour_linger_time = st.selectbox(t("lbl_linger_time"), options=[1, 2, 3, 4, 5, 10, 15], index=3)
            tour_tilt = st.selectbox(t("lbl_tour_tilt"), options=[0, 5, 10, 20], index=1)
            tour_fly_mode = st.radio(t("lbl_camera_fly"), options=["smooth", "bounce"], index=0, horizontal=True,
                                     help="Smooth = cinematic continuous flight. Bounce = camera zooms out and back in between points.")

    except AttributeError:
        st.error("Check for errors in column selection.")

    if st.button(t("btn_generate_kml")):
        try:
            # Coordinate cleaning
            valid_df, skipped_count = filter_valid_coordinates(df_in, 'LATITUDE', 'LONGITUDE')
            valid_count = len(valid_df)

            if skipped_count > 0:
                st.warning(f"⚠️ Skipped {skipped_count} record(s) missing coordinates. {valid_count} valid records will be processed.")

            if valid_count == 0:
                st.error("No valid records found for KML generation. All records are missing latitude or longitude values.")
                return

            kml = simplekml.Kml()
            Label = label_for_icons

            # --- Folder grouping by SOURCE_FILE ---
            has_source = 'SOURCE_FILE' in valid_df.columns
            folders = {}  # source_file -> simplekml.Folder

            path_coords = []  # for optional LineString

            # Shared styles: one per icon/color instead of one per placemark (much faster and smaller KML).
            point_styles, polygon_styles = {}, {}

            def point_style(kml_color):
                if kml_color not in point_styles:
                    style = simplekml.Style()
                    style.iconstyle.icon.href = selected_icon[icon]
                    if kml_color is not None:
                        style.iconstyle.color = kml_color
                    point_styles[kml_color] = style
                return point_styles[kml_color]

            def polygon_style(color):
                if color not in polygon_styles:
                    style = simplekml.Style()
                    style.polystyle.color = color
                    polygon_styles[color] = style
                return polygon_styles[color]

            for row in valid_df.to_dict('records'):
                lon, lat = float(row['LONGITUDE']), float(row['LATITUDE'])
                path_coords.append((lon, lat))

                descript = "\n".join(f"{key}: {value}" for key, value in row.items())
                lab = row[Label]

                # Pick the target container (folder or root kml)
                if has_source:
                    src = str(row.get('SOURCE_FILE', 'Unknown'))
                    if src not in folders:
                        folders[src] = kml.newfolder(name=src)
                    container = folders[src]
                else:
                    container = kml

                point = container.newpoint(name=lab, coords=[(lon, lat)], description=descript)

                # Apply icon + color
                kml_color = None
                if 'POINT_COLOR' in row and pandas.notna(row.get('POINT_COLOR')):
                    hex_color = str(row['POINT_COLOR']).lstrip('#')
                    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                    kml_color = simplekml.Color.rgb(*rgb)
                point.style = point_style(kml_color)

                if footprint and radii:
                    rad = row[radii]
                    polycircle = polycircles.Polycircle(
                        latitude=lat, longitude=lon,
                        radius=float(rad), number_of_vertices=72
                    )
                    pol = container.newpolygon(
                        name=f"{lat}, {lon}, {rad}",
                        outerboundaryis=polycircle.to_kml()
                    )
                    pol.style = polygon_style(kml_color if kml_color is not None else get_footprint_color(icon_Color=icon))

            # --- Optional travel path LineString ---
            if add_path_line and len(path_coords) >= 2:
                line = kml.newlinestring(name="Travel Path")
                line.coords = path_coords
                line.style.linestyle.color = simplekml.Color.changealphaint(180, simplekml.Color.cyan)
                line.style.linestyle.width = 3
                line.altitudemode = simplekml.AltitudeMode.clamptoground

        except Exception as e:
            st.error(f"Error generating KML: {e}")
            return

        # --- Tour: inject into the same KML object ---
        if tour:
            create_kml_tour(
                df=valid_df,
                altitude=tour_altitude, tilt=tour_tilt,
                linger=tour_linger_time, time_column=time_column,
                icon=icon, footprint=False, radii=None,  # placemarks already added above
                fly_mode=tour_fly_mode, kml_obj=kml
            )

        # --- Save & download ---
        # Built in memory: nothing is written to the server's disk.
        if output_format == "KMZ":
            dl_name = "Fetch_KML_Download.kmz"
            st.download_button("Download KMZ", data=kml_to_kmz_bytes(kml), file_name=dl_name,
                               mime="application/vnd.google-earth.kmz", on_click="ignore")
            st.success(f"KMZ file generated: {dl_name}")
        else:
            dl_name = "Fetch_KML_Download.kml"
            st.download_button("Download KML", data=kml.kml().encode("utf-8"), file_name=dl_name,
                               mime="application/vnd.google-earth.kml+xml", on_click="ignore")
            st.success(f"KML file generated: {dl_name}")
