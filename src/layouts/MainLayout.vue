<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="bg-dark">
      <q-toolbar class="q-pl-md q-pl-md-xl">
        <q-avatar square size="42px">
          <img src="/icons/vigilant.png" alt="Vigilant Eye" />
        </q-avatar>

        <q-toolbar-title class="text-h6 text-h5-md text-weight-bold text-white">
          Vigilant Eye
        </q-toolbar-title>

        <q-space />

        <!-- Desktop / tablet: inline tab strip -->
        <div v-if="$q.screen.gt.xs" class="row items-center q-gutter-md">
          <q-tabs
            inline-label
            active-color="accent"
            indicator-color="accent"
            dense
          >
            <q-route-tab
              v-for="tab in tabs"
              :key="tab.to"
              :to="tab.to"
              :label="tab.label"
              :icon="tab.icon"
              content-class="text-white"
            />
          </q-tabs>
        </div>

        <!-- Desktop: header action buttons (dark mode, settings, logout) -->
        <div
          v-if="$q.screen.gt.xs"
          class="row items-center q-gutter-xs q-ml-md"
        >
          <q-btn
            round
            flat
            :icon="darkModeIcon"
            color="white"
            @click="toggleDarkMode"
          >
            <q-tooltip>Toggle theme</q-tooltip>
          </q-btn>
          <q-btn
            round
            flat
            icon="settings"
            color="white"
            @click="openSettings"
          >
            <q-tooltip>Settings</q-tooltip>
          </q-btn>
          <q-btn round flat icon="logout" color="white" @click="logout">
            <q-tooltip>Sign out</q-tooltip>
          </q-btn>
        </div>

        <!-- Mobile: collapse all into one menu -->
        <q-btn-dropdown
          v-else
          flat
          color="white"
          dropdown-icon="more_vert"
          no-caps
          align="right"
        >
          <q-list>
            <q-item clickable v-close-popup @click="toggleDarkMode">
              <q-item-section avatar>
                <q-icon :name="darkModeIcon" />
              </q-item-section>
              <q-item-section>
                {{ $q.dark.isActive ? 'Light mode' : 'Dark mode' }}
              </q-item-section>
            </q-item>
            <q-item clickable v-close-popup @click="openSettings">
              <q-item-section avatar>
                <q-icon name="settings" />
              </q-item-section>
              <q-item-section>Settings</q-item-section>
            </q-item>
            <q-item clickable v-close-popup @click="logout">
              <q-item-section avatar>
                <q-icon name="logout" />
              </q-item-section>
              <q-item-section>Sign out</q-item-section>
            </q-item>
          </q-list>
        </q-btn-dropdown>
      </q-toolbar>
    </q-header>

    <q-page-container :class="{ 'page-container--has-bottom-nav': $q.screen.lt.sm }">
      <router-view />
    </q-page-container>

    <!-- Mobile bottom-nav -->
    <q-footer
      v-if="$q.screen.lt.sm"
      bordered
      class="bg-dark text-white bottom-nav"
    >
      <q-tabs
        dense
        active-color="accent"
        indicator-color="accent"
        narrow-indicator
        class="text-white"
      >
        <q-route-tab
          v-for="tab in tabs"
          :key="tab.to"
          :to="tab.to"
          :label="tab.shortLabel || tab.label"
          :icon="tab.icon"
        />
      </q-tabs>
    </q-footer>

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

    <SettingsDrawer v-model="showSettingsDialog" />
    <ShortcutsHelp v-model="showShortcutsHelp" :shortcuts="shortcuts" />
  </q-layout>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { useUserStore } from 'stores/userStore';
import { useRouter } from 'vue-router';
import { ref, computed } from 'vue';
import SettingsDrawer from 'src/components/SettingsDrawer.vue';
import ShortcutsHelp from 'src/components/ShortcutsHelp.vue';
import {
  useKeyboardShortcuts,
  type KeyboardShortcut,
} from 'src/composables/useKeyboardShortcuts';

