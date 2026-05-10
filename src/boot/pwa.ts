import { boot } from 'quasar/wrappers';
import { Notify } from 'quasar';
import { _internalPwa } from 'src/composables/usePwa';

// PWA boot: registers the service worker, captures beforeinstallprompt,
// detects display-mode, and surfaces "new version available" via Notify.
//
// This file replaces the inline <script> SW registration that used to live
// in index.html so we have access to Quasar's Notify plugin and Vue's
// reactivity for the install/update UI.

export default boot(() => {
  if (typeof window === 'undefined') return;

  _internalPwa.detectStandalone();

  // ---- beforeinstallprompt: cache the event so we can fire it on demand --
  window.addEventListener('beforeinstallprompt', (e) => {
    // Stop the browser's auto-prompt; we'll surface our own button instead.
    e.preventDefault();
    _internalPwa.setDeferredPrompt(e);
  });

  window.addEventListener('appinstalled', () => {
    _internalPwa.markInstalled();
    Notify.create({
      type: 'positive',
      message: 'Vigilant Eye installed.',
      icon: 'check_circle',
      timeout: 2500,
    });
  });

  // ---- Service worker --------------------------------------------------
  if (!('serviceWorker' in navigator)) return;

  let refreshing = false;

  // Reload exactly once after the new SW takes control. This fires when the
  // waiting SW responds to our SKIP_WAITING message and becomes the active
  // controller for this page.
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (refreshing) return;
    refreshing = true;
    window.location.reload();
  });

  navigator.serviceWorker
    .register('/sw.js')
    .then((registration) => {
      _internalPwa.setRegistration(registration);

      // If a SW was already waiting from a prior session, surface the prompt
      // immediately so the user can opt in.
      if (registration.waiting && navigator.serviceWorker.controller) {
        notifyUpdate(registration);
      }

      // A new SW is being installed — listen for it to finish.
      registration.addEventListener('updatefound', () => {
        const installing = registration.installing;
        if (!installing) return;
        installing.addEventListener('statechange', () => {
          // 'installed' + an existing controller means: a previous version is
          // already running and the new one is sitting idle waiting for a
          // controllerchange. That's our cue to ask the user to refresh.
          if (
            installing.state === 'installed' &&
            navigator.serviceWorker.controller
          ) {
            _internalPwa.markUpdateAvailable();
            notifyUpdate(registration);
          }
        });
      });

      // Poll for updates every 30 minutes while the tab is open. Cheap,
      // and far more responsive than waiting for the user to navigate away.
      setInterval(() => {
        registration.update().catch(() => {
          /* offline / network error — try again next interval */
        });
      }, 30 * 60 * 1000);
    })
    .catch((err) => {
      // Don't break the app boot if SW registration fails (private browsing,
      // unsupported browser, file://, etc.).
      // eslint-disable-next-line no-console
      console.warn('[Vigilant] SW registration failed:', err);
    });
});

function notifyUpdate(registration: ServiceWorkerRegistration) {
  Notify.create({
    type: 'info',
    message: 'A new version is available.',
    caption: 'Reload to get the latest features and fixes.',
    icon: 'system_update',
    timeout: 0, // sticky until the user picks an action
    position: 'bottom',
    color: 'accent',
    actions: [
      {
        label: 'Reload',
        color: 'white',
        handler: () => {
          if (registration.waiting) {
            registration.waiting.postMessage({ type: 'SKIP_WAITING' });
          } else {
            window.location.reload();
          }
        },
      },
      {
        label: 'Later',
        color: 'white',
        handler: () => {
          /* dismiss; user will see prompt again on next deploy */
        },
      },
    ],
  });
}
