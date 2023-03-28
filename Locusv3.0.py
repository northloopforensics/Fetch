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
from math import asin, atan2, cos, degrees, radians, sin
from folium.plugins import Draw, Geocoder
from streamlit_folium import st_folium
import pyperclip
import datetime
import geocoder


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
            try:
                search_geo_results = geocoder.osm(user_geo_input)
                search_latlng = search_geo_results.latlng
                search_info_return = search_geo_results.json['address']
                zoom = 17
                print(search_info_return)
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
    
