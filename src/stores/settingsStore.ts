import { defineStore } from 'pinia';

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
  }),
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
  },
});
