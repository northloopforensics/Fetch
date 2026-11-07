"""IP Address Mapping page: extract public IPs from text and map their approximate locations."""
import pandas
import streamlit as st

from fetch.coords import filter_valid_coordinates
from fetch.geo_lookup import (cached_arcgis_result, geo_ip_to_Dataframe, get_IP_locale, invalid_ips,
                              parse_text_for_IPs)
from fetch.i18n import t
from fetch.maps import add_map_basemaps, add_point_layer, fit_to_data, new_map, render_map
from fetch.utils import csv_bytes, fragment


@fragment
def make_IPaddress_Map():   #used to map ips
    user_location = st.text_input("Place Name or Address - Use to Add a Relevant Location to the Map (Place e-mail received, point of comparison, etc)")
    ipdata = st.text_area("Input Data with IP Addresses or an E-Mail Header", height=200)
    ip_geo_button = st.button(t("btn_search"))

    if not ip_geo_button:
        return

    place = None
    if user_location.strip():
        try:
            place = cached_arcgis_result(user_location.strip())
        except Exception as e:
            st.warning(f"Could not locate place/address: {e}")

    parsed_IPs = parse_text_for_IPs(ipdata)  # Parses text for IP addresses
    ip_results = get_IP_locale(invalid_ips, parsed_IPs)  # Filters out local ip and keeps valid public ips
    datfram = geo_ip_to_Dataframe(geo_list=ip_results)
    if datfram.empty:
        st.warning("Warning: No values resembling public IP addresses were found. Check the submitted data.")

    show_these = [c for c in ('IP ADDRESS', 'STATUS', 'SERVICE PROVIDER', 'CITY', 'STATE', 'COUNTRY', 'LATITUDE', 'LONGITUDE')
                  if c in datfram.columns]
    st.dataframe(data=datfram, hide_index=True, column_order=show_these)
    st.download_button(label="Download as CSV",
                       data=csv_bytes(datfram),
                       file_name='Fetch_IP_Lookup.csv',
                       mime='text/csv',
                       on_click="ignore",
                       )

    cleandf, skipped_count = filter_valid_coordinates(datfram, 'LATITUDE', 'LONGITUDE')
    if skipped_count > 0:
        st.warning(f"⚠️ Skipped {skipped_count} IP record(s) that were missing latitude or longitude values. {len(cleandf)} valid records will be processed.")
    if cleandf.empty and place is None:
        st.error("No valid IP records found with location data.")
        return

    ipmap = new_map(zoom=2)
    add_map_basemaps(ipmap)
    if place is not None:
        place_df = pandas.DataFrame({'LATITUDE': [place.json['lat']], 'LONGITUDE': [place.json['lng']],
                                     'ADDRESS': [place.json.get('address', user_location)]})
        add_point_layer(ipmap, place_df, color='Red', radius=10, fill=True, fill_color='White', fill_opacity=1.0)
    if not cleandf.empty:
        popup_cols = [c for c in show_these if c in cleandf.columns]
        add_point_layer(ipmap, cleandf, color='Yellow', radius=5, fields=popup_cols, fill=True, fill_opacity=0.8)
        fit_to_data(ipmap, cleandf)
    render_map(ipmap, download_name="Fetch_Analysis_Map.html", download_key="dl_ip_map")
