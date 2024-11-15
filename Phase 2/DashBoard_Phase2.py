import time
import dash
import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import html, dcc, Input, Output
import atexit
import RPi.GPIO as GPIO
import smtplib
import ssl
import imaplib
import email
from email.message import EmailMessage
from Freenove_DHT import DHT  # Import Freenove_DHT library

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Motor setup
Motor1 = 17 # Enable Pin
Motor2 = 22 # Input Pin
Motor3 = 5 # Input Pin
DHT_PIN = 12

GPIO.setup(17, GPIO.OUT)
GPIO.setup(22, GPIO.OUT)
GPIO.setup(5, GPIO.OUT)

# Initialize the DHT sensor
dht_sensor = DHT(DHT_PIN)  

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
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])

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
    try:
        app.run_server(debug=True)
    finally:
        cleanup_gpio()
