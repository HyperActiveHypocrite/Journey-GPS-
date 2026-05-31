###################################
# Final Assignment : GPS GUI 
# Name : Andrea Martinez
# Date: 5 | 8 | 2026

#obj
'''After constructing a working GPS module that is attached to an arduino Nano, I am able to 
extract the latitude and longitude. Functions in the GUI include a start trip and end trip function and
it will construct a map with a blue line on where you went, along with displaying your latitude, longittude,
how many points in put down, how many meters, and the current status of the GPS. 

note it will not work very well in indoor settings

Credits:
Jim for teaching me how to solder
My brother for attempting to teach me how to solder

 '''



import sys
import serial
import math
import folium

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from folium.plugins import AntPath



############ Helper Function to load the style sheet qss/css ############

# opens and reads style qss file otherwise this project is ugly 
def load_stylesheet(path):
    with open(path, "r") as f:
        return f.read()


######### Libraries you may have to download ##########

"""
pip install pyserial --> this is for the arduino (communicates w/ serial ports) so we can harvest the data coming from the gps

pip install folium   // This is for the map to generate 

pip install PyQt5 // this to make your own GUI :)
"""

########################################################


#### main box, using PyQt5  ##########
class Main(QWidget):
    def __init__(self):
        super().__init__()

        # Window box set up 
        self.setGeometry(200, 200, 500, 400)
        self.setFixedSize(700, 700) #want it set to a singuar size otherwise it'd look ugly 
        self.setWindowTitle("Home made GPS")

        layout = QVBoxLayout()
        layout.setSpacing(18)
        layout.setContentsMargins(10, 20, 10, 20)

        #the title on the top of this GUI
        title = QLabel("Track Your Journey!")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)

        layout.addWidget(title)


    ############ arduino set up ###########

        #nothing is happening right now so set initials to 0 and false cause it don't exist 
        self.tracking = False
        self.points = []
        self.total_distance = 0.0
        self.last = None

        self.ser = serial.Serial('COM4', 9600, timeout=1) #my arduino nano is connected on COM4 , runs 9600 , timeout is 1 cause it crashes

        #set up timer so that GPS runs when the timer is started  --> reads arduino, updtes data, calc distance 
        self.timer = QTimer()
        self.timer.timeout.connect(self.GPS)


        #labels / display of the GPS > contains latitude, ongtitude, the pistance, how many points its putting, status of GPS
        self.LatLabel = QLabel("Latitude:\n---")
        self.LonLabel = QLabel("Longitude:\n---")
        self.DistanceLabel = QLabel("Distance:\n0 m") #Meters
        self.PointsLabel = QLabel("Points:\n0") #PUTS DOWN lots of little points
        self.StatusLabel = QLabel("Status:\nIdle")
        self.StatusLabel.setObjectName("status")

        labels = [
            self.LatLabel,
            self.LonLabel,
            self.DistanceLabel,
            self.PointsLabel,
            self.StatusLabel
        ]
            
        #set the labels to a list then to all be aligned in the center and assigned a class of card 
        for label in labels:
            label.setAlignment(Qt.AlignCenter)
            label.setProperty("class", "card")



        # box
        infoPanel = QFrame() #makes rectangular contianer , blank

        infoLayout = QVBoxLayout() #vertical layout make
        infoLayout.setSpacing(12) #12px between items space

        infoPanel.setLayout(infoLayout) # put the layout inside panel 


        #rows panel of informations
        # _______
        #|-------|
        #|Lat|lon|
        #|_______| 
        #|Dis|poi|   
        #|_______|
        #|Status |       
        #|_______|

        #row 1 --> latitude / longitutde 
        row1 = QHBoxLayout()
        row1.addWidget(self.LatLabel)
        row1.addWidget(self.LonLabel)

        #row 2 --> distance / points
        row2 = QHBoxLayout()
        row2.addWidget(self.DistanceLabel)
        row2.addWidget(self.PointsLabel)

        #row 3 --> GPS Status 
        infoLayout.addLayout(row1)
        infoLayout.addLayout(row2)
        infoLayout.addWidget(self.StatusLabel)

        #put the panel of 
        layout.addWidget(infoPanel)

        #### BUTTONS AT THE BOTTOM #### 

        #Q push button --> makes button " " adds name 

        self.StartButton = QPushButton("Start Trip") #start button 
        self.StopButton = QPushButton("Stop Trip") #stop trip button 
        self.MapButton = QPushButton("Generate Map") #generate map button 


        #make  a frame / call button panel [bottom part]
        buttonPanel = QFrame()

        #give em a box layout put it in 
        buttonLayout = QHBoxLayout()

        #15 pixels spacing between buttons 
        buttonLayout.setSpacing(15)

        # horizontal layer <----->
        buttonPanel.setLayout(buttonLayout)

        #then to the layout we add the buttons we made earlier 
        buttonLayout.addWidget(self.StartButton)
        buttonLayout.addWidget(self.StopButton)
        buttonLayout.addWidget(self.MapButton)

        # ^^ since we completed the general button panel we can now add it to our main window aka the 
        layout.addWidget(buttonPanel)


        # connect the click to start button to the startTrip()
        self.StartButton.clicked.connect(self.startTrip) # click -> runs start trip  startTrip()
        self.StopButton.clicked.connect(self.stopTrip) # runs stop trip
        self.MapButton.clicked.connect(self.GenerateMap)

        #attach main layout to Window otherwise we made the layout without putting it anywhere and then show it
        self.setLayout(layout)
        self.show()

    # HArversine formula where you calculate the distance between 2 points in the globe 
    """ Credits to : 
    Paul McWhorter on youtube 
    https://www.youtube.com/watch?v=QdyWhbJjrow 
    
    and
    
    https://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points 
    # because I had no idea what this was """
    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371000 #This is the radius of the earth!

        #point 1 -> latitude and lon
        #point 2 -> lat and lon
        #returns the distance in METERS. NOT MILES.

        # the two radiuses , the GPS is in degrees but to use trig w/ sin/cos we need it in radians
        lat1 = math.radians(lat1) #latitude 1 , convert to radIANS PLEASE
        lat2 = math.radians(lat2)

        #dlat = difference in lattitude 
        dlat = math.radians(lat2 - lat1)

        #dlon = difference in longittude 
        dlong = math.radians(lon2 - lon1)

        # to get C you need a,  boils down to radius multiplied by the c
        #apparently a is "CORE spherical geometry equation"
        a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlong/2)**2

        # you need that to find c, angle calaculation
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        #angle calculation multiplied by radius of the earth 
        return R * c


    ########## WORKING FUNCTIONS YOU CAN CALL ###############
    def startTrip(self):

        #intialize 
        self.tracking = True #if you press the button it calls the startTrip() and tracking will be set to true to be active
        self.points = [] #clears old GPS coords if there was any
        self.total_distance = 0.0 # intializes everything back to the beggining / 0 , nothing happened none
        self.last = None

        self.timer.start(1000) #1000ms , every second it wil repeat / update the GPS in this whole self running cycle --> want it in 1sec
        self.StatusLabel.setText("Status:\nTracking...") #if trip starts via timer set the status to display tracking 

    def stopTrip(self):  #calls the stopTrip() function , the tracking is set to false, it stops, then status text shows you it stopped
        self.tracking = False
        self.timer.stop()
        self.StatusLabel.setText("Status:\nStopped!")

    
    ##### READING GPS DATA FROM MY ARDUINO ######## // stores coords
    def GPS(self):
        if not self.tracking: #exits function if it isnt tracking cause we don't want an  enternal update
            return
        

        #error handling 
        try:
            #read and decode raw bytes to readable text because the arduino doesnt talk python/human language im not touching c++ , 
            # strip cause incase spaces that doesnt need to be there
            line = self.ser.readline().decode().strip()

            #seperates latitude and longitutde into 2 different parts 
            parts = line.split(",")
            # if the parts are properly split into 2 we can assign the first part as the lat and 2nd part as long 
            if len(parts) >= 2:
                lat = float(parts[0])
                lon = float(parts[1])
            #label the parts to lat and long 
                self.LatLabel.setText(f"Latitude:\n{lat}")
                self.LonLabel.setText(f"Longitude:\n{lon}")
            #adds the coordinates to the end of the trip list >> we will have a list of several coordinates throughout the trip not just one 
                self.points.append((lat, lon))
            # if we do have a last point we can calculate movement distance w/ harversine from first nd last point 
                if self.last is not None:
                    dist = self.haversine(
                        self.last[0], self.last[1],
                        lat, lon
                    ) #adds to total distance , new distance + old/curr distance
                    self.total_distance += dist
                #save current point as previous point to prepare for next update (in a literal second)
                self.last = (lat, lon)

                #now that we have all that data for distance, points, and status we can display them via text for users to read!!
                self.DistanceLabel.setText(f"Distance:\n{self.total_distance:.2f} m")
                self.PointsLabel.setText(f"Points:\n{len(self.points)}")
                self.StatusLabel.setText("Status:\nTracking...")
        #anything goes wrong tell users theres an error w/ the GPS
        except Exception:
            self.StatusLabel.setText("Status:\nGPS Error")

    
    # generate map functions via Folium library
    def GenerateMap(self):
        if len(self.points) == 0: #if there are no points in your data then there is NO gps data thus it will not make a map 
            self.StatusLabel.setText("Status:\nNo GPS data")
            return

        #creates map and start it and zoom it close on your first point GPS recorded
        m = folium.Map(location=self.points[0], zoom_start=15)
        # m is map 
        #add start marker to the first point made, add end maker to last point made, -1 to exit. add to map 
        folium.Marker(self.points[0], tooltip="Start").add_to(m)
        folium.Marker(self.points[-1], tooltip="End").add_to(m)
        #areas on the map with points is colored blue and added to map 
        folium.PolyLine(self.points, color="blue").add_to(m)
        #save the map once doneas "map.html" you can click on it even without internet and it should generate it 
        m.save("map.html")

        #save hoepfully 
        self.StatusLabel.setText("Status:\nMap Saved")



######## RUN THE PROGRAM #########
app = QApplication(sys.argv)

# loads the CSS file sheet, DOES not work if CSS apparently so renamed the file to qss and it works...?
app.setStyleSheet(load_stylesheet("style.qss"))

window = Main()
sys.exit(app.exec_())