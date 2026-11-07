"""Uploaded file parsing (CSV/TSV/Excel/GPX/KML/KMZ), EXIF photo import, and dataset assembly."""
import datetime
import hashlib
import io
import re
import xml.etree.ElementTree as ET
import zipfile
from typing import Optional

import gpxpy
import pandas
import streamlit as st

from fetch.coords import convert_coordinate_column, detect_coordinate_format
from fetch.i18n import t
from fetch.utils import fingerprint, safe_session_get, safe_session_set

LARGE_DATASET_ROWS = 100_000


def detect_and_set_header_from_rows(df: pandas.DataFrame, max_search_rows: int = 15) -> pandas.DataFrame:
    """Inspect the first `max_search_rows` rows of `df` to find a row that contains
    both latitude and longitude column labels (case-insensitive). If found, promote
    that row to be the DataFrame header and drop all rows above it. If not found,
    ensure column names are strings so downstream .str operations won't fail.

    Detection uses simple word-boundary regex for 'lat'/'latitude' and 'lon'/'longitude'.
    """
    if df is None or df.empty:
        return df

    working = df.reset_index(drop=True)
    nrows = min(len(working), max_search_rows)
    lat_pattern = r"\blat\b|\blatitude\b"
    lon_pattern = r"\blon\b|\blongitude\b"

    header_row_idx = None
    for i in range(nrows):
        # convert row values to strings and lowercase for matching
        row = working.iloc[i].astype(str).fillna("").str.lower()
        has_lat = row.str.contains(lat_pattern, regex=True, na=False).any()
        has_lon = row.str.contains(lon_pattern, regex=True, na=False).any()
        if has_lat and has_lon:
            header_row_idx = i
            break

    if header_row_idx is not None:
        # Use that row as header
        new_columns = working.iloc[header_row_idx].astype(str).str.strip().tolist()
        new_df = working.iloc[header_row_idx + 1 :].reset_index(drop=True)
        # Ensure column names are unique strings
        new_df.columns = [str(c) for c in new_columns]
        return new_df

    # If no header row found, convert existing column names to strings
    try:
        working = working.set_axis([str(c) for c in working.columns], axis=1)
    except Exception:
        pass
    return working


def extract_exif_gps(file_bytes: bytes, filename: str = '') -> Optional[dict]:
    """Extract GPS coordinates and metadata from a JPEG/TIFF image's EXIF data.
    Returns dict with LATITUDE, LONGITUDE, DATETIME, FILENAME or None.
    """
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS, GPSTAGS
        import io

        img = Image.open(io.BytesIO(file_bytes))
        exif_data = img._getexif()
        if not exif_data:
            return None

        gps_info = {}
        datetime_original = None

        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, tag_id)
            if tag_name == 'GPSInfo':
                for gps_tag_id, gps_value in value.items():
                    gps_tag_name = GPSTAGS.get(gps_tag_id, gps_tag_id)
                    gps_info[gps_tag_name] = gps_value
            elif tag_name == 'DateTimeOriginal':
                datetime_original = value
            elif tag_name == 'DateTime' and datetime_original is None:
                datetime_original = value

        if not gps_info:
            return None

        # Extract latitude
        lat_data = gps_info.get('GPSLatitude')
        lat_ref = gps_info.get('GPSLatitudeRef', 'N')
        lon_data = gps_info.get('GPSLongitude')
        lon_ref = gps_info.get('GPSLongitudeRef', 'E')

        if not lat_data or not lon_data:
            return None

        def gps_to_decimal(gps_coords, ref):
            """Convert GPS EXIF format to decimal degrees."""
            try:
                d = float(gps_coords[0])
                m = float(gps_coords[1])
                s = float(gps_coords[2])
                decimal = d + m/60.0 + s/3600.0
                if ref in ('S', 'W'):
                    decimal = -decimal
                return decimal
            except (TypeError, IndexError, ValueError):
                return None

        lat = gps_to_decimal(lat_data, lat_ref)
        lon = gps_to_decimal(lon_data, lon_ref)

        if lat is None or lon is None:
            return None

        result = {
            'LATITUDE': lat,
            'LONGITUDE': lon,
            'FILENAME': filename,
        }

        # Parse datetime if available
        if datetime_original:
            try:
                # EXIF datetime format: "2024:01:15 14:30:00"
                dt = datetime.datetime.strptime(datetime_original, '%Y:%m:%d %H:%M:%S')
                result['DATETIME'] = dt
            except (ValueError, TypeError):
                result['DATETIME'] = None
        else:
            result['DATETIME'] = None

        # Extract altitude if available
        alt = gps_info.get('GPSAltitude')
        alt_ref = gps_info.get('GPSAltitudeRef', 0)
        if alt is not None:
            try:
                altitude = float(alt)
                if alt_ref == 1:  # below sea level
                    altitude = -altitude
                result['ELEVATION'] = altitude
            except (TypeError, ValueError):
                pass

        # Extract bearing/direction if available
        img_dir = gps_info.get('GPSImgDirection')
        if img_dir is not None:
            try:
                result['BEARING'] = float(img_dir)
            except (TypeError, ValueError):
                pass

        return result

    except ImportError:
        return None
    except Exception:
        return None


