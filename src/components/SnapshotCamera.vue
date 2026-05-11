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
            :color="targetReached ? 'positive' : 'grey-4'"
            :text-color="targetReached ? 'positive' : 'grey-4'"
            size="sm"
            class="q-ml-sm"
            :icon="targetReached ? 'verified' : 'photo_camera'"
          >
            {{ photos.length }}
            <span v-if="targetCount > 0">/ {{ targetCount }}</span>
          </q-chip>
          <q-space />
          <q-btn
            flat
            round
            dense
            icon="settings"
            :color="optionsOpen ? 'accent' : 'white'"
            @click="optionsOpen = !optionsOpen"
          >
            <q-tooltip>Capture options</q-tooltip>
          </q-btn>
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

        <!-- Target progress (when a target is set) -->
        <q-linear-progress
          v-if="targetCount > 0"
          :value="Math.min(1, photos.length / targetCount)"
          :color="targetReached ? 'positive' : 'accent'"
          size="6px"
          stripe
          class="snap-progress"
        />

        <!-- Brightness coach (only when flash enabled, dismissible) -->
        <q-banner
          v-if="flashEnabled && showBrightnessTip"
          dense
          rounded
          class="snap-bright-tip q-mx-md q-mt-md"
        >
          <template v-slot:avatar>
            <q-icon name="brightness_high" color="white" />
          </template>
          <span class="text-weight-medium">Turn screen brightness up.</span>
          The white flash uses your monitor as a fill light — bump
          brightness to max for the strongest illumination on your face.
          <template v-slot:action>
            <q-btn
              flat
              dense
              label="Got it"
              color="white"
              no-caps
              @click="showBrightnessTip = false"
            />
          </template>
        </q-banner>

        <!-- Options panel -->
        <q-slide-transition>
          <div v-if="optionsOpen" class="snap-options q-pa-md">
            <div class="snap-options__row">
              <div class="snap-option">
                <q-toggle
                  :model-value="flashEnabled"
                  color="accent"
                  label="Screen flash"
                  @update:model-value="setFlashEnabled"
                />
                <div class="snap-option__hint">
                  White-out the screen for fill light
                </div>
              </div>
              <div class="snap-option">
                <q-toggle
                  v-model="faceGuide"
                  color="accent"
                  label="Face guide"
                />
                <div class="snap-option__hint">
                  Oval + thirds overlay for framing
                </div>
              </div>
              <div class="snap-option">
                <q-toggle
                  v-model="autoStopAtTarget"
                  color="accent"
                  label="Auto-stop at target"
                />
                <div class="snap-option__hint">
                  Stops burst when target count is reached
                </div>
              </div>
            </div>
            <div class="snap-options__row">
              <q-select
                v-model="quality"
                :options="qualityOptions"
                label="Quality"
                outlined
                dark
                dense
                color="accent"
                emit-value
                map-options
                class="snap-options__select"
              />
              <q-select
                v-model="burstSpeed"
                :options="burstSpeedOptions"
                label="Burst speed"
                outlined
                dark
                dense
                color="accent"
                emit-value
                map-options
                class="snap-options__select"
              />
              <q-input
                v-model.number="targetCount"
                type="number"
                min="0"
                max="500"
                label="Target captures"
                outlined
                dark
                dense
                color="accent"
                class="snap-options__select"
              >
                <template v-slot:prepend>
                  <q-icon name="flag" />
                </template>
              </q-input>
            </div>
          </div>
        </q-slide-transition>

        <div class="snap-frame">
          <video
            ref="video"
            autoplay
            playsinline
            muted
            class="camera-preview"
            :class="{ 'camera-preview--mirrored': mirror }"
          />
          <!-- Face guide overlay -->
          <svg
            v-if="faceGuide"
            class="snap-face-guide"
            viewBox="0 0 100 75"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            <line
              x1="33.33"
              y1="0"
              x2="33.33"
              y2="75"
              class="snap-face-guide__thirds"
            />
            <line
              x1="66.66"
              y1="0"
              x2="66.66"
              y2="75"
              class="snap-face-guide__thirds"
            />
            <line
              x1="0"
              y1="25"
              x2="100"
              y2="25"
              class="snap-face-guide__thirds"
            />
            <line
              x1="0"
              y1="50"
              x2="100"
              y2="50"
              class="snap-face-guide__thirds"
            />
            <ellipse
              cx="50"
              cy="38"
              rx="14"
              ry="20"
              class="snap-face-guide__oval"
            />
          </svg>

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
            icon="bolt"
            label="Quick shot"
            :disable="countdown > 0 || captureInFlight"
            @click="instantCapture"
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
            Tip: hold spacebar for burst.
            <span v-if="flashEnabled">Flash will fire at every capture.</span>
          </span>
        </q-card-section>

        <q-separator />

        <q-card-section class="snap-thumbs q-pa-md">
          <div
            v-if="!photos.length"
            class="text-grey row items-center q-gutter-sm"
          >
            <q-icon name="info" size="sm" />
            <span>
              No captures yet. Hit
              <strong>Capture</strong>, <strong>Quick shot</strong>, or hold
              <strong>burst</strong>.
            </span>
          </div>
          <div v-else>
            <div class="row items-center q-mb-sm">
              <span class="text-caption text-grey-5">
                Click a thumbnail to remove that frame.
              </span>
              <q-space />
              <q-btn
                v-if="photos.length"
                flat
                dense
                icon="delete_sweep"
                color="grey-5"
                no-caps
                label="Clear all"
                @click="clearAllPhotos"
              />
            </div>
            <div class="thumbs-grid">
              <button
                v-for="(img, idx) in photos"
                :key="idx"
                type="button"
                class="thumbnail"
                :style="{ backgroundImage: `url(${img})` }"
                @click="removePhoto(idx)"
                aria-label="Remove this capture"
              >
                <span class="thumbnail__badge">
                  <q-icon name="delete" size="14px" />
                </span>
              </button>
            </div>
          </div>
        </q-card-section>
      </q-card>
    </div>

    <!-- Full-screen flash overlay (covers the entire viewport so the user's
         monitor lights up like a softbox) -->
    <transition name="flash-overlay">
      <div v-if="flashOverlayActive" class="snap-flash-overlay" aria-hidden="true" />
    </transition>
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

