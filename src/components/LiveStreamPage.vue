<template>
  <q-page class="q-px-md q-px-md-xl q-pt-md q-pt-md-xl live-page">
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

        <!-- Mock face-detection bounding box (synthetic; demo only) -->
        <transition name="fade">
          <svg
            v-if="
              detectionOverlayEnabled &&
              activeBox &&
              streamingActive &&
              !demoIsYoutube
            "
            class="detection-overlay"
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            <rect
              :x="activeBox.x"
              :y="activeBox.y"
              :width="activeBox.w"
              :height="activeBox.h"
              :stroke="activeBox.color"
              fill="none"
              stroke-width="0.6"
              vector-effect="non-scaling-stroke"
            />
            <foreignObject
              :x="activeBox.x"
              :y="Math.max(0, activeBox.y - 6)"
              :width="activeBox.w"
              height="6"
            >
              <div
                class="detection-overlay__label"
                :style="{ background: activeBox.color }"
              >
                {{ activeBox.label }}
              </div>
            </foreignObject>
          </svg>
        </transition>

        <div v-if="settingsStore.demoMode" class="demo-banner">
          <q-icon name="science" size="16px" class="q-mr-xs" />
          <span class="demo-banner__text">
            Demo mode &middot; placeholder feed
          </span>
          <span class="demo-banner__short">DEMO</span>
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
            <q-tooltip>Toggle stream</q-tooltip>
          </q-btn>
          <q-btn
            round
            icon="fiber_manual_record"
            :color="recordingActive ? 'red' : 'grey-7'"
            size="md"
            class="shadow-5"
            @click="toggleRecording"
          >
            <q-tooltip>Toggle recording</q-tooltip>
          </q-btn>
          <q-btn
            round
            icon="add_a_photo"
            color="grey-7"
            size="md"
            class="shadow-5"
            :disable="!canSnapFromFeed"
            @click="openSnapDialog"
          >
            <q-tooltip>
              {{
                canSnapFromFeed
                  ? 'Snap a frame to dataset'
                  : 'Snap unavailable on YouTube source'
              }}
            </q-tooltip>
          </q-btn>
          <q-btn
            round
            :icon="detectionOverlayEnabled ? 'crop_free' : 'visibility_off'"
            :color="detectionOverlayEnabled ? 'accent' : 'grey-7'"
            size="md"
            class="shadow-5"
            :disable="demoIsYoutube"
            @click="detectionOverlayEnabled = !detectionOverlayEnabled"
          >
            <q-tooltip>
              {{
                demoIsYoutube
                  ? 'Detection overlay unavailable on YouTube source'
                  : detectionOverlayEnabled
                  ? 'Hide detection overlay'
                  : 'Show detection overlay'
              }}
            </q-tooltip>
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
            Recording {{ formatRecordingDuration }}
          </q-chip>
        </div>
      </div>

      <div class="notification-panel-container">
        <div class="notification-panel-header">
          <q-icon name="notifications_active" size="sm" color="accent" />
          <span class="text-weight-bold">Notifications</span>
          <q-badge
            v-if="filteredNotifications.length"
            color="accent"
            text-color="white"
            class="q-ml-sm"
          >
            {{ filteredNotifications.length }}
          </q-badge>
          <q-space />
          <q-btn
            v-if="notifications.length"
            flat
            round
            dense
            icon="clear_all"
            color="grey-5"
            @click="clearAllNotifications"
          >
            <q-tooltip>Clear all</q-tooltip>
          </q-btn>
        </div>
        <q-input
          v-model="notifSearch"
          dense
          dark
          outlined
          color="accent"
          placeholder="Search notifications"
          clearable
          class="notif-search"
        >
          <template v-slot:prepend>
            <q-icon name="search" />
          </template>
        </q-input>
        <div class="notif-filters">
          <q-chip
            v-for="opt in notifFilterOptions"
            :key="opt.value"
            clickable
            :selected="notifFilters.has(opt.value)"
            :color="notifFilters.has(opt.value) ? 'accent' : 'grey-9'"
            text-color="white"
            size="sm"
            dense
            @click="toggleNotifFilter(opt.value)"
          >
            {{ opt.label }}
          </q-chip>
        </div>
        <div class="notification-panel">
          <div
            v-if="!filteredNotifications.length"
            class="text-grey text-center q-py-md"
          >
            {{
              notifications.length
                ? 'No notifications match the current filter.'
                : 'No notifications yet.'
            }}
          </div>
          <div
            v-for="(item, index) in filteredNotifications"
            :key="index"
            class="notification-item"
            :class="`notification-item--${item.severity}`"
          >
            <q-icon
              :name="severityIcon(item.severity)"
              size="14px"
              class="q-mr-xs"
            />
            <span>{{ item.message }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Snap-from-feed dialog -->
    <q-dialog v-model="snapDialog" :maximized="$q.screen.lt.sm">
      <q-card class="snap-dialog-card">
        <q-card-section class="row items-center vigilant-demo-banner q-pa-md">
          <q-icon name="add_a_photo" size="sm" class="q-mr-sm" />
          <div class="text-h6">Save frame to dataset</div>
          <q-space />
          <q-btn flat round dense icon="close" v-close-popup />
        </q-card-section>
        <q-card-section>
          <q-img
            v-if="snapPreviewUrl"
            :src="snapPreviewUrl"
            :ratio="16 / 9"
            class="q-mb-md"
            style="border-radius: 8px"
          />
          <q-btn-toggle
            v-model="snapFolderMode"
            spread
            no-caps
            unelevated
            toggle-color="accent"
            class="q-mb-md"
            :options="[
              { label: 'Existing', value: 'existing', icon: 'folder_open' },
              { label: 'New', value: 'new', icon: 'person_add' },
            ]"
          />
          <q-select
            v-if="snapFolderMode === 'existing'"
            v-model="snapExistingFolder"
            :options="existingFolderOptions"
            label="Folder"
            outlined
            dark
            color="accent"
            emit-value
            map-options
          />
          <q-input
            v-else
            v-model="snapNewFolder"
            label="New folder name"
            outlined
            dark
            color="accent"
          />
        </q-card-section>
        <q-card-actions align="right" class="q-px-md q-pb-md">
          <q-btn flat label="Cancel" color="grey-6" v-close-popup />
          <q-btn
            unelevated
            color="accent"
            icon="save"
            label="Save to dataset"
            :disable="!canSubmitSnap"
            @click="confirmSnap"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
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
  demoImageFolders,
  findDemoImageFolder,
} from 'src/demo/demoData';
import {
  demoState,
  addDemoFolder,
  addDemoImages,
  getDemoExtraImages,
} from 'src/demo/demoState';

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

