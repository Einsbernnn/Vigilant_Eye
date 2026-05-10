<template>
  <q-page class="q-px-md q-px-md-xl q-pt-md q-pt-md-xl">
    <q-banner
      v-if="settingsStore.demoMode"
      class="vigilant-demo-banner q-mb-md"
      rounded
      dense
    >
      <template v-slot:avatar>
        <q-icon name="science" color="white" />
      </template>
      <span class="text-weight-medium">Demo data:</span>
      folders, clips, thumbnails, and detection logs are placeholder content.
      No real footage is stored on this deployment.
    </q-banner>

    <div class="library-clock q-mb-md">{{ currentDateTime }}</div>

    <div class="gallery-wrapper">
      <!-- Folder index view -->
      <div v-if="!selectedFolder">
        <!-- Stats strip -->
        <div class="library-stats q-mb-md">
          <div class="library-stat">
            <q-icon name="folder" size="sm" color="accent" />
            <div>
              <div class="library-stat__value">{{ folders.length }}</div>
              <div class="library-stat__label">Folders</div>
            </div>
          </div>
          <div class="library-stat">
            <q-icon name="movie" size="sm" color="accent" />
            <div>
              <div class="library-stat__value">{{ totalClipCount }}</div>
              <div class="library-stat__label">Clips</div>
            </div>
          </div>
          <div class="library-stat">
            <q-icon name="schedule" size="sm" color="accent" />
            <div>
              <div class="library-stat__value">
                {{ totalDurationLabel }}
              </div>
              <div class="library-stat__label">Total runtime</div>
            </div>
          </div>
        </div>

        <!-- Toolbar -->
        <div class="library-toolbar q-mb-md">
          <q-input
            v-model="folderSearchQuery"
            dense
            outlined
            placeholder="Search folders"
            class="library-search"
            clearable
          >
            <template v-slot:prepend>
              <q-icon name="search" />
            </template>
          </q-input>
          <q-btn
            color="primary"
            label="Refresh"
            icon="refresh"
            unelevated
            @click="refreshFolders"
          />
          <q-btn-dropdown
            color="primary"
            outline
            icon="sort"
            :label="folderSortLabel"
            no-caps
          >
            <q-list>
              <q-item
                v-for="opt in folderSortOptions"
                :key="opt.value"
                clickable
                v-close-popup
                @click="folderSortMode = opt.value"
              >
                <q-item-section>{{ opt.label }}</q-item-section>
                <q-item-section v-if="folderSortMode === opt.value" side>
                  <q-icon name="check" color="accent" />
                </q-item-section>
              </q-item>
            </q-list>
          </q-btn-dropdown>
        </div>

        <!-- Folder grid -->
        <div class="row q-col-gutter-md">
          <div
            v-for="folder in filteredFolders"
            :key="folder"
            class="col-6 col-sm-4 col-md-3 col-lg-2"
          >
            <q-card
              class="image-card folder-card cursor-pointer"
              @click="selectFolder(folder)"
            >
              <q-badge
                v-if="settingsStore.demoMode"
                color="purple"
                text-color="white"
                class="demo-pill"
              >
                Demo
              </q-badge>
              <div class="column items-center q-pa-md">
                <q-icon name="folder" color="accent" size="48px" />
                <div class="text-center text-weight-bold q-mt-sm folder-name">
                  {{ folder }}
                </div>
                <div class="text-caption text-grey-6 q-mt-xs">
                  {{
                    formatDate(parseDateFromFolderName(folder) || new Date())
                  }}
                </div>
                <q-chip
                  square
                  size="sm"
                  color="accent"
                  text-color="white"
                  class="q-mt-xs folder-count-chip"
                >
                  {{ folderClipCount(folder) }}
                </q-chip>
                <div class="row q-gutter-xs q-mt-sm">
                  <q-btn
                    dense
                    flat
                    icon="edit"
                    color="primary"
                    @click.stop="showRenameDialog(folder)"
                  >
                    <q-tooltip>Rename</q-tooltip>
                  </q-btn>
                  <q-btn
                    dense
                    flat
                    icon="delete"
                    color="negative"
                    @click.stop="showDeleteDialog(folder)"
                  >
                    <q-tooltip>Delete</q-tooltip>
                  </q-btn>
                  <q-btn
                    dense
                    flat
                    icon="download"
                    color="accent"
                    @click.stop="downloadFolder(folder)"
                  >
                    <q-tooltip>Download</q-tooltip>
                  </q-btn>
                </div>
              </div>
            </q-card>
          </div>
        </div>
        <div
          v-if="!filteredFolders.length"
          class="text-grey text-center q-pa-lg full-width"
        >
          {{ folderSearchQuery ? 'No matches.' : 'No folders found.' }}
        </div>
      </div>

      <!-- In-folder view -->
      <div v-else>
        <div class="library-folder-toolbar q-mb-md">
          <q-btn
            flat
            icon="arrow_back"
            color="accent"
            @click="clearSelectedFolder"
            label="Back"
            no-caps
          />
          <div class="text-h6 ellipsis">{{ selectedFolder }}</div>
          <q-space />
          <q-input
            v-model="searchQuery"
            dense
            outlined
            placeholder="Search clips"
            clearable
            class="library-search-clips"
          >
            <template v-slot:prepend>
              <q-icon name="search" />
            </template>
          </q-input>
          <q-btn-dropdown
            color="primary"
            outline
            icon="sort"
            :label="videoSortLabel"
            no-caps
          >
            <q-list>
              <q-item
                v-for="opt in videoSortOptions"
                :key="opt.value"
                clickable
                v-close-popup
                @click="videoSortMode = opt.value"
              >
                <q-item-section>{{ opt.label }}</q-item-section>
                <q-item-section v-if="videoSortMode === opt.value" side>
                  <q-icon name="check" color="accent" />
                </q-item-section>
              </q-item>
            </q-list>
          </q-btn-dropdown>
          <q-btn-toggle
            v-model="viewMode"
            no-caps
            unelevated
            toggle-color="accent"
            :options="[
              { value: 'grid', icon: 'view_module', tooltip: 'Grid view' },
              { value: 'list', icon: 'view_list', tooltip: 'List view' },
            ]"
          />
          <input
            ref="videoUploadInput"
            type="file"
            multiple
            accept="video/*"
            style="display: none"
            @change="handleVideoFiles"
          />
          <q-btn
            color="accent"
            unelevated
            icon="cloud_upload"
            label="Upload"
            no-caps
            :loading="isUploading"
            @click="triggerVideoUpload"
          />
        </div>

        <!-- Tag filter strip -->
        <div class="library-tag-filters q-mb-md">
          <q-icon name="label" size="sm" color="grey-5" />
          <q-chip
            v-for="t in CLIP_TAGS"
            :key="t.value"
            clickable
            :selected="tagFilters.has(t.value)"
            :color="tagFilters.has(t.value) ? t.color : 'grey-9'"
            text-color="white"
            size="sm"
            dense
            @click="toggleTagFilter(t.value)"
          >
            {{ t.label }}
          </q-chip>
          <q-btn
            v-if="tagFilterCount > 0"
            flat
            dense
            icon="filter_alt_off"
            color="grey-5"
            label="Clear"
            no-caps
            size="sm"
            @click="clearTagFilters"
          />
        </div>

        <!-- Bulk action bar (only when something is selected) -->
        <div v-if="selectedVideoCount > 0" class="library-bulk-bar q-mb-md">
          <span>{{ selectedVideoCount }} selected</span>
          <q-space />
          <q-btn
            flat
            icon="close"
            label="Clear"
            color="grey-3"
            no-caps
            @click="clearSelection"
          />
          <q-btn
            outline
            icon="delete"
            label="Delete"
            color="negative"
            no-caps
            @click="bulkDeleteSelected"
          />
        </div>

        <!-- Grid view -->
        <div v-if="viewMode === 'grid'" class="video-grid">
          <q-card
            v-for="video in sortedFilteredVideos"
            :key="video.id"
            class="video-card"
            :class="{ 'video-card--selected': selectedVideoIds.has(video.id) }"
            v-ripple
          >
            <div class="thumbnail-wrapper">
              <q-checkbox
                :model-value="selectedVideoIds.has(video.id)"
                @update:model-value="toggleVideoSelection(video.id)"
                color="accent"
                class="select-checkbox"
                dark
              />
              <q-img
                :src="getVideoThumbnail(video)"
                :ratio="16 / 9"
                class="thumbnail"
              >
                <div class="hover-actions absolute-full flex flex-center">
                  <q-btn
                    round
                    icon="play_circle"
                    color="white"
                    size="lg"
                    class="play-btn"
                    @click="playVideo(video)"
                  />
                </div>
              </q-img>

              <q-badge color="dark" class="duration-badge">
                {{
                  video.duration > 0
                    ? formatShortDuration(video.duration)
                    : 'Loading…'
                }}
              </q-badge>
              <q-badge
                v-if="settingsStore.demoMode"
                color="purple"
                text-color="white"
                class="demo-pill demo-pill--video"
              >
                Demo
              </q-badge>
            </div>

            <q-card-section class="card-content">
              <div class="text-subtitle1 text-weight-bold ellipsis">
                {{ video.title }}
              </div>
              <div class="text-caption text-grey q-mt-xs">
                {{ formatDate(video.timestamp) }}
              </div>
              <div v-if="tagsFor(video.id).length" class="card-tags q-mt-xs">
                <q-chip
                  v-for="t in tagsFor(video.id)"
                  :key="t"
                  :color="tagMeta(t).color"
                  text-color="white"
                  size="sm"
                  dense
                  removable
                  @remove="onToggleClipTag(video.id, t)"
                >
                  {{ tagMeta(t).label }}
                </q-chip>
              </div>
            </q-card-section>

            <q-card-actions class="card-actions">
              <q-btn flat round dense icon="label" color="grey-6">
                <q-tooltip>Tag clip</q-tooltip>
                <q-menu auto-close>
                  <q-list dense>
                    <q-item
                      v-for="t in CLIP_TAGS"
                      :key="t.value"
                      clickable
                      @click="onToggleClipTag(video.id, t.value)"
                    >
                      <q-item-section avatar>
                        <q-icon
                          :name="
                            tagsFor(video.id).includes(t.value)
                              ? 'check_box'
                              : 'check_box_outline_blank'
                          "
                          :color="t.color"
                        />
                      </q-item-section>
                      <q-item-section>{{ t.label }}</q-item-section>
                    </q-item>
                  </q-list>
                </q-menu>
              </q-btn>
              <q-btn
                flat
                round
                dense
                icon="delete"
                color="grey-6"
                @click="deleteVideo(video)"
              />
              <q-btn
                flat
                round
                dense
                icon="download"
                color="grey-6"
                @click="downloadVideo(video)"
              />
              <q-space />
              <q-btn
                flat
                round
                dense
                icon="play_arrow"
                color="accent"
                @click="playVideo(video)"
              />
            </q-card-actions>
          </q-card>
        </div>

        <!-- List view -->
        <q-list v-else separator class="library-list">
          <q-item
            v-for="video in sortedFilteredVideos"
            :key="video.id"
            clickable
            v-ripple
            @click="playVideo(video)"
          >
            <q-item-section avatar>
              <q-checkbox
                :model-value="selectedVideoIds.has(video.id)"
                @update:model-value="toggleVideoSelection(video.id)"
                @click.stop
                color="accent"
              />
            </q-item-section>
            <q-item-section avatar>
              <q-img
                :src="getVideoThumbnail(video)"
                :ratio="16 / 9"
                style="width: 96px; border-radius: 6px"
              />
            </q-item-section>
            <q-item-section>
              <q-item-label class="text-weight-bold">
                {{ video.title }}
              </q-item-label>
              <q-item-label caption>
                {{ formatDate(video.timestamp) }}
              </q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-badge color="dark">
                {{
                  video.duration > 0
                    ? formatShortDuration(video.duration)
                    : '—'
                }}
              </q-badge>
            </q-item-section>
            <q-item-section side>
              <div class="row q-gutter-xs">
                <q-btn
                  flat
                  round
                  dense
                  icon="play_arrow"
                  color="accent"
                  @click.stop="playVideo(video)"
                />
                <q-btn
                  flat
                  round
                  dense
                  icon="download"
                  color="grey-6"
                  @click.stop="downloadVideo(video)"
                />
                <q-btn
                  flat
                  round
                  dense
                  icon="delete"
                  color="grey-6"
                  @click.stop="deleteVideo(video)"
                />
              </div>
            </q-item-section>
          </q-item>
        </q-list>

        <div
          v-if="!sortedFilteredVideos.length"
          class="text-grey text-center q-pa-lg"
        >
          No clips in this folder.
        </div>
      </div>
    </div>
    <q-dialog v-model="renameDialog" persistent>
      <q-card>
        <q-card-section>
          <div class="text-h6">Rename Folder</div>
          <q-input v-model="renameInput" label="New Folder Name" autofocus />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn
            flat
            label="Rename"
            color="primary"
            @click="renameFolderConfirm"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
    <q-dialog v-model="deleteDialog" persistent>
      <q-card>
        <q-card-section>
          <div class="text-h6">Delete Folder</div>
          <div>
            Are you sure you want to delete <b>{{ folderToDelete }}</b
            >?
          </div>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn
            flat
            label="Delete"
            color="negative"
            @click="deleteFolderConfirm"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
    <q-dialog
      v-model="videoDialog"
      persistent
      :maximized="$q.screen.lt.sm"
    >
      <q-card class="playback-card">
        <div class="playback-card__body">
          <div class="playback-card__video">
            <div class="row items-center q-px-md q-pt-md q-pb-sm">
              <span class="text-h6">Playing</span>
              <q-badge
                v-if="settingsStore.demoMode"
                color="purple"
                text-color="white"
                class="q-ml-sm"
              >
                Demo clip
              </q-badge>
              <q-space />
              <q-btn
                flat
                round
                dense
                icon="close"
                v-close-popup
                color="grey-6"
              />
            </div>
            <video
              v-if="videoToPlay"
              ref="playbackVideoEl"
              :src="getVideoUrl(videoToPlay)"
              controls
              autoplay
              class="playback-video"
              @error="onVideoError"
            ></video>
            <div v-if="videoError" class="text-negative q-px-md q-pb-sm">
              Failed to load video.
            </div>
          </div>
          <div class="playback-card__logs">
            <div class="text-subtitle1 q-mb-sm">Detection Logs</div>
            <div v-if="logs.length === 0" class="text-grey">
              No detection events recorded for this clip.
            </div>
            <q-list v-else dense class="logs-scrollable">
              <q-item
                v-for="(log, idx) in logs"
                :key="idx"
                clickable
                v-ripple
                @click="seekToTimestamp(log.timestamp)"
              >
                <q-item-section avatar>
                  <q-badge
                    :color="
                      log.event_type === 'motion'
                        ? 'primary'
                        : log.event_type === 'unknown'
                        ? 'negative'
                        : 'positive'
                    "
                    class="event-badge"
                  >
                    {{ log.event_type }}
                  </q-badge>
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-mono">
                    {{ formatShortDuration(log.timestamp) }}
                  </q-item-label>
                  <q-item-label
                    v-if="log.extra && log.extra.name"
                    caption
                  >
                    {{ log.extra.name }}
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-icon name="play_arrow" color="accent" size="sm" />
                </q-item-section>
              </q-item>
            </q-list>
          </div>
        </div>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<style lang="scss" scoped>