// New: capture options panel + features
const optionsOpen = ref(false);
const flashEnabled = ref(false);
const showBrightnessTip = ref(false);
const faceGuide = ref(false);
const autoStopAtTarget = ref(false);
const targetCount = ref(30); // 0 = no target
const captureInFlight = ref(false);

type Quality = 'low' | 'med' | 'high';
const quality = ref<Quality>('med');
const qualityOptions = [
  { label: 'Low (smaller files)', value: 'low' },
  { label: 'Medium', value: 'med' },
  { label: 'High (best quality)', value: 'high' },
];
const qualityValue = computed<number>(() => {
  switch (quality.value) {
    case 'low':
      return 0.6;
    case 'high':
      return 0.95;
    case 'med':
    default:
      return 0.82;
  }
});

const burstSpeed = ref(300);
const burstSpeedOptions = [
  { label: 'Very fast (200 ms)', value: 200 },
  { label: 'Fast (300 ms)', value: 300 },
  { label: 'Steady (500 ms)', value: 500 },
  { label: 'Slow (1 s)', value: 1000 },
];

// Full-screen white overlay used for the flash effect.
const flashOverlayActive = ref(false);

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

const targetReached = computed(
  () => targetCount.value > 0 && photos.value.length >= targetCount.value
);

const setFlashEnabled = (val: boolean) => {
  flashEnabled.value = val;
  if (val) {
    showBrightnessTip.value = true;
  }
};

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
    if (!folderName) {
      folderError.value = 'Please enter a person name to start taking photos.';
      $q.notify({
        type: 'warning',
        message: 'Please enter a person name to start taking photos.',
        icon: 'person_add',
      });
      return;
    }
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
    if (!folderName) {
      folderError.value = 'Please pick an existing folder to add photos to.';
      $q.notify({
        type: 'warning',
        message: 'Please pick an existing folder to add photos to.',
        icon: 'folder_open',
      });
      return;
    }
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
  const dataUrl = canvas.toDataURL('image/jpeg', qualityValue.value);
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

// Capture pipeline: optionally show the screen flash, wait for the camera's
// auto-exposure to adapt to the brighter scene, take the photo, then drop
// the flash. Single-shot path; burst keeps the flash on for its duration.
async function captureWithOptionalFlash() {
  if (captureInFlight.value) return;
  captureInFlight.value = true;
  try {
    if (flashEnabled.value) {
      flashOverlayActive.value = true;
      // Let the webcam exposure settle on the brighter scene before grabbing.
      await new Promise((r) => setTimeout(r, 350));
    }
    takePhoto();
    if (flashEnabled.value) {
      // Hold the flash a beat after capture so the user sees it as a real flash.
      await new Promise((r) => setTimeout(r, 180));
      flashOverlayActive.value = false;
    }
  } finally {
    captureInFlight.value = false;
  }
}

function instantCapture() {
  if (countdown.value > 0) return;
  captureWithOptionalFlash();
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
      captureWithOptionalFlash();
    }
  }, 1000);
}

async function startBurst() {
  if (bursting.value) return;
  bursting.value = true;
  if (flashEnabled.value) {
    flashOverlayActive.value = true;
    // Brief warm-up before the first burst frame so it isn't too dark.
    await new Promise((r) => setTimeout(r, 250));
  }
  takePhoto();
  if (autoStopAtTarget.value && targetReached.value) {
    stopBurst();
    return;
  }
  burstTimer = window.setInterval(() => {
    if (autoStopAtTarget.value && targetReached.value) {
      stopBurst();
      return;
    }
    takePhoto();
  }, burstSpeed.value);
}

