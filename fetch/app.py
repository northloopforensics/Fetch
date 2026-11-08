"""App entrypoint: page setup, data loading, Manage Ingested Data, and page navigation."""
import streamlit as st

from fetch.branding import LOGO_PNG_BASE64
from fetch.data_manager import manage_ingested_data
from fetch.i18n import t
from fetch.ingest import LARGE_DATASET_ROWS, ingest_multiple_files

APP_VERSION = "5.4"
LANGUAGES = {"English": "en", "Español": "es", "Português": "pt", "Deutsch": "de", "Русский": "ru"}

PAGE_STYLE = """
<style>
div.stButton > button:first-child {
    background-color: #ff0000;
    color:#ffffff;
}
div.stButton > button:hover {
    background-color: #8b0000;
    color:#ff0000;
}
#MainMenu {visibility: visible;}
footer {visibility: hidden;}
</style>"""

PRIVACY_STATEMENT = """
## Data Privacy Statement and API Usage Information

We take your privacy seriously. North Loop Consulting will only have temporary access to small portions of data that may be involved in error reporting.  
This data will not be stored for any period longer than needed to identify and correct any issues, if at all.
            
We make use of a third party company, Streamlit, to provide hosting for Fetch.  
For more information about Streamlit and their handling of user data, please refer to their [Privacy Policy](https://streamlit.io/privacy-policy).

For specific information about how Streamlit handles data sets you have uploaded as files, please refer to their 
[documents on file uploads](https://docs.streamlit.io/knowledge-base/using-streamlit/where-file-uploader-store-when-deleted).

It is always best to avoid uploading sensitive data to any online service. Please do not upload any data that may contain personal identifiable information or sensitive data.

Fetch is intended to be a free tool available to everyone.  To do this, free resources are used to return information like IP address data.  There are caps on this free usage.  You may run into periods where that cap has been met and these resources are not available. If you would like to explore financial support for the tool to expand these capabilities, I am open to the conversation. Just reach out via the Contact Page on our site.   
"""


def _header():
    header_col, lang_col = st.columns([7, 1])
    with header_col:
        st.markdown(f"<img src='data:image/png;base64,{LOGO_PNG_BASE64}' class='img-fluid'>", unsafe_allow_html=True)
    with lang_col:
        lang = st.selectbox("🌐", list(LANGUAGES), key="_ui_lang_sel", label_visibility="collapsed")
        st.session_state["_ui_lang_code"] = LANGUAGES[lang]
    st.markdown(PAGE_STYLE, unsafe_allow_html=True)


def main():
    st.set_page_config(
        page_title=f"Fetch v{APP_VERSION}",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={}
    )
    _header()

    data, fp = ingest_multiple_files()
    filters_active = False
    if data is not None:
        if len(data) > LARGE_DATASET_ROWS:
            st.warning(f"⚠️ Large dataset detected ({len(data):,} rows). Map rendering and analysis may be slow. Consider filtering or sampling your data.")
        data, fp, filters_active = manage_ingested_data(data, fp)

    # Page modules are imported lazily, so only the libraries the selected page needs are loaded.
    def preview_kml():
        from fetch.views.preview import preview_page
        preview_page(data, fp)

    def analysis_maps():
        from fetch.views.analysis_map import make_map
        try:
            make_map(data, fp)
        except AttributeError:
            st.error(t("msg_check_lat_lon"))

    def create_geofence():
        from fetch.views.geofence import make_geofence_map
        make_geofence_map()

    def advanced_analysis():
        from fetch.views.advanced import advanced_page
        advanced_page(data, fp)

    def ip_mapping():
        from fetch.views.ip_mapping import make_IPaddress_Map
        make_IPaddress_Map()

    if data is not None:
        pages = [
            st.Page(preview_kml, title=t("tab_preview_kml"), url_path="preview"),
            st.Page(analysis_maps, title=t("tab_analysis_maps"), url_path="analysis-maps", default=True),
            st.Page(create_geofence, title=t("tab_create_geofence"), url_path="geofence"),
            st.Page(advanced_analysis, title=t("tab_advanced_analysis"), url_path="advanced-analysis"),
            st.Page(ip_mapping, title=t("tab_ip_mapping"), url_path="ip-mapping"),
        ]
    else:
        pages = [
            st.Page(create_geofence, title=t("tab_geofence"), url_path="geofence", default=True),
            st.Page(ip_mapping, title=t("tab_ip_mapping"), url_path="ip-mapping"),
        ]
    page = st.navigation(pages, position="top")
    has_data = data is not None
    data_just_loaded = has_data and not st.session_state.get("_fetch_navigation_has_data", False)
    st.session_state["_fetch_navigation_has_data"] = has_data
    if data_just_loaded:
        st.switch_page(pages[1])
    if filters_active:
        st.markdown(":orange[Filters are active]")
    page.run()

    st.markdown("---")
    with st.expander("Privacy Statement and API Use"):
        st.write(PRIVACY_STATEMENT)
    st.markdown(f":orange[© 2026 North Loop Consulting - Fetch_v{APP_VERSION}]")
