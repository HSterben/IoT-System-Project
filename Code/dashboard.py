import dash
import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import html, dcc, Input, Output, State
import atexit
import RPi.GPIO as GPIO

GPIO.setwarnings(False)
LED_GPIO_PIN = 17
GPIO.setmode(GPIO.BCM)  
GPIO.setup(LED_GPIO_PIN, GPIO.OUT)

# Creating a Dash application
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SUPERHERO])

# Layout of the app
app.layout = dbc.Container(fluid=True, children=[
    # App header
    html.H1('Raspberry Pi IoT Dashboard', 
            style={'font-family': 'Courier New'}, 
            className='text-center text-info my-4'),
    
    # LED Control Card
    dbc.Row([
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
        ], width=12)
    ]),
    
    dbc.Row(
        dbc.Col([
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


@app.callback(
    [Output('led-status', 'children'), 
     Output('led-toggle', 'on'),
     Output('led-image', 'src')],
    [Input('led-toggle', 'on')]
)
def update_led_status(toggle_state):
    led_status = 'ON' if toggle_state else 'OFF'
    GPIO.output(LED_GPIO_PIN, toggle_state)  # Control the LED based on switch state
    
    img_src = '/assets/light_on.png' if toggle_state else '/assets/light_off.png'
    
    return f'LED is {led_status}', toggle_state, img_src

# GPIO cleanup
@app.server.before_first_request
def setup_cleanup():
    @atexit.register
    def gpio_cleanup():
        GPIO.cleanup()

if __name__ == '__main__':
    app.run_server(debug=True)

