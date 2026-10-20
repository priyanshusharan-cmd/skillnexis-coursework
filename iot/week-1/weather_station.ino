// ESP32 + DHT11 + ThingSpeak telemetry starter. No credentials are included.
#include <WiFi.h>
#include <HTTPClient.h>
#include "DHT.h"
#define DHTPIN 4
#define DHTTYPE DHT11
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* THINGSPEAK_WRITE_KEY = "YOUR_CHANNEL_WRITE_KEY";
const char* THINGSPEAK_URL = "https://api.thingspeak.com/update";
DHT dht(DHTPIN,DHTTYPE);
unsigned long lastSend=0;
const unsigned long sendEveryMs=20000; // channel update interval
void setup(){Serial.begin(115200);dht.begin();WiFi.begin(WIFI_SSID,WIFI_PASSWORD);}
void loop(){
  if(WiFi.status()!=WL_CONNECTED){delay(1000);return;}
  if(millis()-lastSend<sendEveryMs){delay(100);return;}
  lastSend=millis();float humidity=dht.readHumidity(),temperature=dht.readTemperature();
  if(isnan(humidity)||isnan(temperature)){Serial.println("DHT read failed");return;}
  HTTPClient http;String url=String(THINGSPEAK_URL)+"?api_key="+THINGSPEAK_WRITE_KEY+"&field1="+String(temperature,1)+"&field2="+String(humidity,1);
  http.begin(url);int code=http.GET();
  if(code>0)Serial.printf("HTTP %d; entry=%s\n",code,http.getString().c_str());
  else Serial.printf("HTTP request failed: %s\n",http.errorToString(code).c_str());
  http.end();
  // Add an alert only after setting a safe threshold and a provider endpoint.
}
