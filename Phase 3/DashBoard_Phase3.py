import time
import dash
import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import html, dcc, Input, Output, State
import atexit
import RPi.GPIO as GPIO
import threading
import email
from email.message import EmailMessage
import smtplib
import ssl
import imaplib
import paho.mqtt.client as mqtt

# GPIO Setup
GPIO.setwarnings(False)
LED_GPIO_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_GPIO_PIN, GPIO.OUT)

source_address = 'liamgroupiot@gmail.com'
dest_address = 'websterliam25@gmail.com'
password = 'unip eiah qvyn bjbp'
imap_srv = 'smtp.gmail.com'
imap_port = 993

# Global variables for light data

light_intensity = 0
email_sent = False
motor_on = False

# MQTT Setup
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "IoTLabPhase3/Ilan"

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe(MQTT_TOPIC)


# MQTT Client Handlers
def on_message(client, userdata, message):
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



# Dash App Initialization
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SUPERHERO])
app.title = "IoT Dashboard"

# App Layout
app.layout = dbc.Container(fluid=True, children=[
    # Header
    html.H1('Raspberry Pi IoT Dashboard',
            style={'font-family': 'Courier New'},
            className='text-center text-info my-4'),

    # LED Control and Light Intensity
    dbc.Row([

             # Light Intensity
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Light Intensity", className="text-center text-white"),
                    html.H6("Real-time monitoring of light intensity",
                            className="text-center text-muted mb-4"),
                    html.Div(id='light-intensity-display', className='text-center text-info',
                             style={'font-family': 'Courier New', 'font-size': '24px'}),
                    html.Div(id='email-message-display', className='text-center text-warning mt-2',
                             style={'font-family': 'Courier New', 'font-size': '18px'})
                ])
            ], style={'background-color': 'rgba(255, 255, 255, 0.1)',
                      'width': '60%', 'margin': '0 auto', 'box-shadow': '0px 4px 12px rgba(0, 0, 0, 0.4)'})
        ], width=6),

        # LED Control
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("LED Status", className="text-center text-white"),
                    html.Div(id='led-status', className='text-center text-info',
                             style={'font-family': 'Courier New', 'margin-top': '20px'}),
                    html.Img(id='led-image', src='/assets/light_off.png',
                    style={'display': 'block', 'margin': '20px auto', 'width': '100px'})
                ])
            ], style={'background-color': 'rgba(255, 255, 255, 0.1)',
                      'width': '60%', 'margin': '0 auto', 'box-shadow': '0px 4px 12px rgba(0, 0, 0, 0.4)'})
        ], width=6),
    ]),

    # Image Display
    dbc.Row(dbc.Col([
        html.Img(id='led-image', src='/assets/light_off.png',
                 style={'display': 'block', 'margin': '20px auto', 'width': '100px'})
    ])),

    # Footer
    dbc.Row([
        dbc.Col([
            html.H6("Powered by Raspberry Pi",
                    className="text-center text-muted",
                    style={'margin-top': '30px', 'font-family': 'Courier New'})
        ], width=12)
    ]),

    # Auto-refresh Interval
    dcc.Interval(id="update-interval", interval=2000, n_intervals=0)
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

# Email Manager
class EmailManager:
    def __init__(self):
        self.EMAIL = "liamgroupiot@gmail.com"
        self.PASSWORD = "unip eiah qvyn bjbp"
        self.SERVER = "smtp.gmail.com"

    def send_email(self, light_intensity):
        current_time = datetime.now().strftime("%H:%M")
        email_content = f"The Light is ON at {current_time}. Current Light Intensity: {light_intensity}."
        em = EmailMessage()
        em["From"] = self.EMAIL
        em["To"] = "receiver@example.com"
        em["Subject"] = "Light Intensity Alert"
        em.set_content(email_content)

        with smtplib.SMTP_SSL(self.SERVER, 465) as smtp:
            smtp.login(self.EMAIL, self.PASSWORD)
            smtp.send_message(em)

email_manager = EmailManager()

# Callbacks
@app.callback(
    [Output('led-status', 'children'),
     Output('led-toggle', 'on'),
     Output('led-image', 'src')],
    [Input('led-toggle', 'on')]
)
def update_led_status(toggle_state):
    GPIO.output(LED_GPIO_PIN, toggle_state)
    img_src = '/assets/light_on.png' if toggle_state else '/assets/light_off.png'
    return f'LED is {"ON" if toggle_state else "OFF"}', toggle_state, img_src


@app.callback(
    [Output('light-intensity-display', 'children'),
     Output('email-message-display', 'children')],
    [Input('update-interval', 'n_intervals')]
)

def update_light_data(n):
    return f"Light Intensity: {light_intensity} Lux", email_message


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

# Dash App Initialization
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# App Layout
app.layout = dbc.Container(fluid=True, children=[
    html.H1("Raspberry Pi IoT Dashboard - Phase #3", className="text-center my-4"),
    
    # Light Intensity and LED Status Card
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Light Intensity and LED Status", className="text-center", style={'font-size': '24px'}),
                dbc.CardBody([
                    html.Label("Current Light Intensity (Lux)", className="label"),
                    daq.Gauge(
                        id="light-intensity-gauge",
                        min=0,
                        max=1000,
                        value=0,
                        color={'gradient': True, 'ranges': {'red': [0, 400], 'yellow': [400, 700], 'green': [700, 1000]}}
                    ),
                    html.Div(id="light-intensity-display", className="text-center", style={'font-size': '20px'}),
                    html.Div(id="led-status", className="text-center", style={'margin-top': '10px'}),
                    html.Div(id="email-status", className="text-center", style={'margin-top': '10px'})
                ])
            ])
        )
    ], className="mb-4"),

    dcc.Interval(
        id="update-interval",
        interval=5 * 1000,  # Update every 5 seconds
        n_intervals=0
    ),

    # Footer
    dbc.Row([
        dbc.Col([
            html.Footer("Powered by Raspberry Pi", className="text-center text-muted", style={'margin-top': '30px'})
        ], width=12)
    ])
])


# GPIO Cleanup
@app.server.before_first_request
def setup_cleanup():
    @atexit.register
    def cleanup_gpio():
        GPIO.cleanup()

# Run the Server
if __name__ == '__main__':
    app.run_server(debug=True)



