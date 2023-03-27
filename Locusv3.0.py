#Python3
# Place the Streamlit script to be compiled here
#This program takes data of longtitude and latitude from the csv file and plots the points on google earth.

#   TO DO - time slider is not updated when picking dates w calendar, declutter
            #remove export button from inside of maps that exports geojson files

import simplekml #the library used to map longitudes and latitudes on google earth
import pandas #used to read spreadsheet data
import re
import operator
import streamlit as st
import chardet
import os
from polycircles import polycircles
import os
import leafmap.foliumap as leafmap
from leafmap.foliumap import plugins
import geopandas
import folium
from shapely.wkt import loads
from math import asin, atan2, cos, degrees, radians, sin
from folium.plugins import Draw, Geocoder
from streamlit_folium import st_folium
import pyperclip
import datetime
import geocoder
import PySimpleGUI as sg

st.set_page_config(
   page_title="Fetch v3.0",
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
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 


### Global Variables ###
# out_file = '/Users/nlc/Desktop/test/mappy.kml'
get_headings = ""
selected_encoding = ""
icon_options = ["Yellow Paddle", "Green Paddle", "Blue Paddle", "White Paddle", "Teal Paddle", "Red Paddle", "Yellow Pushpin", "White Pushpin", "Red Pushpin", "Square"]
selected_icon = {'Square' :'http://maps.google.com/mapfiles/kml/shapes/placemark_square.png','Yellow Pushpin' : "http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png",'Red Pushpin' : "http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png",'White Pushpin' : "http://maps.google.com/mapfiles/kml/pushpin/wht-pushpin.png",'Red Paddle' : "http://maps.google.com/mapfiles/kml/paddle/red-circle.png",'Green Paddle' : "http://maps.google.com/mapfiles/kml/paddle/grn-circle.png",'Blue Paddle' : "http://maps.google.com/mapfiles/kml/paddle/blu-circle.png",'Teal Paddle' : "http://maps.google.com/mapfiles/kml/paddle/ltblu-circle.png",'Yellow Paddle' : "http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png",'White Paddle' : "http://maps.google.com/mapfiles/kml/paddle/wht-circle.png"}

####    Functions Live Here     ######

def get_point_at_distance(lat1, lon1, d, bearing, R=6371):
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
    geomap = folium.Map(zoom_start=4)
    Draw(export=True,draw_options=({'circle': False,'circlemarker':False, 'marker':False})).add_to(geomap)
    folium.TileLayer(tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr = 'Esri',
    name = 'Esri Satellite',
    overlay = False,
    control = True
    ).add_to(geomap)
    folium.LayerControl(position="topright", collapsed=True).add_to(geomap)
            
    # try:          
    #     outputmap = st_folium(geomap, width=1000, height=500,zoom=2)
    # except ValueError:
    #     print("output map error line 120")
    if len(user_geo_input) == 0:
        global search_latlng
        search_latlng = [40,-100]

    if len(user_geo_input) > 0:
        ipv4_ipv6_regex = "(^\s*((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))\s*$)|(^\s*((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\s*$)"
        
        
        if bool(re.search(ipv4_ipv6_regex, user_geo_input)) == False:   #    searches user input for alphabet if true geocode address search - false ip address search
            search_geo_results = geocoder.osm(user_geo_input)
            search_latlng = search_geo_results.latlng
            search_info_return = search_geo_results.json['address']
            zoom = 17
            
            print(search_info_return)
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
    # else:
    #     geomap = folium.Map(location=search_latlng,zoom_start=3) 
    
    outputmap = st_folium(geomap, width=1500, height=500)
    
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
        copy_dis = st.button("Copy to Clipboard")
        if copy_dis == True:
            pyperclip.copy(text_of_coords)
        
    except TypeError:
        # print("no data to populate - add some data")
        pass
            
def make_map(in_df):       #bring in pandas dataframe
    gdf = geopandas.GeoDataFrame(in_df, geometry=geopandas.points_from_xy(in_df.LONGITUDE, in_df.LATITUDE))
    
    map_Type = st.radio("Select Map Type", options=["Clustered Markers", "Circle Markers", "Heat Map", "Cell Sites"], horizontal=True)
    Map = leafmap.Map()
    #Zooms to bounds of the dataframe
    Map.zoom_to_gdf(gdf) 
    Map.add_basemap(basemap='ROADMAP')
    # Map.add_basemap(basemap='SATELLITE')
    Map.add_basemap(basemap='TERRAIN')
    Map.add_basemap(basemap='HYBRID')
    # Map.add_basemap(basemap='CartoDB.Positron')
    Map.add_basemap(basemap="CartoDB.DarkMatter") 
    # folium.TileLayer(tiles = 'https://api.mapbox.com/styles/v1/mapbox/dark-v11/tiles/1/1/0?access_token=pk.eyJ1Ijoibm9ydGhsb29wY29uc3VsdGluZyIsImEiOiJjbGU0YzcwbHUwMWxyM29wN294MXMzdmc2In0.eCdLlE9Nlu4RKqBsrUK-3g',
    # attr = 'Mapbox',
    # name = 'Dark',
    # overlay = True,
    # control = True
    # ).add_to(Map)
    
    

    if map_Type == "Clustered Markers":
        grouped_Points = Map.add_points_from_xy(gdf, x="LONGITUDE", y="LATITUDE", min_width=10,max_width=250,layer_name="Clustered Points", add_legend=False)
    
    if map_Type == "Heat Map":
        in_df.columns = in_df.columns.str.upper()
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


    if map_Type == "Circle Markers":
        st.markdown("---")
        Map.zoom_to_gdf(gdf) 
        points_or_path = st.radio(label="Select map activity", options=["Markers", "Show Point Progression"], horizontal=True)
        
        if points_or_path == "Markers":     #Shows markers only
            color = st.selectbox(label="Choose",options=['DarkRed', 'Yellow','Pink', 'Green', 'Teal', "Blue", "White"])
            circle_Points = Map.add_circle_markers_from_xy(data=gdf, x="LONGITUDE", y="LATITUDE",color=color,fill_color=color, radius=5)

        if points_or_path == "Show Point Progression":      #Shows the moving path between markers
            list_of_path_points = []    #stores coordinates from dataframe, but in long/lat format
            pathpointforreal = []       #stores corrected coordinates in lat/long form to be used by the Antpath tool
            color = st.selectbox(label="Choose",options=['DarkRed', 'Yellow','Pink', 'Green', 'Teal', "Blue", "White"])
            # date_column = st.selectbox("Select the date column", options=in_df.columns)
            # try:
            #     gdf[date_column] = pandas.to_datetime(gdf[date_column])
            # except Exception:
                # st.error("Select a column containing date data.")
            try:
                circle_Points = Map.add_circle_markers_from_xy(data=gdf, x="LONGITUDE", y="LATITUDE",color=color,fill_color=color, radius=5)
            except ValueError:
                st.error("Select")
            for index, row in gdf.iterrows():
                for pt in list(row['geometry'].coords):
                    list_of_path_points.append(pt)
            
            for ting in list_of_path_points:        #   Takes list and swaps from long/lat tuple and strings to list lat/long floats
                [longy, laty] = ting
                ltlng = (str(laty) + "," + str(longy))
                ltlng2list = [float(value) for value in ltlng.split(",")]
                # print(ltlng2list)
                pathpointforreal.append(ltlng2list)
            plugins.AntPath(locations=pathpointforreal,color=color).add_to(Map)

        #   GOTTA ORDER THE DATAFRAME BY TIME AND DATE THEN ADD THE POINTS IN ORDER TO A LIST TO BE READ BY THE ANTPATH

        
    
    if map_Type == "Cell Sites":
        gdf.columns = gdf.columns.str.upper()
        gdf.geometry = gdf["GEOMETRY"]
        st.markdown("---")

        col1, col2, col3,col4 = st.columns(4)
        with col1:
            wedge_color = st.selectbox("Sector Color", options=['Red', 'Blue', 'Green', 'Purple', 'Orange', 'DarkRed', 'Beige', 'DarkBlue', 'DarkGreen', 'CadetBlue', 'Pink', 'LightBlue', 'LightGreen', 'Gray', 'Black', 'LightGray'])
        with col2:
            # Long = st.selectbox("Longitude", options=in_df.columns)
            radii_list = ["1.5 Miles", "1 Kilometer"]
            for oto in in_df.columns:
                radii_list.append(oto)
            radii = st.selectbox("Sector Footprint Size", options=radii_list)
            if radii == "1.5 Miles":
                in_df["1.5 Miles"] = pandas.Series(2414 for x in range(len(in_df.index)))
            if radii == "1 Kilometer":
                in_df["1 Kilometer"] = pandas.Series(1000 for x in range(len(in_df.index)))


        with col3:
            Azimuth = st.selectbox("Sector Azimuth", options=in_df.columns)
            
        with col4:
            beam_width = st.selectbox("Sector Beam Width", options=in_df.columns)

        try:
            for index, row in gdf.iterrows():           #   iterates through the data frame to place points,shapes
                # print(row["LATITUDE"],row["LONGITUDE"])
                plugins.SemiCircle((row["LATITUDE"],row["LONGITUDE"]),      #wedge shape 
                radius=row[radii]/2,
                direction=row[Azimuth],
                arc=row[beam_width],
                color=None,
                fill_color=wedge_color,
                opacity=1,
                fill_opacity=.5,
                popup="Azimuth - " + str(row[Azimuth]) + " degrees, Beam width - " + str(row[beam_width]) + " degrees",
                ).add_to(Map)
                length = row[radii]/1000  #convert to meters
                # print(length/1000)
                half_beamwidth = row[beam_width] / 2
                upside =  (row[Azimuth] + half_beamwidth)  #calc angle from center of beam up
                upside %= 360       # accomodates crossing 360 degree point
                downside = (row[Azimuth] - half_beamwidth)  #calc angle from center of beam down
                downside %= 360      # accomodates crossing 360 degree point
                # print("AZ- "+str(row[Azimuth]) + " up-" + str(upside) + " down-" + str(downside))

                up_lat, up_lon = get_point_at_distance(row["LATITUDE"], row["LONGITUDE"],d=length,bearing=upside)
                dwn_lat, dwn_lon = get_point_at_distance(row["LATITUDE"], row["LONGITUDE"],d=length,bearing=downside)
                leafmap.folium.PolyLine([[row["LATITUDE"],row["LONGITUDE"]], [up_lat,up_lon]],color=wedge_color).add_to(Map)    # lines for exterior wedge shape
                leafmap.folium.PolyLine([[row["LATITUDE"],row["LONGITUDE"]], [dwn_lat,dwn_lon]],color=wedge_color).add_to(Map)

        except TypeError:
            st.info("Assign columns for Sector Footprint Size (Radius from Station in Meters), Tower Direction/Azimuth (Degrees), & Beam Width (Degrees)")
        
    Map.to_streamlit()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        sav_HTML = st.button("Export to HTML")
    with col2:
        print("")
    with col3:
        print("")
    with col4:
        print("")
    with col5:
        print("")
    if sav_HTML == True:
        if len(filename) == 0:
            st.error("Provide a map name above")
        else:
            try:
                sav_location = HTML_output_file(filename)
                Map.to_html(sav_location)
                with notices:
                    st.success("HTML file has been stored to: " + sav_location)
            except TypeError:
                print("woot")
        

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

def get_file_encoding(infile):
    return (chardet.detect(infile.read()))

    
def preview_csv(infile, outfile):       #   This facilitates the onscreen preview and KML creation
    try:
        dataf = pandas.read_csv(infile, encoding=selected_encoding)
    # dataf = dataf.applymap(lambda s: s.upper() if type(s) == str else s) #makes the frame uppercase
        n = lines_t0_remove
        if n > 0:
            dataf.columns = dataf.iloc[n-1]   
        dataf.columns = dataf.columns.str.upper()
 
        dataf = dataf[0:]
        dataf = dataf.iloc[n:]
        first_five_lines = dataf.head(6)
        first_five_lines = first_five_lines.loc[:,~first_five_lines.columns.duplicated()]
        # style_table = first_five_lines.style.hide_index()
        st.dataframe(data=first_five_lines, use_container_width=True)
        headers = dataf.columns.to_list()
        #
        return headers, dataf 
    except UnicodeError:
        st.error("Decoding error. Try another encoding method.")
        pass 

def create_kml(df_in, outfile):
    try:
        headers = df_in.columns.to_list()
    
        # print(headers)
        st.subheader("Assign Columns for KML")
        label_for_icons = st.selectbox("Map Icon Labels", options=headers)
        # print(label_for_icons)
        point_description = st.selectbox("Additional Descriptions", options=headers)
        if footprint == True:
            radii = st.selectbox("Radius/Distance-from-Point in Meters", options=headers)
        # print(point_description)
    except AttributeError:
        print("Attribute error on variable headers in createkml")
        st.error("Check for errors in column selection.")
    except UnboundLocalError:
        print("Attribute error on variable headers in createkml")
        st.error("Check for errors in column selection.")
    if KML == True:
        if len(filename) == 0:
            with notices:
                st.error("Map Name Required")
        if len(filename) > 0:
            kml = simplekml.Kml()
            Descript = point_description
            Label = label_for_icons
            
            # try:
            if footprint == True: 
                footy_color = get_footprint_color(icon_Color=icon)
                for lon, lat, lab, desc, rad in zip(df_in["LONGITUDE"], df_in["LATITUDE"], df_in[Label], df_in[Descript], df_in[radii]):  #zip with for 
            
                    lo_search = re.findall(r'([0-9.-]+).+?([0-9.-]+)', str(lon))    #regex to find what appears to be longitude, makes tuple, only provides first result of tuple
                    first_result_lo = map(operator.itemgetter(0), lo_search)
                    for i in first_result_lo:
                        long = i

                    la_search = re.findall(r'([0-9.-]+).+?([0-9.-]+)', str(lat))
                    first_result_la = map(operator.itemgetter(0), la_search)
                    for f in first_result_la:
                        lati = f

                    point = kml.newpoint(name=lab, coords= [(long, lati)], description=desc) #15(lon),15(lat) are geological coordinates of the location.     
                    point.style.iconstyle.icon.href = selected_icon[icon]
                    if footprint == True:
                        try:
                            polycircle = polycircles.Polycircle(latitude=float(lati),
                                            longitude=float(long),
                                            radius=float(rad),
                                            number_of_vertices=72)

                            pol = kml.newpolygon(name=(str(lati) + ', ' + str(long) + ', ' + str(rad)), outerboundaryis=polycircle.to_kml())
                            pol.style.polystyle.color = \
                                footy_color #changes the radius circle color
                        except ValueError:
                            with notices:
                                st.error("Value Error - Inspect Latitude, Longitude, and Radius Columns")
            if footprint == False: 
                for lon, lat, lab, desc in zip(df_in["LONGITUDE"], df_in["LATITUDE"], df_in[Label], df_in[Descript]):  #zip with for 

                    lo_search = re.findall(r'([0-9.-]+).+?([0-9.-]+)', str(lon))    #regex to find what appears to be longitude, makes tuple, only provides first result of tuple
                    first_result_lo = map(operator.itemgetter(0), lo_search)
                    for i in first_result_lo:
                        long = i

                    la_search = re.findall(r'([0-9.-]+).+?([0-9.-]+)', str(lat))
                    first_result_la = map(operator.itemgetter(0), la_search)
                    for f in first_result_la:
                        lati = f

                    point = kml.newpoint(name=lab, coords= [(long, lati)], description=desc) #15(lon),15(lat) are geological coordinates of the location.     
                    point.style.iconstyle.icon.href = selected_icon[icon]
        # except KeyError:
        #     print("There was a keyerror")

            kml.save(outfile) # To save kml file to use in google earth use:
            with notices:
                st.success("KML file has been stored to: " + outfile)

def cell_site(in_df):
    gdf = geopandas.GeoDataFrame(in_df, geometry=geopandas.points_from_xy(in_df.LONGITUDE, in_df.LATITUDE))
    gdf.columns = gdf.columns.str.upper()
    gdf.geometry = gdf["GEOMETRY"]
    col1, col2, col3,col4,col5 = st.columns(5)
    with col1:
        Lat = st.selectbox("Latitude", options=in_df.columns)
    with col2:
        Long = st.selectbox("Longitude", options=in_df.columns)
    with col3:
        radii = st.selectbox("Radius", options=in_df.columns)
    with col4:
        Azimuth = st.selectbox("Azimuth", options=in_df.columns)
    with col5:
        beam_width = st.selectbox("Beam Width", options=in_df.columns)

    Map = leafmap.Map()
    Map.zoom_to_gdf(gdf)
    Map.add_basemap(basemap='ROADMAP')
    Map.add_basemap(basemap='SATELLITE')
    Map.add_basemap(basemap='TERRAIN')
    Map.add_basemap(basemap='HYBRID')
    Map.add_basemap(basemap='CartoDB.Positron')
    Map.add_basemap(basemap="CartoDB.DarkMatter")
    
    # _Points = Map.add_circle_markers_from_xy(gdf, x="LONGITUDE", y="LATITUDE", radius=5)

    for index, row in gdf.iterrows():
        print(row["LATITUDE"],row["LONGITUDE"])
        plugins.SemiCircle((row["LATITUDE"],row["LONGITUDE"]),
        radius=row[radii],
        direction=row[Azimuth],
        arc=row[beam_width],
        color="darkred",
        fill_color="darkred",
        opacity=1,
        popup="Direction - 0 degrees, arc 90 degrees",
        ).add_to(Map)
    Map.to_streamlit()
    cell2html = st.button("Cell Map to HTML")
    if cell2html == True:
        sav_location = HTML_output_file(filename)
        Map.to_html(sav_location)
        

def time_range_slider(in_df):
 ## Range selector
    try:
        in_df[datetime_Column] = pandas.to_datetime(in_df[datetime_Column])
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
    except Exception:
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
########################################
########################################
# st.text("Investigative Mapping Tool")
# st.markdown("<h5 style='text-align: left; font-family: monaco; font-size: 72px; color: darkorange;'>  FETCH</h5>", unsafe_allow_html=True)

# st.write("An Investigative Geolocation Tool")
# st.markdown("---")


####    Main Page   ####
notices = st.empty()
filename = st.text_input(":red[Provide Map Name*]",)
uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])



