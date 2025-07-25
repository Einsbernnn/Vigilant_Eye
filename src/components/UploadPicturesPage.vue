<template>
  <q-page class="q-pa-lg">
    <div class="column items-center q-gutter-lg">
      <q-card class="upload-card q-pa-lg shadow-5">
        <q-form @submit.prevent="handleUpload" class="column q-gutter-y-md">
          <div class="q-mb-md">
            <q-select
              v-model="selectedFolder"
              :options="folders"
              label="Select a folder"
              option-label="name"
              option-value="name"
              dense
              outlined
              clearable
              emit-value
              map-options
              class="folder-select"
            />
            <!-- Enhanced File Input -->
            <div
              class="file-drop-area q-mt-md"
              @dragover.prevent
              @drop.prevent="handleDrop"
              @click="triggerFileInput"
            >
              <q-icon name="cloud_upload" size="48px" color="accent" />
              <div class="text-grey text-caption q-mt-sm">
                Drag and drop files here or click to select
              </div>
              <input
                type="file"
                multiple
                ref="fileInput"
                @change="handleFiles"
                style="display: none"
              />
            </div>

            <div v-if="selectedFiles.length" class="file-list q-mt-sm">
              <div
                v-for="(file, index) in selectedFiles"
                :key="index"
                class="file-item"
              >
                <q-icon name="insert_drive_file" size="16px" class="q-mr-sm" />
                {{ file.name }}
              </div>
            </div>
          </div>
          <div class="row items-center justify-end q-mb-md">
            <q-btn
              type="submit"
              color="accent"
              label="Upload"
              icon-right="send"
              :loading="isUploading"
              size="md"
              push
            >
              <template v-slot:loading>
                <q-spinner-hourglass size="xs" />
              </template>
            </q-btn>
          </div>

          <q-linear-progress
            v-if="isUploading"
            indeterminate
            color="accent"
            class="q-mt-md"
          />

          <transition-group
            name="staggered-fade"
            tag="div"
            class="q-mt-lg row q-col-gutter-md justify-center"
            v-if="previewImages.length"
          >
            <q-card
              v-for="(image, index) in previewImages"
              :key="index"
              class="preview-card cursor-pointer"
              @click="removeImage(index)"
            >
              <q-img
                :src="image"
                ratio="1"
                class="preview-image"
                spinner-color="accent"
              >
                <div class="absolute-top-right bg-transparent">
                  <q-btn
                    round
                    dense
                    flat
                    icon="close"
                    color="negative"
                    class="remove-btn"
                  />
                </div>

                <template v-slot:loading>
                  <q-spinner-puff color="accent" />
                </template>
              </q-img>
            </q-card>
          </transition-group>
        </q-form>
      </q-card>

      <q-card
        class="gallery-card q-pa-md"
        style="max-width: 1200px; width: 100%"
      >
        <div class="row items-center justify-between q-mb-md">
          <h5 class="q-ma-none text-weight-bold">Image Folder</h5>
          <div class="row items-center q-gutter-sm">
            <q-btn
              color="primary"
              icon="add"
              label="New Folder"
              @click="showCreateFolderDialog"
            />
            <q-btn
              color="accent"
              icon="refresh"
              label="Refresh"
              @click="fetchFolders"
              :loading="isFetchingFolders"
              v-if="!selectedFolder"
            />
            <q-btn
              color="positive"
              icon="play_arrow"
              label="Train Model"
              @click="triggerTrainingWithLogs"
              :loading="isTraining"
            >
              <template v-slot:loading>
                <q-spinner-hourglass size="xs" />
              </template>
            </q-btn>
          </div>
        </div>

        <div v-if="isTraining" class="q-mb-md">
          <q-banner class="bg-grey-2 text-dark q-pa-sm" rounded>
            <div
              ref="logContainer"
              style="
                max-height: 200px;
                overflow-y: auto;
                font-family: monospace;
                font-size: 13px;
              "
            >
              <div v-for="(line, idx) in trainingLogs" :key="idx">
                {{ line }}
              </div>
            </div>
          </q-banner>
          <div v-if="progress" class="text-center q-mt-md">
            <div class="text-grey">
              Processing image {{ progress.current }} of {{ progress.total }}
            </div>
            <q-linear-progress
              :value="progress.current / progress.total"
              color="accent"
              class="q-mt-sm"
            />
          </div>
        </div>

        <div v-if="isFetchingFolders" class="text-center q-pa-lg">
          <q-spinner color="accent" size="3em" />
          <div class="q-mt-sm text-grey">Loading folders...</div>
        </div>

        <q-banner
          v-else-if="fetchFoldersError"
          class="bg-negative text-white q-mb-md"
          rounded
        >
          <template v-slot:avatar>
            <q-icon name="error" color="white" />
          </template>
          Error loading folders: {{ fetchFoldersError }}
        </q-banner>

        <div v-else-if="!selectedFolder">
          <div class="row q-col-gutter-md">
            <div
              v-for="folder in folders"
              :key="folder"
              class="col-xs-6 col-sm-4 col-md-3 col-lg-2"
            >
              <q-card
                class="image-card folder-card cursor-pointer"
                @click="openFolder(folder)"
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
                      color="accent"
                      @click.stop="showRenameDialog(folder)"
                    />
                    <q-btn
                      dense
                      flat
                      icon="delete"
                      color="negative"
                      @click.stop="showDeleteDialog(folder)"
                    />
                  </div>
                </div>
              </q-card>
            </div>
            <div
              v-if="!folders.length && !isFetchingFolders"
              class="text-grey text-center q-pa-lg full-width"
            >
              No folders found
            </div>
          </div>
        </div>

        <div v-else>
          <div class="row items-center q-mb-md">
            <q-btn
              flat
              icon="arrow_back"
              color="accent"
              @click="closeFolder"
              label="Back to Folders"
            />
            <div class="q-ml-md text-h6">{{ selectedFolder }}</div>
            <q-space />
            <q-btn
              color="accent"
              icon="refresh"
              label="Refresh"
              @click="fetchImagesInFolder"
              :loading="isFetchingImages"
            />
          </div>
          <div v-if="isFetchingImages" class="text-center q-pa-lg">
            <q-spinner color="accent" size="3em" />
            <div class="q-mt-sm text-grey">Loading images...</div>
          </div>
          <q-banner
            v-else-if="fetchImagesError"
            class="bg-negative text-white q-mb-md"
            rounded
          >
            <template v-slot:avatar>
              <q-icon name="error" color="white" />
            </template>
            Error loading images: {{ fetchImagesError }}
          </q-banner>
          <div v-else class="row q-col-gutter-md">
            <div
              v-for="(image, index) in folderImages"
              :key="index"
              class="col-xs-6 col-sm-4 col-md-3 col-lg-2"
            >
              <q-card class="image-card">
                <q-img
                  :src="`${API_BASE}/dataset/${selectedFolder}/${image}`"
                  :ratio="1"
                  class="image-item"
                  spinner-color="accent"
                >
                  <template v-slot:loading>
                    <q-spinner-puff color="accent" />
                  </template>
                  <div
                    class="absolute-bottom text-caption text-center text-white overlay"
                  >
                    {{ image }}
                  </div>
                </q-img>
              </q-card>
            </div>
            <div
              v-if="!folderImages.length && !isFetchingImages"
              class="text-grey text-center q-pa-lg full-width"
            >
              No images found in this folder
            </div>
          </div>
        </div>
      </q-card>
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
            color="accent"
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
    <q-dialog v-model="createFolderDialog" persistent>
      <q-card>
        <q-card-section>
          <div class="text-h6">Create New Folder</div>
          <q-input v-model="newFolderName" label="Folder Name" autofocus />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn
            flat
            label="Create"
            color="accent"
            @click="createFolderConfirm"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { useQuasar } from 'quasar';