.gallery-wrapper {
  max-width: 1600px;
  margin: 0 auto;
}

.library-clock {
  text-align: center;
  font-size: 0.95rem;
  color: var(--vigilant-text-dim, rgba(244, 238, 249, 0.7));
  letter-spacing: 0.02em;
}

.library-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.library-stat {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(156, 39, 176, 0.06);
  border: 1px solid rgba(156, 39, 176, 0.2);
  min-width: 0;
}

:global(.body--dark) .library-stat {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
}

.library-stat__value {
  font-size: 1.25rem;
  font-weight: 700;
  line-height: 1.15;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.library-stat__label {
  font-size: 0.7rem;
  color: rgba(0, 0, 0, 0.55);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

:global(.body--dark) .library-stat__label {
  color: rgba(244, 238, 249, 0.65);
}

.library-toolbar,
.library-folder-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.library-search,
.library-search-clips {
  flex: 1 1 220px;
  min-width: 0;
  max-width: 360px;
}

.library-bulk-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(156, 39, 176, 0.18);
  border: 1px solid rgba(156, 39, 176, 0.4);
  border-radius: 8px;
}

.library-tag-filters {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.card-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.folder-card {
  position: relative;
  transition: transform 0.2s ease, box-shadow 0.2s ease,
    border-color 0.2s ease;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.folder-card:hover {
  transform: translateY(-2px);
  border-color: rgba(156, 39, 176, 0.4);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.18);
}

.folder-name {
  font-size: 0.9rem;
  word-break: break-word;
  text-align: center;
  line-height: 1.2;
}

.folder-count-chip {
  font-weight: 600;
}

.demo-pill {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 2;
  letter-spacing: 0.05em;
}

.demo-pill--video {
  top: 8px;
  right: 8px;
  bottom: auto;
  left: auto;
}

.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(280px, 100%), 1fr));
  gap: 20px;
}

