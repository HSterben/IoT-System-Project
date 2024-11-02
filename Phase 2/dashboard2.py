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

# Creating a Dash application
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SUPERHERO])

# Layout of the app
app.layout = dbc.Container(fluid=True, children=[
    # App header
    html.H1('Raspberry Pi IoT Dashboard for Phase 2', # Title for Dashboard
            style={'font-family': 'Courier New'}, # Styling
            className='text-center text-info my-4'),
    # Temperature and Humidity Gauges
    dcc.Interval(id='update-interval', interval=120000, n_intervals=0),  # Update every 2 minutes
    dbc.Row([
        dbc.Col(daq.Gauge(id='temp-gauge', min=0, max=50, value=0, label='Temperature (°C)')),
        dbc.Col(daq.Gauge(id='humidity-gauge', min=0, max=100, value=0, label='Humidity (%)'))
    ]),
    dbc.Row([
        dbc.Col(html.Button('Send Email', id='email-button', n_clicks=0), width=4),
        dbc.Col(html.Div(id='email-status'), width=8),
    ], className="mb-4"),
    # LED Control Card
    dbc.Row([ # Create row
        dbc.Col([ # Create column
            dbc.Card([
                dbc.CardBody([
                    html.H4("LED Control", className="text-center text-white"),
                    html.H6("Toggle the LED On/Off", className="text-center text-muted mb-4"),
                    # Toggle switch used for turning led on/off
                    daq.BooleanSwitch(id='led-toggle', on=False, 
                                      style={'transform': 'scale(2)', 'margin': '0 auto'}),
                    # Display current status of LED in DIV
                    html.Div(id='led-status', className='text-center text-info', 
                             style={'font-family': 'Courier New', 'margin-top': '20px'})
                ])
                # Card body styling
            ], style={'background-color': 'rgba(255, 255, 255, 0.1)', 
                      'width': '60%', 'margin': '0 auto', 'box-shadow': '0px 4px 12px rgba(0, 0, 0, 0.4)'})
        ], width=12)
    ]),
    
    dbc.Row(
        dbc.Col([
            # Display image of LED status in row
            html.Img(id='led-image', src='/assets/light_off.png',
                     style={'display': 'block', 'margin': '20px auto', 'width': '100px'})
            ])  
        ),
    
    # Footer
    dbc.Row([
        dbc.Col([
            html.H6("Powered by Raspberry Pi", 
                    className="text-center text-muted", 
                    style={'margin-top': '30px', 'font-family': 'Courier New'})
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
    return temperature, humidity

# Callback for sending email alert
@app.callback(
    Output('email-status', 'children'),
    Input('email-button', 'n_clicks'),
    State('temp-gauge', 'value')
)
def handle_email_alert(n_clicks, current_temp):
    if n_clicks > 0:
        email_manager = EmailManager()
        email_manager.send_email(current_temp, "recipient@example.com")
        return "Email sent!"
    return ""

# Callback for checking email response to control the motor
@app.callback(
    Output('hidden-div', 'children'),
    [Input('update-interval', 'n_intervals')]
)
def check_for_email_response(_):
    email_manager = EmailManager()
    if email_manager.receive_email():
        GPIO.output([Motor1, Motor2, Motor3], [GPIO.HIGH, GPIO.LOW, GPIO.HIGH])  # Turn on the fan
    return ""

# Callback for LED toggle switch and updating LED status
@app.callback(
    [Output('led-status', 'children'), Output('led-toggle', 'on'), Output('led-image', 'src')],
    [Input('led-toggle', 'on')]
)
def update_led_status(toggle_state):
    GPIO.output(LED_PIN, GPIO.HIGH if toggle_state else GPIO.LOW)
    led_status = "LED is ON" if toggle_state else "LED is OFF"
    led_image = '/assets/light_on.png' if toggle_state else '/assets/light_off.png'
    return led_status, toggle_state, led_image

# GPIO cleanup
@app.server.before_first_request
def register_cleanup():
    @atexit.register
    def cleanup_gpio():
        GPIO.cleanup()

if __name__ == '__main__':
    app.run_server(debug=True)
