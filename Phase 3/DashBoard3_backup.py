import time
import dash # Dash is used for creating web applications in python 
import dash_bootstrap_components as dbc # Access to Dash bootstrap components for styling (col, row, card, etc)
import dash_daq as daq 
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
PASSWORD = "unip eiah qvyn bjbp"
SERVER = 'smtp.gmail.com'

class EmailManager:
# Send an email
#
# Takes parameter: temp as the current temperature emmited by the DHT11
# Sends an email to parameter: email_receiver
# Returns: Nothing (void)
    def send_email(self, temp, email_receiver):
        # Variable with email sender
        email_sender = self.EMAIL
        email_password = self.PASSWORD
        temp_str = str(temp)

        em = EmailMessage()
        em['From'] = email_sender
        em['To'] = email_receiver
        em['Subject'] = "Temperature Is Getting High"
        em.set_content(
            f"Hello, the current temperature is {temp_str}. Please reply 'YES' to this email if you wish to turn the fan on."
        )

        # Create a secure SSL context
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.SERVER, 465, context=context) as smtp:  # Port 465 for SMTP_SSL
            # Login into liamgroupiot@gmail.com
            smtp.login(email_sender, email_password)
            # Send the email to email_receiver
            smtp.sendmail(email_sender, email_receiver, em.as_string())

# Check the sent email's response
#
# Takes parameter: sender_email which is the email used to reply (email we sent to)
# Returns: True if the user replies 'YES' to the sent email or 'None' otherwise
    def receive_email(self, sender_email):
        # Connect to the server and go to its inbox
        mail = imaplib.IMAP4_SSL(self.SERVER)
        mail.login(self.EMAIL, self.PASSWORD)
        # Selects inbox
        mail.select('inbox')

        # Search the inbox for a specific email
        status, data = mail.search(None, 'UNSEEN', f'HEADER SUBJECT "Temperature Is Getting High"', f'HEADER FROM "{sender_email}"')

        mail_ids = []
        for block in data:
            # Transform the bytes into a list using white spaces as separator
            mail_ids += block.split()

        # Fetch each email by ID
        for i in mail_ids:
            # Fetch the email given its ID and desired format
            status, data = mail.fetch(i, '(RFC822)')

            for response_part in data:
                if isinstance(response_part, tuple):
                    # Extract the email message
                    message = email.message_from_bytes(response_part[1])
                    mail_from = message['from']
                    mail_subject = message['subject']

                    # Extract the email content
                    if message.is_multipart():
                        mail_content = ''
                        for part in message.get_payload():
                            if part.get_content_type() == 'text/plain':
                                mail_content += part.get_payload(decode=True).decode()
                    else:
                        mail_content = message.get_payload(decode=True).decode()

                    #Return  True if the user replies 'YES' to the sent email
                    return "yes" in mail_content.lower()

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