.video-card {
  transition: transform 0.3s ease, box-shadow 0.3s ease, outline 0.2s ease;
  border-radius: 12px;
  outline: 2px solid transparent;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25) !important;

    .hover-actions {
      opacity: 1;
    }
    .select-checkbox {
      opacity: 1;
    }
  }
}

.video-card--selected {
  outline-color: var(--q-accent, #9c27b0);

  .select-checkbox {
    opacity: 1;
  }
}

.thumbnail-wrapper {
  position: relative;
}

.thumbnail {
  border-radius: 12px 12px 0 0;
}

.select-checkbox {
  position: absolute;
  top: 6px;
  left: 6px;
  z-index: 2;
  background: rgba(0, 0, 0, 0.55);
  border-radius: 6px;
  padding: 2px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.hover-actions {
  background: rgba(0, 0, 0, 0.5);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.play-btn {
  transform: scale(1.4);
}

.duration-badge {
  position: absolute;
  bottom: 10px;
  right: 10px;
  padding: 4px 8px;
  border-radius: 4px;
}

.card-content {
  padding: 12px 16px 8px;
}

.card-actions {
  padding: 4px 12px 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.library-list {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
}

.text-mono {
  font-family: 'SFMono-Regular', Menlo, Consolas, monospace;
}

.event-badge {
  text-transform: uppercase;
  font-size: 0.7rem;
  letter-spacing: 0.05em;
}

.playback-card {
  width: min(1100px, 96vw);
  max-width: 100%;
}

.playback-card__body {
  display: flex;
  flex-wrap: wrap;
}

.playback-card__video {
  flex: 2 1 480px;
  min-width: 0;
}

.playback-card__logs {
  flex: 1 1 280px;
  min-width: 0;
  border-left: 1px solid rgba(0, 0, 0, 0.08);
  padding: 16px;
  max-height: 70vh;
  overflow-y: auto;
}

.body--dark .playback-card__logs {
  border-left-color: rgba(255, 255, 255, 0.08);
}

.playback-video {
  width: 100%;
  display: block;
  background: #000;
  max-height: 70vh;
}

.logs-scrollable {
  max-height: 60vh;
  overflow-y: auto;
  padding-right: 4px;
}

@media (max-width: 599px) {
  .library-stats {
    /* keep 3 columns but compact: stack icon over text inside each tile */
    gap: 6px;
  }
  .library-stat {
    flex-direction: column;
    align-items: flex-start;
    padding: 8px 10px;
    gap: 4px;
  }
  .library-stat__value {
    font-size: 1rem;
  }
  .library-stat__label {
    font-size: 0.6rem;
    letter-spacing: 0.02em;
  }
  .library-toolbar,
  .library-folder-toolbar {
    gap: 8px;
  }
  .library-search,
  .library-search-clips {
    flex-basis: 100%;
    max-width: 100%;
  }
  .playback-card__logs {
    flex-basis: 100%;
    border-left: none;
    border-top: 1px solid rgba(0, 0, 0, 0.08);
    max-height: 40vh;
  }
  .playback-video {
    max-height: 50vh;
  }
}
</style>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import { useQuasar } from 'quasar';
import { useSettingsStore } from 'stores/settingsStore';
import {
  demoVideoFolders,
  findDemoVideoFolder,
  buildDemoLogs,
} from 'src/demo/demoData';
import {
  CLIP_TAGS,
  toggleClipTag,
  getClipTags,
  demoState,
  type ClipTag,
} from 'src/demo/demoState';

interface Video {
  id: string;
  title: string;
  timestamp: Date;
  duration: number;
  thumbnail: string;
  url: string;
}

interface LogEntry {
  event_type: 'motion' | 'unknown' | 'known';
  timestamp: number;
  extra?: Record<string, unknown>;
}

const $q = useQuasar();
const settingsStore = useSettingsStore();
const API_BASE = ref(settingsStore.uploadApiUrl);

const searchQuery = ref('');
const dateRange = ref<{ from: string | null; to: string | null }>({
  from: null,
  to: null,
});
const dateRangeString = ref<string | null>(null);

const selectedFolder = ref('');
const videoFiles = ref<File[]>([]);
const isUploading = ref(false);
const folders = ref<string[]>([]);

const renameDialog = ref(false);
const deleteDialog = ref(false);
const renameInput = ref('');
const folderToRename = ref('');
const folderToDelete = ref('');

const videoDialog = ref(false);
const videoToPlay = ref<Video | null>(null);
const videoError = ref(false);
const playbackVideoEl = ref<HTMLVideoElement | null>(null);

const folderSearchQuery = ref('');

type FolderSortMode = 'newest' | 'oldest' | 'name';
const folderSortOptions: { value: FolderSortMode; label: string }[] = [
  { value: 'newest', label: 'Newest first' },
  { value: 'oldest', label: 'Oldest first' },
  { value: 'name', label: 'Name (A → Z)' },
];
const folderSortMode = ref<FolderSortMode>('newest');
const folderSortLabel = computed(
  () => folderSortOptions.find((o) => o.value === folderSortMode.value)?.label ?? 'Sort'
);

const filteredFolders = computed(() => {
  const filtered = folders.value.filter((folder) => {
    const matchesSearchQuery = folder
      .toLowerCase()
      .includes(folderSearchQuery.value.toLowerCase());

    const folderDate = parseDateFromFolderName(folder);
    const matchesDateRange =
      (!dateRange.value.from ||
        (folderDate && folderDate >= new Date(dateRange.value.from))) &&
      (!dateRange.value.to ||
        (folderDate && folderDate <= new Date(dateRange.value.to)));

    return matchesSearchQuery && matchesDateRange;
  });
  return filtered.sort((a, b) => {
    if (folderSortMode.value === 'name') return a.localeCompare(b);
    const dateA = parseDateFromFolderName(a);
    const dateB = parseDateFromFolderName(b);
    if (dateA && dateB) {
      return folderSortMode.value === 'newest'
        ? dateB.getTime() - dateA.getTime()
        : dateA.getTime() - dateB.getTime();
    }
    if (dateA) return -1;
    if (dateB) return 1;
    return a.localeCompare(b);
  });
});

// Cached count per folder so the chip doesn't make every render thrash. In
// demo mode we read the static folder length; in real mode we don't have it
// without a fetch, so fall back to a dash.
const folderClipCount = (folder: string): string => {
  if (settingsStore.demoMode) {
    const match = demoVideoFolders.find((f) => f.name === folder);
    if (!match) return '—';
    const n = match.videos.length;
    return `${n} ${n === 1 ? 'clip' : 'clips'}`;
  }
  return '—';
};

const totalClipCount = computed(() => {
  if (settingsStore.demoMode) {
    return demoVideoFolders.reduce((sum, f) => sum + f.videos.length, 0);
  }
  return folders.value.length; // best-effort: number of folders as a stand-in
});

const totalDurationLabel = computed(() => {
  // Demo clips are short samples; we approximate the total runtime as
  // 12 s per clip so the strip shows something meaningful in demo mode.
  if (settingsStore.demoMode) {
    const seconds = totalClipCount.value * 12;
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}m ${String(s).padStart(2, '0')}s`;
  }
  return '—';
});

watch(dateRangeString, (newValue) => {
  if (newValue) {
    const [from, to] = newValue.split(' to ');
    dateRange.value = { from, to };
  } else {
    dateRange.value = { from: null, to: null };
  }
});

const videos = ref<Video[]>([]);

type VideoSortMode = 'newest' | 'oldest' | 'longest' | 'shortest';
const videoSortOptions: { value: VideoSortMode; label: string }[] = [
  { value: 'newest', label: 'Newest first' },
  { value: 'oldest', label: 'Oldest first' },
  { value: 'longest', label: 'Longest duration' },
  { value: 'shortest', label: 'Shortest duration' },
];
const videoSortMode = ref<VideoSortMode>('newest');
const videoSortLabel = computed(
  () => videoSortOptions.find((o) => o.value === videoSortMode.value)?.label ?? 'Sort'
);

const viewMode = ref<'grid' | 'list'>('grid');

// Bulk selection — Set of Video.id, persists per session.
const selectedVideoIds = ref<Set<string>>(new Set());
const selectedVideoCount = computed(() => selectedVideoIds.value.size);
const toggleVideoSelection = (id: string) => {
  const next = new Set(selectedVideoIds.value);
  if (next.has(id)) {
    next.delete(id);
  } else {
    next.add(id);
  }
  selectedVideoIds.value = next;
};
const clearSelection = () => {
  selectedVideoIds.value = new Set();
};
const bulkDeleteSelected = () => {
  const ids = selectedVideoIds.value;
  if (ids.size === 0) return;
  videos.value = videos.value.filter((v) => !ids.has(v.id));
  $q.notify({
    type: 'positive',
    message: `Removed ${ids.size} clip${ids.size === 1 ? '' : 's'} from view${
      settingsStore.demoMode ? ' (demo)' : ''
    }.`,
  });
  clearSelection();
};

const filteredVideos = computed(() => {
  return videos.value.filter((video) => {
    const matchesSearchQuery = video.title
      .toLowerCase()
      .includes(searchQuery.value.toLowerCase());

    const videoDate = new Date(video.timestamp);
    const matchesDateRange =
      (!dateRange.value.from || videoDate >= new Date(dateRange.value.from)) &&
      (!dateRange.value.to || videoDate <= new Date(dateRange.value.to));

    return matchesSearchQuery && matchesDateRange;
  });
});

// Active tag filters — empty = show all. Touch demoState.clipTags inside the
// computed below so Vue tracks tag mutations and re-renders.
const tagFilters = ref<Set<ClipTag>>(new Set());
const tagFilterCount = computed(() => tagFilters.value.size);

const toggleTagFilter = (tag: ClipTag) => {
  const next = new Set(tagFilters.value);
  if (next.has(tag)) {
    next.delete(tag);
  } else {
    next.add(tag);
  }
  tagFilters.value = next;
};

const clearTagFilters = () => {
  tagFilters.value = new Set();
};

const tagsFor = (clipId: string): ClipTag[] => {
  // Read from demoState to keep reactivity tracked.
  void demoState.clipTags;
  return getClipTags(clipId);
};

const tagMeta = (tag: ClipTag) =>
  CLIP_TAGS.find((t) => t.value === tag) ?? CLIP_TAGS[0];

const sortedFilteredVideos = computed(() => {
  const arr = filteredVideos.value.filter((video) => {
    if (!tagFilters.value.size) return true;
    const tags = tagsFor(video.id);
    for (const t of tagFilters.value) {
      if (!tags.includes(t)) return false;
    }
    return true;
  });
  switch (videoSortMode.value) {
    case 'oldest':
      return arr.sort((a, b) => +a.timestamp - +b.timestamp);
    case 'longest':
      return arr.sort((a, b) => b.duration - a.duration);
    case 'shortest':
      return arr.sort((a, b) => a.duration - b.duration);
    case 'newest':
    default:
      return arr.sort((a, b) => +b.timestamp - +a.timestamp);
  }
});

const onToggleClipTag = (clipId: string, tag: ClipTag) => {
  toggleClipTag(clipId, tag);
};

const formatDate = (date: Date) => {
  return new Intl.DateTimeFormat('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
};

// Compact mm:ss[.t] used in cards and the detection log list. Falls back to
// h:mm:ss for long clips.
const formatShortDuration = (seconds: number) => {
  if (!isFinite(seconds) || seconds < 0) return '0:00';
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }
  return `${minutes}:${String(secs).padStart(2, '0')}`;
};

const getVideoUrl = (video: Video) => video.url;
const getVideoThumbnail = (video: Video) =>
  video.thumbnail || '/icons/vigilant.png';

const playVideo = (video: Video) => {
  videoToPlay.value = video;
  videoDialog.value = true;
  videoError.value = false;
};

const onVideoError = () => {
  videoError.value = true;
};

const downloadVideo = (video: Video) => {
  const link = document.createElement('a');
  link.href = getVideoUrl(video);
  link.download = video.title;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

const deleteVideo = (video: Video) => {
  videos.value = videos.value.filter((v) => v.id !== video.id);
  if (selectedVideoIds.value.has(video.id)) {
    const next = new Set(selectedVideoIds.value);
    next.delete(video.id);
    selectedVideoIds.value = next;
  }
  $q.notify({
    type: 'positive',
    message: `Removed "${video.title}" from view${
      settingsStore.demoMode ? ' (demo)' : ''
    }.`,
  });
};

const videoUploadInput = ref<HTMLInputElement | null>(null);

const triggerVideoUpload = () => {
  videoUploadInput.value?.click();
};

const handleVideoFiles = async (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (!input.files || !input.files.length) return;
  videoFiles.value = Array.from(input.files);
  await uploadVideos();
  // Reset the input so the same file selected twice still fires change.
  input.value = '';
};

const uploadVideos = async () => {
  if (!selectedFolder.value) {
    $q.notify({
      type: 'negative',
      message: 'Please select a folder',
      icon: 'warning',
    });
    return;
  }
  if (!videoFiles.value.length) {
    $q.notify({
      type: 'negative',
      message: 'Please select videos to upload',
      icon: 'warning',
    });
    return;
  }
  if (settingsStore.demoMode) {
    $q.notify({
      type: 'info',
      message: 'Demo mode: upload is disabled.',
      icon: 'science',
    });
    videoFiles.value = [];
    return;
  }
  isUploading.value = true;
  try {
    const formData = new FormData();
    formData.append('folder', selectedFolder.value);
    videoFiles.value.forEach((file) => {
      formData.append('videos', file);
    });
    await fetch(`${API_BASE.value}/api/upload-video`, {
      method: 'POST',
      body: formData,
    });
    $q.notify({
      type: 'positive',
      message: 'Videos uploaded successfully!',
      icon: 'check_circle',
    });
    videoFiles.value = [];
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: `Upload failed: ${
        error instanceof Error ? error.message : 'Unknown error'
      }`,
      icon: 'error',
    });
  } finally {
    isUploading.value = false;
  }
};

// Helper to parse date from folder name (e.g., 'May, 07, 2025 - 14:23:45')
function parseDateFromFolderName(folder: string): Date | null {
  // Try multiple formats
  // 1. 'May, 06, 2025 - 08:53:35'
  let match = folder.match(
    /([A-Za-z]+), (\d{2}), (\d{4}) - (\d{2}):(\d{2}):(\d{2})/
  );
  if (match) {
    const [, month, day, year, hour, min, sec] = match;
    return new Date(`${month} ${day}, ${year} ${hour}:${min}:${sec}`);
  }
  // 2. 'May 07, 2025, 12:58:02'
  match = folder.match(/([A-Za-z]+) (\d{2}), (\d{4}), (\d{2}):(\d{2}):(\d{2})/);
  if (match) {
    const [, month, day, year, hour, min, sec] = match;
    return new Date(`${month} ${day}, ${year} ${hour}:${min}:${sec}`);
  }
  // 3. 'May-5-2025' or 'May-06-2025'
  match = folder.match(/([A-Za-z]+)-(\d{1,2})-(\d{4})/);
  if (match) {
    const [, month, day, year] = match;
    return new Date(`${month} ${day}, ${year}`);
  }
  // 4. 'May 07, 2025' (no time)
  match = folder.match(/([A-Za-z]+) (\d{2}), (\d{4})/);
  if (match) {
    const [, month, day, year] = match;
    return new Date(`${month} ${day}, ${year}`);
  }
  return null;
}

// Helper to parse date from video filename (e.g., '2025-05-07_14-23-45.mp4')
function parseDateFromVideoFilename(filename: string): Date | null {
  const match = filename.match(
    /(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})/
  );
  if (!match) return null;
  const [, year, month, day, hour, min, sec] = match;
  return new Date(`${year}-${month}-${day}T${hour}:${min}:${sec}`);
}

function fetchVideoDurations() {
  videos.value.forEach((video, idx) => {
    const tempVideo = document.createElement('video');
    tempVideo.preload = 'metadata';
    tempVideo.src = video.url;
    tempVideo.onloadedmetadata = () => {
      videos.value[idx].duration = tempVideo.duration;
    };
    tempVideo.onerror = () => {
      videos.value[idx].duration = 0;
    };
  });
}

function generateVideoThumbnails() {
  videos.value.forEach((video, idx) => {
    if (video.thumbnail) return; // Skip if already set
    const tempVideo = document.createElement('video');
    tempVideo.preload = 'metadata';
    tempVideo.src = video.url;
    tempVideo.muted = true;
    tempVideo.currentTime = 0.5; // Try to grab a frame at 0.5s
    tempVideo.onloadeddata = () => {
      const canvas = document.createElement('canvas');
      canvas.width = tempVideo.videoWidth;
      canvas.height = tempVideo.videoHeight;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(tempVideo, 0, 0, canvas.width, canvas.height);
        videos.value[idx].thumbnail = canvas.toDataURL('image/png');
      }
    };
    tempVideo.onerror = () => {
      videos.value[idx].thumbnail = '/icons/vigilant.png';
    };
  });
}

const fetchFolders = async () => {
  if (settingsStore.demoMode) {
    folders.value = demoVideoFolders.map((f) => f.name);
    return;
  }
  try {
    const res = await fetch(`${API_BASE.value}/api/video-folders`);
    if (!res.ok) throw new Error('Failed to fetch folders');
    folders.value = await res.json();
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: `Failed to load folders: ${
        error instanceof Error ? error.message : 'Unknown error'
      }`,
      icon: 'error',
    });
  }
};

const fetchVideosInFolder = async () => {
  if (!selectedFolder.value) return;
  if (settingsStore.demoMode) {
    const demo = findDemoVideoFolder(selectedFolder.value);
    videos.value = (demo?.videos ?? []).map((v, idx) => ({
      id: `${selectedFolder.value}-${idx}`,
      title: v.filename,
      timestamp: parseDateFromVideoFilename(v.filename) || new Date(),
      duration: 0,
      thumbnail: v.thumbnail,
      url: v.url,
    }));
    fetchVideoDurations();
    return;
  }
  try {
    const res = await fetch(
      `${API_BASE.value}/api/folder-videos?folder=${encodeURIComponent(
        selectedFolder.value
      )}`
    );
    if (!res.ok) throw new Error('Failed to fetch videos');
    const files = await res.json();
    // Only include browser-friendly files (hide .mov)
    const filteredFiles = files.filter((filename: string) =>
      /\.(mp4|avi|mkv)$/i.test(filename)
    );
    videos.value = filteredFiles.map((filename: string, idx: number) => ({
      id: `${selectedFolder.value}-${idx}`,
      title: filename,
      timestamp: parseDateFromVideoFilename(filename) || new Date(),
      duration: 0,
      thumbnail: '',
      url: `${API_BASE.value}/footage/${selectedFolder.value}/${filename}`,
    }));
    fetchVideoDurations();
    generateVideoThumbnails();
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: `Failed to load videos: ${
        error instanceof Error ? error.message : 'Unknown error'
      }`,
      icon: 'error',
    });
  }
};

const selectFolder = (folder: string) => {
  selectedFolder.value = folder;
  clearSelection();
  fetchVideosInFolder();
};

const clearSelectedFolder = () => {
  selectedFolder.value = '';
  videoFiles.value = [];
  videos.value = [];
  clearSelection();
};

function showRenameDialog(folder: string) {
  folderToRename.value = folder;
  renameInput.value = folder;
  renameDialog.value = true;
}

async function renameFolderConfirm() {
  if (settingsStore.demoMode) {
    $q.notify({ type: 'info', message: 'Demo mode: rename is disabled.' });
    renameDialog.value = false;
    return;
  }
  try {
    await fetch(`${API_BASE.value}/api/rename-folder`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: 'video',
        oldName: folderToRename.value,
        newName: renameInput.value,
      }),
    });
    $q.notify({ type: 'positive', message: 'Folder renamed!' });
    renameDialog.value = false;
    fetchFolders();
  } catch (e) {
    $q.notify({ type: 'negative', message: 'Rename failed' });
  }
}

function showDeleteDialog(folder: string) {
  folderToDelete.value = folder;
  deleteDialog.value = true;
}

async function deleteFolderConfirm() {
  if (settingsStore.demoMode) {
    $q.notify({ type: 'info', message: 'Demo mode: delete is disabled.' });
    deleteDialog.value = false;
    return;
  }
  try {
    await fetch(`${API_BASE.value}/api/delete-folder`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: 'video',
        name: folderToDelete.value,
      }),
    });
    $q.notify({ type: 'positive', message: 'Folder deleted!' });
    deleteDialog.value = false;
    fetchFolders();
  } catch (e) {
    $q.notify({ type: 'negative', message: 'Delete failed' });
  }
}

async function downloadFolder(folder: string) {
  const url = `${
    API_BASE.value
  }/api/download-folder?type=video&name=${encodeURIComponent(folder)}`;
  window.open(url, '_blank');
}

const logs = ref<LogEntry[]>([]);

watch(videoToPlay, async (newVideo) => {
  logs.value = [];
  if (!newVideo || !selectedFolder.value) return;
  if (settingsStore.demoMode) {
    logs.value = buildDemoLogs(newVideo.title);
    return;
  }
  try {
    const res = await fetch(
      `${API_BASE.value}/get-logs?folder=${encodeURIComponent(
        selectedFolder.value
      )}&video=${encodeURIComponent(newVideo.title)}`
    );
    if (res.ok) {
      logs.value = await res.json();
    }
  } catch (e) {
    logs.value = [];
  }
});

function seekToTimestamp(ts: number) {
  const videoEl = playbackVideoEl.value;
  if (!videoEl) return;
  videoEl.currentTime = ts;
  // Make the seek feel like an action, not a preference: jump and keep playing.
  const playPromise = videoEl.play();
  if (playPromise && typeof playPromise.catch === 'function') {
    playPromise.catch(() => {
      // Autoplay restrictions in some browsers — user can press play.
    });
  }
}

// Removed unused function 'updateDateRangeString' to resolve the compile error.

// Removed unused function 'filterFoldersByDate' to resolve the compile error.

function refreshFolders() {
  fetchFolders();
  $q.notify({
    type: 'positive',
    message: 'Folders refreshed!',
    icon: 'check_circle',
  });
}

const currentDateTime = ref('');
function updateCurrentDateTime() {
  const now = new Date();
  currentDateTime.value = now.toLocaleString('en-US', {
    dateStyle: 'full',
    timeStyle: 'medium',
  });
}

onMounted(() => {
  updateCurrentDateTime();
  setInterval(updateCurrentDateTime, 1000);
  fetchFolders();
});
</script>
