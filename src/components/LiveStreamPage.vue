<template>
  <q-page class="q-px-xl q-pt-xl">
    <div class="stream-wrapper">
      <div class="video-container">
        <!-- Use <img> for MJPEG streams -->
        <img
          v-if="streamingActive"
          ref="videoPlayer"
          class="video-element"
          :class="{ 'video-glow': streamingActive }"
          :src="videoSrc"
          @error="onStreamError"
          alt="Live Stream"
        />
        <div v-else class="video-element video-placeholder">
          <span class="placeholder-text">Stream is paused</span>
        </div>

        <div class="overlay-controls">
          <q-btn
            round
            :icon="streamingActive ? 'pause' : 'play_arrow'"
            :color="streamingActive ? 'accent' : 'primary'"
            size="lg"
            class="shadow-5"
            @click="toggleStream"
          />

          <q-chip
            v-if="connectionStatus"
            :color="connectionStatus.color"
            text-color="white"
            class="status-chip"
          >
            <q-avatar :icon="connectionStatus.icon" />
            {{ connectionStatus.text }}
          </q-chip>
        </div>
      </div>

      <div class="placeholder-panel q-mt-lg">
        <p class="placeholder-text"></p>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue';

const streamingActive = ref(false);
const videoSrc = computed(() =>
  streamingActive.value ? 'http://192.168.100.24:5000/video' : ''
);
const connectionStatus = reactive({
  color: 'green',
  icon: 'check_circle',
  text: 'Connected',
});

const toggleStream = () => {
  streamingActive.value = !streamingActive.value;
  if (!streamingActive.value) {
    connectionStatus.color = 'grey';
    connectionStatus.icon = 'pause_circle';
    connectionStatus.text = 'Paused';
  } else {
    connectionStatus.color = 'green';
    connectionStatus.icon = 'check_circle';
    connectionStatus.text = 'Connected';
  }
};

const onStreamError = () => {
  connectionStatus.color = 'red';
  connectionStatus.icon = 'error';
  connectionStatus.text = 'Stream Error';
  streamingActive.value = false;
};
</script>

<style lang="scss" scoped>
.stream-wrapper {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.video-container {
  flex: 2;
  position: relative;
  border-radius: 16px;
  overflow: hidden;
  background: #000;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  transition: transform 0.3s ease;

  &:hover {
    transform: translateY(-2px);
  }
}

.video-element {
  width: 100%;
  height: 70vh;
  object-fit: cover;
}

.video-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #222;
  color: #ccc;
  width: 100%;
  height: 70vh;
}

.video-glow {
  box-shadow: 0 0 30px rgba(66, 133, 244, 0.2);
}

.overlay-controls {
  position: absolute;
  bottom: 20px;
  left: 20px;
  display: flex;
  gap: 15px;
  align-items: center;
}

.status-chip {
  backdrop-filter: blur(5px);
  background: rgba(255, 255, 255, 0.1) !important;
}

.placeholder-panel {
  flex: 1;
  padding: 20px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  backdrop-filter: blur(5px);
  display: flex;
  justify-content: center;
  align-items: center;
}

.placeholder-text {
  font-size: 1.2em;
  color: #ccc;
  text-align: center;
}
</style>
