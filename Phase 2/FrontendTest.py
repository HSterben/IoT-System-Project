import time
import dash # Dash is used for creating web applications in python 
import dash_bootstrap_components as dbc # Access to Dash bootstrap components for styling (col, row, card, etc)
import dash_daq as daq # Access to components for designing our dashboard (BooleanSwitch)
from dash import html, dcc, Input, Output, State # Getting specific components from Dash library
import atexit # Used for cleanup and releasing resources
import RPi.GPIO as GPIO # Rasberry Pi GPIO Library
import Adafruit_DHT
import smtplib
import ssl
import imaplib
import email
from email.message import EmailMessage

GPIO.setwarnings(False) # Surpress GPIO Library warnings
GPIO.setmode(GPIO.BCM)

#Motor
Motor1 = 4 # Enable Pin
Motor2 = 5 # Input Pin
Motor3 = 18 # Input Pin
LED_PIN = 13 #Assuming GPIO13 
DHT_PIN = 24 #Assuming GPIO24


GPIO.setup([Motor1, Motor2, Motor3, LED_PIN], GPIO.OUT)



#Temperature + humidity initialization
SENSOR = Adafruit_DHT.DHT11
current_temp = 0 #Will need to be changed and updated according to the DHT11
current_humidity = 0 #Will need to be changed and updated according to the DHT11

#EMAIL
EMAIL = "liamgroupiot@gmail.com"
PASSWORD = "your_email_password"
SERVER = 'smtp.gmail.com'

class EmailManager:
    def send_email(self, temp, email_receiver):
        with smtplib.SMTP_SSL(SERVER, 465, context=ssl.create_default_context()) as smtp:
            smtp.login(EMAIL, PASSWORD)
            msg = EmailMessage()
            msg.set_content(f"Hello, the current temperature is {temp}°C. Please reply 'YES' to turn on the fan.")
            msg['Subject'] = 'Temperature Alert'
            msg['From'] = EMAIL
            msg['To'] = email_receiver
            smtp.send_message(msg)

    def receive_email(self):
        with imaplib.IMAP4_SSL(SERVER) as mail:
            mail.login(EMAIL, PASSWORD)
            mail.select('inbox')
            _, data = mail.search(None, '(UNSEEN SUBJECT "Temperature Alert")')
            for num in data[0].split():
                _, data = mail.fetch(num, '(RFC822)')
                message = email.message_from_bytes(data[0][1])
                if "yes" in message.get_payload(decode= True).decode().lower():
                    return True
        return False

#	Receive response
#	if (response == 'YES')
    #update_motor_status(toggle_state)
    #Turn on fan image

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])

app.layout = dbc.Container(fluid=True, children=[
    # App header
    html.H1('Raspberry Pi IoT Dashboard Phase #2', className='text-center my-4'),

    # Temperature and Humidity Gauges Section
     dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Temperature and Humidity", style={'backgroundColor': '#28a745', 'color': 'white'}),
                dbc.CardBody(
                    dbc.Row([
                        dbc.Col(daq.Gauge(id='temp-gauge', min=0, max=50, value=0, label='Temperature (°C)', style={'margin-bottom': '20px'}), width=6),
                        dbc.Col(daq.Gauge(id='humidity-gauge', min=0, max=100, value=0, label='Humidity (%)', style={'margin-bottom': '20px'}), width=6)
                    ])
                )
            ], style={'backgroundColor': '#3B3B3F'})  # Light green background for the card
        ], width=12)
    ], className="mb-4"),

    # Fan Control Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Fan Control", className="text-center"),
                dbc.CardBody([
                    html.Img(id='fan-image', src='/assets/fan_off.png', style={'display': 'block', 'margin': '20px auto', 'width': '100px'}),
                    html.Div(id='fan-status', className='text-center', style={'margin-top': '20px'}),
                ])
            ], style={'background-color': '#3B3B3F'})
        ], width=12)
    ], className="mb-4"),

    # Footer
    dbc.Row([
        dbc.Col([
            html.Footer("Powered by Raspberry Pi", className="text-center text-muted", style={'margin-top': '30px'})
        ], width=12)
    ])
])



# callback automatically update parts of the app when certain inputs change
# Callbacks for updating temperature and humidity data
@app.callback(
    [Output('temp-gauge', 'value'), Output('humidity-gauge', 'value')],
    [Input('update-interval', 'n_intervals')]
)
def update_sensor_data(_):
    humidity, temperature = Adafruit_DHT.read_retry(SENSOR, DHT_PIN)
    
    #check if temp is bigger than 24c
    
    if temperature > 24:
        email_manager = EmailManager()
        email_manager.send_email(temperature,"liamgroupiot@gmail.com")
    return temperature, humidity



# Callback for checking email response to control the motor
@app.callback(
    [Output('fan-image', 'src'), Output('fan-status', 'children')],
    [Input('update-interval', 'n_intervals')]
)

def check_for_email_response(_):
    email_manager = EmailManager()
    if email_manager.receive_email():
        GPIO.output([Motor1, Motor2, Motor3], [GPIO.HIGH, GPIO.LOW, GPIO.HIGH])  # Turn on the fan
        return '/assets/fan_on.png', "Fan is currently turned ON."  #updating fan image to on
    return '/assets/fan_off.png', "Fan is currently turned OFF." #default image fan off

# GPIO cleanup
@app.server.before_first_request
def register_cleanup():
    @atexit.register
    def cleanup_gpio():
        GPIO.cleanup()

if __name__ == '__main__':
    app.run_server(debug=True)
