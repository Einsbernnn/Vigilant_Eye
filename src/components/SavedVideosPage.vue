<template>
  <q-page class="q-px-xl q-pt-xl">
    <div class="gallery-wrapper">
      <div v-if="!selectedFolder">
        <div class="row q-col-gutter-md items-center">
          <div class="row items-center no-wrap">
            <q-input
              dense
              outlined
              v-model="dateRangeString"
              placeholder="Select date range"
              class="date-picker"
              readonly
            >
              <template v-slot:prepend>
                <q-icon name="event" />
              </template>
              <q-popup-proxy>
                <q-date
                  range
                  v-model="dateRange"
                  mask="YYYY-MM-DD"
                  color="accent"
                  bordered
                  @update:model-value="updateDateRangeString"
                />
              </q-popup-proxy>
            </q-input>
            <q-btn
              color="primary"
              label="Search"
              icon="search"
              @click="filterFoldersByDate"
              class="q-ml-sm"
              push
            />
          </div>
        </div>
        <div
          v-for="folder in filteredFolders"
          :key="folder"
          class="col-xs-6 col-sm-4 col-md-3 col-lg-2"
        >
          <q-card
            class="image-card folder-card cursor-pointer"
            @click="selectFolder(folder)"
          >
            <div class="column items-center q-pa-md">
              <q-icon name="folder" color="accent" size="64px" />
              <div class="text-center text-weight-bold q-mt-sm">
                {{ folder }}
              </div>
              <div class="row q-gutter-xs q-mt-sm">
                <q-btn
                  dense
                  flat
                  icon="edit"
                  color="primary"
                  @click.stop="showRenameDialog(folder)"
                />
                <q-btn
                  dense
                  flat
                  icon="delete"
                  color="negative"
                  @click.stop="showDeleteDialog(folder)"
                />
                <q-btn
                  dense
                  flat
                  icon="download"
                  color="accent"
                  @click.stop="downloadFolder(folder)"
                />
              </div>
            </div>
          </q-card>
        </div>
        <div
          v-if="!folders.length"
          class="text-grey text-center q-pa-lg full-width"
        >
          No folders found
        </div>
      </div>
      <div v-else>
        <div class="row items-center q-mb-md">
          <q-btn
            flat
            icon="arrow_back"
            color="accent"
            @click="clearSelectedFolder"
            label="Back to Folders"
          />
          <div class="q-ml-md text-h6">{{ selectedFolder }}</div>
          <q-space />
          <input
            type="file"
            multiple
            accept="video/*"
            @change="handleVideoFiles"
          />
          <q-btn
            color="accent"
            icon="cloud_upload"
            label="Upload Video"
            @click="uploadVideos"
            :loading="isUploading"
          />
        </div>
        <div class="video-grid">
          <q-card
            v-for="video in filteredVideos"
            :key="video.id"
            class="video-card"
            v-ripple
          >
            <div class="thumbnail-wrapper">
              <q-img :src="video.thumbnail" :ratio="16 / 9" class="thumbnail">
                <div class="hover-actions absolute-full flex flex-center">
                  <q-btn
                    round
                    icon="play_circle"
                    color="white"
                    size="lg"
                    class="play-btn"
                  />
                </div>
              </q-img>

              <q-badge color="dark" class="duration-badge">
                {{ formatDuration(video.duration) }}
              </q-badge>
            </div>

            <q-card-section class="card-content">
              <div class="text-h6 text-weight-bold">{{ video.title }}</div>
              <div class="text-caption text-grey q-mt-xs">
                {{ formatDate(video.timestamp) }}
              </div>
            </q-card-section>

            <q-card-actions class="card-actions">
              <q-btn
                flat
                round
                icon="delete"
                color="grey-6"
                @click="deleteVideo(video)"
              />
              <q-btn
                flat
                round
                icon="download"
                color="grey-6"
                @click="downloadVideo(video)"
              />
              <q-space />
              <q-btn flat round icon="info" color="grey-6" />
            </q-card-actions>
          </q-card>
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
  </q-page>
</template>

<style lang="scss" scoped>
.gallery-wrapper {
  max-width: 1600px;
  margin: 0 auto;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

.search-input {
  flex-grow: 1;
  max-width: 400px;
}

.date-picker {
  flex-grow: 1;
  max-width: 400px;
}

.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.video-card {
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  border-radius: 12px;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2) !important;

    .hover-actions {
      opacity: 1;
    }
  }
}

.thumbnail-wrapper {
  position: relative;
}

.thumbnail {
  border-radius: 12px 12px 0 0;
}

.hover-actions {
  background: rgba(0, 0, 0, 0.5);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.play-btn {
  transform: scale(1.5);
}

.duration-badge {
  position: absolute;
  bottom: 10px;
  right: 10px;
  padding: 4px 8px;
  border-radius: 4px;
}

.card-content {
  padding: 16px;
}

.card-actions {
  padding: 8px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.date-picker {
  max-width: 300px;
  flex-grow: 1;
}
</style>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import { useQuasar } from 'quasar';
import { useSettingsStore } from 'stores/settingsStore';

interface Video {
  id: string;
  title: string;
  timestamp: Date;
  duration: number;
  thumbnail: string;
  url: string;
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

const folderSearchQuery = ref('');
const filteredFolders = computed(() => {
  return folders.value.filter((folder) => {
    const matchesSearchQuery = folder
      .toLowerCase()
      .includes(folderSearchQuery.value.toLowerCase());

    const folderDate = new Date(folder); // Assuming folder names are dates
    const matchesDateRange =
      (!dateRange.value.from || folderDate >= new Date(dateRange.value.from)) &&
      (!dateRange.value.to || folderDate <= new Date(dateRange.value.to));

    return matchesSearchQuery && matchesDateRange;
  });
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

const formatDate = (date: Date) => {
  return new Intl.DateTimeFormat('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
};

const formatDuration = (seconds: number) => {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
};

const downloadVideo = (video: Video) => {
  console.log('Downloading:', video);
};

const deleteVideo = (video: Video) => {
  console.log('Deleting:', video);
};

const handleVideoFiles = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (input.files) {
    videoFiles.value = Array.from(input.files);
  }
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

const fetchFolders = async () => {
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
  try {
    const res = await fetch(
      `${API_BASE.value}/api/folder-videos?folder=${encodeURIComponent(
        selectedFolder.value
      )}`
    );
    if (!res.ok) throw new Error('Failed to fetch videos');
    const files = await res.json();
    videos.value = files.map((filename: string, idx: number) => ({
      id: `${selectedFolder.value}-${idx}`,
      title: filename,
      timestamp: new Date(),
      duration: 0,
      thumbnail: '',
      url: `${API_BASE.value}/footage/${selectedFolder.value}/${filename}`,
    }));
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
  fetchVideosInFolder();
};

const clearSelectedFolder = () => {
  selectedFolder.value = '';
  videoFiles.value = [];
  videos.value = [];
};

function showRenameDialog(folder: string) {
  folderToRename.value = folder;
  renameInput.value = folder;
  renameDialog.value = true;
}

async function renameFolderConfirm() {
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

function updateDateRangeString() {
  if (dateRange.value.from && dateRange.value.to) {
    dateRangeString.value = `${dateRange.value.from} to ${dateRange.value.to}`;
  } else {
    dateRangeString.value = null;
  }
}

function filterFoldersByDate() {
  // Logic to filter folders based on the selected date range
  console.log('Filtering folders by date range:', dateRange.value);
}

onMounted(() => {
  fetchFolders();
});
</script>
