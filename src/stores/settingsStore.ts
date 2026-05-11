import { defineStore } from 'pinia';

// Each preset ships a full palette so the entire app re-skins on accent change.
//   - main / dark: the bold colors used on buttons, active states, gradients
//   - rgb / darkRgb: RGB triplets so rgba(..., alpha) compositing works
//   - bgLight / bgLightDeep: the page background in light mode — a tonal
//     (same-hue, heavily-desaturated) shade of the accent. Subtle enough to
//     recede behind content, distinct enough to feel branded.
//   - bgDark / bgDarkDeep: same idea for dark mode — near-black with the
//     faintest hint of the accent hue.
//
// Surface tokens (card / elevated / etc.) are mode-driven, not preset-driven,
// so cards stay clean (white on light, alpha-white on dark) and don't pick
// up a hue cast that would fight with content.
interface AccentPalette {
  main: string;
  dark: string;
  rgb: string;
  darkRgb: string;
  bgLight: string;
  bgLightDeep: string;
  bgDark: string;
  bgDarkDeep: string;
}

const ACCENT_PRESETS: Record<string, AccentPalette> = {
  violet: {
    main: '#9c27b0',
    dark: '#4c065c',
    rgb: '156, 39, 176',
    darkRgb: '76, 6, 92',
    bgLight: '#f7f4f8',
    bgLightDeep: '#ede8ef',
    bgDark: '#131015',
    bgDarkDeep: '#08070a',
  },
  teal: {
    main: '#26a69a',
    dark: '#004d40',
    rgb: '38, 166, 154',
    darkRgb: '0, 77, 64',
    bgLight: '#f4f7f6',
    bgLightDeep: '#e8eded',
    bgDark: '#101415',
    bgDarkDeep: '#070a0a',
  },
  orange: {
    main: '#fb8c00',
    dark: '#bf360c',
    rgb: '251, 140, 0',
    darkRgb: '191, 54, 12',
    bgLight: '#f8f5f2',
    bgLightDeep: '#efebe5',
    bgDark: '#15110d',
    bgDarkDeep: '#0a0806',
  },
  red: {
    main: '#c10015',
    dark: '#7f0010',
    rgb: '193, 0, 21',
    darkRgb: '127, 0, 16',
    bgLight: '#f8f3f4',
    bgLightDeep: '#efe8e9',
    bgDark: '#151012',
    bgDarkDeep: '#0a0708',
  },
  green: {
    main: '#21ba45',
    dark: '#1b5e20',
    rgb: '33, 186, 69',
    darkRgb: '27, 94, 32',
    bgLight: '#f3f6f4',
    bgLightDeep: '#e8ede9',
    bgDark: '#101510',
    bgDarkDeep: '#070a07',
  },
};

export type AccentPreset = keyof typeof ACCENT_PRESETS;

const applyAccent = (name: AccentPreset) => {
  if (typeof document === 'undefined') return;
  const palette = ACCENT_PRESETS[name];
  const root = document.documentElement.style;
  root.setProperty('--q-accent', palette.main);
  root.setProperty('--vigilant-accent-dark', palette.dark);
  root.setProperty('--vigilant-accent-rgb', palette.rgb);
  root.setProperty('--vigilant-accent-dark-rgb', palette.darkRgb);
  // Tonal background colors: page bg adopts a heavily-desaturated tint of
  // the accent's hue so changing accent visibly retints the room without
  // ever looking loud. app.scss reads --vigilant-bg-light/-dark to switch
  // between modes.
  root.setProperty('--vigilant-bg-light', palette.bgLight);
  root.setProperty('--vigilant-bg-light-deep', palette.bgLightDeep);
  root.setProperty('--vigilant-bg-dark', palette.bgDark);
  root.setProperty('--vigilant-bg-dark-deep', palette.bgDarkDeep);
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
    // Accent color preset. Drives --q-accent + the vigilant-accent-* CSS
    // variables consumed by every gradient and tinted surface in the app.
    accentColor: 'violet' as AccentPreset,
  }),
  getters: {
    accentHex: (state) => ACCENT_PRESETS[state.accentColor].main,
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
      applyAccent(name);
    },
    // Call once on app boot so the saved accent re-applies on reload.
    syncAccentToDom() {
      applyAccent(this.accentColor);
    },
  },
});

// Picker UI in SettingsDrawer reads this for the swatch grid. Maps preset
// name → main hex so the grid shows each option's headline color.
export const accentPresets = Object.fromEntries(
  Object.entries(ACCENT_PRESETS).map(([name, p]) => [name, p.main])
) as Record<AccentPreset, string>;
