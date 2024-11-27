import time
import dash
import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import html, dcc, Input, Output
import atexit
import RPi.GPIO as GPIO
import threading
import smtplib
from email.message import EmailMessage
import paho.mqtt.client as mqtt
from datetime import datetime
import logging
import imaplib
import ssl
import sqlite3
from Freenove_DHT import DHT
import Database_setup as db
from bluepy.btle import Scanner

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

#LED Pin
LED_PIN = 25

# Motor setup
Motor1 = 17 # Enable Pin
Motor2 = 22 # Input Pin
Motor3 = 5 # Input Pin
DHT_PIN = 12

light_intensity = 0

GPIO.setup(17, GPIO.OUT)
GPIO.setup(22, GPIO.OUT)
GPIO.setup(5, GPIO.OUT)
GPIO.setup(25, GPIO.OUT)


# Initialize the DHT sensor
dht_sensor = DHT(DHT_PIN)

# MQTT Setup
MQTT_BROKER = "172.20.10.11"
MQTT_PORT = 1883
MQTT_TOPIC_LIGHT = "room/light"
MQTT_TOPIC_RFID = "rfid/user_id"

# Global threshold values with the default values.
global light_threshold, temperature_threshold, humidity_threshold
light_threshold = 400  # Default value, update as needed
temperature_threshold = 24  # Default value, update as needed
humidity_threshold = 50  # Default value, update as needed
profile_name = "Unknown"

class User:
    def __init__(self, profile_name, rfid, temp_threshold, humidity_threshold, light_intensity):
        self.profile_name = profile_name
        self.rfid = rfid
        self.temp_threshold = temp_threshold
        self.humidity_threshold = humidity_threshold
        self.light_intensity = light_intensity
    
instance_user = User(profile_name, "XX XX XX XX", temperature_threshold, humidity_threshold, light_threshold) # used for testing 


# Initialize Database
db.create_table()
db.insert_user("dashboard.db", "User1", 22, 1000, "2394F919")
db.insert_user("dashboard.db", "User2", 25, 500, "8343D4F7")




def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(MQTT_TOPIC_LIGHT)
    client.subscribe(MQTT_TOPIC_RFID)

def on_message(client, userdata, msg):
    global light_intensity, current_profile
    if msg.topic == MQTT_TOPIC_LIGHT:
        try:
            light_intensity = int(msg.payload.decode())
        except ValueError:
            print("Invalid light intensity message")
    elif msg.topic == MQTT_TOPICS_RFID:
        user_rfid = msg.payload.decode()
        user_data = db.select_user_by_rfid("dashboard.db", user_rfid)
        if user_data:
            current_profile = {
                "name": user_data[0][1],
                "temp_threshold": user_data[0][2],
                "light_threshold": user_data[0][3],
            }


# Initialize MQTT client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()


# Bluetooth notifications
BL_notification = html.Div(
    id='bluetooth',
    children=[
        dbc.Button('Find Bluetooth Devices', id='BL_button', color='primary', class_name='mr-2'),
        html.Div([
            
            html.Img(src='assets/bluetooth.png',width='60px', height='60px', style={'padding': '10px'}),
            dbc.Row([
                dbc.Col(html.H5('Bluetooth Devices Nearby'), width=3, lg=1),
                dbc.Col(html.H5('', id='bluetooth_count'), width=1, lg=1)
            ], justify="around"),
            
            dbc.Row([
                dbc.Col(html.H5('RSSI Threshold'), width=3, lg=1),
                dbc.Col(html.H5('-50', id='rssi_threshold'), width=1, lg=1)
            ], justify="around")
        ]),  
    ],
    style={'text-align': 'center'}
)

