// Weather lookup. Uses OpenWeatherMap when an API key is supplied, otherwise Open-Meteo (no key needed).
const WMO = {
  0: 'Clear sky', 1: 'Mainly clear', 2: 'Partly cloudy', 3: 'Overcast', 45: 'Fog', 48: 'Rime fog',
  51: 'Light drizzle', 53: 'Drizzle', 55: 'Dense drizzle', 61: 'Light rain', 63: 'Rain', 65: 'Heavy rain',
  71: 'Light snow', 73: 'Snow', 75: 'Heavy snow', 80: 'Rain showers', 81: 'Rain showers', 82: 'Violent rain showers',
  95: 'Thunderstorm', 96: 'Thunderstorm with hail', 99: 'Thunderstorm with heavy hail',
};

async function getJson(url) {
  const res = await fetch(url);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const err = new Error(body.message || `Request failed (${res.status})`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

async function fromOpenWeatherMap(city, key) {
  const d = await getJson(`https://api.openweathermap.org/data/2.5/weather?q=${encodeURIComponent(city)}&units=metric&appid=${encodeURIComponent(key)}`);
  return { city: `${d.name}, ${d.sys.country}`, temperature: d.main.temp, humidity: d.main.humidity, condition: d.weather[0].description, source: 'OpenWeatherMap' };
}

async function fromOpenMeteo(city) {
  const geo = await getJson(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(city)}&count=1&language=en&format=json`);
  if (!geo.results || geo.results.length === 0) {
    const err = new Error(`City not found: ${city}`);
    err.status = 404;
    throw err;
  }
  const g = geo.results[0];
  const w = await getJson(`https://api.open-meteo.com/v1/forecast?latitude=${g.latitude}&longitude=${g.longitude}&current=temperature_2m,relative_humidity_2m,weather_code`);
  return {
    city: `${g.name}, ${g.country_code}`,
    temperature: w.current.temperature_2m,
    humidity: w.current.relative_humidity_2m,
    condition: WMO[w.current.weather_code] || `Code ${w.current.weather_code}`,
    source: 'Open-Meteo',
  };
}

async function getWeather(city, openWeatherKey) {
  const name = (city || '').trim();
  if (!name) throw new Error('Enter a city name');
  return openWeatherKey ? fromOpenWeatherMap(name, openWeatherKey) : fromOpenMeteo(name);
}

if (typeof module !== 'undefined') module.exports = { getWeather };
else window.getWeather = getWeather;