function stopBurst() {
  if (!bursting.value) return;
  bursting.value = false;
  if (burstTimer) {
    clearInterval(burstTimer);
    burstTimer = null;
  }
  if (flashOverlayActive.value && !captureInFlight.value) {
    flashOverlayActive.value = false;
  }
  if (targetReached.value && autoStopAtTarget.value) {
    $q.notify({
      type: 'positive',
      message: `Target of ${targetCount.value} reached.`,
      icon: 'verified',
      timeout: 1500,
    });
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

function removePhoto(index: number) {
  photos.value.splice(index, 1);
  // photoCount intentionally not decremented — savePhotoToBackend uses it as
  // a monotonically-increasing local id; the demo store also has its own
  // filename counter, so deleting a thumbnail here only affects the local
  // preview strip, not entries already pushed to demoState.
}

function clearAllPhotos() {
  photos.value = [];
}

function doneSession() {
  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
    stream = null;
  }
  // Make sure the flash overlay isn't left on.
  flashOverlayActive.value = false;
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
  flashOverlayActive.value = false;
  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
  }
});
</script>

<style lang="scss" scoped>
.snap-page {
  // Background + text color now come from the shared body styling in
  // app.scss so Snap Shot matches Live Stream / Media Library / Face
  // Recognition in both light and dark mode.
  min-height: 100vh;
  color: var(--vigilant-text);
  padding: 24px;
}

.snap-shell {
  max-width: 760px;
  margin: 0 auto;
}

.snap-card {
  background: var(--vigilant-surface);
  border: 1px solid var(--vigilant-border);
  color: var(--vigilant-text);
  border-radius: 16px;
  box-shadow: var(--vigilant-shadow-md);
  overflow: hidden;
}

.snap-capture__header {
  background: linear-gradient(
    135deg,
    rgba(var(--vigilant-accent-dark-rgb), 0.4),
    rgba(var(--vigilant-accent-rgb), 0.3)
  );
}

.snap-progress {
  width: 100%;
}

.snap-bright-tip {
  background: linear-gradient(135deg, var(--vigilant-accent-dark), var(--q-accent));
  color: #fff;
  font-size: 0.85rem;
}

.snap-options {
  background: var(--vigilant-surface-strong);
  border-top: 1px solid var(--vigilant-border);
  border-bottom: 1px solid var(--vigilant-border);
}

.snap-options__row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  align-items: start;
}

.snap-options__row + .snap-options__row {
  margin-top: 16px;
}

.snap-option {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.snap-option__hint {
  font-size: 0.7rem;
  color: var(--vigilant-text-dim);
  margin-left: 32px;
}

.snap-options__select {
  min-width: 0;
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

.snap-face-guide {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 2;
}

.snap-face-guide__thirds {
  stroke: rgba(255, 255, 255, 0.18);
  stroke-width: 0.15;
  vector-effect: non-scaling-stroke;
}

.snap-face-guide__oval {
  fill: none;
  stroke: rgba(255, 255, 255, 0.55);
  stroke-width: 0.4;
  stroke-dasharray: 1.5 1;
  vector-effect: non-scaling-stroke;
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
  z-index: 3;
}

.snap-flash {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.85);
  pointer-events: none;
  z-index: 4;
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
  background: rgba(var(--vigilant-accent-rgb), 0.18);
}

.thumbs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(80px, 100%), 1fr));
  gap: 8px;
}

.thumbnail {
  position: relative;
  aspect-ratio: 1 / 1;
  background-size: cover;
  background-position: center;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  transition: transform 0.2s ease, border-color 0.2s ease;
  cursor: pointer;
  padding: 0;
  background-color: #000;
  outline: none;
}

.thumbnail:hover {
  transform: scale(1.05);
  border-color: var(--q-accent, #c2185b);
}

.thumbnail:focus-visible {
  border-color: var(--q-accent, #c2185b);
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.3);
}

.thumbnail__badge {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.7);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.thumbnail:hover .thumbnail__badge,
.thumbnail:focus-visible .thumbnail__badge {
  opacity: 1;
}

.snap-flash-overlay {
  position: fixed;
  inset: 0;
  background: #fff;
  z-index: 9999;
  pointer-events: none;
  // Soft warm tint at the very edges so it feels like a softbox, not a
  // harsh strobe — matters for both UX and how the camera meters white.
  box-shadow: inset 0 0 200px rgba(255, 240, 220, 0.3);
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

.flash-overlay-enter-active,
.flash-overlay-leave-active {
  transition: opacity 0.15s ease;
}
.flash-overlay-enter-from,
.flash-overlay-leave-to {
  opacity: 0;
}

@media (max-width: 599px) {
  .snap-page {
    padding: 12px;
  }
  .snap-options__row {
    grid-template-columns: 1fr;
  }
  .snap-controls {
    gap: 8px;
  }
  .snap-btn-shoot {
    flex-basis: 100%;
  }
}
</style>