import { useSettingsStore } from 'stores/settingsStore';

const $q = useQuasar();
const settingsStore = useSettingsStore();

const API_BASE = ref(settingsStore.uploadApiUrl); // Ensure no trailing slash

const selectedFiles = ref<File[]>([]);
const previewImages = ref<string[]>([]);
const isUploading = ref(false);
const uploadSuccess = ref(false);

const triggerFileInput = () => {
  const fileInput = document.querySelector(
    'input[type="file"]'
  ) as HTMLInputElement;
  fileInput.click();
};

const handleFiles = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (input.files) {
    selectedFiles.value = Array.from(input.files);
    previewImages.value = selectedFiles.value.map((file) =>
      URL.createObjectURL(file)
    );
  }
};

const handleDrop = (event: DragEvent) => {
  if (event.dataTransfer?.files) {
    selectedFiles.value = Array.from(event.dataTransfer.files);
    previewImages.value = selectedFiles.value.map((file) =>
      URL.createObjectURL(file)
    );
  }
};

const removeImage = (index: number) => {
  selectedFiles.value.splice(index, 1);
  previewImages.value.splice(index, 1);
};

const handleUpload = async () => {
  if (!selectedFiles.value.length) {
    $q.notify({
      type: 'negative',
      message: 'Please select images to upload',
      icon: 'warning',
    });
    return;
  }
  if (!selectedFolder.value) {
    $q.notify({
      type: 'negative',
      message: 'Please select a folder',
      icon: 'warning',
    });
    return;
  }

  isUploading.value = true;

  try {
    const formData = new FormData();
    formData.append('folder', selectedFolder.value);
    selectedFiles.value.forEach((file) => {
      formData.append('images', file);
    });

    await fetch(`${API_BASE.value}/api/upload`, {
      method: 'POST',
      body: formData,
    });

    uploadSuccess.value = true;
    $q.notify({
      type: 'positive',
      message: `${selectedFiles.value.length} images uploaded successfully!`,
      icon: 'check_circle',
    });

    setTimeout(() => {
      uploadSuccess.value = false;
    }, 1000);

    await fetchFolders();

    // Revoke object URLs to avoid memory leaks
    previewImages.value.forEach((url) => URL.revokeObjectURL(url));
    selectedFiles.value = [];
    previewImages.value = [];
  } catch (error) {
    console.error('Upload error:', error);
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

const folders = ref<string[]>([]);
const isFetchingFolders = ref(true);
const fetchFoldersError = ref<string | null>(null);
const selectedFolder = ref<string | null>(null);
const folderImages = ref<string[]>([]);
const isFetchingImages = ref(false);
const fetchImagesError = ref<string | null>(null);

const fetchFolders = async () => {
  isFetchingFolders.value = true;
  fetchFoldersError.value = null;
  try {
    const res = await fetch(`${API_BASE.value}/api/image-folders`);
    if (!res.ok) throw new Error('Failed to fetch folders');
    folders.value = await res.json();
  } catch (error) {
    fetchFoldersError.value =
      error instanceof Error ? error.message : 'Failed to load folders';
  } finally {
    isFetchingFolders.value = false;
  }
};

const openFolder = (folder: string) => {
  selectedFolder.value = folder;
  fetchImagesInFolder();
};

const closeFolder = () => {
  selectedFolder.value = null;
  folderImages.value = [];
  fetchImagesError.value = null;
};

const fetchImagesInFolder = async () => {
  if (!selectedFolder.value) return;
  isFetchingImages.value = true;
  fetchImagesError.value = null;
  try {
    const res = await fetch(
      `${API_BASE.value}/api/folder-images?folder=${encodeURIComponent(
        selectedFolder.value
      )}`
    );
    if (!res.ok) throw new Error('Failed to fetch images');
    folderImages.value = (await res.json()).filter((img: string) =>
      /\.(jpg|jpeg|png)$/i.test(img)
    );
  } catch (error) {
    fetchImagesError.value =
      error instanceof Error ? error.message : 'Failed to load images';
  } finally {
    isFetchingImages.value = false;
  }
};

const renameDialog = ref(false);
const deleteDialog = ref(false);
const createFolderDialog = ref(false);
const renameInput = ref('');
const folderToRename = ref('');
const folderToDelete = ref('');
const newFolderName = ref('');

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
        type: 'image',
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
        type: 'image',
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

function showCreateFolderDialog() {
  newFolderName.value = '';
  createFolderDialog.value = true;
}

async function createFolderConfirm() {
  if (!newFolderName.value.trim()) {
    $q.notify({ type: 'negative', message: 'Folder name cannot be empty' });
    return;
  }
  try {
    await fetch(`${API_BASE.value}/api/create-folder`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: 'image', name: newFolderName.value }),
    });
    $q.notify({ type: 'positive', message: 'Folder created successfully!' });
    createFolderDialog.value = false;
    fetchFolders();
  } catch (e) {
    $q.notify({ type: 'negative', message: 'Failed to create folder' });
  }
}

