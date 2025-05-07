import { defineStore } from 'pinia';

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    liveStreamUrl: 'http://192.168.100.24:5002',
    uploadApiUrl: 'http://192.168.100.24:5000',
    enableCameraLight: false,
    enableCameraPanning: false,
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
  },
});
