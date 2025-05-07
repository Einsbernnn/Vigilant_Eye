<template>
  <q-page class="q-px-xl q-pt-xl">
    <div class="stream-wrapper">
      <div class="video-container">
        <div class="panel-label">Live Stream</div>
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
          >
            <q-tooltip>Toggle Stream</q-tooltip>
          </q-btn>
          <q-btn
            round
            icon="fiber_manual_record"
            :color="recordingActive ? 'red' : 'grey'"
            size="md"
            class="shadow-5"
            @click="toggleRecording"
          >
            <q-tooltip>Toggle Recording</q-tooltip>
          </q-btn>
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
            Recording... {{ formatRecordingDuration }}
          </q-chip>
        </div>
      </div>

      <div class="notification-panel-container" style="height: 75.5vh">
        <div class="panel-label">Notifications</div>
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
import {
  ref,
  reactive,
  computed,
  onMounted,
  onBeforeUnmount,
  watch,
} from 'vue';
import { useSettingsStore } from 'stores/settingsStore';
import { onBeforeRouteLeave } from 'vue-router';

const streamingActive = ref(false);
const recordingActive = ref(false);
const recordingFolder = ref('');
const settingsStore = useSettingsStore();
const videoSrc = computed(() =>
  streamingActive.value ? `${settingsStore.liveStreamUrl}/video` : ''
);
const connectionStatus = reactive({
  color: 'green',
  icon: 'check_circle',
  text: 'Connected',
});

const notifications = ref<string[]>([]);

const addNotification = (message: string) => {
  notifications.value.push(message);
  if (notifications.value.length > 50) {
    notifications.value.shift();
  }
};

// Add this notification when recording starts
watch(recordingActive, (newVal) => {
  if (newVal) {
    addNotification(
      'Recording is in progress. If you leave or refresh, the recording will stop.'
    );
  }
});

const recordingDuration = ref(0); // seconds
let recordingTimer: ReturnType<typeof setInterval> | null = null;

const formatRecordingDuration = computed(() => {
  const h = Math.floor(recordingDuration.value / 3600)
    .toString()
    .padStart(2, '0');
  const m = Math.floor((recordingDuration.value % 3600) / 60)
    .toString()
    .padStart(2, '0');
  const s = (recordingDuration.value % 60).toString().padStart(2, '0');
  return `${h}:${m}:${s}`;
});

watch(recordingActive, (newVal) => {
  if (newVal) {
    recordingDuration.value = 0;
    if (recordingTimer) clearInterval(recordingTimer);
    recordingTimer = setInterval(() => {
      recordingDuration.value++;
    }, 1000);
  } else {
    if (recordingTimer) clearInterval(recordingTimer);
    recordingTimer = null;
  }
});

onBeforeUnmount(() => {
  if (recordingTimer) clearInterval(recordingTimer);
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
    connectionStatus.text = 'Live';
  }
};

const getFrontendTimestamp = () => {
  const now = new Date();
  // Folder: 'May, 07, 2025 - 14:23:45'
  const folder = now
    .toLocaleString('en-US', {
      month: 'short',
      day: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    })
    .replace(/,/, ',')
    .replace(/\//g, ',')
    .replace(/ /g, ' ')
    .replace(/:/g, ':');
  // File: '2025-05-07_14-23-45.mov'
  const pad = (n: number) => n.toString().padStart(2, '0');
  const file = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(
    now.getDate()
  )}_${pad(now.getHours())}-${pad(now.getMinutes())}-${pad(
    now.getSeconds()
  )}.mov`;
  return { folder, file };
};

const toggleRecording = async () => {
  if (!streamingActive.value) {
    addNotification('Cannot start recording. Stream is not active.');
    return;
  }
  if (!recordingActive.value) {
    // Start recording
    try {
      const { folder, file } = getFrontendTimestamp();
      const res = await fetch(
        `${settingsStore.liveStreamUrl}/start-recording`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ folder_name: folder, filename: file }),
        }
      );
      if (!res.ok) {
        const data = await res.json();
        addNotification(
          `Failed to start recording: ${data.error || res.statusText}`
        );
        return;
      }
      const data = await res.json();
      recordingActive.value = true;
      recordingFolder.value = data.folder;
      addNotification(`Recording started: ${data.folder}`);
    } catch (e) {
      addNotification('Failed to start recording.');
    }
  } else {
    // Stop recording
    try {
      const res = await fetch(`${settingsStore.liveStreamUrl}/stop-recording`, {
        method: 'POST',
      });
      if (!res.ok) {
        const data = await res.json();
        addNotification(
          `Failed to stop recording: ${data.error || res.statusText}`
        );
        return;
      }
      const data = await res.json();
      recordingActive.value = false;
      addNotification(`Recording stopped. Saved in: ${data.folder}`);
    } catch (e) {
      addNotification('Failed to stop recording.');
    }
  }
};

const onStreamError = () => {
  connectionStatus.color = 'red';
  connectionStatus.icon = 'error';
  connectionStatus.text = 'Stream Error';
  streamingActive.value = false;
};

const showRecordingWarning = ref(false);

// Warn on browser refresh/close
const beforeUnloadHandler = (e: BeforeUnloadEvent) => {
  if (recordingActive.value) {
    e.preventDefault();
    e.returnValue =
      'Recording is in progress. If you leave or refresh, the recording will stop.';
    return e.returnValue;
  }
};

onMounted(() => {
  window.addEventListener('beforeunload', beforeUnloadHandler);
});
onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', beforeUnloadHandler);
});

// Vue router navigation guard
onBeforeRouteLeave((to, from, next) => {
  if (recordingActive.value) {
    showRecordingWarning.value = true;
    if (
      confirm(
        'Recording is in progress. If you leave this page, the recording will stop. Are you sure you want to leave?'
      )
    ) {
      showRecordingWarning.value = false;
      next();
    } else {
      showRecordingWarning.value = false;
      next(false);
    }
  } else {
    next();
  }
});
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
  background: rgba(0, 0, 0, 1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.9);
}

.notification-panel {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  background: rgba(0, 0, 0, 0.1);
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

.panel-label {
  font-size: 1.2em;
  font-weight: bold;
  color: #fff;
  margin-bottom: 10px;
  text-align: center;
}
</style>
