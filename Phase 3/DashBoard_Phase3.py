import time
import dash
import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import html, dcc, Input, Output, State
import atexit
import RPi.GPIO as GPIO
import threading
import paho.mqtt.client as mqtt

# GPIO Setup
GPIO.setwarnings(False)
LED_GPIO_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_GPIO_PIN, GPIO.OUT)

# MQTT Configuration
MQTT_BROKER = "127.0.0.1"
MQTT_TOPIC = "IoTLabPhase3/Ilan"
MQTT_PORT = 1883
MQTT_CLIENT = mqtt.Client()

source_address = 'liamgroupiot@gmail.com'
dest_address = 'websterliam25@gmail.com'
password = 'unip eiah qvyn bjbp'
imap_srv = 'smtp.gmail.com'
imap_port = 993

# Global variables for light data
light_intensity = 0
email_message = ""

# MQTT Client Handlers
def on_message(client, userdata, message):
    global light_intensity, email_message
    try:
        data = int(message.payload.decode())
        light_intensity = data
        if data < 400:
            GPIO.output(LED_GPIO_PIN, True)
            email_message = "Email sent! LED turned ON."
        else:
            GPIO.output(LED_GPIO_PIN, False)
            email_message = ""
    except ValueError:
        pass

def mqtt_thread():
    MQTT_CLIENT.on_message = on_message
    MQTT_CLIENT.connect(MQTT_BROKER)
    MQTT_CLIENT.subscribe(MQTT_TOPIC)
    MQTT_CLIENT.loop_forever()

# Start MQTT client in a separate thread
thread = threading.Thread(target=mqtt_thread)
thread.daemon = True
thread.start()

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
        # LED Control
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("LED Control", className="text-center text-white"),
                    html.H6("Toggle the LED On/Off", className="text-center text-muted mb-4"),
                    daq.BooleanSwitch(id='led-toggle', on=False,
                                      style={'transform': 'scale(2)', 'margin': '0 auto'}),
                    html.Div(id='led-status', className='text-center text-info',
                             style={'font-family': 'Courier New', 'margin-top': '20px'})
                ])
            ], style={'background-color': 'rgba(255, 255, 255, 0.1)',
                      'width': '60%', 'margin': '0 auto', 'box-shadow': '0px 4px 12px rgba(0, 0, 0, 0.4)'})
        ], width=6),

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
        ], width=6)
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

# GPIO Cleanup
@app.server.before_first_request
def setup_cleanup():
    @atexit.register
    def gpio_cleanup():
        GPIO.cleanup()

# Run the Server
if __name__ == '__main__':
    app.run_server(debug=True)


