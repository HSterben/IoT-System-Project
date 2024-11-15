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