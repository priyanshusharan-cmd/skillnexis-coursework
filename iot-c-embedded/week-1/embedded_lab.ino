// SkillNexis Week 1: select one lab mode (1-5) before uploading.
#define LAB_MODE 1
const byte buttonPin = 10, buzzerPin = 11;
const byte leds[] = {2,3,4,5,6,7,8};
const byte ledCount = sizeof(leds) / sizeof(leds[0]);

bool stableButton = HIGH, lastReading = HIGH;
unsigned long changedAt = 0;
const unsigned long debounceMs = 35;
bool ledState = false;

bool pressed() {
  bool reading = digitalRead(buttonPin);
  if (reading != lastReading) changedAt = millis();
  if (millis() - changedAt >= debounceMs && reading != stableButton) {
    stableButton = reading;
    if (stableButton == LOW) { lastReading = reading; return true; }
  }
  lastReading = reading;
  return false;
}
void allOff() { for (byte p : leds) digitalWrite(p, LOW); }
void setup() {
  for (byte p : leds) pinMode(p, OUTPUT);
  pinMode(buttonPin, INPUT_PULLUP); pinMode(buzzerPin, OUTPUT);
  Serial.begin(9600); randomSeed(analogRead(A0));
}
void loop() {
#if LAB_MODE == 1
  // Basic LED blink.
  digitalWrite(leds[0], HIGH); delay(500); digitalWrite(leds[0], LOW); delay(500);
#elif LAB_MODE == 2
  // Debounced button toggles an LED without blocking delays.
  if (pressed()) ledState = !ledState;
  digitalWrite(leds[0], ledState);
#elif LAB_MODE == 3
  // 8-bit pattern, shown on seven physical LEDs (bit 7 is printed to Serial).
  static byte value = 0; static unsigned long tick = 0;
  if (millis() - tick >= 250) {
    tick = millis(); value++;
    for (byte i=0; i<ledCount; i++) digitalWrite(leds[i], (value >> i) & 1);
    Serial.println(value, BIN);
  }
#elif LAB_MODE == 4
  // Simple timed traffic light: red, red+amber, green, amber.
  static byte phase=0; static unsigned long phaseAt=0;
  const unsigned long durations[] = {4000,1000,4000,1000};
  if (millis()-phaseAt >= durations[phase]) { phase=(phase+1)%4; phaseAt=millis(); }
  allOff();
  if (phase==0) digitalWrite(leds[0], HIGH);
  if (phase==1) { digitalWrite(leds[0], HIGH); digitalWrite(leds[1], HIGH); }
  if (phase==2) digitalWrite(leds[2], HIGH);
  if (phase==3) digitalWrite(leds[1], HIGH);
#elif LAB_MODE == 5
  // Dice pattern: seven LEDs form a pip grid; press to roll.
  if (pressed()) {
    byte face = random(1,7); allOff();
    const byte faces[6][7] = {
      {0,0,0,1,0,0,0}, {1,0,0,0,0,0,1}, {1,0,0,1,0,0,1},
      {1,0,1,0,1,0,1}, {1,0,1,1,1,0,1}, {1,1,1,0,1,1,1}
    };
    for (byte i=0;i<7;i++) digitalWrite(leds[i], faces[face-1][i]);
    tone(buzzerPin, 880, 80); Serial.print("Dice: "); Serial.println(face);
  }
#endif
}