// ---- Notification severity classification + filtering --------------------
type Severity = 'motion' | 'known' | 'unknown' | 'telegram' | 'system';

const classifyNotification = (raw: string): Severity => {
  const m = raw.toLowerCase();
  if (m.includes('telegram')) return 'telegram';
  if (m.includes('intruder') || m.includes('unknown')) return 'unknown';
  if (m.includes('known face') || m.includes('recognized')) return 'known';
  if (m.includes('motion') || m.includes('pir')) return 'motion';
  return 'system';
};

const severityIcon = (s: Severity): string => {
  switch (s) {
    case 'motion':
      return 'directions_run';
    case 'known':
      return 'verified';
    case 'unknown':
      return 'priority_high';
    case 'telegram':
      return 'chat';
    case 'system':
    default:
      return 'info';
  }
};

const notifFilterOptions: { value: Severity; label: string }[] = [
  { value: 'motion', label: 'Motion' },
  { value: 'known', label: 'Known' },
  { value: 'unknown', label: 'Unknown' },
  { value: 'telegram', label: 'Telegram' },
  { value: 'system', label: 'System' },
];
// Empty Set means "show all". Selecting any chip narrows the view to those.
const notifFilters = ref<Set<Severity>>(new Set());
const notifSearch = ref('');

const toggleNotifFilter = (sev: Severity) => {
  const next = new Set(notifFilters.value);
  if (next.has(sev)) {
    next.delete(sev);
  } else {
    next.add(sev);
  }
  notifFilters.value = next;
};

const filteredNotifications = computed(() => {
  const q = notifSearch.value.trim().toLowerCase();
  return notifications.value
    .map((message) => ({ message, severity: classifyNotification(message) }))
    .filter((entry) => {
      if (notifFilters.value.size && !notifFilters.value.has(entry.severity)) {
        return false;
      }
      if (q && !entry.message.toLowerCase().includes(q)) {
        return false;
      }
      return true;
    })
    .slice()
    .reverse(); // newest first
});

const clearAllNotifications = () => {
  notificationStore.clearNotifications();
};

