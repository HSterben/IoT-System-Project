# This should make the photo resistor work
void setup() {
    Serial.begin(9600);
}

void loop() {
    int value = analogRead(A0);
    Serial.println("Analog value : ");
    Serial.println(value);

    if (value < 400) {
        digitalWrite(8, HIGH);
    }
    else {
        digitalWrite(8, LOW);
    }
    delay(1000);
}


# This is for the front end using dash (If we use dash)
html.Div([
    html.Label('Light Intensity:'),
    daq.Slider(
        id='light-slider',
        min=0,
        max=4095,  # Adjust max value
        value=0,
        marks={str(i): str(i) for i in range(0, 4096, 500)},  # Example marks
        step=1
    ),
    html.Div(id='slider-output-container')
])

# Add callback for updating the slider
@app.callback(
    Output('light-slider', 'value'),
    Input('update-interval', 'n_intervals')
)
def update_slider(_):
    return light_level if light_level is not None else 0