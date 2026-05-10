<template>
  <q-page class="snap-page">
    <q-banner
      v-if="settingsStore.demoMode"
      class="vigilant-demo-banner q-mb-md"
      rounded
      dense
    >
      <template v-slot:avatar>
        <q-icon name="science" color="white" />
      </template>
      <span class="text-weight-medium">Demo:</span>
      camera preview uses your real webcam. Captured frames go into a
      session-only folder and appear in Face Recognition until you reload.
    </q-banner>

    <div class="snap-shell">
      <!-- Setup view -->
      <q-card v-if="!firstName" class="snap-card snap-setup">
        <q-card-section>
          <div class="text-h6">Start a snapshot session</div>
          <div class="text-grey-5 text-caption q-mt-xs">
            Pick or create an identity folder. Captured frames will be added to
            it.
          </div>
        </q-card-section>

        <q-card-section class="q-pt-none q-gutter-md">
          <q-btn-toggle
            v-model="folderMode"
            spread
            no-caps
            unelevated
            toggle-color="accent"
            :options="[
              { label: 'New person', value: 'new', icon: 'person_add' },
              { label: 'Existing folder', value: 'existing', icon: 'folder_open' },
            ]"
          />

          <q-input
            v-if="folderMode === 'new'"
            v-model="nameInput"
            label="Person name"
            filled
            dark
            color="accent"
            :error="!!folderError"
            :error-message="folderError ?? undefined"
            @keyup.enter="setFirstName"
          >
            <template v-slot:prepend>
              <q-icon name="person" />
            </template>
          </q-input>

          <q-select
            v-else
            v-model="existingFolderChoice"
            :options="existingFolderOptions"
            label="Choose a folder"
            filled
            dark
            color="accent"
            emit-value
            map-options
          />

          <q-select
            v-if="videoDevices.length > 1"
            v-model="selectedDeviceId"
            :options="videoDeviceOptions"
            label="Camera"
            filled
            dark
            color="accent"
            emit-value
            map-options
          />

          <div v-if="cameraError" class="text-negative">
            <q-icon name="error" size="sm" class="q-mr-xs" />
            {{ cameraError }}
          </div>

          <q-btn
            color="accent"
            unelevated
            class="full-width"
            size="lg"
            icon-right="arrow_forward"
            label="Start camera"
            :disable="
              folderMode === 'new'
                ? !nameInput.trim()
                : !existingFolderChoice
            "
            @click="setFirstName"
          />
        </q-card-section>
      </q-card>

      <!-- Capture view -->
      <q-card v-else class="snap-card snap-capture">
        <q-card-section
          class="snap-capture__header row items-center q-pa-md"
        >
          <q-icon name="videocam" size="sm" class="q-mr-sm" />
          <span class="text-weight-bold">{{ firstName }}</span>
          <q-chip
            outline
            color="grey-4"
            text-color="grey-4"
            size="sm"
            class="q-ml-sm"
          >
            {{ photos.length }} captured
          </q-chip>
          <q-space />
          <q-btn
            flat
            round
            dense
            :icon="mirror ? 'flip' : 'flip_to_back'"
            :color="mirror ? 'accent' : 'white'"
            @click="mirror = !mirror"
          >
            <q-tooltip>Mirror preview</q-tooltip>
          </q-btn>
          <q-btn
            flat
            round
            dense
            icon="restart_alt"
            color="white"
            @click="redoSession"
          >
            <q-tooltip>Clear and redo</q-tooltip>
          </q-btn>
          <q-btn
            flat
            round
            dense
            icon="check"
            color="positive"
            @click="doneSession"
          >
            <q-tooltip>End session</q-tooltip>
          </q-btn>
        </q-card-section>

        <div class="snap-frame">
          <video
            ref="video"
            autoplay
            playsinline
            muted
            class="camera-preview"
            :class="{ 'camera-preview--mirrored': mirror }"
          />
          <transition name="fade">
            <div v-if="countdown > 0" class="snap-countdown">
              {{ countdown }}
            </div>
          </transition>
          <transition name="flash">
            <div v-if="flashing" class="snap-flash" />
          </transition>
          <div v-if="cameraError" class="snap-frame__error">
            <q-icon name="error" size="sm" class="q-mr-xs" />
            {{ cameraError }}
          </div>
        </div>

        <q-card-section class="snap-controls q-pa-md">
          <q-btn
            color="accent"
            unelevated
            size="lg"
            class="snap-btn-shoot"
            icon="photo_camera"
            label="Capture"
            :disable="countdown > 0"
            @click="startCountdown(3)"
          />
          <q-btn
            outline
            color="accent"
            size="lg"
            icon="burst_mode"
            :label="bursting ? 'Release to stop' : 'Hold for burst'"
            :class="{ 'snap-btn-active': bursting }"
            @mousedown="startBurst"
            @mouseup="stopBurst"
            @mouseleave="stopBurst"
            @touchstart.prevent="startBurst"
            @touchend.prevent="stopBurst"
          />
          <span class="text-grey-5 text-caption snap-controls__hint">
            Tip: hold spacebar for burst capture.
          </span>
        </q-card-section>

        <q-separator />

        <q-card-section class="snap-thumbs q-pa-md">
          <div v-if="!photos.length" class="text-grey">
            No captures yet. Hit Capture or hold the burst button.
          </div>
          <div v-else class="thumbs-grid">
            <div
              v-for="(img, idx) in photos"
              :key="idx"
              class="thumbnail"
              :style="{ backgroundImage: `url(${img})` }"
            />
          </div>
        </q-card-section>
      </q-card>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import {
  ref,
  computed,
  onMounted,
  onBeforeUnmount,
  watch,
  nextTick,
} from 'vue';
import { useQuasar } from 'quasar';
import { useSettingsStore } from 'stores/settingsStore';
import {
  demoImageFolders,
  findDemoImageFolder,
} from 'src/demo/demoData';
import {
  addDemoFolder,
  addDemoImages,
  getDemoExtraImages,
  demoState,
} from 'src/demo/demoState';

