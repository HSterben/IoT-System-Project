# Front End

import dash_daq as daq


dbc.Row([
    dbc.Col([
        daq.Gauge(
            id='temperature-gauge',
            label="Temperature (°C)",
            min=0,
            max=50,
            value=0,
            color={"gradient":True,"ranges":{"green":[0,24],"yellow":[24,32],"red":[32,50]}},
            style={'width': '100%', 'height': 'auto'}
        ),
    ], width=6),
    dbc.Col([
        daq.Gauge(
            id='humidity-gauge',
            label="Humidity (%)",
            min=0,
            max=100,
            value=0,
            color={"gradient":True,"ranges":{"blue":[0,40],"green":[40,60],"orange":[60,80],"red":[80,100]}},
            style={'width': '100%', 'height': 'auto'}
        )
    ], width=6)
])

# Back-End

import Adafruit_DHT

SENSOR = Adafruit_DHT.DHT11
DHT_PIN = 24  # Assuming GPI24 is used (someone correct it if wrong)

@app.callback(
    [Output('temperature-gauge', 'value'),
     Output('humidity-gauge', 'value')],
    [Input('interval-component', 'n_intervals')]
)
def update_temperature_humidity(_):
    humidity, temperature = Adafruit_DHT.read_retry(SENSOR, DHT_PIN)
    return temperature, humidity

# Add this component anywhere in your layout:
dcc.Interval(
    id='interval-component',
    interval=1*60000,  # in milliseconds
    n_intervals=0
)