# Email Manager
class EmailManager:
    def __init__(self):
        self.EMAIL = "liamgroupiot@gmail.com"
        self.PASSWORD = "unip eiah qvyn bjbp"  # App password
        self.SERVER = 'smtp.gmail.com'
        
    def send_email(self, temp, email_receiver):
        temp_str = str(temp)
        em = EmailMessage()
        em['From'] = self.EMAIL
        em['To'] = email_receiver
        em['Subject'] = "Temperature Is Getting High"
        em.set_content(
            f"Hello, the current temperature is {temp_str}°C. Please reply 'YES' to this email if you wish to turn the fan on."
        )

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.SERVER, 465, context=context) as smtp:
            smtp.login(self.EMAIL, self.PASSWORD)
            smtp.sendmail(self.EMAIL, email_receiver, em.as_string())

    def receive_email(self, sender_email):
        mail = imaplib.IMAP4_SSL(self.SERVER)
        mail.login(self.EMAIL, self.PASSWORD)
        mail.select('inbox')

        status, data = mail.search(None, 'UNSEEN', f'HEADER SUBJECT "Temperature Is Getting High"', f'HEADER FROM "{sender_email}"')
        
        mail_ids = []
        for block in data:
            mail_ids += block.split()

        for i in mail_ids:
            status, data = mail.fetch(i, '(RFC822)')
            for response_part in data:
                if isinstance(response_part, tuple):
                    message = email.message_from_bytes(response_part[1])
                    mail_content = ''
                    if message.is_multipart():
                        for part in message.get_payload():
                            if part.get_content_type() == 'text/plain':
                                mail_content += part.get_payload(decode=True).decode()
                    else:
                        mail_content = message.get_payload(decode=True).decode()

                    return "yes" in mail_content.lower()
        return False

# Global variables
email_sent = False
motor_on = False
last_temp = 0
last_humidity = 0

# Dash application
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SUPERHERO])

app.layout = dbc.Container(fluid=True, children=[
    html.H1('Raspberry Pi IoT Dashboard Phase #2', className='text-center my-4'),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Temperature and Humidity", style={'font-size': '24px'}, className="text-center"),
                dbc.CardBody(
                    dbc.Row([
                        dbc.Col(
                            html.Div([
                                html.Label('Temperature (°C)', className='label'),  
                                daq.Gauge(
                                    id='temp-gauge', 
                                    min=0, 
                                    max=50, 
                                    value=0, 
                                    style={'margin-bottom': '1px'},
                                    color={'gradient': True, 'ranges': {'red': [0, 20], 'yellow': [20, 35], 'green': [35, 50]}}
                                ),
                                html.Div(id='temp-display', className='text-center', style={'font-size': '20px', 'margin-top': '1px', 'color': 'white'})  # Numerical temperature reading
                            ], className='card-body-center'),
                            width=6
                        ),
                        dbc.Col(
                            html.Div([
                                html.Label('Humidity (%)', className='label'),  
                                daq.Gauge(
                                    id='humidity-gauge', 
                                    min=0, 
                                    max=100, 
                                    value=0, 
                                    style={'margin-bottom': '1px'},
                                    color={'gradient': True, 'ranges': {'red': [0, 40], 'yellow': [40, 70], 'green': [70, 100]}}
                                ),
                                html.Div(id='humidity-display', className='text-center', style={'font-size': '20px', 'margin-top': '1px', 'color': 'white'})  # Numerical humidity reading
                            ], className='card-body-center'),
                            width=6
                        )
                    ])
                )
            ])
        ], width=12)
    ], className="mb-4"),
    # Fan control card
    dbc.Row([
    dbc.Col(BL_notification, width=6, lg=3),
    dbc.Col([
        dbc.Card([
            dbc.CardHeader("Fan Control", className="text-center", style={'font-size': '24px'}),
            dbc.CardBody([
                html.Img(id='fan-image', src='/assets/fan_off_spinning.png', style={'display': 'block', 'margin': '20px auto', 'width': '200px'}),
                html.Div(id='fan-status', className='text-center', children="The fan is currently turned OFF."),
            ])
        ])
    ], width=6, lg=3)
], className="mb-4"),
    dcc.Interval(
        id='update-interval',
        interval=5*1000,  # Updates every 5 seconds
        n_intervals=0
    ),
    dbc.Row([
        dbc.Col([
            html.Footer("Powered by Raspberry Pi", className="text-center text-muted", style={'margin-top': '30px'})
        ], width=12)
    ])
])

