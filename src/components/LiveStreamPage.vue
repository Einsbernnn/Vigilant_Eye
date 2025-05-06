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
            size="md"
            class="shadow-5"
            @click="toggleStream"
          />
          <q-btn
            round
            icon="fiber_manual_record"
            :color="recordingActive ? 'red' : 'grey'"
            size="md"
            class="shadow-5"
            @click="toggleRecording"
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
          <q-chip
            v-if="recordingActive"
            color="red"
            text-color="white"
            class="status-chip"
          >
            <q-avatar icon="fiber_manual_record" />
            Recording...
          </q-chip>
        </div>
      </div>

      <div class="notification-panel-container">
        <div class="notification-panel">
          <div
            v-for="(notification, index) in notifications"
            :key="index"
            class="notification-item"
          >
            {{ notification }}
          </div>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
import { useSettingsStore } from 'stores/settingsStore';

const streamingActive = ref(false);
const recordingActive = ref(false);
const settingsStore = useSettingsStore();
const videoSrc = computed(() =>
  streamingActive.value ? `${settingsStore.liveStreamUrl}/video` : ''
);
const connectionStatus = reactive({
  color: 'green',
  icon: 'check_circle',
  text: 'Connected',
});

const notifications = ref<string[]>([
  'Stream started successfully.',
  'Recording started.',
  'Stream paused.',
  'Recording stopped.',
  'Stream started successfully.',
  'Recording started.',
  'Stream paused.',
  'Recording stopped.',
  'Stream started successfully.',
  'Recording started.',
  'Stream paused.',
  'Recording stopped.',
  'Stream started successfully.',
  'Recording started.',
  'Stream paused.',
  'Recording stopped.',
]);

// const addNotification = (message: string) => {
//   notifications.value.push(message);
//   if (notifications.value.length > 50) {
//     notifications.value.shift(); // Keep the list manageable
//   }
// };

const toggleStream = () => {
  streamingActive.value = !streamingActive.value;
  if (!streamingActive.value) {
    connectionStatus.color = 'grey';
    connectionStatus.icon = 'pause_circle';
    connectionStatus.text = 'Paused';
  } else {
    connectionStatus.color = 'green';
    connectionStatus.icon = 'check_circle';
    connectionStatus.text = 'Live';
  }
};

const toggleRecording = () => {
  recordingActive.value = !recordingActive.value;
  if (recordingActive.value) {
    console.log('Recording started');
  } else {
    console.log('Recording stopped');
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
  display: flex;
  align-items: center;
  gap: 8px;
}

.notification-panel-container {
  flex: 1;
  height: 70vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.05);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.notification-panel {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 16px;
}

.notification-item {
  padding: 8px;
  margin-bottom: 5px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  color: #fff;
  font-size: 0.9em;
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

.notification-item {
  padding: 8px;
  margin-bottom: 5px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  color: #fff;
  font-size: 0.9em;
}
</style>