// ---- Mock face-detection overlay -----------------------------------------
const detectionOverlayEnabled = ref(false);
const activeBox = ref<{
  x: number;
  y: number;
  w: number;
  h: number;
  color: string;
  label: string;
} | null>(null);
let activeBoxClearTimer: ReturnType<typeof setTimeout> | null = null;

const triggerDetectionOverlay = (severity: Severity, label: string) => {
  if (!detectionOverlayEnabled.value) return;
  if (demoIsYoutube.value) return; // can't draw over an iframe meaningfully
  const w = 18 + Math.random() * 14; // 18-32% of width
  const h = w * 1.25;
  const x = 8 + Math.random() * (84 - w);
  const y = 12 + Math.random() * (76 - h);
  const color = severity === 'unknown' ? '#ff5252' : '#21ba45';
  activeBox.value = { x, y, w, h, color, label };
  if (activeBoxClearTimer) clearTimeout(activeBoxClearTimer);
  activeBoxClearTimer = setTimeout(() => {
    activeBox.value = null;
  }, 2200);
};

// ---- Snap-from-feed -------------------------------------------------------
const snapDialog = ref(false);
const snapPreviewUrl = ref<string | null>(null);
const snapBlob = ref<Blob | null>(null);
const snapFolderMode = ref<'existing' | 'new'>('existing');
const snapExistingFolder = ref<string | null>(null);
const snapNewFolder = ref('');
const videoPlayer = ref<HTMLImageElement | null>(null);

const existingFolderOptions = computed(() => [
  ...demoImageFolders.map((f) => ({ label: f.name, value: f.name })),
  ...demoState.extraFolders.map((n) => ({ label: n, value: n })),
]);

const canSnapFromFeed = computed(
  () => streamingActive.value && !demoIsYoutube.value
);

const canSubmitSnap = computed(() => {
  if (!snapBlob.value) return false;
  if (snapFolderMode.value === 'existing') return !!snapExistingFolder.value;
  return !!snapNewFolder.value.trim();
});

const captureCurrentFrame = (): Blob | null => {
  // Pick the right source element. For <video>, we have the ref. For <img>
  // (MJPEG), drawImage works as long as the image is same-origin or has
  // CORS headers; in real-mode this depends on the Pi's CORS config.
  const source: HTMLVideoElement | HTMLImageElement | null =
    demoVideoEl.value ?? videoPlayer.value;
  if (!source) return null;
  const w = (source as HTMLVideoElement).videoWidth || source.clientWidth;
  const h = (source as HTMLVideoElement).videoHeight || source.clientHeight;
  if (!w || !h) return null;
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d');
  if (!ctx) return null;
  try {
    ctx.drawImage(source as CanvasImageSource, 0, 0, w, h);
  } catch {
    return null; // tainted canvas
  }
  // toDataURL → blob (synchronous-ish). Use toBlob for fidelity.
  return new Promise<Blob | null>((resolve) => {
    canvas.toBlob((b) => resolve(b), 'image/jpeg', 0.9);
  }) as unknown as Blob;
};

const openSnapDialog = async () => {
  // captureCurrentFrame returns a Promise wrapped in a cast — await it here.
  let blob: Blob | null = null;
  try {
    blob = (await (captureCurrentFrame() as unknown as Promise<Blob | null>)) ?? null;
  } catch {
    blob = null;
  }
  if (!blob) {
    $q.notify({
      type: 'negative',
      message:
        'Could not capture a frame. Try waiting until the stream loads.',
    });
    return;
  }
  if (snapPreviewUrl.value) URL.revokeObjectURL(snapPreviewUrl.value);
  snapBlob.value = blob;
  snapPreviewUrl.value = URL.createObjectURL(blob);
  snapDialog.value = true;
};

