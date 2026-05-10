// Vigilant Eye service worker
//
// Strategy:
//   - Install:  precache the app shell, then wait. We do NOT call skipWaiting
//               here. The page (boot/pwa.ts) detects the waiting SW and asks
//               the user to reload via a Notify toast; on Reload it posts a
//               SKIP_WAITING message back, which lets us activate.
//   - Activate: clean up old caches, then claim controlled clients so the
//               very next navigation is served by us (no half-applied state).
//   - Fetch:    network-first for navigations, cache-first for hashed assets,
//               network-first-with-fallback for everything else.
//
// Bump CACHE_VERSION whenever cached shell entries change.

const CACHE_VERSION = 'v4';
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
  // No skipWaiting() — the page decides when to activate via SKIP_WAITING.
  event.waitUntil(
    caches
      .open(SHELL_CACHE)
      .then((cache) => Promise.allSettled(SHELL_FILES.map((f) => cache.add(f))))
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

// Page → SW handshake to apply an update. boot/pwa.ts posts this when the
// user clicks Reload on the "new version available" notification.
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
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
