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
from Freenove_DHT import DHT
import Database_setup as db

# GPIO Setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Pins
LED_PIN = 25
MOTOR_PINS = [17, 22, 5]
DHT_PIN = 12

GPIO.setup(LED_PIN, GPIO.OUT)
for pin in MOTOR_PINS:
    GPIO.setup(pin, GPIO.OUT)

# MQTT Setup
MQTT_BROKER = "172.20.10.6"
MQTT_PORT = 1883
MQTT_TOPICS = {"light": "room/light", "rfid": "rfid/user_id"}

# Global variables
light_intensity = 0
temperature = 0
humidity = 0
email_sent = False
motor_on = False
current_profile = {"name": "Unknown", "temp_threshold": 24, "light_threshold": 400}

# Initialize DHT Sensor
dht_sensor = DHT(DHT_PIN)

# Initialize Database
db.create_table()
db.insert_user("dashboard.db", "User1", 22, 1000, "2394F919")
db.insert_user("dashboard.db", "User2", 25, 500, "8343D4F7")

# Email Manager
class EmailManager:
    def __init__(self):
        self.EMAIL = "liamgroupiot@gmail.com"
        self.PASSWORD = "unip eiah qvyn bjbp"
        self.SERVER = "smtp.gmail.com"

    def send_email(self, subject, content, recipient):
        msg = EmailMessage()
        msg["From"] = self.EMAIL
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.set_content(content)

        with smtplib.SMTP_SSL(self.SERVER, 465) as smtp:
            smtp.login(self.EMAIL, self.PASSWORD)
            smtp.send_message(msg)

email_manager = EmailManager()

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    for topic in MQTT_TOPICS.values():
        client.subscribe(topic)

def on_message(client, userdata, msg):
    global light_intensity, current_profile
    if msg.topic == MQTT_TOPICS["light"]:
        try:
            light_intensity = int(msg.payload.decode())
        except ValueError:
            print("Invalid light intensity message")
    elif msg.topic == MQTT_TOPICS["rfid"]:
        user_rfid = msg.payload.decode()
        user_data = db.select_user_by_rfid("dashboard.db", user_rfid)
        if user_data:
            current_profile = {
                "name": user_data[0][1],
                "temp_threshold": user_data[0][2],
                "light_threshold": user_data[0][3],
            }

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

# Dash App Initialization
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SUPERHERO])

# App Layout
app.layout = dbc.Container(fluid=True, children=[
    html.H1("Raspberry Pi IoT Dashboard", className="text-center my-4"),
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("Light Intensity and LED Status"),
            dbc.CardBody([
                daq.Gauge(id="light-intensity-gauge", min=0, max=6000, value=0, color={'gradient': True}),
                html.Div(id="light-intensity-display", className="text-center mt-2"),
                html.Div(id="led-status", className="text-center mt-2"),
                html.Img(id="led-image", src="/assets/light_off.png", className="center"),
            ])
        ]), width=6),
        dbc.Col(dbc.Card([
            dbc.CardHeader("Temperature and Humidity"),
            dbc.CardBody([
                daq.Gauge(id="temp-gauge", min=0, max=50, value=0, color={'gradient': True}),
                html.Div(id="temp-display", className="text-center mt-2"),
                daq.Gauge(id="humidity-gauge", min=0, max=100, value=0, color={'gradient': True}),
                html.Div(id="humidity-display", className="text-center mt-2"),
            ])
        ]), width=6),
    ]),
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("Fan Control"),
            dbc.CardBody([
                html.Img(id="fan-image", src="/assets/fan_off.png", className="center"),
                html.Div(id="fan-status", className="text-center mt-2"),
            ])
        ]), width=6),
    ]),
    dcc.Interval(id="update-interval", interval=2000, n_intervals=0),
])

# Callbacks
@app.callback(
    [
        Output("light-intensity-gauge", "value"),
        Output("light-intensity-display", "children"),
        Output("led-status", "children"),
        Output("led-image", "src"),
    ],
    Input("update-interval", "n_intervals"),
)
def update_light(n):
    if light_intensity < current_profile["light_threshold"]:
        GPIO.output(LED_PIN, GPIO.HIGH)
        led_status = "LED is ON"
        led_img = "/assets/light_on.png"
        email_manager.send_email("Low Light Intensity", "LED turned on.", "websterliam25@gmail.com")
    else:
        GPIO.output(LED_PIN, GPIO.LOW)
        led_status = "LED is OFF"
        led_img = "/assets/light_off.png"
    return light_intensity, f"{light_intensity} Lux", led_status, led_img

@app.callback(
    [
        Output("temp-gauge", "value"),
        Output("temp-display", "children"),
        Output("humidity-gauge", "value"),
        Output("humidity-display", "children"),
    ],
    Input("update-interval", "n_intervals"),
)
def update_temp_humidity(n):
    if dht_sensor.readDHT11() == 0:
        temp = dht_sensor.getTemperature()
        hum = dht_sensor.getHumidity()
        if temp > current_profile["temp_threshold"] and not email_sent:
            email_manager.send_email("High Temperature", f"Current Temp: {temp}", "websterliam25@gmail.com")
    else:
        temp = humidity = 0
    return temp, f"{temp}°C", hum, f"{hum}%"

@app.callback(
    [
        Output("fan-image", "src"),
        Output("fan-status", "children"),
    ],
    Input("update-interval", "n_intervals"),
)
def control_fan(n):
    global motor_on
    if motor_on:
        GPIO.output(MOTOR_PINS, GPIO.HIGH)
        return "/assets/fan_on.png", "Fan is ON"
    else:
        GPIO.output(MOTOR_PINS, GPIO.LOW)
        return "/assets/fan_off.png", "Fan is OFF"

# GPIO Cleanup
@atexit.register
def cleanup():
    GPIO.cleanup()

if __name__ == "__main__":
    app.run_server(debug=True)
