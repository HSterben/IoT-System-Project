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

# GPIO Setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
Motor1, Motor2, Motor3 = 22, 27, 17
GPIO.setup([Motor1, Motor2, Motor3], GPIO.OUT)

# Sensors
SENSOR = Adafruit_DHT.DHT11
DHT_PIN = 4  # Assuming GPIO4 is used

# Email
EMAIL = "liamgroupiot@gmail.com"
PASSWORD = "your_email_password"
SERVER = 'smtp.gmail.com'

class EmailManager:
    def send_email(self, temp, email_receiver):
        with smtplib.SMTP_SSL(SERVER, 465, context=ssl.create_default_context()) as smtp:
            smtp.login(EMAIL, PASSWORD)
            msg = EmailMessage()
            msg.set_content(f"Hello, the current temperature is {temp}°C. Please reply 'YES' to turn on the fan.")
            msg['Subject'] = "Temperature Alert"
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
                if "yes" in message.get_payload(decode=True).decode().lower():
                    return True
        return False

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H1("IoT Dashboard for Temperature and Humidity", className="text-center"),
    dcc.Interval(id='update-interval', interval=120000, n_intervals=0),  # Update every 2 minutes
    dbc.Row([
        dbc.Col(daq.Gauge(id='temp-gauge', min=0, max=50, value=0, label='Temperature (°C)')),
        dbc.Col(daq.Gauge(id='humidity-gauge', min=0, max=100, value=0, label='Humidity (%)'))
    ]),
    dbc.Row(html.Button('Send Email', id='email-button', n_clicks=0)),
    dbc.Row(html.Div(id='email-status')),
    html.Div(id='hidden-div', style={'display':'none'})
])

@app.callback(
    [Output('temp-gauge', 'value'), Output('humidity-gauge', 'value')],
    [Input('update-interval', 'n_intervals')]
)
def update_sensor_data(_):
    humidity, temperature = Adafruit_DHT.read_retry(SENSOR, DHT_PIN)
    return temperature, humidity

@app.callback(
    Output('email-status', 'children'),
    [Input('email-button', 'n_clicks')],
    [Output('temp-gauge', 'value')]
)
def handle_email_alert(n_clicks, current_temp):
    if n_clicks > 0:
        email_manager = EmailManager()
        email_manager.send_email(current_temp, "recipient@example.com")
        return "Email sent!"
    return ""

@app.callback(
    Output('hidden-div', 'children'),
    [Input('update-interval', 'n_intervals')]
)
def check_for_email_response(_):
    email_manager = EmailManager()
    if email_manager.receive_email():
        GPIO.output([Motor1, Motor2, Motor3], [GPIO.HIGH, GPIO.LOW, GPIO.HIGH])  # Turn on the fan
    return ""

@app.server.before_first_request
def register_cleanup():
    @atexit.register
    def cleanup_gpio():
        GPIO.cleanup()

if __name__ == '__main__':
    app.run_server(debug=True)
