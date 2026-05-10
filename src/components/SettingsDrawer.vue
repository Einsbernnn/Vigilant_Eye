<template>
  <q-dialog
    v-model="model"
    :maximized="$q.screen.lt.sm"
    transition-show="slide-left"
    transition-hide="slide-right"
    position="right"
  >
    <q-card class="settings-card column">
      <q-card-section class="settings-card__header row items-center q-pa-md">
        <q-icon name="settings" size="sm" class="q-mr-sm" />
        <div class="text-h6">Settings</div>
        <q-space />
        <q-btn flat round dense icon="close" v-close-popup />
      </q-card-section>

      <q-separator />

      <q-scroll-area class="col">
        <q-list separator class="q-py-sm">
          <q-item-label header class="text-uppercase text-weight-bold">
            <q-icon name="cable" size="xs" class="q-mr-xs" />
            Connection
          </q-item-label>
          <q-item>
            <q-item-section>
              <q-input
                v-model="liveUrlDraft"
                label="Live Stream URL"
                filled
                dense
                hint="Backend camera service (port 5002)"
              />
            </q-item-section>
          </q-item>
          <q-item>
            <q-item-section>
              <q-input
                v-model="uploadUrlDraft"
                label="Upload API URL"
                filled
                dense
                hint="Backend file/dataset service (port 5000)"
              />
            </q-item-section>
          </q-item>
          <q-item tag="label" v-ripple>
            <q-item-section>
              <q-item-label>Demo mode</q-item-label>
              <q-item-label caption>
                Use placeholder data instead of the real Pi backend.
              </q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-toggle
                :model-value="settingsStore.demoMode"
                @update:model-value="settingsStore.updateDemoMode($event)"
                color="accent"
              />
            </q-item-section>
          </q-item>

          <q-item-label header class="text-uppercase text-weight-bold q-mt-sm">
            <q-icon name="palette" size="xs" class="q-mr-xs" />
            Appearance
          </q-item-label>
          <q-item tag="label" v-ripple>
            <q-item-section>
              <q-item-label>Dark mode</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-toggle
                :model-value="$q.dark.isActive"
                @update:model-value="$q.dark.toggle()"
                color="accent"
              />
            </q-item-section>
          </q-item>
          <q-item>
            <q-item-section>
              <q-item-label>Accent color</q-item-label>
              <q-item-label caption>
                Re-skins buttons, chips, and highlights.
              </q-item-label>
              <div class="row q-gutter-sm q-mt-sm">
                <button
                  v-for="(hex, name) in accentPresets"
                  :key="name"
                  type="button"
                  class="accent-swatch"
                  :class="{
                    'accent-swatch--active': settingsStore.accentColor === name,
                  }"
                  :style="{ background: hex }"
                  :aria-label="name"
                  @click="settingsStore.updateAccentColor(name)"
                />
              </div>
            </q-item-section>
          </q-item>

          <q-item-label header class="text-uppercase text-weight-bold q-mt-sm">
            <q-icon name="videocam" size="xs" class="q-mr-xs" />
            Camera
          </q-item-label>
          <q-item>
            <q-item-section>
              <q-input
                v-model="cameraLocation"
                label="Camera location label"
                filled
                dense
              />
            </q-item-section>
          </q-item>
          <q-item tag="label" v-ripple>
            <q-item-section>
              <q-item-label>Turn on camera light</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-toggle
                :model-value="settingsStore.enableCameraLight"
                @update:model-value="
                  settingsStore.updateCameraLight($event); flashIfReal();
                "
                color="accent"
                :disable="doNotDisturb"
              />
            </q-item-section>
          </q-item>
          <q-item tag="label" v-ripple>
            <q-item-section>
              <q-item-label>Disable camera panning</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-toggle
                :model-value="settingsStore.enableCameraPanning"
                @update:model-value="settingsStore.updateCameraPanning($event)"
                color="accent"
                :disable="doNotDisturb"
              />
            </q-item-section>
          </q-item>

          <q-item-label header class="text-uppercase text-weight-bold q-mt-sm">
            <q-icon name="sensors" size="xs" class="q-mr-xs" />
            Sensors
          </q-item-label>
          <q-item tag="label" v-ripple>
            <q-item-section>
              <q-item-label>Disable buzzer sound</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-toggle
                v-model="enableBuzzerSound"
                color="accent"
                :disable="doNotDisturb"
                @update:model-value="toggleBuzzerSound"
              />
            </q-item-section>
          </q-item>
          <q-item tag="label" v-ripple>
            <q-item-section>
              <q-item-label>Disable motion sensor</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-toggle
                v-model="enableMotionSensor"
                color="accent"
                :disable="doNotDisturb"
                @update:model-value="toggleMotionSensor"
              />
            </q-item-section>
          </q-item>

          <q-item-label header class="text-uppercase text-weight-bold q-mt-sm">
            <q-icon name="notifications" size="xs" class="q-mr-xs" />
            Notifications
          </q-item-label>
          <q-item tag="label" v-ripple>
            <q-item-section>
              <q-item-label>Notification sound</q-item-label>
              <q-item-label caption>
                Play a short beep with each toast.
              </q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-toggle
                :model-value="settingsStore.notificationSound"
                @update:model-value="
                  settingsStore.updateNotificationSound($event)
                "
                color="accent"
              />
            </q-item-section>
          </q-item>
          <q-item tag="label" v-ripple>
            <q-item-section>
              <q-item-label>Do not disturb</q-item-label>
              <q-item-label caption>
                Mutes peripherals and toasts.
              </q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-toggle
                v-model="doNotDisturb"
                color="negative"
                @update:model-value="onDoNotDisturbChange"
              />
            </q-item-section>
          </q-item>

          <q-item-label header class="text-uppercase text-weight-bold q-mt-sm">
            <q-icon name="storage" size="xs" class="q-mr-xs" />
            Data
          </q-item-label>
          <q-item v-if="settingsStore.demoMode">
            <q-item-section>
              <q-item-label>Reset demo data</q-item-label>
              <q-item-label caption>
                Clears uploaded folders, snapshots, and training history. Static
                seed identities are kept.
              </q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-btn
                outline
                color="negative"
                icon="restart_alt"
                label="Reset"
                dense
                @click="onResetDemo"
              />
            </q-item-section>
          </q-item>
          <q-item v-else>
            <q-item-section class="text-grey">
              Reset is only available in demo mode.
            </q-item-section>
          </q-item>
        </q-list>
      </q-scroll-area>

      <q-separator />

      <q-card-actions align="right" class="q-pa-md">
        <q-btn flat label="Close" v-close-popup color="grey-7" />
        <q-btn
          unelevated
          color="accent"
          icon="check"
          label="Save"
          @click="onSave"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useQuasar } from 'quasar';
