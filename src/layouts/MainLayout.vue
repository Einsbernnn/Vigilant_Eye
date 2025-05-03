<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="bg-dark">
      <q-toolbar class="q-px-xl">
        <q-avatar square size="lg">
          <img src="https://cdn.quasar.dev/logo-v2/svg/logo-mono-white.svg" />
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
          </q-tabs>

          <q-btn
            round
            flat
            icon="dark_mode"
            color="white"
            @click="toggleDarkMode"
          />
        </div>
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';

const $q = useQuasar();

const toggleDarkMode = () => {
  $q.dark.toggle();
};
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