# Callbacks
@app.callback(
    [
        Output("light-intensity-gauge", "value"),
        Output("light-intensity-display", "children"),
        Output("led-status", "children"),
        Output('led-image', 'src'), 
        Output("email-status", "children")
    ],
    Input("update-interval", "n_intervals")
)
def update_dashboard(n):
    global email_sent

    # Update light intensity
    light_display = f"Current Light Intensity: {light_intensity} Lux"

    # LED and email logic
    if light_intensity < 400:
        GPIO.output(LED_GPIO_PIN, GPIO.HIGH)
        led_status = "LED is ON"
        img_src = '/assets/light_on.png' 
        #email_manager.send_email(light_intensity)
        email_thread = threading.Thread(target=email_manager.send_email, args=(light_intensity,))
        email_thread.start()
        email_sent = True
        email_status = "Email sent to notify low light intensity."
    else:
        GPIO.output(LED_GPIO_PIN, GPIO.LOW)
        led_status = "LED is OFF"
        img_src = '/assets/light_off.png' 
        email_sent = False
        email_status = ""

    return light_intensity, light_display, led_status,img_src, email_status




# Bluetooth Logic
@app.callback(
    Output("bluetooth_count", "children"),
    [Input("BL_button", "n_clicks")]
)

def update_bluetooth(n_clicks):
    if n_clicks is None:
        return "0"
    else:
        disabled = True # disable the button until the function is finished
        scanner = Scanner()
        devices = scanner.scan(10.0)
        device_list = []
        for device in devices:
            if device.rssi > -50: # and device.connectable == True:
                device_list.append(device.addr)
        disabled = False
        return f"{len(device_list)}"


#User Profile display
@app.callback(
    [Output('profile-name-display', 'children'),
     Output('profile-temperature-display', 'children'),
     Output('profile-humidity-display', 'children'),
     Output('profile-light-display', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_profile_display(n):
    global profile_name, temperature_threshold, humidity_threshold, light_threshold
    return [
        f"{profile_name}",
        f"{temperature_threshold}°C",
        f"{humidity_threshold}%",
        f"{light_threshold}"
    ]


# Callback for updating temperature, humidity data, and displaying numerical values
@app.callback(
    [Output('temp-gauge', 'value'), Output('humidity-gauge', 'value'),
     Output('temp-display', 'children'), Output('humidity-display', 'children')],
    [Input('update-interval', 'n_intervals')]
)
def update_sensor_data(_):
    global email_sent, last_temp, last_humidity

    # Read the sensor using Freenove_DHT
    if dht_sensor.readDHT11() == 0:  # Check if read was successful
        temperature = dht_sensor.getTemperature()
        humidity = dht_sensor.getHumidity()
        
        # Update last known valid readings
        last_temp = temperature
        last_humidity = humidity
        
        # Send email if temperature threshold is exceeded and email hasn't been sent
        if temperature > 20 and not email_sent:
            email_manager = EmailManager()
            email_manager.send_email(temperature, "websterliam25@gmail.com")
            email_sent = True  # Set flag to avoid re-sending the email
    else:
        # Use the last valid readings if the current read fails
        temperature = last_temp
        humidity = last_humidity

    # Return temperature, humidity, and numerical display strings
    return temperature, humidity, f"{temperature}°C", f"{humidity}%"


# Callback for checking email response and controlling the motor
@app.callback(
    [Output('fan-image', 'src'), Output('fan-status', 'children')],
    [Input('update-interval', 'n_intervals')]
)
def check_for_email_response(_):
    global motor_on
    email_manager = EmailManager()

    # Check email response if motor is not already on
    if not motor_on and email_manager.receive_email("websterliam25@gmail.com"):
        motor_on = True
        GPIO.output([Motor1, Motor2, Motor3], [GPIO.HIGH, GPIO.HIGH, GPIO.LOW])
        time.sleep(10)
        GPIO.output([Motor1, Motor2, Motor3], [GPIO.LOW, GPIO.LOW, GPIO.LOW])

    # Set the fan image and status based on motor state
    if motor_on:
        return '/assets/fan_on_spinning.png', "The fan is currently turned ON."
    return '/assets/fan_off_spinning.png', "The fan is currently turned OFF."

# GPIO cleanup
@app.server.before_first_request
def register_cleanup():
    @atexit.register
    def cleanup_gpio():
        GPIO.cleanup()

if __name__ == '__main__':
    app.run_server(debug=True)
    try:
        app.run_server(debug=True)
    finally:
        cleanup_gpio()
