import time
import dash
import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import html, dcc, Input, Output
import atexit
import RPi.GPIO as GPIO
import Adafruit_DHT
import smtplib
import ssl
import imaplib
import email
from email.message import EmailMessage

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Motor
Motor1 = 4  # Enable Pin
Motor2 = 5  # Input Pin
Motor3 = 18  # Input Pin
LED_PIN = 13  # Assuming GPIO13
DHT_PIN = 24  # Assuming GPIO24

GPIO.setup([Motor1, Motor2, Motor3, LED_PIN], GPIO.OUT)

# Temperature + humidity initialization
SENSOR = Adafruit_DHT.DHT11
current_temp = 0
current_humidity = 0

# Email Manager
class EmailManager:
    
    def __init__(self):
        self.EMAIL = "liamgroupiot@gmail.com"
        self.PASSWORD = "unip eiah qvyn bjbp"  # App password
        self.SERVER = 'smtp.gmail.com'
        
    def send_email(self, temp, email_receiver):
        temp_str = str(temp)  # Make sure to convert temp to string
        em = EmailMessage()
        em['From'] = self.EMAIL
        em['To'] = email_receiver
        em['Subject'] = "Temperature Is Getting High"
        em.set_content(
            f"Hello, the current temperature is {temp_str}. Please reply 'YES' to this email if you wish to turn the fan on."
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
                                    style={'margin-bottom': '20px'},
                                    color={'gradient': True, 'ranges': {'red': [0, 20], 'yellow': [20, 35], 'green': [35, 50]}}
                                )
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
                                    style={'margin-bottom': '20px'},
                                    color={'gradient': True, 'ranges': {'red': [0, 40], 'yellow': [40, 70], 'green': [70, 100]}}
                                )
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
        interval=10*1000,  # Updates every 10 seconds
        n_intervals=0
    ),
    dbc.Row([
        dbc.Col([
            html.Footer("Powered by Raspberry Pi", className="text-center text-muted", style={'margin-top': '30px'})
        ], width=12)
    ])
])

# Callbacks for updating temperature and humidity data
@app.callback(
    [Output('temp-gauge', 'value'), Output('humidity-gauge', 'value')],
    [Input('update-interval', 'n_intervals')]
)
def update_sensor_data(_):
    humidity, temperature = Adafruit_DHT.read_retry(SENSOR, DHT_PIN)
    
    if temperature is not None and temperature > 24:
        email_manager = EmailManager()
        email_manager.send_email(temperature, "liamgroupiot@gmail.com")
    return temperature if temperature is not None else 0, humidity if humidity is not None else 0

# Callback for checking email response to control the motor
@app.callback(
    [Output('fan-image', 'src'), Output('fan-status', 'children')],
    [Input('update-interval', 'n_intervals')]
)
def check_for_email_response(_):
    email_manager = EmailManager()
    if email_manager.receive_email("liamgroupiot@gmail.com"):
        GPIO.output([Motor1, Motor2, Motor3], [GPIO.HIGH, GPIO.LOW, GPIO.HIGH])  # Turn on the fan
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
