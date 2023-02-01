#This program takes data of longtitude and latitude from the csv file and plots the points on google earth.

import simplekml #the library used to map longitudes and latitudes on google earth
import pandas #used to read spreadsheet data
import PySimpleGUI as sg


def kmlFunction(infile, outfile): #where infile and outfile are the two parameters
    df = pandas.read_csv(infile)
    df = df.applymap(lambda s: s.upper() if type(s) == str else s) #makes the frame uppercase
    df.columns = df.columns.str.upper()
    print(df)
    kml = simplekml.Kml()
    try:
        for lon, lat, time in zip(df["LONGITUDE"], df["LATITUDE"], df["TIMESTAMP"]):  #zip with for used to iterate two columns
            if "Â±" in lon:
                lon = lon.split("Â±")
                long = lon[0]
                accuracy = lon[1]
            if "Â±" in lat:
                lat = lat.split("Â±")
                lati = lat[0]
            else:
                lati = lat
                long = lon
            print("lat " + lati + "   Long " + long)
            point = kml.newpoint(name=time, coords= [(long, lati)]) #15(lon),15(lat) are geological coordinates of the location.
            
    except KeyError:
       print("There was a keyerror")
       
    
    kml.save(outfile) # To save kml file to use in google earth use:


sg.theme('lightgray6')  #GUI color scheme
layout = [[sg.Text("""\nThis program generates a KML file from the provided CSV file.\n\nIt requires at minimum the following exact column headings: 'Latitude', 'Longitude' & 'Timestamp'.
\n\nIf rows exist above these column headings, delete them from your working copy.\n\n""")],
        [sg.In(), sg.FileBrowse("Select CSV",file_types=("CSV Files", "*.csv"), key="-CSV-")], 
        [sg.In(), sg.FolderBrowse("Select Output Folder", key="-OUT-")],
        [sg.Button("Generate KML", key="-KML-")]]
        

#******************** BRINGS GUI & FUNCTIONS TOGETHER ********************************


# Create the Window
window = sg.Window('Snapchat CSV-2-KML', layout, no_titlebar=False, alpha_channel=1, grab_anywhere=False)

# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Exit': # if user closes window or clicks cancel
        break
    if event == '-KML-':
        in_file = values["-CSV-"]
        out_file = values["-OUT-"] + "/Snap_CSV2KML.kml"
        print(in_file + " " + out_file)
        kmlFunction(in_file, out_file)
    
    window.refresh()
window.close()
            
