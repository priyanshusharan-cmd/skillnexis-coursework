# IoT with AI — Week 1

This folder covers the supplied IoT fundamentals and Smart LED exercise, plus a separate ESP32/DHT11 cloud telemetry starter for the course page's connected weather-station mini project. `smart_led.ino` is local GPIO practice; `weather_station.ino` is a code template that sends temperature and humidity to ThingSpeak over HTTPS.

Architecture: DHT11 → ESP32 GPIO → Wi-Fi/HTTPS → ThingSpeak channel → dashboard/threshold alert. The code uses placeholders for Wi-Fi credentials and the channel write key. Create a private test channel and add secrets locally before use. Do not commit real keys. No hardware, cloud account, or alert was configured or tested here.

The PDF asks for 10 IoT applications, sensor descriptions, architecture, analog/digital comparison, LED/button/sensor exercises, and a smart LED concept; those are covered in the notes and existing sketch. Wiring remains a plan, not verified evidence.
