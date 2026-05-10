import { reactive, readonly } from 'vue';

// Module-level singleton — every component that calls usePwa() reads the
// same reactive state. The boot file `boot/pwa.ts` mutates this; components
// only read it (via the readonly proxy).

export interface PwaState {
  /** A beforeinstallprompt event was captured and an install can be invoked. */
  canInstall: boolean;
  /** App is currently running as an installed PWA (display-mode: standalone). */
  isInstalled: boolean;
  /** A new service worker is waiting to take over. */
  updateAvailable: boolean;
}

const state = reactive<PwaState>({
  canInstall: false,
  isInstalled: false,
  updateAvailable: false,
});

// Captured beforeinstallprompt event. Browser only lets us call .prompt() once
// per event; after that we have to wait for a fresh event (e.g. user visits
// again later). We re-arm canInstall when the OS hands us a new event.
let deferredPrompt: BeforeInstallPromptEvent | null = null;

// Service worker registration; populated from boot/pwa.ts after registration
// resolves. Used by applyUpdate() to message the waiting SW.
let registration: ServiceWorkerRegistration | null = null;

// Internal hooks for boot/pwa.ts to write state without exposing setters
// to general components.
export const _internalPwa = {
  setRegistration(reg: ServiceWorkerRegistration) {
    registration = reg;
  },
  setDeferredPrompt(e: BeforeInstallPromptEvent | null) {
    deferredPrompt = e;
    state.canInstall = !!e;
  },
  markInstalled() {
    state.isInstalled = true;
    state.canInstall = false;
    deferredPrompt = null;
  },
  markUpdateAvailable() {
    state.updateAvailable = true;
  },
  detectStandalone() {
    if (typeof window === 'undefined') return;
    const matched = window.matchMedia?.('(display-mode: standalone)').matches;
    // iOS Safari uses navigator.standalone instead of matchMedia.
    const iosStandalone =
      typeof navigator !== 'undefined' &&
      (navigator as Navigator & { standalone?: boolean }).standalone === true;
    if (matched || iosStandalone) {
      state.isInstalled = true;
    }
  },
};

export function usePwa() {
  /** Trigger the captured install prompt. Resolves to true if the user accepted. */
  async function install(): Promise<boolean> {
    if (!deferredPrompt) return false;
    try {
      await deferredPrompt.prompt();
      const choice = await deferredPrompt.userChoice;
      // Per spec, the event is consumed regardless of outcome.
      deferredPrompt = null;
      state.canInstall = false;
      return choice.outcome === 'accepted';
    } catch {
      return false;
    }
  }

  /** Activate the waiting service worker and reload to pick up its assets. */
  function applyUpdate(): void {
    if (!registration?.waiting) {
      // Fallback: just reload — some browsers replace the SW silently.
      window.location.reload();
      return;
    }
    // Once the new SW activates and takes control, the controllerchange
    // listener (in boot/pwa.ts) reloads the page.
    registration.waiting.postMessage({ type: 'SKIP_WAITING' });
  }

  return {
    state: readonly(state) as Readonly<PwaState>,
    install,
    applyUpdate,
  };
}

// ---- Type augmentation for the non-standard prompt event ------------------
declare global {
  // The HTML spec defines this in the install-app section but TS lib.dom does
  // not yet include it.
  interface BeforeInstallPromptEvent extends Event {
    readonly platforms: string[];
    readonly userChoice: Promise<{
      outcome: 'accepted' | 'dismissed';
      platform: string;
    }>;
    prompt(): Promise<void>;
  }

  interface WindowEventMap {
    beforeinstallprompt: BeforeInstallPromptEvent;
    appinstalled: Event;
  }
}
