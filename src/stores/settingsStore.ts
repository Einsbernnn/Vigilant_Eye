import { defineStore } from 'pinia';

const ACCENT_PRESETS = {
  violet: '#9c27b0',
  teal: '#26a69a',
  orange: '#fb8c00',
  red: '#c10015',
  green: '#21ba45',
} as const;

export type AccentPreset = keyof typeof ACCENT_PRESETS;

const applyAccent = (hex: string) => {
  if (typeof document !== 'undefined') {
    document.documentElement.style.setProperty('--q-accent', hex);
  }
};

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    liveStreamUrl: 'http://192.168.100.24:5002',
    uploadApiUrl: 'http://192.168.100.24:5000',
    enableCameraLight: false,
    enableCameraPanning: false,
    // Demo / placeholder mode. Defaults to true everywhere so dev and the
    // Vercel deploy both render mock data without a reachable Pi. Flip via
    // settingsStore.updateDemoMode(false) when you're back on the Pi network.
    demoMode: true,
    // URL shown on the live-stream tile when demoMode is on. Recognized forms:
    //   - YouTube watch / youtu.be / embed / live  → <iframe> embed
    //   - .mp4 / .webm / .mov / .m4v / .ogv         → <video>
    //   - anything else                              → <img> (for MJPEG / static)
    // Default is Jackson Hole Town Square — a long-running 24/7 outdoor live
    // cam that feels like real surveillance footage.
    demoLiveStreamUrl: 'https://www.youtube.com/watch?v=1EiC9bvVGnk',
    // Whether $q.notify toast events should also play a short beep. Pure UI
    // pref, no backend. Default off so the demo doesn't beep at first load.
    notificationSound: false,
    // Accent color preset, mirrored into the --q-accent CSS variable so the
    // Settings drawer can re-skin the app at runtime.
    accentColor: 'violet' as AccentPreset,
  }),
  getters: {
    accentHex: (state) => ACCENT_PRESETS[state.accentColor],
  },
  actions: {
    updateLiveStreamUrl(url: string) {
      this.liveStreamUrl = url;
    },
    updateUploadApiUrl(url: string) {
      this.uploadApiUrl = url;
    },
    updateCameraLight(enabled: boolean) {
      this.enableCameraLight = enabled;
    },
    updateCameraPanning(enabled: boolean) {
      this.enableCameraPanning = enabled;
    },
    updateDemoMode(enabled: boolean) {
      this.demoMode = enabled;
    },
    updateDemoLiveStreamUrl(url: string) {
      this.demoLiveStreamUrl = url;
    },
    updateNotificationSound(enabled: boolean) {
      this.notificationSound = enabled;
    },
    updateAccentColor(name: AccentPreset) {
      this.accentColor = name;
      applyAccent(ACCENT_PRESETS[name]);
    },
    // Call once on app boot so the saved accent re-applies on reload.
    syncAccentToDom() {
      applyAccent(ACCENT_PRESETS[this.accentColor]);
    },
  },
});

export const accentPresets = ACCENT_PRESETS;