if uploaded_file != None:
    with st.expander("Manage Ingested Data"):
        tabi, tabii, tabiii = st.tabs(["Review Ingest Data", "Time Filter", "Declutter"])
        with tabi:
            lines_t0_remove = st.slider(label="Number of Rows to Remove from Start of Table      (First line must include 'Latitude' and 'Longitude')", min_value=0, max_value=10)
            
            if uploaded_file != None:   
                
                suggested_encoding = get_file_encoding(uploaded_file)       #   block attempts to find csv encoding and allow manual choice
                encode_options = st.radio(label="Encoding Options", options=["Use Suggested Encoding: " + str(suggested_encoding['encoding']), "Use Manual Encoding Selection"],horizontal=True)
                if encode_options == "Use Suggested Encoding: " + str(suggested_encoding['encoding']):
                    selected_encoding = suggested_encoding['encoding']
                if encode_options == "Use Manual Encoding Selection":       
                    selected_encoding = st.selectbox("Choose File Encoding",options=["utf-8", 'utf-8-sig', 'utf-16', 'ISO-8859-1'])
            
                uploaded_file.seek(0)       #refresh action
                
                outFile = KML_output_file(filename)
                # print(outFile)
                get_headings, preview_data = preview_csv(uploaded_file, outfile=outFile)

        with tabii:
            filterbytime = st.checkbox("Filter by Date/Time")
            if filterbytime == True:
                datetime_Column = st.selectbox("Select Date/Time Column", options=preview_data.columns)
                # try:
                preview_data = time_filter(preview_data,date_column=datetime_Column)
                print(preview_data)
                # except Exception:
                #     st.error("Select column containing date/time data.")
        with tabiii:
            
            declutter_dis = st.checkbox("Consolidate points to an average location based on selected time interval.")
            if declutter_dis == True:
                try:
                    datetim_Column = st.selectbox("Choose Date/Time Column", options=preview_data.columns)
                except AttributeError:
                    st.error("Select column with Date/Time data.")
                try:
                    preview_data = declutterer(preview_data, date_column=datetim_Column)
                    print(preview_data)
                except Exception:
                    st.error("Select date/time column")

if uploaded_file == None:
    tabA, tabB = st.tabs(["Create Geofence", "Add a Data Set for More Functionality"])
    with tabA:
        make_geofence_map()
# 
if uploaded_file != None:
    if declutter_dis or filterbytime == True:
        st.markdown(":orange[FILTERS ARE IN EFFECT]")
    tab1, tab2, tab3 = st.tabs(["Preview/KML Map", "Analysis Maps", "Create Geofence"])
    with tab1:
        try:
            st.map(preview_data)
        except TypeError:
            st.error("Ensure you have correct settings in Manage CSV and Date/Time Filtering")
        icon = st.selectbox("Select Map Point Icon Style", options=icon_options)
        footprint = st.checkbox("Dataset includes radius/area information",)
        
        KML = st.button("GENERATE KML")
        st.markdown("---")
        create_kml(df_in=preview_data,outfile=outFile)
    with tab2:
        make_map(preview_data)
        
    with tab3:
        make_geofence_map()
    