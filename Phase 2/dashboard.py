import time
import dash # Dash is used for creating web applications in python 
import dash_bootstrap_components as dbc # Access to Dash bootstrap components for styling (col, row, card, etc)
import dash_daq as daq # Access to components for designing our dashboard (BooleanSwitch)
from dash import html, dcc, Input, Output, State # Getting specific components from Dash library
import atexit # Used for cleanup and releasing resources
import RPi.GPIO as GPIO # Rasberry Pi GPIO Library

GPIO.setwarnings(False) # Surpress GPIO Library warnings
LED_GPIO_PIN = 17 
GPIO.setmode(GPIO.BCM)  
GPIO.setup(LED_GPIO_PIN, GPIO.OUT) # Configures GPIO17 as an output pin

# Creating a Dash application
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SUPERHERO])

# Layout of the app
app.layout = dbc.Container(fluid=True, children=[
    # App header
    html.H1('Raspberry Pi IoT Dashboard', # Title for Dashboard
            style={'font-family': 'Courier New'}, # Styling
            className='text-center text-info my-4'),
    
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
@app.callback(
    # output is what will be updated when the callback is triggeres
    [Output('led-status', 'children'), # Updates the text inside the div with the ID led-status
     Output('led-toggle', 'on'), # Updates the state of the toggle switch
     Output('led-image', 'src')], # Updates the source of the image shown based on the LED state
     # input triggers the callback
    [Input('led-toggle', 'on')]  # passed to update_led_status as toggle_state
)

# Called by Dash whenever the state of the toggle switch changes
def update_led_status(toggle_state):
    # ON for true, OFF for false
    led_status = 'ON' if toggle_state else 'OFF'

    # Control the LED based on switch state
    GPIO.output(LED_GPIO_PIN, toggle_state)  
    
    # Changes image based on toggle_state
    img_src = '/assets/light_on.png' if toggle_state else '/assets/light_off.png'
    
    #return 3 values to update the app
    return f'LED is {led_status}', toggle_state, img_src

# GPIO cleanup
@app.server.before_first_request
def setup_cleanup():
    @atexit.register
    def gpio_cleanup():
        GPIO.cleanup()

if __name__ == '__main__':
    app.run_server(debug=True)

