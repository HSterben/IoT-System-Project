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

# GPIO Setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
LED_GPIO_PIN = 21
GPIO.setup(LED_GPIO_PIN, GPIO.OUT)

# Global variables
light_intensity = 0

# MQTT Setup
MQTT_BROKER = "172.20.10.6"
MQTT_PORT = 1883
MQTT_TOPIC = "room/light"

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    global light_intensity
    try:
        message = msg.payload.decode()
        light_intensity = int(message.split(": ")[0])
        print(f"Received message '{light_intensity}' on topic '{msg.topic}'")
    except (ValueError, IndexError) as e:
        print(f"Error processing MQTT message: {e}")

# Initialize MQTT client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

# Email Manager
class EmailManager:
    def __init__(self):
        self.EMAIL = "liamgroupiot@gmail.com"
        self.PASSWORD = "unip eiah qvyn bjbp"
        self.SERVER = "smtp.gmail.com"

    def send_email(self, intensity):
        c = datetime.now()
        current_time = c.strftime('%H:%M')
        email_content = f"Light intensity is low. LED was turned on at {current_time}."
        msg = EmailMessage()
        msg["From"] = self.EMAIL
        msg["To"] = "wliam2525@gmail.com"
        msg["Subject"] = "Light Intensity Alert"
        msg.set_content(email_content)

        with smtplib.SMTP_SSL(self.SERVER, 465) as smtp:
            smtp.login(self.EMAIL, self.PASSWORD)
            smtp.send_message(msg)

email_manager = EmailManager()

# Dash App Initialization
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SUPERHERO])
app.title = "Raspberry Pi IoT Dashboard"

# App Layout
app.layout = dbc.Container(fluid=True, children=[
    html.H1("Raspberry Pi IoT Dashboard", className="text-center my-4"),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Light Intensity and LED Status", className="text-center", style={'font-size': '24px'}),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([daq.Gauge(
                        id="light-intensity-gauge",
                        min=0,
                        max=6000,
                        value=0,
                        color={'gradient': True, 'ranges': {'red': [0, 1000], 'yellow': [1000, 3500], 'green': [3500, 6000]}}
                    )]),
                        dbc.Col([ html.Div(id="light-intensity-display", className="text-center", style={'font-size': '20px'}),
                    html.Div(id="led-status", className="text-center mt-2"),
                    html.Img(id='led-image', src='/assets/light_off.png',style={'display': 'block', 'margin': '20px auto', 'width': '100px'}),
                    html.Div(id="email-status", className="text-center mt-2")])
                     
                          ])
                    
                    
                ])
            ])
        )
    ]),
    dcc.Interval(id="update-interval", interval=2000, n_intervals=0),
    html.Footer("Powered by Raspberry Pi", className="text-center text-muted mt-4")
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

# GPIO Cleanup on exit
@app.server.before_first_request
def setup_cleanup():
    @atexit.register
    def cleanup_gpio():
        GPIO.cleanup()

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
