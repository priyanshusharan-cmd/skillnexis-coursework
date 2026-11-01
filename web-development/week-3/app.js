const form = document.getElementById('form');
const cityInput = document.getElementById('city');
const keyInput = document.getElementById('key');
const card = document.getElementById('card');
const status = document.getElementById('status');

try { keyInput.value = localStorage.getItem('owm-key') || ''; } catch (e) { /* storage unavailable */ }

function render(w) {
  card.innerHTML = '';
  const h = document.createElement('h2');
  h.textContent = w.city;
  const t = document.createElement('p');
  t.className = 'temp';
  t.textContent = `${Math.round(w.temperature)}°C`;
  const c = document.createElement('p');
  c.textContent = w.condition.charAt(0).toUpperCase() + w.condition.slice(1);
  const hum = document.createElement('p');
  hum.textContent = `Humidity: ${w.humidity}%`;
  const src = document.createElement('small');
  src.textContent = `Source: ${w.source}`;
  card.append(h, t, c, hum, src);
  card.hidden = false;
}

form.addEventListener('submit', async e => {
  e.preventDefault();
  const key = keyInput.value.trim();
  try { localStorage.setItem('owm-key', key); } catch (err) { /* ignore */ }
  status.textContent = 'Loading...';
  card.hidden = true;
  try {
    render(await getWeather(cityInput.value, key));
    status.textContent = '';
  } catch (err) {
    status.textContent = err.status === 401 ? 'The API key was rejected.' : err.message;
  }
});
