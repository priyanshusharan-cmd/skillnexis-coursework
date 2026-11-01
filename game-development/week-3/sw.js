// Service worker: caches the game files so it starts offline after the first visit. Bump VERSION to ship an update.
const VERSION = 'gem-run-v1';
const FILES = ['./', 'index.html', 'style.css', 'core.js', 'audio.js', 'game.js', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png'];

self.addEventListener('install', e => e.waitUntil(caches.open(VERSION).then(c => c.addAll(FILES)).then(() => self.skipWaiting())));
self.addEventListener('activate', e => e.waitUntil(
  caches.keys().then(keys => Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k)))).then(() => self.clients.claim())
));
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request).catch(() => caches.match('index.html'))));
});
