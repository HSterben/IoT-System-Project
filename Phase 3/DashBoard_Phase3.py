import time
import dash
import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import html, dcc, Input, Output, Dash, State
import atexit
import Freenove_DHT as DHT
import RPi.GPIO as GPIO
import smtplib
import ssl
import imaplib
import email
import datetime
import paho.mqtt.client as mqtt
import easyimap as imap

from email.message import EmailMessage
from Freenove_DHT import DHT  # Import Freenove_DHT library
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Motor and LED setup
Motor1 = 4  # Enable Pin
Motor2 = 5  # Input Pin
Motor3 = 18  # Input Pin
LED_PIN = 13  # Assuming GPIO13
DHT_PIN = 17  # Assuming GPIO17 for the DHT sensor

GPIO.setup([Motor1, Motor2, Motor3, LED_PIN], GPIO.OUT)

source_address = 'liamgroupiot@gmail.com'
dest_address = 'websterliam25@gmail.com'
password = 'unip eiah qvyn bjbp'
imap_srv = 'smtp.gmail.com'
imap_port = 993

# Initialize the DHT sensor
dht_sensor = DHT(DHT_PIN)  

# Global variables
email_sent = False
motor_on = False
last_temp = 0
last_humidity = 0

# MQTT Setup
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "IoTLabPhase3/Ilan"
light_level = None  # Variable to store the light level


# Dash application
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])



def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    global light_level
    try:
        # decode payload message
        message = msg.payload.decode()
        # parse JSON payload
        light_level = int(message.split(': ')[1])
        print(f"Received message '{light_level}' on topic '{msg.topic}'")
    except ValueError as e:
        print(f"Error converting MQTT message to integer: {e}")
    except IndexError as e:
        print(f"Error splitting the message: {e}")

#SETUP MQTT CLIENT
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

# Body components
ledBox = html.Div([
    html.H3('LED Control'),
    html.Img(id='led-image', src=app.get_asset_url('lightbulb_off.png'), style={'width': '100px', 'height': '100px'}),
    html.P(id='light-level-text', children="Waiting for light level data..."),
    html.P(id='email-sent-confirmation', children='', style={'color': 'green'})
], style={'text-align': 'center'})

def send_email(subject, body):
    smtp_srv = 'smtp.gmail.com'
    smtp_port = 587
    smtp_user = source_address
    smtp_pass = password

    msg = 'Subject: {}\n\n{}'.format(subject, body)
    server = smtplib.SMTP(smtp_srv, smtp_port)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(smtp_user, smtp_pass)
    server.sendmail(smtp_user, dest_address, msg)
    server.quit()

def receive_email():
    #global emailReceived
    mail = imaplib.IMAP4_SSL(imap_srv)
    mail.login(source_address, password)
    mail.select('inbox')
    status, data = mail.search(None,
    'UNSEEN',
    'HEADER SUBJECT "Temperature is High"',
    'HEADER FROM "' + dest_address +  '"')

    mail_ids = []
    for block in data:
        mail_ids += block.split()
    for i in mail_ids:
        status, data = mail.fetch(i, '(RFC822)')
        for response_part in data:
            if isinstance(response_part, tuple):
                message = email.message_from_bytes(response_part[1])
                mail_from = message['from']
                mail_subject = message['subject']
                if message.is_multipart():
                    mail_content = ''
                    for part in message.get_payload():
                        if part.get_content_type() == 'text/plain':
                            mail_content += part.get_payload()
                else:
                    mail_content = message.get_payload().lower()
                return "yes" in mail_content.lower()

                if 'yes' in mail_content:

                    return True
                elif 'no' in mail_content:
                    emailReceived = False
                    return True
                else:
                    return False


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


app.layout = dbc.Container(fluid=True, children=[
    html.H1('Raspberry Pi IoT Dashboard Phase #3', className='text-center my-4'),
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
    dbc.Row(
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Fan Control", className="text-center", style={'font-size': '24px'}),
                dbc.CardBody([
                    html.Img(id='fan-image', src='/assets/fan_off.png', style={'display': 'block', 'margin': '20px auto', 'width': '200px'}),
                    html.Div(id='fan-status', className='text-center', children="The fan is currently turned OFF."),
                ])
            ])
        )
    , className="mb-4"),
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

# Callbacks for light level and email
@app.callback(
    [Output('email-sent-confirmation', 'children'),
     Output('light-level-text', 'children')],
    Input('interval-component', 'n_intervals')
)
def update_light_level_and_email(n):
    global emailSent
    confirmation_message = ''
    if light_level is not None:
        current_time = datetime.datetime.now().strftime("%H:%M")
        if light_level < 400 and not emailSent:
            send_email("The light is ON", f"The light is ON at {current_time} time!")
            emailSent = True
            confirmation_message = "Email has been sent!"
        elif light_level >= 400:
            emailSent = False  # Reset the email sent flag when condition is no longer met

        light_level_display = f"Current light level: {light_level}"
    else:
        light_level_display = "Waiting for light level data..."
    return confirmation_message, light_level_display


@app.callback(
    Output('led-image', 'src'),
    Input('interval-component', 'n_intervals')
)
def update_led_image(n):
    if light_level is not None:
        if light_level < 400:
            GPIO.output(40, GPIO.HIGH)
            return app.get_asset_url('lightbulb_on.png')
        else:
            GPIO.output(40, GPIO.LOW)
            return app.get_asset_url('lightbulb_off.png')
    return app.get_asset_url('lightbulb_off.png')


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
        GPIO.output([Motor1, Motor2, Motor3], [GPIO.HIGH, GPIO.LOW, GPIO.HIGH])
        time.sleep(10)
        GPIO.output([Motor1, Motor2, Motor3], [GPIO.LOW, GPIO.LOW, GPIO.LOW]) #turn off after 10 seconds

    # Set the fan image and status based on motor state
    if motor_on:
        return '/assets/fan_on.png', "The fan is currently turned ON."
    return '/assets/fan_off.png', "The fan is currently turned OFF."

# GPIO cleanup
@app.server.before_first_request
def register_cleanup():
    @atexit.register
    def cleanup_gpio():
        GPIO.cleanup()

if __name__ == '__main__':
    app.run_server(debug=True)
