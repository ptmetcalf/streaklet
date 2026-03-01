// Service Worker for Streaklet PWA
const SW_VERSION = 'v5-20260301';
const STATIC_CACHE = `streaklet-static-${SW_VERSION}`;
const SAME_ORIGIN = self.location.origin;

const STATIC_ASSETS = [
  '/static/css/style.css',
  '/static/css/components.css',
  '/static/manifest.json'
];

const NON_CACHEABLE_API_PREFIXES = [
  '/api/days/',
  '/api/streak',
  '/api/fitbit/connection',
  '/api/fitbit/connect',
  '/api/fitbit/callback'
];

function shouldBypassApiCache(pathname) {
  return NON_CACHEABLE_API_PREFIXES.some((prefix) => pathname.startsWith(prefix));
}

function isStaticRequest(request, url) {
  if (url.origin !== SAME_ORIGIN) return false;
  if (url.pathname.startsWith('/static/')) return true;

  return ['style', 'script', 'font', 'image', 'manifest'].includes(request.destination);
}

async function fetchWithStaticCacheUpdate(request) {
  const cachedResponse = await caches.match(request);

  const networkPromise = fetch(request)
    .then(async (response) => {
      if (response.ok) {
        const cache = await caches.open(STATIC_CACHE);
        await cache.put(request, response.clone());
      }
      return response;
    })
    .catch((error) => {
      console.warn('[SW] Static fetch failed:', request.url, error);
      return null;
    });

  if (cachedResponse) {
    // Serve fast from cache while updating in background.
    void networkPromise;
    return cachedResponse;
  }

  const networkResponse = await networkPromise;
  if (networkResponse) return networkResponse;

  return new Response('Offline', { status: 503, statusText: 'Offline' });
}

self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker', SW_VERSION);

  self.skipWaiting();
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => cache.addAll(STATIC_ASSETS))
      .catch((error) => {
        console.warn('[SW] Precaching failed:', error);
      })
  );
});

self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker', SW_VERSION);

  event.waitUntil(
    caches.keys().then((cacheNames) => Promise.all(
      cacheNames.map((cacheName) => {
        if (!cacheName.startsWith('streaklet-')) return Promise.resolve();
        if (cacheName === STATIC_CACHE) return Promise.resolve();

        console.log('[SW] Deleting old cache:', cacheName);
        return caches.delete(cacheName);
      })
    ))
  );

  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const { request } = event;

  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== SAME_ORIGIN) return;

  if (request.mode === 'navigate' || request.destination === 'document') {
    event.respondWith(
      fetch(request, { cache: 'no-store' })
        .then(async (response) => {
          const cache = await caches.open(STATIC_CACHE);
          await cache.put(request, response.clone());
          return response;
        })
        .catch(async (error) => {
          console.warn('[SW] Navigation fetch failed, trying cache:', request.url, error);
          const cached = await caches.match(request);
          if (cached) return cached;

          return new Response(
            '<!doctype html><html><body><h1>Offline</h1><p>No network connection available.</p></body></html>',
            {
              status: 503,
              headers: { 'Content-Type': 'text/html' }
            }
          );
        })
    );
    return;
  }

  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request, { cache: shouldBypassApiCache(url.pathname) ? 'no-store' : 'default' })
        .catch((error) => {
          console.warn('[SW] API fetch failed:', url.pathname, error);
          return new Response(
            JSON.stringify({
              error: 'Offline',
              message: 'You are currently offline. Please check your connection.'
            }),
            {
              status: 503,
              headers: { 'Content-Type': 'application/json' }
            }
          );
        })
    );
    return;
  }

  if (isStaticRequest(request, url)) {
    event.respondWith(fetchWithStaticCacheUpdate(request));
    return;
  }

  event.respondWith(
    fetch(request).catch(async (error) => {
      console.warn('[SW] Generic fetch failed, trying cache:', request.url, error);
      const cached = await caches.match(request);
      if (cached) return cached;
      return new Response('Offline', { status: 503, statusText: 'Offline' });
    })
  );
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
