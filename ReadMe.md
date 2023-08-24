A tool to help investigators convert raw data into actionable maps. 

# Version 3 is here!

Try out the web app: https://northloopforensics-fetch-fetch-v3-5-vklwtp.streamlit.app/

![alt text](https://user-images.githubusercontent.com/73806121/228633379-85d9099e-33b9-4ccf-841f-9f012e994a85.png)

### Here is how it works:

As the tool opens you may generate a geo-fence by drawing shapes on the provided map to collect coordinates. Simply close the shape you are drawing to see the latitude and longitude for each point you create. 

![alt text](https://user-images.githubusercontent.com/73806121/228658331-31734cbf-5ee8-4ce9-b3c3-68b76b802609.png)

OR  You can provide a data set and generate your own maps.

![alt text](https://user-images.githubusercontent.com/73806121/228634875-80765455-a23b-48a2-abe7-80dc9c930c8b.png)

If the input file is correctly configured you will see a preview map. If not, the collapsable Manage Ingested Data window allows you to select the number of header lines to remove, filter for specific time frames, and average/consolidate points for a time interval (ex. 1 point every 5 minutes).  **The input file MUST contain columns labeled "Latitude" and "Longitude".**

![alt text](https://user-images.githubusercontent.com/73806121/228635721-460059b3-dab4-4f1f-b652-6c9f586df7ab.png)

Analysis Maps include points, heat map, and cell site options.

![alt text](https://user-images.githubusercontent.com/73806121/228637473-05096005-f11b-46f1-bf14-58629ef7e2c0.png)

Each of these analysis options may prompt you for additional information before data will populate. 

Remove map layers to access new helpful views.

![alt text](https://user-images.githubusercontent.com/73806121/228639100-54afb552-2309-4f5c-80a4-1e82b46ef334.png)

KML Map labels are assigned by selecting a column. Descriptions can be assigned to each location to provide additional information about that point. The data in that column will appear with map points on Google Earth.After making the appropriate selections for your data set, hit the Generate KML button.  

The below image is Google Earth output.

![alt text](https://user-images.githubusercontent.com/73806121/216791825-56539e9d-67fc-483c-b8b7-1052e5805f0b.png)

KML and HTML maps can be downloaded for later use.

![alt text](https://user-images.githubusercontent.com/73806121/228637714-52c48ce7-6400-491c-a58e-7cd537fcab3d.png)

The below image is an I.P. address query result using ipinfo.io on the Geofence page.

![alt text](https://user-images.githubusercontent.com/73806121/228654864-60173577-0cfc-4ab7-bcab-a8eabd65d764.png)

Additional support for mapping IP addresses has been added in "IP Address Mapping" allowing batch IP address searches. The best part is you don't have to weed through e-mail headers or large data sets to find the IP addresses.  Fetch will locate IP addresses and remove local addresses like 10.0.0.1 or 127.0.0.1 to query the geographic area for public facing IPs. Add your own relevant location to perhaps indicate where a victim received an email.

![alt text](https://github.com/northloopforensics/Fetch/assets/73806121/ff4c2a98-eb86-4b6c-ad9d-34aeeed25e5d)

Thanks to Jonathan Todd for contributions on GPX support!