const confirmSnap = () => {
  if (!snapBlob.value) return;
  let folder =
    snapFolderMode.value === 'existing'
      ? snapExistingFolder.value ?? ''
      : snapNewFolder.value.trim();
  if (!folder) return;

  if (snapFolderMode.value === 'new') {
    addDemoFolder(folder);
  }

  const slug = folder.toLowerCase().replace(/[^a-z0-9]+/g, '_');
  const existingCount =
    (findDemoImageFolder(folder)?.images.length ?? 0) +
    getDemoExtraImages(folder).length;
  const filename = `${slug}_${String(existingCount + 1).padStart(3, '0')}.jpg`;
  // Reuse the preview blob URL — it stays alive after the dialog closes
  // because we hand the same URL to the dataset entry.
  const url = snapPreviewUrl.value ?? URL.createObjectURL(snapBlob.value);
  addDemoImages(folder, [{ filename, url }]);
  $q.notify({
    type: 'positive',
    message: `Saved frame to "${folder}".`,
    icon: 'check_circle',
  });
  // Reset state, but DO NOT revoke the blob URL — dataset card is using it.
  snapBlob.value = null;
  snapPreviewUrl.value = null;
  snapDialog.value = false;
  snapNewFolder.value = '';
  snapExistingFolder.value = folder;
  folder = '';
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
  // Mock detection visual: only for face-related events (known/unknown).
  const sev = classifyNotification(n.message);
  if (sev === 'known' || sev === 'unknown') {
    const labelMatch = n.message.match(/recognized:\s*([A-Za-z]+)/i);
    const label =
      labelMatch?.[1] ?? (sev === 'unknown' ? 'Unknown' : 'Known');
    triggerDetectionOverlay(sev, label);
  }
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
  if (activeBoxClearTimer) clearTimeout(activeBoxClearTimer);
  if (snapPreviewUrl.value) {
    // Only revoke if the preview wasn't accepted as a dataset entry. If it
    // was accepted, the dataset card is now rendering it; revoking would
    // break the image. The flow nullifies snapPreviewUrl on accept so this
    // condition never matches in that case.
    URL.revokeObjectURL(snapPreviewUrl.value);
  }
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
.live-page {
  max-width: 1400px;
  margin: 0 auto;
}

.stream-wrapper {
  display: flex;
  gap: 20px;
  align-items: stretch;
  flex-wrap: wrap;
}

.video-container {
  flex: 2 1 480px;
  min-width: 0;
  position: relative;
  border-radius: 16px;
  overflow: hidden;
  background: #000;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.video-element {
  width: 100%;
  aspect-ratio: 16 / 9;
  max-height: 70vh;
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

.demo-banner__short {
  display: none;
}

.detection-overlay {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 3;
}

.detection-overlay__label {
  font-size: 4px; /* viewBox is 100×100, so this maps to a sane on-screen size */
  color: #fff;
  padding: 0 1px;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.overlay-controls {
  position: absolute;
  bottom: 20px;
  left: 20px;
  right: 20px;
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
  z-index: 4;
}

.status-chip {
  backdrop-filter: blur(5px);
  background: rgba(255, 255, 255, 0.1) !important;
  display: flex;
  align-items: center;
  gap: 8px;
}

.notification-panel-container {
  flex: 1 1 320px;
  min-width: 0;
  display: flex;
  flex-direction: column;
  border-radius: 16px;
  background: rgba(12, 2, 24, 0.9);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  padding: 16px;
  gap: 12px;
  max-height: 70vh;
}

.notification-panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #f3eafa;
}

.notif-search {
  width: 100%;
}

.notif-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.notification-panel {
  flex: 1;
  overflow-y: auto;
  padding: 4px;
  background: rgba(0, 0, 0, 0.25);
  border-radius: 8px;
  min-height: 200px;
}

.notification-item {
  padding: 8px 10px;
  margin-bottom: 6px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 6px;
  color: #fff;
  font-size: 0.82rem;
  line-height: 1.35;
  display: flex;
  align-items: flex-start;
  gap: 4px;
  border-left: 3px solid transparent;
}

.notification-item--motion {
  border-left-color: #31ccec;
}
.notification-item--known {
  border-left-color: #21ba45;
}
.notification-item--unknown {
  border-left-color: #ff5252;
}
.notification-item--telegram {
  border-left-color: #c2185b;
}
.notification-item--system {
  border-left-color: #9e9e9e;
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

.panel-label {
  font-size: 0.85rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: rgba(255, 255, 255, 0.7);
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 2;
}

.snap-dialog-card {
  width: min(520px, 96vw);
  background: var(--vigilant-bg, #0c0218);
  color: #f3eafa;
}

@media (max-width: 1023px) {
  .stream-wrapper {
    flex-direction: column;
  }
  .notification-panel-container {
    max-height: 50vh;
  }
}

@media (max-width: 599px) {
  .video-element {
    aspect-ratio: 16 / 10;
    max-height: 50vh;
  }
  .demo-banner {
    padding: 4px 8px;
  }
  .demo-banner__text {
    display: none;
  }
  .demo-banner__short {
    display: inline;
  }
  .overlay-controls {
    bottom: 12px;
    left: 12px;
    right: 12px;
    gap: 8px;
  }
  .panel-label {
    top: 12px;
    right: 12px;
  }
}
</style>
