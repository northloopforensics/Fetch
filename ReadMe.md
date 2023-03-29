A tool to help investigators convert raw data into actionable maps. 

# Version 3 is here!


![alt text](https://user-images.githubusercontent.com/73806121/228633379-85d9099e-33b9-4ccf-841f-9f012e994a85.png)

### Here is how it works:
Run the installer executable for Windows.
Fetch will be added to your Start Menu. The first run of the program will launch a small web server in the background that will prompt for permission to run.  Occasionally, a system reboot is needed to run the program. 

![alt text](https://user-images.githubusercontent.com/73806121/228640870-cfb2cb6e-9855-4c00-8890-f83359621282.png)

A browser tab will then open to Fetch.

As the tool opens you may generate a geo-fence by drawing shapes on the provided map to collect coordinates. Simply close the shape you are drawing to see the latitude and logitude for each shape you create. 

![alt text](https://user-images.githubusercontent.com/73806121/228658331-31734cbf-5ee8-4ce9-b3c3-68b76b802609.png)

OR  You can provide a data set and generate your own maps.

![alt text](https://user-images.githubusercontent.com/73806121/228634875-80765455-a23b-48a2-abe7-80dc9c930c8b.png)

If the CSV is correctly configured you will see a preview map. If not, the collapsable Manage Ingested Data window allows you to select the number of header lines to remove, filter for specific time frames, and average/consolidate points for a time interval (ex. 1 point every 5 minutes).  **The CSV file MUST contain columns labeled "Latitude" and "Longitude".**

![alt text](https://user-images.githubusercontent.com/73806121/228635721-460059b3-dab4-4f1f-b652-6c9f586df7ab.png)

Analysis Maps include points, heat map, and cell site options.

![alt text](https://user-images.githubusercontent.com/73806121/228637473-05096005-f11b-46f1-bf14-58629ef7e2c0.png)

Each of these analysis options may prompt you for additional information before data will populate. 

Remove map layers to access new helpful views.

![alt text](https://user-images.githubusercontent.com/73806121/228639100-54afb552-2309-4f5c-80a4-1e82b46ef334.png)

KML Map labels are assigned by selecting a column. Descriptions can be assigned to each location to provide additional information about that point. The data in that column will appear with map points on Google Earth.After making the appropriate selections for your data set, hit the Generate KML button.  

Below image is Google Earth output.

![alt text](https://user-images.githubusercontent.com/73806121/216791825-56539e9d-67fc-483c-b8b7-1052e5805f0b.png)

Exported KML and HTML maps will be stored in username/Documents/Fetch_Maps/

![alt text](https://user-images.githubusercontent.com/73806121/228637714-52c48ce7-6400-491c-a58e-7cd537fcab3d.png)

Below image is I.P. address query result using ipinfo.io

![alt text](https://user-images.githubusercontent.com/73806121/228654864-60173577-0cfc-4ab7-bcab-a8eabd65d764.png)

