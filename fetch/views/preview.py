"""Preview/KML page: quick preview map, CSV export, and KML/KMZ generation."""
import streamlit as st

from fetch.coords import filter_valid_coordinates
from fetch.kml_export import create_kml
from fetch.utils import csv_bytes, session_memo


def preview_page(preview_data, fp):
    try:
        if 'LATITUDE' in preview_data.columns and 'LONGITUDE' in preview_data.columns:
            clean_preview, skipped_count = session_memo(
                "preview_valid_records", fp, lambda: filter_valid_coordinates(preview_data))
            if skipped_count > 0:
                st.info(f"ℹ️ Preview map: Showing {len(clean_preview)} valid records. {skipped_count} records with missing coordinates were excluded from the map display.")
            if not clean_preview.empty:
                st.map(clean_preview, latitude='LATITUDE', longitude='LONGITUDE',
                       color='POINT_COLOR' if 'POINT_COLOR' in clean_preview.columns else None)
            else:
                st.error("No valid coordinate data available for preview map.")
        else:
            st.warning("No LATITUDE / LONGITUDE columns found — cannot render preview map.")

        # Generated only when clicked, instead of serializing the whole dataset on every rerun.
        st.download_button("Download as CSV", data=csv_bytes(preview_data), file_name="Fetch_CSV_Export.csv",
                           mime="text/csv", on_click="ignore")
    except TypeError:
        st.error("Ensure you have correct settings in Manage Ingested Data and Date/Time Filtering. Remove any non-numeric characters from your Lat/Long columns.")
    st.markdown("---")
    try:
        create_kml(df_in=preview_data)
    except Exception as e:
        st.error(f"Error generating KML: {e}")