const $q = useQuasar();
const settingsStore = useSettingsStore();
const API_BASE = settingsStore.uploadApiUrl;

const video = ref<HTMLVideoElement | null>(null);
const photos = ref<string[]>([]);
const firstName = ref<string | null>(null);
const nameInput = ref('');
const folderMode = ref<'new' | 'existing'>('new');
const existingFolderChoice = ref<string | null>(null);
const photoCount = ref(0);
const mirror = ref(true);
const countdown = ref(0);
const flashing = ref(false);
const bursting = ref(false);

let stream: MediaStream | null = null;
let burstTimer: number | null = null;
let countdownTimer: number | null = null;

const videoDevices = ref<MediaDeviceInfo[]>([]);
const selectedDeviceId = ref<string | null>(null);
const cameraError = ref<string | null>(null);
const folderError = ref<string | null>(null);

const existingFolderOptions = computed(() => [
  ...demoImageFolders.map((f) => ({ label: f.name, value: f.name })),
  ...demoState.extraFolders.map((n) => ({ label: n, value: n })),
]);

const videoDeviceOptions = computed(() =>
  videoDevices.value.map((d) => ({
    label: d.label || `Camera ${d.deviceId.slice(0, 8)}`,
    value: d.deviceId,
  }))
);

async function getVideoDevices() {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    videoDevices.value = devices.filter((d) => d.kind === 'videoinput');
    if (videoDevices.value.length > 0 && !selectedDeviceId.value) {
      selectedDeviceId.value = videoDevices.value[0].deviceId;
    }
  } catch {
    cameraError.value = 'Could not list video devices.';
  }
}