import {
  useSettingsStore,
  accentPresets,
} from 'src/stores/settingsStore';
import { resetDemoState } from 'src/demo/demoState';
import { api } from 'boot/axios';

const props = defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{ (e: 'update:modelValue', v: boolean): void }>();

const $q = useQuasar();
const settingsStore = useSettingsStore();

const model = ref(props.modelValue);
watch(
  () => props.modelValue,
  (v) => {
    model.value = v;
    if (v) {
      // Re-seed local drafts when opening so the URL inputs show current store
      // values, not whatever was last typed.
      liveUrlDraft.value = settingsStore.liveStreamUrl;
      uploadUrlDraft.value = settingsStore.uploadApiUrl;
    }
  }
);
watch(model, (v) => emit('update:modelValue', v));

const liveUrlDraft = ref(settingsStore.liveStreamUrl);
const uploadUrlDraft = ref(settingsStore.uploadApiUrl);

// Local-only fields not in the store yet (kept for parity with the legacy
// inline dialog so we don't lose visual fidelity).
const cameraLocation = ref('');
const enableBuzzerSound = ref(false);
const enableMotionSensor = ref(false);
const doNotDisturb = ref(false);

const flashIfReal = () => {
  if (settingsStore.demoMode) {
    $q.notify({
      type: 'info',
      message: 'Demo mode: camera light toggle is cosmetic.',
      icon: 'science',
      timeout: 1500,
    });
  }
};

const toggleBuzzerSound = async (val: boolean) => {
  if (settingsStore.demoMode) {
    $q.notify({
      type: 'info',
      message: `Buzzer ${val ? 'enabled' : 'disabled'} (demo).`,
      timeout: 1500,
    });
    return;
  }
  try {
    await api.post('/set-buzzer', { enabled: val });
    $q.notify({
      type: 'info',
      message: `Buzzer ${val ? 'enabled' : 'disabled'}.`,
    });
  } catch {
    $q.notify({ type: 'negative', message: 'Failed to update buzzer.' });
  }
};

const toggleMotionSensor = async (val: boolean) => {
  if (settingsStore.demoMode) {
    $q.notify({
      type: 'info',
      message: `Motion sensor ${val ? 'enabled' : 'disabled'} (demo).`,
      timeout: 1500,
    });
    return;
  }
  try {
    await api.post('/set-motion-sensor', { enabled: val });
    $q.notify({
      type: 'info',
      message: `Motion sensor ${val ? 'enabled' : 'disabled'}.`,
    });
  } catch {
    $q.notify({
      type: 'negative',
      message: 'Failed to update motion sensor.',
    });
  }
};

const onDoNotDisturbChange = (val: boolean) => {
  if (val) {
    enableBuzzerSound.value = false;
    enableMotionSensor.value = false;
  }
};

const onResetDemo = () => {
  $q.dialog({
    title: 'Reset demo data?',
    message:
      'Clears uploaded folders, snapshots, and the simulated training history. Static demo identities (Alice, Bob, Carol, David) stay.',
    cancel: true,
    persistent: true,
    color: 'negative',
  }).onOk(() => {
    resetDemoState();
    $q.notify({
      type: 'positive',
      message: 'Demo data reset.',
      icon: 'restart_alt',
    });
  });
};

const onSave = () => {
  if (liveUrlDraft.value.trim()) {
    settingsStore.updateLiveStreamUrl(liveUrlDraft.value.trim());
  }
  if (uploadUrlDraft.value.trim()) {
    settingsStore.updateUploadApiUrl(uploadUrlDraft.value.trim());
  }
  $q.notify({
    type: 'positive',
    message: 'Settings saved.',
    icon: 'check',
    timeout: 1500,
  });
  model.value = false;
};
</script>

<style lang="scss" scoped>
.settings-card {
  width: 420px;
  max-width: 100vw;
  height: 100vh;
  border-radius: 0;
  background: var(--vigilant-bg, #0c0218);
  color: #f3eafa;
}

.settings-card__header {
  background: linear-gradient(
    135deg,
    var(--vigilant-purple-2, #4c065c),
    var(--vigilant-purple-1, #6a1b9a)
  );
  color: #fff;
}

:deep(.q-item-label--header) {
  color: rgba(244, 238, 249, 0.6);
  letter-spacing: 0.08em;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
}

:deep(.q-item) {
  color: #f3eafa;
}

.accent-swatch {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
  padding: 0;
  transition: transform 0.15s ease, border-color 0.15s ease;
}

.accent-swatch:hover {
  transform: scale(1.1);
}

.accent-swatch--active {
  border-color: #fff;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.25);
}

@media (max-width: 599px) {
  .settings-card {
    width: 100vw;
  }
}
</style>
