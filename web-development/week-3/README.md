# Web Development — Week 3: JavaScript Logic & APIs

A weather app: enter a city and get the current temperature, humidity and condition in a card, fetched with the Fetch API and parsed from JSON.

The brief names OpenWeatherMap, which needs a personal API key. This app uses OpenWeatherMap when you paste your own key in the page, which is stored only in your browser. Otherwise it uses Open-Meteo, which needs no key, so the app works as soon as it is opened. No key is included in this repository.

Open `index.html`. `node test.js` runs a live check against Open-Meteo, including the error cases for empty and unknown cities.
