<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="bg-dark">
      <q-toolbar class="q-pl-xl">
        <q-avatar square size="lg">
          <img src="src/assets/rpi-logo.svg" />
        </q-avatar>

        <q-toolbar-title class="text-h5 text-weight-bold text-white">
          PiVision
        </q-toolbar-title>

        <q-space />

        <div class="row items-center q-gutter-xl">
          <q-tabs inline-label active-color="accent" indicator-color="accent">
            <q-route-tab
              to="/live-stream"
              label="Live Stream"
              icon="live_tv"
              content-class="text-white"
            />
            <q-route-tab
              to="/saved-videos"
              label="Media Library"
              icon="video_library"
              content-class="text-white"
            />
            <q-route-tab
              to="/upload-pictures"
              label="Face Recognition"
              icon="camera_enhance"
              content-class="text-white"
            />
          </q-tabs>
        </div>

        <div class="row items-center q-gutter-sm q-ml-xl">
          <q-btn
            round
            flat
            :icon="darkModeIcon"
            color="white"
            @click="toggleDarkMode"
          />
          <q-btn
            round
            flat
            icon="settings"
            color="white"
            @click="openSettings"
          />
          <q-btn round flat icon="logout" color="white" @click="logout" />
        </div>
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>

    <q-dialog v-model="showLogoutDialog" persistent>
      <q-card class="logout-dialog-card" style="width: 400px; max-width: 90vw">
        <q-card-section class="bg-accent text-white q-pa-md">
          <div class="row items-center no-wrap">
            <q-icon name="logout" size="sm" class="q-mr-sm" />
            <div class="text-h6">Confirm Logout</div>
          </div>
        </q-card-section>

        <q-separator color="accent" />

        <q-card-section class="q-pt-lg q-pb-md text-body1">
          <div class="row items-center q-mb-sm">
            <q-icon name="warning" color="warning" class="q-mr-sm" size="sm" />
            Are you sure you want to log out?
          </div>
        </q-card-section>

        <q-card-actions align="right" class="q-px-md q-pb-md">
          <q-btn
            flat
            label="Cancel"
            color="grey-7"
            class="q-px-lg"
            v-close-popup
            unelevated
          />
          <q-btn
            label="Logout"
            color="negative"
            class="q-px-lg"
            @click="confirmLogout"
            push
            unelevated
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <q-dialog v-model="showSettingsDialog" persistent>
      <q-card
        class="settings-dialog-card"
        style="width: 400px; max-width: 90vw"
      >
        <q-card-section class="bg-accent text-white q-pa-md">
          <div class="row items-center no-wrap">
            <q-icon name="settings" size="sm" class="q-mr-sm" />
            <div class="text-h6">Settings</div>
          </div>
        </q-card-section>

        <q-separator color="accent" />

        <q-card-section class="q-pt-lg q-pb-md text-body1">
          <q-input
            v-model="settings.liveStreamUrl"
            label="Live Stream URL"
            filled
          />
          <q-input
            v-model="settings.uploadApiUrl"
            label="Upload API URL"
            filled
            class="q-mt-md"
          />
        </q-card-section>

        <q-card-actions align="right" class="q-px-md q-pb-md">
          <q-btn
            flat
            label="Cancel"
            color="grey-7"
            class="q-px-lg"
            v-close-popup
            unelevated
          />
          <q-btn
            label="Save"
            color="positive"
            class="q-px-lg"
            @click="saveSettings"
            push
            unelevated
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-layout>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { useUserStore } from 'stores/userStore';
import { useRouter } from 'vue-router';
import { ref, computed } from 'vue';
import { useSettingsStore } from 'stores/settingsStore';

const $q = useQuasar();
const userStore = useUserStore();
const router = useRouter();
const showLogoutDialog = ref(false);
const showSettingsDialog = ref(false);
const settings = ref({
  liveStreamUrl: '',
  uploadApiUrl: '',
});

const toggleDarkMode = () => {
  $q.dark.toggle();
};

const logout = () => {
  showLogoutDialog.value = true;
};

const confirmLogout = () => {
  userStore.logout();
  router.push('/login');
  showLogoutDialog.value = false;
};

const openSettings = () => {
  showSettingsDialog.value = true;
};

const saveSettings = () => {
  const settingsStore = useSettingsStore();

  if (settings.value.liveStreamUrl.trim()) {
    settingsStore.updateLiveStreamUrl(settings.value.liveStreamUrl);
  } else {
    settings.value.liveStreamUrl = settingsStore.liveStreamUrl;
  }

  if (settings.value.uploadApiUrl.trim()) {
    settingsStore.updateUploadApiUrl(settings.value.uploadApiUrl);
  } else {
    settings.value.uploadApiUrl = settingsStore.uploadApiUrl;
  }

  showSettingsDialog.value = false;
};

const darkModeIcon = computed(() =>
  $q.dark.isActive ? 'light_mode' : 'dark_mode'
);
</script>

<style lang="scss">
.q-header {
  background: linear-gradient(145deg, #1a1a1a 0%, #2d2d2d 100%);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.q-tab__icon {
  font-size: 1.4rem;
}
</style>
