// Vigilant Eye service worker
// Strategy: minimal precache of the app shell + runtime cache for static
// assets. Install / activate are kept lightweight so updates roll out fast.
// Bump CACHE_VERSION whenever the cached shell needs to be invalidated.

const CACHE_VERSION = 'v3';
const SHELL_CACHE = `vigilant-shell-${CACHE_VERSION}`;
const RUNTIME_CACHE = `vigilant-runtime-${CACHE_VERSION}`;

// Files we know exist at root and want available offline immediately.
const SHELL_FILES = [
  '/',
  '/index.html',
  '/manifest.webmanifest',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/icons/apple-touch-icon.png',
];

self.addEventListener('install', (event) => {
  // Install fast — don't fail install if a single asset 404s.
  event.waitUntil(
    caches
      .open(SHELL_CACHE)
      .then((cache) => Promise.allSettled(SHELL_FILES.map((f) => cache.add(f))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((k) => ![SHELL_CACHE, RUNTIME_CACHE].includes(k))
            .map((k) => caches.delete(k))
        )
      )
      .then(() => self.clients.claim())
  );
});

const isHashedAsset = (url) =>
  url.pathname.startsWith('/assets/') || /\.[a-f0-9]{8,}\./.test(url.pathname);

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // Don't touch cross-origin (YouTube embeds, randomuser, mixkit, picsum, etc.)
  if (url.origin !== self.location.origin) return;

  // Navigation requests: try network first, fall back to cached index.html so
  // the SPA still boots offline.
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req).catch(() => caches.match('/index.html'))
    );
    return;
  }

  // Hashed build assets are immutable: cache-first, perpetual.
  if (isHashedAsset(url)) {
    event.respondWith(
      caches.match(req).then((hit) => {
        if (hit) return hit;
        return fetch(req).then((res) => {
          const copy = res.clone();
          caches.open(RUNTIME_CACHE).then((c) => c.put(req, copy));
          return res;
        });
      })
    );
    return;
  }

  // Everything else: network-first, fall back to cache.
  event.respondWith(
    fetch(req)
      .then((res) => {
        const copy = res.clone();
        caches.open(RUNTIME_CACHE).then((c) => c.put(req, copy));
        return res;
      })
      .catch(() => caches.match(req))
  );
});
