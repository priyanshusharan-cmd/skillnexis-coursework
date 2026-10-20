const int LED_PIN = 9;
const int BUTTON_PIN = 2;
int previous = HIGH;
bool ledOn = false;
void setup() { pinMode(LED_PIN, OUTPUT); pinMode(BUTTON_PIN, INPUT_PULLUP); Serial.begin(9600); }
void loop() {
  int current = digitalRead(BUTTON_PIN);
  if (previous == HIGH && current == LOW) { ledOn = !ledOn; digitalWrite(LED_PIN, ledOn ? HIGH : LOW); Serial.println(ledOn ? "LED ON" : "LED OFF"); delay(30); }
  previous = current;
}
