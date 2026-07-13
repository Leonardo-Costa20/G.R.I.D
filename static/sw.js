const CACHE_NAME   = 'grid-os-v7';
const CACHE_STATIC = 'grid-static-v7';
 
// Assets estáticos que devem ser cacheados na instalação
const STATIC_ASSETS = [
  '/',
  '/app',
  '/login',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  'https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700;800&display=swap',
  'https://cdn.tailwindcss.com',
];
 
// Rotas que NUNCA devem ser servidas do cache (sempre network)
const NETWORK_ONLY = [
  '/admin',
  '/admin/',
  '/login',
  '/logout',
  '/register',
  '/dashboard',
];
 
// ── Instalação ──────────────────────────────────────────────────
self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_STATIC).then((cache) => {
      return cache.addAll(STATIC_ASSETS.filter(url => !url.startsWith('http') || url.includes('fonts.googleapis')));
    }).catch(() => {})
  );
});
 
// ── Activação: limpa caches antigos ────────────────────────────
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k !== CACHE_NAME && k !== CACHE_STATIC)
          .map((k) => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});
 
// ── Fetch: estratégia por tipo de recurso ──────────────────────
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
 
  // Ignora WebSockets e chamadas não-GET
  if (request.method !== 'GET') return;
  if (url.protocol === 'ws:' || url.protocol === 'wss:') return;
 
  // Rotas críticas de autenticação/admin: sempre network
  const isNetworkOnly = NETWORK_ONLY.some(
    (path) => url.pathname === path || url.pathname.startsWith('/admin/')
  );
  if (isNetworkOnly) {
    event.respondWith(fetch(request).catch(() => caches.match('/app') || caches.match('/')));
    return;
  }
 
  // Assets estáticos (JS, CSS, fontes, imagens): cache-first
  if (
    url.pathname.startsWith('/static/') ||
    url.hostname.includes('fonts.gstatic.com') ||
    url.hostname.includes('fonts.googleapis.com') ||
    url.hostname.includes('cdnjs.cloudflare.com') ||
    url.hostname.includes('cdn.tailwindcss.com') ||
    url.hostname.includes('code.jquery.com')
  ) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;
        return fetch(request).then((response) => {
          if (response && response.status === 200) {
            const clone = response.clone();
            caches.open(CACHE_STATIC).then((cache) => cache.put(request, clone));
          }
          return response;
        });
      })
    );
    return;
  }
 
  // Tudo o resto: network-first com fallback para cache
  event.respondWith(
    fetch(request)
      .then((response) => {
        if (response && response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
        }
        return response;
      })
      .catch(() => caches.match(request))
  );
});
 
// ── Push Notifications (futuro) ────────────────────────────────
self.addEventListener('push', (event) => {
  if (!event.data) return;
  const data = event.data.json();
  self.registration.showNotification(data.title || 'G.R.I.D Alert', {
    body:    data.body || '',
    icon:    '/static/icons/icon-192.png',
    badge:   '/static/icons/icon-192.png',
    tag:     'grid-alert',
    vibrate: [200, 100, 200],
  });
});