def ingest_photos(uploaded_photos) -> Optional[pandas.DataFrame]:
    """Process uploaded photo files and extract GPS data.
    Returns DataFrame with LATITUDE, LONGITUDE, DATETIME, FILENAME, etc.
    """
    if not uploaded_photos:
        return None

    records = []
    errors = []
    for photo in uploaded_photos:
        try:
            photo.seek(0)
            photo_bytes = photo.read()
            result = extract_exif_gps(photo_bytes, photo.name)
            if result:
                records.append(result)
            else:
                errors.append(photo.name)
        except Exception as e:
            errors.append(f"{photo.name}: {str(e)}")

    if errors:
        st.warning(f"No GPS data found in {len(errors)} photo(s): {', '.join(errors[:5])}" +
                   (f"... and {len(errors)-5} more" if len(errors) > 5 else ""))

    if not records:
        return None

    df = pandas.DataFrame(records)
    return df


def convert_kml_2_DF(kml_file):
    if isinstance(kml_file, str):   # used for parsing kml collected from kmz
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

        # Extract ExtendedData/Data elements
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
    return df


def _parse_uploaded_file(name: str, enc: str, _upload):
    """Parse an uploaded file once per upload; returns (df or None, [(st_level, message), ...])."""
    notices = []
    lower = name.lower()
    file = io.BytesIO(_upload.getvalue())
    df = None
    # Excel files: read without inferring header so we can detect custom header rows
    if any(ext in lower for ext in [".xls", ".xlsx"]):
        try:
            df = pandas.read_excel(file, header=None)
            df = detect_and_set_header_from_rows(df, max_search_rows=15)
        except Exception:
            file.seek(0)
            df = pandas.read_excel(file)
    elif any(ext in lower for ext in [".csv", ".txt"]):
        try:
            df = pandas.read_csv(file, encoding=enc, header=None)
            df = detect_and_set_header_from_rows(df, max_search_rows=15)
        except Exception:
            file.seek(0)
            df = pandas.read_csv(file, encoding=enc)
    elif ".tsv" in lower:
        try:
            df = pandas.read_csv(file, encoding=enc, sep="\t", header=None)
            df = detect_and_set_header_from_rows(df, max_search_rows=15)
        except Exception:
            file.seek(0)
            df = pandas.read_csv(file, encoding=enc, sep="\t")
    elif ".gpx" in lower:
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
    elif ".kml" in lower:
        df = convert_kml_2_DF(file)
        df.columns = df.columns.str.upper()
        if 'LAT' in df.columns and 'LATITUDE' not in df.columns:
            df = df.rename(columns={'LAT': 'LATITUDE'})
        if 'LON' in df.columns and 'LONGITUDE' not in df.columns:
            df = df.rename(columns={'LON': 'LONGITUDE'})
    elif ".kmz" in lower:
        with zipfile.ZipFile(file, 'r') as kmz:
            kml_file_name = next((n for n in kmz.namelist() if n.endswith('.kml')), None)
            if not kml_file_name:
                return None, [("error", f"No KML file found in {name}")]
            df = convert_kml_2_DF(kmz.read(kml_file_name).decode('utf-8'))

    if df is None or df.empty:
        return None, [("warning", f"File {name} contains no data")]
    df = df.reset_index(drop=True)
    df.columns = df.columns.astype(str).str.upper()
    if len(df.columns) == 0:
        return None, [("error", f"File {name} has no valid columns")]
    df = df.loc[:, ~df.columns.duplicated()]

    if "LATITUDE" not in df.columns or "LONGITUDE" not in df.columns:
        return None, [("error", f"File {name} - first 15 rows were searched for latitude/longitude columns. None found. Data must include 'latitude' and 'longitude' columns.")]

    # --- Coordinate Format Conversion (Feature #6) ---
    for coord_col in ['LATITUDE', 'LONGITUDE']:
        fmt = detect_coordinate_format(df[coord_col])
        if fmt in ('dms', 'ddm', 'mixed'):
            notices.append(("info", f"📐 {name}: Detected **{fmt.upper()}** format in {coord_col} — converting to decimal degrees."))
            df[coord_col] = convert_coordinate_column(df[coord_col])
        elif fmt == 'decimal':
            df[coord_col] = pandas.to_numeric(df[coord_col], errors='coerce')
        else:
            df[coord_col] = convert_coordinate_column(df[coord_col])
    return df, notices



def _upload_key(upload) -> str:
    # The upload id avoids re-hashing the whole file on every rerun.
    return getattr(upload, "file_id", None) or hashlib.md5(upload.getvalue()).hexdigest()