const isTraining = ref(false);
const trainingLogs = ref<string[]>([]);
const logContainer = ref<HTMLElement | null>(null);
const progress = ref<{ current: number; total: number } | null>(null);

function parseProgressFromLog(line: string) {
  // Example: [INFO] processing image 4/789
  const match = line.match(/processing image (\d+)[\/](\d+)/i);
  if (match) {
    progress.value = {
      current: parseInt(match[1], 10),
      total: parseInt(match[2], 10),
    };
  }
}

// Prevent closing/navigating away during training
function handleBeforeUnload(e: BeforeUnloadEvent) {
  if (isTraining.value) {
    e.preventDefault();
    e.returnValue = '';
    return '';
  }
}
onMounted(() => {
  window.addEventListener('beforeunload', handleBeforeUnload);
});
onUnmounted(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload);
});

// Auto-scroll logs to latest
watch(trainingLogs, () => {
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight;
    }
  });
});

const triggerTrainingWithLogs = () => {
  isTraining.value = true;
  trainingLogs.value = [];
  progress.value = null;
  const eventSource = new EventSource(
    `${API_BASE.value}/api/train-model-stream`
  );
  eventSource.onmessage = (event) => {
    if (event.data === '[DONE]') {
      isTraining.value = false;
      eventSource.close();
      progress.value = null;
      $q.notify({
        type: 'positive',
        message: 'Model training completed!',
        icon: 'check_circle',
      });
    } else if (event.data.startsWith('ERROR:')) {
      isTraining.value = false;
      eventSource.close();
      progress.value = null;
      $q.notify({
        type: 'negative',
        message: event.data,
        icon: 'error',
      });
    } else {
      trainingLogs.value.push(event.data);
      parseProgressFromLog(event.data);
    }
  };
  eventSource.onerror = () => {
    isTraining.value = false;
    eventSource.close();
    progress.value = null;
    $q.notify({
      type: 'negative',
      message: 'Connection lost or server error.',
      icon: 'error',
    });
  };
};

