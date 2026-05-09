<template>
  <q-page class="q-px-xl q-pt-xl">
    <div class="stream-wrapper">
      <div class="video-container">
        <div class="panel-label">Live Stream</div>
        <!-- Demo mode: YouTube iframe, video file, or static image. Real mode: <img> for MJPEG. -->
        <iframe
          v-if="streamingActive && demoIsYoutube"
          class="video-element"
          :class="{ 'video-glow': streamingActive }"
          :src="youtubeEmbedUrl"
          frameborder="0"
          allow="autoplay; encrypted-media; picture-in-picture"
          allowfullscreen
        />
        <video
          v-else-if="streamingActive && demoIsVideo"
          ref="demoVideoEl"
          class="video-element"
          :class="{ 'video-glow': streamingActive }"
          :src="videoSrc"
          :muted="true"
          loop
          autoplay
          playsinline
          @loadedmetadata="onDemoVideoReady"
          @error="onStreamError"
        />
        <img
          v-else-if="streamingActive"
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

        <div v-if="settingsStore.demoMode" class="demo-banner">
          <q-icon name="science" size="16px" class="q-mr-xs" />
          Demo mode &middot; placeholder feed
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
import { useNotificationStore } from 'stores/notificationStore';
import { onBeforeRouteLeave } from 'vue-router';
import { useQuasar } from 'quasar';
import {
  buildRandomDemoNotification,
  buildDemoNotificationSeed,
} from 'src/demo/demoData';

const $q = useQuasar();
const settingsStore = useSettingsStore();
const notificationStore = useNotificationStore();
// In demo mode, start streaming immediately so the placeholder video plays on
// page load. In real mode, the user clicks ▶ to connect to the Pi.
const streamingActive = ref(settingsStore.demoMode);
const recordingActive = ref(false);
const recordingFolder = ref('');
const demoVideoEl = ref<HTMLVideoElement | null>(null);

const onDemoVideoReady = () => {
  const el = demoVideoEl.value;
  if (!el) return;
  // Belt-and-braces: explicitly set muted as a property and kick off play().
  // Chrome's autoplay policy checks the property, not just the attribute.
  el.muted = true;
  const playPromise = el.play();
  if (playPromise && typeof playPromise.catch === 'function') {
    playPromise.catch(() => {
      // Autoplay was blocked; the user can press play manually.
    });
  }
};

const videoSrc = computed(() => {
  if (!streamingActive.value) return '';
  return settingsStore.demoMode
    ? settingsStore.demoLiveStreamUrl
    : `${settingsStore.liveStreamUrl}/video`;
});

const youtubeIdFromUrl = (url: string): string | null => {
  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/live\/)([a-zA-Z0-9_-]{11})/,
  ];
  for (const p of patterns) {
    const m = url.match(p);
    if (m) return m[1];
  }
  return null;
};

const demoIsYoutube = computed(() => {
  if (!settingsStore.demoMode) return false;
  return youtubeIdFromUrl(settingsStore.demoLiveStreamUrl) !== null;
});

const youtubeEmbedUrl = computed(() => {
  const id = youtubeIdFromUrl(settingsStore.demoLiveStreamUrl);
  if (!id) return '';
  // autoplay + mute (required by browsers for autoplay), no controls/branding,
  // loop the same id as a fallback in case the live stream ends.
  const params = new URLSearchParams({
    autoplay: '1',
    mute: '1',
    controls: '0',
    playsinline: '1',
    modestbranding: '1',
    rel: '0',
    loop: '1',
    playlist: id,
  });
  return `https://www.youtube.com/embed/${id}?${params.toString()}`;
});

const demoIsVideo = computed(() => {
  if (!settingsStore.demoMode) return false;
  if (demoIsYoutube.value) return false;
  return /\.(mp4|webm|mov|m4v|ogv)(\?.*)?$/i.test(
    settingsStore.demoLiveStreamUrl
  );
});

const connectionStatus = reactive(
  settingsStore.demoMode
    ? { color: 'purple', icon: 'science', text: 'Demo' }
    : { color: 'green', icon: 'check_circle', text: 'Connected' }
);

const notifications = computed(() => notificationStore.notifications);

const addNotification = (message: string) => {
  notificationStore.addNotification(message);
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
  } else if (settingsStore.demoMode) {
    connectionStatus.color = 'purple';
    connectionStatus.icon = 'science';
    connectionStatus.text = 'Demo';
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
  if (settingsStore.demoMode) {
    recordingActive.value = !recordingActive.value;
    addNotification(
      recordingActive.value
        ? 'Demo recording started (no file is actually saved).'
        : 'Demo recording stopped.'
    );
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
  // In demo mode the source is a static asset; transient load hiccups (slow
  // network, momentary CDN errors) shouldn't kill the stream — let the browser
  // retry on its own.
  if (settingsStore.demoMode) return;
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

let pirPollTimer: ReturnType<typeof setInterval> | null = null;
let demoNotifTimer: ReturnType<typeof setTimeout> | null = null;

const fireDemoNotification = () => {
  const n = buildRandomDemoNotification();
  addNotification(n.message);
  $q.notify({
    type: n.level,
    message: n.message,
    timeout: 4000,
    position: 'top-right',
  });
};

const scheduleNextDemoNotification = () => {
  // Random 12–22s gap so the feed feels organic instead of metronomic.
  const delayMs = 12_000 + Math.floor(Math.random() * 10_000);
  demoNotifTimer = setTimeout(() => {
    fireDemoNotification();
    scheduleNextDemoNotification();
  }, delayMs);
};

onMounted(() => {
  window.addEventListener('beforeunload', beforeUnloadHandler);

  if (settingsStore.demoMode) {
    // Seed the panel so it isn't empty on first paint, then start the
    // randomized trigger loop. Skips the real Pi poller entirely.
    if (notificationStore.notifications.length === 0) {
      buildDemoNotificationSeed().forEach((n) => addNotification(n.message));
    }
    scheduleNextDemoNotification();
    return;
  }

  // Poll for PIR notifications every 2 seconds
  pirPollTimer = setInterval(async () => {
    try {
      const res = await fetch(
        `${settingsStore.liveStreamUrl}/pir-notification`
      );
      if (res.ok) {
        const data = await res.json();
        if (data.notification) {
          addNotification(data.notification);
          $q.notify({
            type: 'warning',
            message: data.notification,
            timeout: 5000,
            position: 'top-right',
          });
        }
      }
    } catch (e) {
      // Ignore errors
    }
  }, 2000);
});
onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', beforeUnloadHandler);
  if (pirPollTimer) clearInterval(pirPollTimer);
  if (demoNotifTimer) clearTimeout(demoNotifTimer);
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
  border: 0;
  display: block;
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

.demo-banner {
  position: absolute;
  top: 16px;
  left: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(76, 6, 92, 0.7);
  color: #f3eafa;
  border-radius: 8px;
  font-size: 0.75rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  backdrop-filter: blur(6px);
  z-index: 2;
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