async function setFirstName() {
  folderError.value = null;
  let folderName = '';
  if (folderMode.value === 'new') {
    folderName = nameInput.value.trim();
    if (!folderName) return;
    if (settingsStore.demoMode) {
      const taken =
        demoImageFolders.some(
          (f) => f.name.toLowerCase() === folderName.toLowerCase()
        ) ||
        demoState.extraFolders.some(
          (n) => n.toLowerCase() === folderName.toLowerCase()
        );
      if (taken) {
        folderError.value =
          'Folder already exists. Pick a different name or use Existing folder.';
        return;
      }
      addDemoFolder(folderName);
    } else {
      const res = await fetch(`${API_BASE}/api/create-folder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: folderName }),
      });
      if (res.status === 409) {
        folderError.value =
          'Folder already exists. Please choose a new name.';
        return;
      }
      if (!res.ok) {
        folderError.value = 'Error creating folder. Please try again.';
        return;
      }
    }
  } else {
    folderName = existingFolderChoice.value ?? '';
    if (!folderName) return;
  }
  firstName.value = folderName;
}

async function startCamera() {
  cameraError.value = null;
  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
    stream = null;
  }
  if (!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)) {
    cameraError.value = 'Camera API not supported in this environment.';
    return;
  }
  try {
    const constraints: MediaStreamConstraints = selectedDeviceId.value
      ? { video: { deviceId: { exact: selectedDeviceId.value } } }
      : { video: true };
    stream = await navigator.mediaDevices.getUserMedia(constraints);
    if (video.value) {
      video.value.srcObject = stream;
    }
  } catch (err: unknown) {
    if (err instanceof Error) {
      cameraError.value = `Camera error: ${err.message || err.name}`;
    } else {
      cameraError.value = 'Camera error: Unknown error occurred.';
    }
  }
}

watch(firstName, async (val) => {
  if (val) {
    await nextTick();
    await startCamera();
  }
});

watch(selectedDeviceId, async (val, oldVal) => {
  if (firstName.value && val !== oldVal) {
    await startCamera();
  }
});

function takePhoto() {
  if (!video.value) return;
  const canvas = document.createElement('canvas');
  canvas.width = video.value.videoWidth;
  canvas.height = video.value.videoHeight;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  ctx.drawImage(video.value, 0, 0, canvas.width, canvas.height);
  const dataUrl = canvas.toDataURL('image/jpeg');
  photos.value.push(dataUrl);
  photoCount.value += 1;
  flashing.value = true;
  window.setTimeout(() => {
    flashing.value = false;
  }, 220);
  savePhotoToBackend(dataUrl, photoCount.value);
}

function dataURLtoBlob(dataurl: string) {
  const arr = dataurl.split(',');
  const mime = arr[0].match(/:(.*?);/)?.[1] ?? '';
  const bstr = atob(arr[1]);
  const u8arr = new Uint8Array(bstr.length);
  for (let i = 0; i < bstr.length; i++) {
    u8arr[i] = bstr.charCodeAt(i);
  }
  return new Blob([u8arr], { type: mime });
}

function savePhotoToBackend(dataUrl: string, count: number) {
  if (!firstName.value) return;
  const folder = firstName.value;
  const slug = folder.toLowerCase().replace(/[^a-z0-9]+/g, '_');
  const startIndex =
    (findDemoImageFolder(folder)?.images.length ?? 0) +
    getDemoExtraImages(folder).length;
  const filename = `${slug}_${String(startIndex + 1).padStart(3, '0')}.jpg`;
  const blob = dataURLtoBlob(dataUrl);

  if (settingsStore.demoMode) {
    addDemoImages(folder, [{ filename, url: URL.createObjectURL(blob) }]);
    return;
  }

  const formData = new FormData();
  formData.append('folder', folder);
  formData.append('images', blob, `${folder}${count}.jpg`);
  fetch(`${API_BASE}/api/upload`, {
    method: 'POST',
    body: formData,
  });
}

function startCountdown(seconds: number) {
  if (countdown.value > 0) return;
  countdown.value = seconds;
  countdownTimer = window.setInterval(() => {
    countdown.value -= 1;
    if (countdown.value <= 0) {
      if (countdownTimer) {
        clearInterval(countdownTimer);
        countdownTimer = null;
      }
      takePhoto();
    }
  }, 1000);
}

function startBurst() {
  if (bursting.value) return;
  bursting.value = true;
  takePhoto();
  burstTimer = window.setInterval(takePhoto, 300);
}

function stopBurst() {
  if (!bursting.value) return;
  bursting.value = false;
  if (burstTimer) {
    clearInterval(burstTimer);
    burstTimer = null;
  }
}

function handleKeyDown(e: KeyboardEvent) {
  if (e.code === 'Space' && !bursting.value && firstName.value) {
    e.preventDefault();
    startBurst();
  }
}
function handleKeyUp(e: KeyboardEvent) {
  if (e.code === 'Space') {
    stopBurst();
  }
}

function doneSession() {
  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
    stream = null;
  }
  const message = settingsStore.demoMode
    ? `Session complete. ${photos.value.length} snapshot${
        photos.value.length === 1 ? '' : 's'
      } added to "${firstName.value}".`
    : `Session complete. ${photos.value.length} snapshot${
        photos.value.length === 1 ? '' : 's'
      } sent to backend.`;
  $q.notify({ type: 'positive', message, icon: 'check_circle' });
  // Reset for a fresh session.
  firstName.value = null;
  nameInput.value = '';
  existingFolderChoice.value = null;
  photos.value = [];
  photoCount.value = 0;
}

function redoSession() {
  photos.value = [];
  photoCount.value = 0;
}

onMounted(() => {
  getVideoDevices();
  window.addEventListener('keydown', handleKeyDown);
  window.addEventListener('keyup', handleKeyUp);
});

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeyDown);
  window.removeEventListener('keyup', handleKeyUp);
  stopBurst();
  if (countdownTimer) {
    clearInterval(countdownTimer);
    countdownTimer = null;
  }
  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
  }
});
</script>

<style lang="scss" scoped>
.snap-page {
  min-height: 100vh;
  background: radial-gradient(
      ellipse at top,
      rgba(76, 6, 92, 0.4),
      transparent 60%
    ),
    linear-gradient(180deg, #1a0529 0%, #0c0218 100%);
  color: #f3eafa;
  padding: 24px;
}

.snap-shell {
  max-width: 720px;
  margin: 0 auto;
}

.snap-card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #f3eafa;
  border-radius: 16px;
  backdrop-filter: blur(8px);
}

.snap-capture__header {
  background: linear-gradient(
    135deg,
    rgba(76, 6, 92, 0.4),
    rgba(106, 27, 154, 0.3)
  );
  border-radius: 16px 16px 0 0;
}

.snap-frame {
  position: relative;
  width: 100%;
  aspect-ratio: 4 / 3;
  background: #000;
  overflow: hidden;
}

.camera-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.camera-preview--mirrored {
  transform: scaleX(-1);
}

.snap-countdown {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: clamp(80px, 18vw, 180px);
  font-weight: 800;
  color: rgba(255, 255, 255, 0.92);
  text-shadow: 0 4px 30px rgba(0, 0, 0, 0.6);
  pointer-events: none;
}

.snap-flash {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.85);
  pointer-events: none;
}

.snap-frame__error {
  position: absolute;
  bottom: 12px;
  left: 12px;
  right: 12px;
  background: rgba(193, 0, 21, 0.85);
  color: #fff;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 0.8rem;
}

.snap-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.snap-btn-shoot {
  flex: 1 1 200px;
  min-width: 0;
}

.snap-controls__hint {
  flex-basis: 100%;
}

.snap-btn-active {
  background: rgba(156, 39, 176, 0.18);
}

.thumbs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(80px, 100%), 1fr));
  gap: 8px;
}

.thumbnail {
  aspect-ratio: 1 / 1;
  background-size: cover;
  background-position: center;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  transition: transform 0.2s ease;
}

.thumbnail:hover {
  transform: scale(1.05);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.flash-enter-active,
.flash-leave-active {
  transition: opacity 0.18s ease;
}
.flash-enter-from,
.flash-leave-to {
  opacity: 0;
}

@media (max-width: 599px) {
  .snap-page {
    padding: 12px;
  }
  .snap-controls {
    gap: 8px;
  }
  .snap-btn-shoot {
    flex-basis: 100%;
  }
}
</style>