watch(
  () => settingsStore.uploadApiUrl,
  (newValue) => {
    API_BASE.value = newValue;
  }
);

onMounted(() => {
  fetchFolders();
});
</script>

<style lang="scss" scoped>
.upload-card,
.gallery-card {
  border-radius: 12px;
  width: 100%;
}

.upload-card {
  max-width: 600px;
}

.gallery-card {
  max-width: 1200px;
}

.preview-card {
  width: 140px;
  position: relative;
  transition: transform 0.3s ease;

  &:hover {
    transform: translateY(-5px);
    .remove-btn {
      opacity: 1;
    }
  }
}

.preview-image {
  border-radius: 8px;
  width: 100%; // Ensure the image fits within the card
  height: auto; // Maintain aspect ratio
}

.remove-btn {
  position: absolute; // Position the button relative to the card
  top: 4px; // Adjust to place it in the top-right corner
  right: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;
  z-index: 10; // Ensure it appears above the image
}

.image-card {
  transition: transform 0.3s ease, box-shadow 0.3s ease;

  &:hover {
    transform: translateY(-5px);
    box-shadow: $shadow-5;

    .overlay {
      opacity: 1;
    }
  }
}

.preview-image,
.image-item {
  border-radius: 8px;
}

.remove-btn {
  opacity: 0;
  transition: opacity 0.2s ease;
}

.overlay {
  opacity: 0;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
  padding: 8px;
  transition: opacity 0.3s ease;
}

.staggered-fade-enter-active,
.staggered-fade-leave-active {
  transition: all 0.5s ease;
}

.staggered-fade-enter-from,
.staggered-fade-leave-to {
  opacity: 0;
  transform: scale(0.9);
}

.custom-file-input {
  display: flex;
  flex-direction: column;
  align-items: flex-start;

  .file-list {
    margin-top: 8px;
    .file-item {
      display: flex;
      align-items: center;
      font-size: 14px;
      color: #555;
    }
  }
}

.file-drop-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  transition: border-color 0.3s ease;

  &:hover {
    border-color: #007bff;
  }

  .text-caption {
    font-size: 14px;
  }
}

.folder-select {
  width: 100%;
  max-width: 400px;
}
</style>
