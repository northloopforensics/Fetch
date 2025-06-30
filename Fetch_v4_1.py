#Python3

#This program creates geofence data based on user input and plotting locations provided in CSV, TSV, and Excel formats

#   TO DO - Time slider is not updated when picking dates w calendar, declutter
#           
#           on the analysis maps adopt point colors for multi file entries
#           if single file keep the color option

# Completed Updates:
# 1.  


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
from folium.plugins import Draw, Geocoder, TimestampedGeoJson       
from streamlit_folium import st_folium          #   used to create geofences
import datetime
import geocoder                         #   search bar for geofence, api calls for address and ip lookups
import gpxpy
import numpy as np
from dateutil import parser
import xml.etree.ElementTree as ET
import zipfile

now = datetime.datetime.now()
st.set_page_config(
   page_title="Fetch v4.0",
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

### Global Variables ###
get_headings = ""
selected_encoding = ""
icon_options = ["Yellow Paddle", "Green Paddle", "Blue Paddle", "White Paddle", "Teal Paddle", "Red Paddle", "Yellow Pushpin", "White Pushpin", "Red Pushpin", "Square"]
selected_icon = {'Square' :'http://maps.google.com/mapfiles/kml/shapes/placemark_square.png','Yellow Pushpin' : "http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png",'Red Pushpin' : "http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png",'White Pushpin' : "http://maps.google.com/mapfiles/kml/pushpin/wht-pushpin.png",'Red Paddle' : "http://maps.google.com/mapfiles/kml/paddle/red-circle.png",'Green Paddle' : "http://maps.google.com/mapfiles/kml/paddle/grn-circle.png",'Blue Paddle' : "http://maps.google.com/mapfiles/kml/paddle/blu-circle.png",'Teal Paddle' : "http://maps.google.com/mapfiles/kml/paddle/ltblu-circle.png",'Yellow Paddle' : "http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png",'White Paddle' : "http://maps.google.com/mapfiles/kml/paddle/wht-circle.png"}
invalid_ips = ['0', '10.', '127.0.0.1','172.16', '172.17', '172.18', '172.19', '172.2',  '172.21', '172.22', '172.23', '172.24', '172.25',
            '172.26', '172.27', '172.28', '172.29', '172.30',  '172.31', '192.168', '169.254', "255.255" ,"fc00"]
geo_list = []

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

    help_Box = st.expander(label="Help")
    with st.form("geoform"):
        user_geo_input = st.text_input("Street and I.P. Address Search",placeholder=None,)
        search_geo_button = st.form_submit_button("Search")
    with help_Box:
        st.write("""Use the shape elements in the map toolbar to create shapes for the geofence. \n\nOnce your geofence has been drawn, 
        the coordinates will populate below the map.  \n\nYou can add the coordinates to your clipboard to be pasted elsewhere or you 
        can save the entire page using your browser.\n\nATTENTION: Internet Protocol searches ARE NOT INDICATIVE OF THE LOCATION WHERE THE IP WAS USED. 
        THEY INDICATE A GENERAL AREA ASSOCIATED WITH THE SERVICE PROVIDER AND MAY BE COMPLETELY INACCURATE IN SOME INSTANCES. \n\nVerify 
        any addresses or locations presented by the search bar. \n\nAccuracy varies based on location.""")
    global geomap
    geomap = folium.Map(zoom_start=14)
    geomap.fit_bounds([[27,-140],[48,-59]])
    Draw(export=True,draw_options=({'circle': False,'circlemarker':False, 'marker':False})).add_to(geomap)
    folium.TileLayer(tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr = 'Esri',
    name = 'Esri Satellite',
    overlay = False,
    control = True
    ).add_to(geomap)
    folium.LayerControl(position="topright", collapsed=True).add_to(geomap)
            
    if len(user_geo_input) == 0:
        global search_latlng
        search_latlng = [40,-100]

    if len(user_geo_input) > 0:
        ipv4_ipv6_regex = "(^\s*((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))\s*$)|(^\s*((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\s*$)"
        
        
        if bool(re.search(ipv4_ipv6_regex, user_geo_input)) == False:   #    searches user input for alphabet if true geocode address search - false ip address search
            try:
                # search_geo_results = geocoder.osm(user_geo_input) # Limits are too restrictive for free use
                search_geo_results = geocoder.arcgis(user_geo_input)
                search_latlng = search_geo_results.latlng
                search_info_return = search_geo_results.json['address']
                zoom = 17
                # print(search_info_return)
            except TypeError:
                st.error("Search input produced no results")
            
        if bool(re.search(ipv4_ipv6_regex, user_geo_input)) == True:   #    searches user input for alphabet if true geocode address search - false ip address search
            search_geo_results = geocoder.ipinfo(user_geo_input)
            search_latlng = search_geo_results.latlng
            search_info_return = search_geo_results.json
            dont_show = "raw"
            ip_stats = [value for key, value in search_info_return.items() if key not in dont_show]
            zoom = 11
            st.markdown(":blue[I.P. geolocation is a rough estimate related to provider coverage, and the point provided does not indicate use/user location.]")
            st.json(search_info_return, expanded=False)
            print(search_info_return)
            
        
        try:        
            geomap = folium.Map(location=search_latlng,zoom_start=zoom)  
            folium.Marker(location=search_latlng,draggable=True,).add_to(geomap)
            Draw(export=True,draw_options=({'circle': False,'circlemarker':False, 'marker':False})).add_to(geomap)
            folium.TileLayer(tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr = 'Esri',
            name = 'Esri Satellite',
            overlay = False,
            control = True
            ).add_to(geomap)
            folium.LayerControl(position="topright", collapsed=True).add_to(geomap)
        except UnboundLocalError:
            print("geomap issue line 159")
    # else:
    #     geomap = folium.Map(location=search_latlng,zoom_start=3) 
    
    outputmap = st_folium(geomap, width=1500, height=900)
    
    try:        #   pulls the lats and longs from the returned JSON encoded map points
        parse1 = (outputmap['last_active_drawing'])
        parse2 = (parse1['geometry'])
        parse3 = (parse2['coordinates'])
        st.subheader("Geofence Coordinates")
        text_of_coords = "Latitude, Longitude\n"
        for list in parse3:
            for coord in list:
                lon, lat = coord[0], coord[1]
                text_of_coords = text_of_coords + "\n" + (str(lat) + ", " + str(lon)) + "\n"
        texting = st.write(text_of_coords)
        download_coords = st.download_button(label="Download Coordinates", data=text_of_coords, file_name="Fetch_GeoFence_Coordinates.txt")
        
    except TypeError:
        # print("no data to populate - add some data")
        pass


def parse_text_for_IPs(text):  #used to map ips
    ipv4_pattern = r'(?:\d{1,3}\.){3}\d{1,3}\b'
    ipv6_pattern = r'(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))'

    ipv4_addresses = re.findall(ipv4_pattern, text)
    ipv6_addresses = re.findall(ipv6_pattern, text)
    
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
    
    for thing in valid_only:
        try:
            pull_geo_data = geocoder.ipinfo(thing)
            
            # Check specifically for 429 error in the response
            if pull_geo_data.status_code == 429:
                st.error(f"""
                🚫 IP lookup limit reached (Error 429)
                
                The free IP geolocation service is limited to {api_limit} lookups per day.
                
                Options:
                - Wait until tomorrow when the limit resets

                If you regularly encounter this error, feel free to drop us a line to discuss financial support for this free tool.
                """)
                break
            
            # If successful, add to results
            if pull_geo_data.ok:
                lookup_count += 1
                geo_list.append(pull_geo_data.json)
                
                # Show progress every 10 lookups
                if lookup_count % 10 == 0:
                    st.info(f"✓ Processed {lookup_count} IP addresses")
            else:
                st.warning(f"⚠️ Error looking up IP {thing}: {pull_geo_data.status}")
                
        except Exception as e:
            st.warning(f"⚠️ Error processing IP {thing}: {str(e)}")
            continue
    
    return geo_list

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
        
            # Count original records
            original_count = len(datfram)
            
            cleandf = pandas.DataFrame.dropna(datfram, subset=["LONGITUDE","LATITUDE"])
            
            # Additional validation to ensure numeric values
            cleandf = cleandf[
                pandas.to_numeric(cleandf['LATITUDE'], errors='coerce').notna() &
                pandas.to_numeric(cleandf['LONGITUDE'], errors='coerce').notna()
            ].copy()
            
            # Convert to numeric and remove infinite values
            cleandf['LATITUDE'] = pandas.to_numeric(cleandf['LATITUDE'], errors='coerce')
            cleandf['LONGITUDE'] = pandas.to_numeric(cleandf['LONGITUDE'], errors='coerce')
            
            cleandf = cleandf[
                pandas.notna(cleandf['LATITUDE']) & 
                pandas.notna(cleandf['LONGITUDE']) &
                np.isfinite(cleandf['LATITUDE']) &
                np.isfinite(cleandf['LONGITUDE'])
            ]
            
            # Final dropna to ensure cleanliness
            cleandf = cleandf.dropna(subset=["LONGITUDE","LATITUDE"])
            cleandf = cleandf.reset_index()
            
            # Count valid records and notify user
            valid_count = len(cleandf)
            skipped_count = original_count - valid_count
            
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
            downloadfile = ipmap.to_html()               # for downloads
            download_test = st.download_button(label="Download HTML Map", data=downloadfile,file_name="Fetch_Analysis_Map.html")
        except UnboundLocalError:
            pass
        #     st.error("Input Data is required OR No location data was located from the provided data.")


def make_map(in_df):       #bring in pandas dataframe
    try:
        mapbox_token = "pk.eyJ1Ijoibm9ydGhsb29wY29uc3VsdGluZyIsImEiOiJjbTIyMng3ZmYwMnRyMmtvaGx6NnJvdnFpIn0.ixLwI99ZfD6vtsM_hoxDtA"
        
        # Count records before filtering
        original_count = len(in_df)
        
        # Filter out records without valid latitude or longitude FIRST
        # Also filter out any records where lat/lng are not numeric
        valid_records = in_df.dropna(subset=['LATITUDE', 'LONGITUDE']).copy()
        
        # Additional validation to ensure numeric values and remove any remaining nulls
        valid_records = valid_records[
            pandas.to_numeric(valid_records['LATITUDE'], errors='coerce').notna() &
            pandas.to_numeric(valid_records['LONGITUDE'], errors='coerce').notna()
        ].copy()
        
        # Convert to numeric to ensure proper data types and remove any non-finite values
        valid_records['LATITUDE'] = pandas.to_numeric(valid_records['LATITUDE'], errors='coerce')
        valid_records['LONGITUDE'] = pandas.to_numeric(valid_records['LONGITUDE'], errors='coerce')
        
        # Remove any infinite values
        valid_records = valid_records[
            pandas.notna(valid_records['LATITUDE']) & 
            pandas.notna(valid_records['LONGITUDE']) &
            np.isfinite(valid_records['LATITUDE']) &
            np.isfinite(valid_records['LONGITUDE'])
        ]
        
        # Final check to ensure no nulls remain
        valid_records = valid_records.dropna(subset=['LATITUDE', 'LONGITUDE'])
        
        # Update count after all filtering
        valid_count = len(valid_records)
        skipped_count = original_count - valid_count
        
        # Notify user if records were skipped
        if skipped_count > 0:
            st.warning(f"⚠️ Skipped {skipped_count} record(s) that were missing latitude or longitude values. {valid_count} valid records will be processed.")
        
        # Check if we have any valid records left
        if valid_count == 0:
            st.error("No valid records found. All records are missing latitude or longitude values.")
            return
        
        gdf = geopandas.GeoDataFrame(valid_records, geometry=geopandas.points_from_xy(valid_records.LONGITUDE, valid_records.LATITUDE))
        map_Type = st.radio("Select Map Type", options=["Clustered Markers", "Points & Trails", "Heat Map", "Cell Sites"], horizontal=True)
        Map = leafmap.Map()
        #Zooms to bounds of the dataframe
        Map.zoom_to_gdf(gdf) 
        Map.add_basemap(basemap='ROADMAP')
        # Map.add_basemap(basemap='SATELLITE')
        Map.add_basemap(basemap='TERRAIN')
        Map.add_basemap(basemap='HYBRID')
        Map.add_basemap(basemap="CartoDB.DarkMatter") 
        

        if map_Type == "Clustered Markers":
            grouped_Points = Map.add_points_from_xy(gdf, x="LONGITUDE", y="LATITUDE", min_width=10,max_width=250,layer_name="Clustered Points", add_legend=False)
        
        if map_Type == "Heat Map":
            valid_records.columns = valid_records.columns.str.upper()
            weight_type = st.radio("Select Weight Type", options=["Point Density", "Weighted Density"], horizontal=True)
            if weight_type == "Point Density":
                set_weight_to_one = gdf.assign(weight_column=1)
                # print(set_weight_to_one)
                try:
                    heatmap = Map.add_heatmap(set_weight_to_one, longitude="LONGITUDE", latitude="LATITUDE",value='weight_column',name="Heat Map", radius=25,)
                except Exception:
                    st.info("Heat Maps use weighted numeric values to accomodate issues like population density. Select column for your dataset.")

            if weight_type == "Weighted Density":
                weighted_value_column = st.selectbox("Weighted Value Column", options=gdf.columns)
                try:
                    heatmap = Map.add_heatmap(gdf, longitude="LONGITUDE", latitude="LATITUDE",value=weighted_value_column,name="Heat Map", radius=25,)
                except Exception:
                    st.info("Heat Maps use weighted numeric values to accomodate issues like population density. Select column for your dataset.")


        if map_Type == "Points & Trails":
            st.markdown("---")
            Map.zoom_to_gdf(gdf) 
            points_or_path = st.radio(label="Select map activity", options=["Markers", "Show Point Progression", "Vapour Trail"], horizontal=True)
            
            if points_or_path == "Markers":     #Shows markers only
                if "POINT_COLOR" in valid_records.columns:
                    # First add the accuracy circles with lower z-index
                    if st.checkbox("Data has Accuracy or Radius Information"):
                        radius_value = st.selectbox(label="Radius/Footprint in Meters", options=gdf.columns)
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
                        except KeyError:
                            st.error("Please select the column with the radius or accuracy information.")
                    
                    # Then add the markers with higher z-index
                    for idx, row in gdf.iterrows():
                        circle_Points = Map.add_circle_markers_from_xy(
                            data=gdf.iloc[[idx]], 
                            x="LONGITUDE", 
                            y="LATITUDE",
                            color=row["POINT_COLOR"],
                            fill_color=row["POINT_COLOR"],
                            radius=5,
                        )

                else:
                    # Similar pattern for single color points
                    color = st.selectbox(label="Choose",options=['DarkRed', 'Yellow','Pink', 'Green', 'Teal', "Blue", "White"])
                    
                    if st.checkbox("Data has Accuracy or Radius Information"):
                        radius_value = st.selectbox(label="Radius/Footprint in Meters", options=gdf.columns)
                        try:
                            for idx, row in gdf.iterrows():
                                rad_value = row[radius_value]
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
                        except KeyError:
                            st.error("Please select the column with the radius or accuracy information.")
                    
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
            
           
            if points_or_path == "Show Point Progression":      #Shows the moving path between markers
                list_of_path_points = []    #stores coordinates from dataframe, but in long/lat format
                pathpointforreal = []       #stores corrected coordinates in lat/long form to be used by the Antpath tool
                
                if "SOURCE_FILE" in valid_records.columns and "POINT_COLOR" in valid_records.columns:
                    # Group data by source file
                    grouped = valid_records.groupby('SOURCE_FILE')
                    
                    # Create markers and paths for each source file
                    for source_file, group_df in grouped:
                        # Convert group DataFrame to GeoDataFrame
                        group_gdf = geopandas.GeoDataFrame(
                            group_df, 
                            geometry=geopandas.points_from_xy(group_df.LONGITUDE, group_df.LATITUDE)
                        )
                        
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
                    # Original single-file behavior
                    color = st.selectbox(label="Choose",options=['DarkRed', 'Yellow','Pink', 'Green', 'Teal', "Blue", "White"])
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

            Azimuth = st.selectbox("Sector Azimuth", options=valid_records.columns)   
            beam_width = st.selectbox("Sector Beam Width", options=valid_records.columns, placeholder='None')
            
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

        Map.to_streamlit()
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            # sav_HTML = st.button("Export to HTML")  # for use with local save of HTML
            downloadfile = Map.to_html()               # for downloads
            download_test = st.download_button(label="Download HTML Map", data=downloadfile,file_name="Fetch_Analysis_Map.html")
        with col2:
            print("")
        with col3:
            print("")
        with col4:
            print("")
        with col5:
            print("")
    # except AttributeError:
    #     #print the full error message
       
    #     st.error("No Latitude and Longitude columns found in the data provided.")
    except ValueError:
        st.error("Invalid symbols were found in Lat/Long data columns. Please remove any non-numeric characters.")
        
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


def time_range_slider(in_df):
 ## Range selector
    try:
        in_df[datetime_Column] = pandas.to_datetime(in_df[datetime_Column])
    except ValueError:          # This is happening on the GPX inputs
        in_df[datetime_Column] = pandas.to_datetime(in_df[datetime_Column], utc=True)
        in_df[datetime_Column] = in_df[datetime_Column].dt.tz_convert('UTC')

    try:
        format = 'YYYY-MM-DD'  # format output
        start_date = min(in_df[datetime_Column]).to_pydatetime()    # get start date of data frame
        end_date = max(in_df[datetime_Column]).to_pydatetime()      # get end date of data frame
        slider = st.slider('Select Date (YYYY-MM-DD)', min_value=start_date, value=(start_date,end_date) ,max_value=end_date, format=format)
        return slider   #kicks out start and end datetime
    except TypeError:
        st.error("slider error")

def time_filter(in_df, date_column):
    try:
        starting, ending = time_range_slider(in_df=in_df)
        sorted = in_df.sort_values(by=date_column)
        # print(sorted)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
                start_date = st.date_input("Start Date",value=starting)     
        with col2:
                start_time = st.time_input("Start Time", value=datetime.time(0, 00, 00))
        with col3:
                end_date = st.date_input("End Date",value=ending)
        with col4:
                end_time = st.time_input("End Time", value=datetime.time(23, 59, 59))
        first_is = str(start_date) + " " + str(start_time)
        last_is = str(end_date) + " " + str(end_time)
        selected_time = sorted[(sorted[date_column] > first_is) & (sorted[date_column] < last_is)]
        st.markdown(":orange[Filtered Records:]  " + str(len(selected_time.index)))
        st.table(selected_time)
        return selected_time
    except parser.ParserError:
        st.error("Select column with Date/Time data.")

def declutterer(in_df, date_column):
    # resample every N minutes to get a mean value for lat and long.
    #     Sample Frequency cheatsheet
    # B         business day frequency
    # C         custom business day frequency (experimental)
    # D         calendar day frequency
    # W         weekly frequency
    # M         month end frequency
    # SM        semi-month end frequency (15th and end of month)
    # BM        business month end frequency
    # CBM       custom business month end frequency
    # MS        month start frequency
    # SMS       semi-month start frequency (1st and 15th)
    # BMS       business month start frequency
    # CBMS      custom business month start frequency
    # Q         quarter end frequency
    # BQ        business quarter endfrequency
    # QS        quarter start frequency
    # BQS       business quarter start frequency
    # A         year end frequency
    # BA, BY    business year end frequency
    # AS, YS    year start frequency
    # BAS, BYS  business year start frequency
    # BH        business hour frequency
    # H         hourly frequency
    # T, min    minutely frequency
    # S         secondly frequency
    # L, ms     milliseconds
    # U, us     microseconds
    # N         nanoseconds
    in_df[date_column] = pandas.to_datetime(in_df[date_column])
    declutter_data = in_df.set_index(date_column)
    Time_intervals = { "Year": "A", "Month": "M", "Week": "W", "Day": "D", "Hour" : "H", "Minute": "T","Second": "S"}
    spot1, spot2, spot3, spot4 = st.columns(4)
    with spot1:
        count_of_time = st.number_input("Interval Count", min_value=1, max_value=60,)
    with spot2:
        choose_interval = st.selectbox("Interval Type", options=list(Time_intervals.keys()))
    resample_Rate = str(count_of_time) + Time_intervals[choose_interval]
    print(resample_Rate)
    declutter_data = declutter_data.resample(resample_Rate).agg({'LATITUDE': 'mean', 'LONGITUDE': 'mean'})
    declutter_data = declutter_data[declutter_data['LATITUDE'].notna()]
    st.markdown(":orange[Number of Averaged Locations:]  " + str(len(declutter_data.index)))
    # declutter_data = in_df.resample("5D").mean()
    return declutter_data

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
                color_selections[file.name] = st.color_picker(
                    f"Select color for points in {file.name}", 
                    value="#FF0000", 
                    key=f"color_picker_{file.name}"
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
            df = df.copy().reset_index(drop=True)
            
            # Standardize column names and remove duplicates
            df.columns = df.columns.str.upper()
            df = df.loc[:, ~df.columns.duplicated()]
            
            # Add source tracking
            df["SOURCE_FILE"] = file.name
            df["POINT_COLOR"] = color_selections.get(file.name, "#FF0000")
            
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
    preview_data = combined_df
        

if preview_data is not None:
    with st.expander("Manage Ingested Data"):
        tabi, tabii, tabiii = st.tabs(["Review Ingest Data","Time Filter","Declutter"])
        with tabi:
    
            # Existing code for lines to remove
            lines_t0_remove = st.slider(
                label="Number of Rows to Remove from Start of Table (First line must include 'Latitude' and 'Longitude')", 
                min_value=0, 
                max_value=10
            )            

           
        with tabii:
            filterbytime = st.checkbox("Filter by Date/Time")
            if filterbytime == True:
                datetime_Column = st.selectbox("Select Date/Time Column", options=preview_data.columns)
                preview_data = time_filter(preview_data,date_column=datetime_Column)
                
        with tabiii:
            declutter_dis = st.checkbox("Consolidate points to an average location based on selected time interval.")
            if declutter_dis == True:
                try:
                    datetim_Column = st.selectbox("Choose Date/Time Column", options=preview_data.columns)
                except AttributeError:
                    st.error("Select column with Date/Time data.")
                try:
                    preview_data = declutterer(preview_data, date_column=datetim_Column)
                    
                except Exception:
                    st.error("Select date/time column")

if preview_data is None:
    tabA, tabB = st.tabs(["Create Geofence", "IP Address Mapping"])
    with tabA:
        make_geofence_map()
    with tabB:
        make_IPaddress_Map()
        

if preview_data is not None:
    if declutter_dis or filterbytime == True:
        st.markdown(":orange[FILTERS ARE IN EFFECT]")
    tab1, tab2, tab3 = st.tabs(["Preview/KML Map", "Analysis Maps", "Create Geofence"])
    with tab1:
        try:
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
st.markdown(":orange[© 2025 North Loop Consulting - Fetch_v4.0]")