const $q = useQuasar();
const userStore = useUserStore();
const router = useRouter();
const showLogoutDialog = ref(false);
const showSettingsDialog = ref(false);

const tabs = [
  {
    to: '/live-stream',
    label: 'Live Stream',
    shortLabel: 'Live',
    icon: 'live_tv',
  },
  {
    to: '/saved-videos',
    label: 'Media Library',
    shortLabel: 'Library',
    icon: 'video_library',
  },
  {
    to: '/upload-pictures',
    label: 'Face Recognition',
    shortLabel: 'Faces',
    icon: 'camera_enhance',
  },
  {
    to: '/snapshot-camera',
    label: 'Snap Shot',
    shortLabel: 'Snap',
    icon: 'photo_camera',
  },
];

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

const darkModeIcon = computed(() =>
  $q.dark.isActive ? 'light_mode' : 'dark_mode'
);

const showShortcutsHelp = ref(false);

const goTo = (path: string) => {
  router.push(path);
};

const shortcuts: KeyboardShortcut[] = [
  {
    key: '?',
    description: 'Show keyboard shortcuts',
    group: 'General',
    handler: () => {
      showShortcutsHelp.value = true;
    },
  },
  {
    key: ',',
    description: 'Open settings',
    group: 'General',
    handler: () => {
      showSettingsDialog.value = true;
    },
  },
  {
    key: 'd',
    description: 'Toggle dark mode',
    group: 'General',
    handler: () => $q.dark.toggle(),
  },
  {
    key: 'g l',
    description: 'Go to Live Stream',
    group: 'Navigation',
    handler: () => goTo('/live-stream'),
  },
  {
    key: 'g m',
    description: 'Go to Media Library',
    group: 'Navigation',
    handler: () => goTo('/saved-videos'),
  },
  {
    key: 'g f',
    description: 'Go to Face Recognition',
    group: 'Navigation',
    handler: () => goTo('/upload-pictures'),
  },
  {
    key: 'g s',
    description: 'Go to Snap Shot',
    group: 'Navigation',
    handler: () => goTo('/snapshot-camera'),
  },
];

// Two-key sequence shortcuts (g + letter) need a tiny stateful matcher.
// Track a pending leader keypress and clear it on timeout.
let pendingLeader: { key: string; at: number } | null = null;
const LEADER_WINDOW_MS = 800;

const compoundShortcuts = shortcuts.filter((s) => s.key.includes(' '));
const flatShortcuts: KeyboardShortcut[] = shortcuts
  .filter((s) => !s.key.includes(' '))
  .concat(
    compoundShortcuts.map((s) => {
      const [leader] = s.key.split(' ');
      return {
        ...s,
        // Each compound becomes a single-key handler that activates only if
        // the leader was pressed within the window.
        key: s.key.split(' ').slice(-1)[0],
        handler: (e) => {
          if (
            pendingLeader &&
            pendingLeader.key === leader &&
            Date.now() - pendingLeader.at <= LEADER_WINDOW_MS
          ) {
            pendingLeader = null;
            s.handler(e);
          }
        },
      } as KeyboardShortcut;
    })
  )
  .concat([
    {
      key: 'g',
      description: '',
      group: '',
      handler: () => {
        pendingLeader = { key: 'g', at: Date.now() };
      },
    },
  ]);

useKeyboardShortcuts(flatShortcuts);
</script>

<style lang="scss">
.q-header {
  background: linear-gradient(145deg, #1a1a1a 0%, #2d2d2d 100%);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.q-tab__icon {
  font-size: 1.4rem;
}

.bottom-nav {
  background: linear-gradient(180deg, #1a1a1a 0%, #0c0c0c 100%);
}

// Reserve space at the bottom of the page so the fixed footer doesn't cover
// the last row of content on mobile.
.page-container--has-bottom-nav {
  padding-bottom: 60px;
}
</style>