def _parsed_uploads(uploaded_files, encoding: str) -> dict:
    """Parse each upload once per session; results are dropped when the file is removed."""
    store = st.session_state.setdefault("_fetch_parsed_uploads", {})
    current = {}
    for upload in uploaded_files:
        key = (_upload_key(upload), upload.name, encoding)
        if key not in store:
            try:
                with st.spinner(f"Reading {upload.name}..."):
                    store[key] = _parse_uploaded_file(upload.name, encoding, upload)
            except Exception as e:
                store[key] = (None, [("error", f"Error processing {upload.name}: {str(e)}")])
        current[key] = store[key]
    for stale in set(store) - set(current):
        del store[stale]
    return current


def _photo_locations(uploaded_photos):
    """EXIF extraction runs only when the set of uploaded photos changes."""
    key = tuple(_upload_key(photo) for photo in uploaded_photos)
    cached = safe_session_get("_fetch_exif_cache")
    if cached and cached[0] == key:
        return cached[1]
    photo_df = ingest_photos(uploaded_photos)
    safe_session_set("_fetch_exif_cache", (key, photo_df))
    return photo_df


def ingest_multiple_files(encoding: str = "utf-8"):
    """Render the uploaders and return (combined_df, fingerprint), or (None, None) without data.

    The combined dataset is rebuilt only when files, colors, or photos change; callers
    receive a shared object and must not mutate it in place.
    """
    uploaded_files = st.file_uploader(t("lbl_choose_files"),
                                      type=["csv", "txt", "tsv", "xlsx", "xls", "gpx", "kmz", "kml"],
                                      accept_multiple_files=True)

    # --- EXIF Photo Location Import (Feature #13) ---
    exif_df, exif_key = None, None
    with st.expander(t("msg_import_photos"), expanded=False):
        st.caption("Upload JPEG/TIFF photos to extract GPS coordinates from EXIF metadata.")
        uploaded_photos = st.file_uploader(
            "Choose photos",
            type=["jpg", "jpeg", "tiff", "tif"],
            accept_multiple_files=True,
            key="photo_uploader"
        )
        if uploaded_photos:
            try:
                photo_df = _photo_locations(uploaded_photos)
                if photo_df is not None and not photo_df.empty:
                    st.success(f"Extracted GPS data from {len(photo_df)} photo(s)")
                    st.dataframe(photo_df.head(10), width="stretch")
                    photo_color = st.color_picker("Photo point color", value="#00FF00", key="photo_color_picker")
                    exif_df = photo_df.assign(SOURCE_FILE='EXIF_Photos', POINT_COLOR=photo_color)
                    exif_df.columns = exif_df.columns.str.upper()
                    exif_key = (tuple(_upload_key(p) for p in uploaded_photos), photo_color)
                else:
                    st.warning("No GPS data could be extracted from the uploaded photos.")
            except Exception as e:
                st.error(f"Error processing photos: {str(e)}")

    if not uploaded_files:
        if exif_df is None:
            return None, None
        return exif_df, fingerprint("exif", exif_key)

    # Color selector grid, three per row
    num_cols = 3
    color_selections = {}
    for i in range(0, len(uploaded_files), num_cols):
        cols = st.columns(num_cols)
        for j, file in enumerate(uploaded_files[i:i + num_cols]):
            with cols[j]:
                st.markdown(f"**{file.name}**")
                # Deterministic, compact key derived from the filename avoids duplicate-key errors
                _digest = hashlib.md5(file.name.encode()).hexdigest()
                color_selections[file.name] = st.color_picker(
                    f"Select color for points in {file.name}",
                    value="#FF0000",
                    key=f"color_picker_{_digest}"
                )

    parsed = _parsed_uploads(uploaded_files, encoding)
    for (_, name, _), (df, notices) in parsed.items():
        for level, msg in notices:
            getattr(st, level)(msg)
    if exif_df is not None:
        st.info(f"📷 Merged {len(exif_df)} photo location(s) into dataset.")

    dataset_key = fingerprint(sorted((key, color_selections.get(key[1])) for key in parsed), exif_key)
    cached = safe_session_get("_fetch_combined")
    if cached and cached[0] == dataset_key:
        return cached[1], dataset_key

    df_list = [df.assign(SOURCE_FILE=name, POINT_COLOR=color_selections.get(name, "#FF0000"))
               for (_, name, _), (df, _) in parsed.items() if df is not None]
    if not df_list:
        st.error("No valid dataframes were ingested.")
        return None, None
    try:
        combined_df = pandas.concat(df_list, ignore_index=True, sort=False) if len(df_list) > 1 else df_list[0]
        combined_df = combined_df.loc[:, ~combined_df.columns.duplicated()]
        if exif_df is not None:
            combined_df = pandas.concat([combined_df, exif_df], ignore_index=True, sort=False)
            combined_df = combined_df.loc[:, ~combined_df.columns.duplicated()]
        combined_df = combined_df.reset_index(drop=True)
        combined_df.columns = combined_df.columns.astype(str).str.upper()
    except Exception as e:
        st.error(f"Error combining data: {str(e)}")
        return None, None
    safe_session_set("_fetch_combined", (dataset_key, combined_df))
    return combined_df, dataset_key
