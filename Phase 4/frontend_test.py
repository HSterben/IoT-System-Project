import dash
import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import html, dcc, Input, Output
import random

# Dash App Initialization with suppress_callback_exceptions=True
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SUPERHERO], suppress_callback_exceptions=True)
app.title = "Raspberry Pi IoT Dashboard"

# App Layout Front-End
app.layout = dbc.Container(fluid=True, children=[
    # Add the Interval component to trigger periodic updates
    dcc.Interval(id='update-interval', interval=2000, n_intervals=0),  # 2 seconds interval

    html.H1('Raspberry Pi IoT Dashboard Phase #2', className='text-center my-4'),

    # Row containing the Side Panel (User Profile) and Main Content Area
    dbc.Row([
        # Side Panel (User Profile) - Fixed on the left
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("User Profile", style={'font-size': '24px'}, className="text-center"),
                dbc.CardBody([
                    html.Div([
                        html.Img(
                            id='profile-pic',
                            src='/assets/cat.png',  
                            style={'width': '150px', 'height': '150px', 'border-radius': '50%', 'margin-bottom': '15px'}
                        ),
                        html.H5("User Name", className='text-center', style={'font-size': '20px'}),
                        html.P(id="user-rfid", children="RFID Tag: Not Scanned", style={'font-size': '18px'}),
                        html.P(id="temperature-threshold", children="Temp Threshold: Not Set", style={'font-size': '18px'}),
                        html.P(id="light-threshold", children="Light Threshold: Not Set", style={'font-size': '18px'}),
                    ])
                ])
            ]),
        ], width=3, style={'position': 'fixed', 'top': 0, 'left': 0, 'height': '100%', 'overflow-y': 'auto', 'z-index': '10'}),  
       
   
        dbc.Col([
            dbc.Tabs([
                dbc.Tab(label="Temperature & Humidity", tab_id="temperature-humidity-tab"),
                dbc.Tab(label="Light Intensity", tab_id="light-intensity-tab"),
                dbc.Tab(label="Bluetooth", tab_id="bluetooth-tab"),
                dbc.Tab(label="Settings", tab_id="settings-tab")
            ], id="user-profile-tabs", active_tab="temperature-humidity-tab"),

            # Content for the active tab
            html.Div(id="tab-content")
        ], width=9, style={'margin-left': '25%'}),  # Adjust the margin to account for the side panel width
    ], className="mb-4"),

    # Footer
    dbc.Row([
        dbc.Col([
            html.Footer("Powered by Raspberry Pi", className="text-center text-muted", style={'margin-top': '30px'})
        ], width=12)
    ])
])

# Tab Content based on active tab
@app.callback(
    Output('tab-content', 'children'),
    [Input('user-profile-tabs', 'active_tab')]
)
def render_content(tab):
    if tab == 'temperature-humidity-tab':
        return html.Div([
            # Fan Control and Gauges on Dashboard Tab
            html.Div([
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
                                        style={'margin-bottom': '1px'},
                                        color={'gradient': True, 'ranges': {'red': [0, 20], 'yellow': [20, 35], 'green': [35, 50]}}
                                    ),
                                    html.Div(id='temp-display', className='text-center',
                                             style={'font-size': '20px', 'margin-top': '1px', 'color': 'white'})
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
                                        style={'margin-bottom': '1px'},
                                        color={'gradient': True, 'ranges': {'red': [0, 40], 'yellow': [40, 70], 'green': [70, 100]}}
                                    ),
                                    html.Div(id='humidity-display', className='text-center',
                                             style={'font-size': '20px', 'margin-top': '1px', 'color': 'white'})
                                ], className='card-body-center'),
                                width=6
                            )
                        ])
                    )
                ])
            ], className="mb-4"),

            html.Div([
                # Fan Control Section
                dbc.Card([
                    dbc.CardHeader("Fan Control", className="text-center", style={'font-size': '24px'}),
                    dbc.CardBody([
                        html.Img(id='fan-image', src='/assets/fan_off_spinning.png',
                                 style={'display': 'block', 'margin': '20px auto', 'width': '200px'}),
                        html.Div(id='fan-status', className='text-center', children="The fan is currently turned OFF."),
                    ])
                ])
            ], className="mb-4")
        ])
    elif tab == 'light-intensity-tab':
        return html.Div([
            html.H5("Settings", className="text-center"),
            html.P("to be added.")
        ])
    elif tab == 'bluetooth-tab':
        return html.Div([
            html.H5("Settings", className="text-center"),
            html.P("to be added.")
        ])
        
    elif tab == 'settings-tab':
        return html.Div([
            html.H5("Settings", className="text-center"),
            html.P("to be added.")
        ])

# Fake data for gauge and fan image 
@app.callback(
    [Output('temp-gauge', 'value'),
     Output('humidity-gauge', 'value'),
     Output('fan-image', 'src'),
     Output('fan-status', 'children')],
    Input('update-interval', 'n_intervals')
)
def update_gauge_and_fan(n):
  
    temp_value = random.randint(0, 50)
    humidity_value = random.randint(0, 100)
    
    if random.choice([True, False]):
        fan_src = '/assets/fan_on_spinning.gif' 
        fan_status = "The fan is currently turned ON."
    else:
        fan_src = '/assets/fan_off_spinning.png'  
        fan_status = "The fan is currently turned OFF."

    return temp_value, humidity_value, fan_src, fan_status

if __name__ == '__main__':
    app.run_server(debug=True)
