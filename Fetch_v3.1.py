#Python3

import simplekml #the library used to map longitudes and latitudes on google earth
import pandas #used to read spreadsheet data
import re
import operator
import streamlit as st
import chardet      #   used to check file encodings
import os
from polycircles import polycircles     #   creates kml polygons
import leafmap.foliumap as leafmap      #   maps 
from leafmap.foliumap import plugins    #   maps
import geopandas                        
import folium                           #   maps
from math import asin, atan2, cos, degrees, radians, sin    #   calculates shapes and polygons on sphere
from folium.plugins import Draw, Geocoder       
from streamlit_folium import st_folium          #   used to create geofences
import pyperclip                        #   copies geofence coordinates to clipboard
import datetime
import geocoder                         #   search bar for geofence, api calls for address and ip lookups

st.set_page_config(
   page_title="Fetch v3.1",
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

def get_file_encoding(infile):      #checks file encoding
    return (chardet.detect(infile.read()))
 
def make_dataframe(infile, outfile):       #   changes input file to pandas dataframe
    if (".xls") in str(infile):     #   This will work for xls and xlsx file formats
        dataf = pandas.read_excel(infile)
    elif (".csv") in str(infile) or (".txt") in str(infile):
        try:
            dataf = pandas.read_csv(infile, encoding=selected_encoding)
        except UnicodeError:
            st.error("Decoding error. Try another encoding method.")
            pass 
    elif (".tsv") in str(infile):
        try:
            dataf = pandas.read_csv(infile, encoding=selected_encoding, sep=("\t"))
        except UnicodeError:
            st.error("Decoding error. Try another encoding method.")
            pass
    n = lines_t0_remove
    if n > 0:
        dataf.columns = dataf.iloc[n-1]   
    dataf.columns = dataf.columns.str.upper()
    dataf = dataf[0:]
    dataf = dataf.iloc[n:]
    first_five_lines = dataf.head(6)
    first_five_lines = first_five_lines.loc[:,~first_five_lines.columns.duplicated()]
    st.dataframe(data=first_five_lines, use_container_width=True)
    headers = dataf.columns.to_list()
    
    return headers, dataf 
        
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

####    Main Page   ####
notices = st.empty()            #   Places notifications at the top of the screen
filename = st.text_input(":red[Provide Map Name*]",)
uploaded_file = st.file_uploader("Choose a CSV, TXT (Comma Seperated), TSV, or Excel file", type=["csv","txt","tsv","xlsx","xls"], accept_multiple_files=False)

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
                get_headings, preview_data = make_dataframe(uploaded_file, outfile=outFile)

        with tabii:
            filterbytime = st.checkbox("Filter by Date/Time")
            if filterbytime == True:
                datetime_Column = st.selectbox("Select Date/Time Column", options=preview_data.columns)
                preview_data = time_filter(preview_data,date_column=datetime_Column)
                print(preview_data)
                
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
    
