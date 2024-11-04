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
#EMAIL = "liamgroupiot@gmail.com"
#PASSWORD = "unip eiah qvyn bjbp"
#SERVER = 'smtp.gmail.com'

class EmailManager:
    
    def __init__(self):
        self.EMAIL = "liamgroupiot@gmail.com"
        self.PASSWORD = "unip eiah qvyn bjbp"
        self.SERVER = 'smtp.gmail.com'
        
    def send_email(self, temp, email_receiver):
        # Variable with email sender
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

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])

app.layout = dbc.Container(fluid=True, children=[
    # App header
    html.H1('Raspberry Pi IoT Dashboard Phase #2', className='text-center my-4'),

    # Temperature/Humidity card section
    dbc.Row([
       
        dbc.Col([
            dbc.Card([
                # Section header
                dbc.CardHeader("Temperature and Humidity",style={'font-size': '24px'}, className="text-center"),
                dbc.CardBody(
                    dbc.Row([
                         #Temperature Gauge
                        dbc.Col(
                            html.Div([
                                   # Temp Label
                                html.Label('Temperature (°C)', className='label'),  
                                # Gauge Specifications
                                daq.Gauge(
                                    id='temp-gauge', 
                                    min=0, 
                                    max=50, 
                                    value=0, 
                                    style={'margin-bottom': '20px'},
                                    color={'gradient': True, 'ranges': {'red': [0, 20], 'yellow': [20, 35], 'green': [35, 50]}}
                                )
                            ],className='card-body-center'),
                            width=6
                        ),
                        # Humidity Gauge
                        dbc.Col(
                            html.Div([
                                html.Label('Humidity (%)', className='label'),  
                                # Gauge Specifications
                                daq.Gauge(
                                    id='humidity-gauge', 
                                    min=0, 
                                    max=100, 
                                    value=0, 
                                    style={'margin-bottom': '20px'},
                                    color={'gradient': True, 'ranges': {'red': [0, 40], 'yellow': [40, 70], 'green': [70, 100]}}
                                )
                            ],className='card-body-center'),
                            width=6
                        )
                    ])
                )
            ], )  
        ], width=12)
    ], className="mb-4"),

    # Fan control card
    dbc.Row(
        dbc.Col(
            dbc.Card([
                # Section Header
                dbc.CardHeader("Fan Control", className="text-center",style={'font-size': '24px'} ),
                dbc.CardBody([
                    # Fan image (on/off)
                    html.Img(id='fan-image', src='/assets/fan_off.png', style={'display': 'block', 'margin': '20px auto', 'width': '200px'}),
                    # Show fan status as text
                    html.Div(id='fan-status', className='text-center',children="The fan is currently turned OFF."),
                ])
            ],)  
        )
    , className="mb-4"),

    # Interval
    dcc.Interval(
        id='update-interval',
        interval=10*1000,  # Updates every 10 seconds
        n_intervals=0       # initialize counter
    ),
    
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
    
    #check if temp is bigger than 24c, if true then send warning email
    
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
    # If recieve yes email, turn on motors (fan)
    if email_manager.receive_email("liamgroupiot@gmail.com"):
        GPIO.output([Motor1, Motor2, Motor3], [GPIO.HIGH, GPIO.LOW, GPIO.HIGH])  # Turn on the fan
        return '/assets/fan_on.png', "The fan is currently turned ON."  #updating fan image to on
    return '/assets/fan_off.png', "The fan is currently turned OFF." #default image fan off

# GPIO cleanup
@app.server.before_first_request
def register_cleanup():
    @atexit.register
    def cleanup_gpio():
        GPIO.cleanup()

if __name__ == '__main__':
    app.run_server(debug=True)
