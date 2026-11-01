// Images are generated locally as SVG data URIs, so the page works offline.
const PALETTES = [
  ['Sunrise', '#ff9966', '#ff5e62'], ['Lagoon', '#2193b0', '#6dd5ed'], ['Forest', '#134e5e', '#71b280'],
  ['Dusk', '#614385', '#516395'], ['Citrus', '#f7971e', '#ffd200'], ['Berry', '#8e2de2', '#ff6ec4'],
  ['Slate', '#232526', '#6b7b8c'], ['Mint', '#00b09b', '#96c93d'],
];

function makeImage(title, c1, c2, size) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${Math.round(size * 0.66)}" viewBox="0 0 600 400">
    <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${c1}"/><stop offset="1" stop-color="${c2}"/></linearGradient></defs>
    <rect width="600" height="400" fill="url(#g)"/><circle cx="450" cy="120" r="70" fill="#ffffff33"/>
    <path d="M0 330 Q150 230 300 310 T600 290 V400 H0Z" fill="#00000033"/>
    <text x="40" y="360" font-family="sans-serif" font-size="42" fill="#fff">${title}</text></svg>`;
  return 'data:image/svg+xml;utf8,' + encodeURIComponent(svg);
}

const images = PALETTES.map(([title, a, b]) => ({ title, thumb: makeImage(title, a, b, 400), full: makeImage(title, a, b, 1200) }));
const gallery = document.getElementById('gallery');
const lightbox = document.getElementById('lightbox');
const lbImg = document.getElementById('lb-img');
const lbCap = document.getElementById('lb-cap');
let current = 0;
let opener = null;

images.forEach((img, i) => {
  const btn = document.createElement('button');
  btn.className = 'thumb';
  btn.innerHTML = `<img alt="${img.title} gradient" src="${img.thumb}"><span>${img.title}</span>`;
  btn.addEventListener('click', () => open(i, btn));
  gallery.appendChild(btn);
});

function show(i) {
  current = (i + images.length) % images.length;
  lbImg.src = images[current].full;
  lbImg.alt = images[current].title + ' gradient';
  lbCap.textContent = `${images[current].title} (${current + 1} of ${images.length})`;
}
function open(i, from) {
  opener = from;
  show(i);
  lightbox.hidden = false;
  document.getElementById('close').focus();
}
function close() {
  lightbox.hidden = true;
  if (opener) opener.focus();
}
document.getElementById('close').addEventListener('click', close);
document.getElementById('prev').addEventListener('click', () => show(current - 1));
document.getElementById('next').addEventListener('click', () => show(current + 1));
lightbox.addEventListener('click', e => { if (e.target === lightbox) close(); });
document.addEventListener('keydown', e => {
  if (lightbox.hidden) return;
  if (e.key === 'Escape') close();
  if (e.key === 'ArrowLeft') show(current - 1);
  if (e.key === 'ArrowRight') show(current + 1);
});

// Clock and countdown.
const pad = n => String(n).padStart(2, '0');
function formatClock(d) { return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`; }
function formatCountdown(ms) {
  if (ms <= 0) return 'Time is up!';
  const s = Math.floor(ms / 1000);
  return `${Math.floor(s / 86400)}d ${pad(Math.floor(s % 86400 / 3600))}h ${pad(Math.floor(s % 3600 / 60))}m ${pad(s % 60)}s`;
}
const clock = document.getElementById('clock');
const countdown = document.getElementById('countdown');
const target = document.getElementById('target');
const saved = localStorage.getItem('w2-target');
if (saved) target.value = saved;
else {
  const now = new Date();
  target.value = `${now.getFullYear() + 1}-01-01T00:00`;
}
target.addEventListener('change', () => localStorage.setItem('w2-target', target.value));
function tick() {
  clock.textContent = formatClock(new Date());
  const t = new Date(target.value);
  countdown.textContent = isNaN(t) ? 'Pick a date.' : formatCountdown(t - new Date());
}
tick();
setInterval(tick, 1000);

