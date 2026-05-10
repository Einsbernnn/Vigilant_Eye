<template>
  <q-page class="q-pa-md q-pa-md-lg face-page">
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
      base folders and photos are placeholder content from randomuser.me. You
      can create folders, upload images, and run the (simulated) model
      training — changes live in your browser tab and reset on reload.
      Renames and deletes are disabled.
    </q-banner>

    <!-- Dataset stats -->
    <div class="dataset-stats q-mb-md">
      <div class="dataset-stat">
        <q-icon name="group" size="sm" color="accent" />
        <div>
          <div class="dataset-stat__value">{{ identityCount }}</div>
          <div class="dataset-stat__label">Identities</div>
        </div>
      </div>
      <div class="dataset-stat">
        <q-icon name="photo_library" size="sm" color="accent" />
        <div>
          <div class="dataset-stat__value">{{ totalImageCount }}</div>
          <div class="dataset-stat__label">Total images</div>
        </div>
      </div>
      <div class="dataset-stat">
        <q-icon name="model_training" size="sm" color="accent" />
        <div>
          <div class="dataset-stat__value">{{ lastTrainingLabel }}</div>
          <div class="dataset-stat__label">Last training</div>
        </div>
      </div>
      <div class="dataset-stat dataset-stat--action">
        <q-btn
          unelevated
          color="accent"
          icon="psychology"
          label="Test recognition"
          no-caps
          @click="testRecognitionDialog = true"
        />
      </div>
    </div>

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
              class="col-6 col-sm-4 col-md-3 col-lg-2"
            >
              <q-card
                class="image-card folder-card cursor-pointer"
                @click="openFolder(folder)"
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
                  <q-chip
                    square
                    size="sm"
                    color="accent"
                    text-color="white"
                    class="q-mt-xs folder-count-chip"
                  >
                    {{ folderImageCount(folder) }}
                  </q-chip>
                  <div class="row q-gutter-xs q-mt-sm folder-actions">
                    <q-btn
                      dense
                      flat
                      icon="info"
                      color="accent"
                      @click.stop="openIdentityDetail(folder)"
                    >
                      <q-tooltip>Details</q-tooltip>
                    </q-btn>
                    <q-btn
                      dense
                      flat
                      icon="edit"
                      color="accent"
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
          <div v-else class="dataset-grid">
            <div
              v-for="(image, index) in folderImages"
              :key="index"
              class="dataset-grid__cell"
            >
              <q-card class="image-card dataset-card">
                <q-badge
                  v-if="settingsStore.demoMode"
                  color="purple"
                  text-color="white"
                  class="demo-pill"
                >
                  Demo
                </q-badge>
                <q-img
                  :src="imageSrc(image)"
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

    <!-- Identity detail drawer -->
    <q-dialog
      v-model="identityDetailOpen"
      :maximized="$q.screen.lt.sm"
      transition-show="slide-left"
      transition-hide="slide-right"
      position="right"
    >
      <q-card class="identity-detail-card column">
        <q-card-section
          class="identity-detail__header row items-center q-pa-md"
        >
          <q-avatar size="42px" color="accent" text-color="white">
            <span>{{ initialsFor(detailIdentity) }}</span>
          </q-avatar>
          <div class="q-ml-md">
            <div class="text-h6">{{ detailIdentity }}</div>
            <div class="text-caption text-grey-4">
              Identity profile
            </div>
          </div>
          <q-space />
          <q-btn flat round dense icon="close" v-close-popup color="white" />
        </q-card-section>

        <q-scroll-area class="col">
          <div class="q-pa-md">
            <div class="identity-stat-row">
              <div class="identity-stat">
                <div class="identity-stat__value">
                  {{ identityImageCount(detailIdentity) }}
                </div>
                <div class="identity-stat__label">Photos</div>
              </div>
              <div class="identity-stat">
                <div class="identity-stat__value">
                  {{ identityLastSeenLabel(detailIdentity) }}
                </div>
                <div class="identity-stat__label">Last seen</div>
              </div>
              <div class="identity-stat">
                <div class="identity-stat__value">
                  {{ identityQualityScore(detailIdentity) }}%
                </div>
                <div class="identity-stat__label">Train quality</div>
              </div>
            </div>

            <div class="identity-section">
              <div class="identity-section__title">Recent photos</div>
              <div class="identity-thumbs">
                <div
                  v-for="img in recentImagesFor(detailIdentity)"
                  :key="img.filename"
                  class="identity-thumb"
                  :style="{ backgroundImage: `url(${img.url})` }"
                />
                <div
                  v-if="recentImagesFor(detailIdentity).length === 0"
                  class="text-grey"
                >
                  No photos in this folder.
                </div>
              </div>
            </div>

            <div class="identity-section">
              <div class="identity-section__title">Training quality</div>
              <q-linear-progress
                :value="identityQualityScore(detailIdentity) / 100"
                :color="
                  identityQualityScore(detailIdentity) >= 80
                    ? 'positive'
                    : identityQualityScore(detailIdentity) >= 60
                    ? 'warning'
                    : 'negative'
                "
                size="14px"
                rounded
              />
              <div class="text-caption text-grey-5 q-mt-xs">
                Synthetic score from photo count and image variety. Aim for
                30+ photos with mixed angles for the strongest match.
              </div>
            </div>

            <div class="identity-section">
              <div class="identity-section__title">Activity timeline</div>
              <q-timeline color="accent" dense layout="dense">
                <q-timeline-entry
                  v-for="(event, idx) in identityTimeline(detailIdentity)"
                  :key="idx"
                  :title="event.title"
                  :subtitle="event.when"
                  :icon="event.icon"
                  :color="event.color"
                />
              </q-timeline>
            </div>
          </div>
        </q-scroll-area>

        <q-separator />

        <q-card-actions class="q-pa-md">
          <q-btn
            outline
            color="negative"
            icon="delete_forever"
            label="Delete identity"
            no-caps
            :disable="!canDeleteIdentity(detailIdentity)"
            @click="confirmDeleteIdentity"
          />
          <q-space />
          <q-btn
            unelevated
            color="accent"
            icon="folder_open"
            label="Open"
            no-caps
            @click="openIdentityFromDetail"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Test Recognition dialog -->
    <q-dialog
      v-model="testRecognitionDialog"
      :maximized="$q.screen.lt.sm"
      @hide="resetTestRecognition"
    >
      <q-card class="test-recog-card">
        <q-card-section
          class="row items-center vigilant-demo-banner q-pa-md"
        >
          <q-icon name="psychology" size="sm" class="q-mr-sm" />
          <div class="text-h6">Test recognition</div>
          <q-space />
          <q-btn flat round dense icon="close" v-close-popup />
        </q-card-section>

        <q-card-section>
          <div class="text-caption text-grey q-mb-sm">
            Drop or pick an image. The match against the dataset is
            <strong>simulated</strong> — picks a deterministic identity from
            the file's size and name, with a synthetic confidence score.
          </div>

          <div
            class="test-recog-drop"
            :class="{ 'test-recog-drop--has': !!testFile }"
            @dragover.prevent
            @drop.prevent="onTestDrop"
            @click="testFileInput?.click()"
          >
            <q-img
              v-if="testFilePreview"
              :src="testFilePreview"
              :ratio="1"
              class="test-recog-drop__preview"
            />
            <template v-else>
              <q-icon name="add_photo_alternate" size="48px" color="accent" />
              <div class="text-grey text-caption q-mt-sm">
                Drop image here or click to browse
              </div>
            </template>
            <input
              ref="testFileInput"
              type="file"
              accept="image/*"
              style="display: none"
              @change="onTestFileChange"
            />
          </div>

          <div v-if="testResult" class="test-recog-result q-mt-md">
            <div class="row items-center q-gutter-md">
              <q-img
                :src="testResult.matchPreviewUrl"
                :ratio="1"
                class="test-recog-result__avatar"
              />
              <div class="col">
                <div class="text-overline text-grey-5">Best match</div>
                <div class="text-h5 text-weight-bold">
                  {{ testResult.identity }}
                </div>
                <q-linear-progress
                  :value="testResult.confidence"
                  color="accent"
                  size="14px"
                  class="q-mt-sm"
                  rounded
                />
                <div class="text-caption q-mt-xs">
                  Confidence: {{ Math.round(testResult.confidence * 100) }}%
                </div>
              </div>
            </div>
          </div>
        </q-card-section>

        <q-card-actions align="right" class="q-px-md q-pb-md">
          <q-btn flat label="Reset" color="grey-6" @click="resetTestRecognition" />
          <q-btn
            unelevated
            color="accent"
            label="Run match"
            :loading="testRunning"
            :disable="!testFile"
            @click="runTestRecognition"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { useQuasar } from 'quasar';
import { useSettingsStore } from 'stores/settingsStore';
import {
  demoImageFolders,
  findDemoImageFolder,
} from 'src/demo/demoData';
import {
  demoState,
  addDemoFolder,
  addDemoImages,
  getDemoExtraImages,
  markTrainingComplete,
} from 'src/demo/demoState';

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

  if (settingsStore.demoMode) {
    isUploading.value = true;
    // Simulate a brief upload — feels real, not instant.
    await new Promise((resolve) => setTimeout(resolve, 600));
    const folder = selectedFolder.value;
    // Existing image count for this folder so new filenames continue the
    // "alice_NNN.jpg" sequence (or just the folder slug for custom folders).
    const slug = folder.toLowerCase().replace(/[^a-z0-9]+/g, '_');
    const existingCount =
      (findDemoImageFolder(folder)?.images.length ?? 0) +
      getDemoExtraImages(folder).length;
    const entries = selectedFiles.value.map((file, i) => {
      const ext = file.name.match(/\.(jpe?g|png|webp)$/i)?.[0] ?? '.jpg';
      // Reuse the preview blob URL — no need to allocate a second one per
      // file. These intentionally outlive this scope (no revoke) because
      // they are the persistent <q-img> src for the demo folder.
      return {
        filename: `${slug}_${String(existingCount + i + 1).padStart(3, '0')}${ext}`,
        url: previewImages.value[i] ?? URL.createObjectURL(file),
      };
    });
    addDemoImages(folder, entries);
    uploadSuccess.value = true;
    $q.notify({
      type: 'positive',
      message: `${entries.length} image${
        entries.length === 1 ? '' : 's'
      } uploaded (demo).`,
      icon: 'check_circle',
    });
    setTimeout(() => {
      uploadSuccess.value = false;
    }, 1000);
    // Don't revoke previewImages — the new entries reuse those object URLs.
    selectedFiles.value = [];
    previewImages.value = [];
    isUploading.value = false;
    // If the user is viewing this folder, refresh so the uploads appear.
    if (selectedFolder.value === folder) {
      await fetchImagesInFolder();
    }
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
  if (settingsStore.demoMode) {
    folders.value = [
      ...demoImageFolders.map((f) => f.name),
      ...demoState.extraFolders,
    ];
    isFetchingFolders.value = false;
    return;
  }
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

// Demo mode keeps filenames in folderImages (used by v-for + caption); the
// real URL is looked up here so the UI never has to render the long randomuser
// URL as a label.
const demoImageUrlMap = ref<Record<string, string>>({});

const imageSrc = (image: string) => {
  if (/^https?:\/\//i.test(image)) return image;
  if (settingsStore.demoMode && demoImageUrlMap.value[image]) {
    return demoImageUrlMap.value[image];
  }
  return `${API_BASE.value}/dataset/${selectedFolder.value}/${image}`;
};

const openFolder = (folder: string) => {
  selectedFolder.value = folder;
  fetchImagesInFolder();
};

const closeFolder = () => {
  selectedFolder.value = null;
  folderImages.value = [];
  demoImageUrlMap.value = {};
  fetchImagesError.value = null;
};

const fetchImagesInFolder = async () => {
  if (!selectedFolder.value) return;
  isFetchingImages.value = true;
  fetchImagesError.value = null;
  if (settingsStore.demoMode) {
    const demo = findDemoImageFolder(selectedFolder.value);
    const baseEntries = demo?.images ?? [];
    const extras = getDemoExtraImages(selectedFolder.value);
    const entries = [...baseEntries, ...extras];
    folderImages.value = entries.map((e) => e.filename);
    demoImageUrlMap.value = Object.fromEntries(
      entries.map((e) => [e.filename, e.url])
    );
    isFetchingImages.value = false;
    return;
  }
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
  if (settingsStore.demoMode) {
    const name = newFolderName.value.trim();
    addDemoFolder(name);
    folders.value = [
      ...demoImageFolders.map((f) => f.name),
      ...demoState.extraFolders,
    ];
    $q.notify({
      type: 'positive',
      message: 'Folder created (demo).',
      icon: 'check_circle',
    });
    createFolderDialog.value = false;
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
  stopDemoTraining();
});

// Auto-scroll logs to latest
watch(trainingLogs, () => {
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight;
    }
  });
});

// Simulates the train-model-stream Server-Sent Events flow when there is no
// real Pi backend to talk to (demoMode). Streams plausible log lines into the
// same UI bindings (`trainingLogs`, `progress`, `isTraining`) so the demo
// shows a working progress bar, scrolling log box, and success notify.
let demoTrainingTimer: ReturnType<typeof setTimeout> | null = null;

const stopDemoTraining = () => {
  if (demoTrainingTimer) {
    clearTimeout(demoTrainingTimer);
    demoTrainingTimer = null;
  }
};

const runDemoTraining = () => {
  isTraining.value = true;
  trainingLogs.value = [];
  progress.value = null;

  // Use the real demo dataset count so totals are consistent with what's
  // visible in the folder grid.
  const total = demoImageFolders.reduce((sum, f) => sum + f.images.length, 0);
  const folderNames = demoImageFolders.map((f) => f.name);

  const preamble = [
    '[INFO] loading face_recognition models…',
    '[INFO] dlib backend initialized (CNN=False, hog detector)',
    `[INFO] discovered ${folderNames.length} identity folders: ${folderNames.join(
      ', '
    )}`,
    `[INFO] queued ${total} images for encoding`,
    '[INFO] starting encoding pass…',
  ];

  const completion = [
    '[INFO] encoding pass complete',
    `[INFO] writing ${total} encodings to encodings.pickle`,
    '[INFO] verifying pickle integrity… ok',
    '[INFO] training complete.',
  ];

  let step = 0;
  const preambleEnd = preamble.length;
  const processingEnd = preambleEnd + total;
  const completionEnd = processingEnd + completion.length;

  const tick = () => {
    if (!isTraining.value) return; // user navigated away / cancelled

    if (step < preambleEnd) {
      trainingLogs.value.push(preamble[step]);
    } else if (step < processingEnd) {
      const i = step - preambleEnd + 1;
      // Pick the folder this image "belongs to" so the log feels real.
      let acc = 0;
      let owner = folderNames[0];
      for (const f of demoImageFolders) {
        acc += f.images.length;
        if (i <= acc) {
          owner = f.name;
          break;
        }
      }
      const line = `[INFO] processing image ${i}/${total} (${owner})`;
      trainingLogs.value.push(line);
      parseProgressFromLog(line);
    } else if (step < completionEnd) {
      trainingLogs.value.push(completion[step - processingEnd]);
    } else {
      isTraining.value = false;
      progress.value = null;
      demoTrainingTimer = null;
      markTrainingComplete();
      $q.notify({
        type: 'positive',
        message: 'Model training completed! (demo)',
        icon: 'check_circle',
      });
      return;
    }

    step++;
    // Setup is leisurely, processing is fast, finalize settles back down so it
    // feels like real I/O instead of a metronome.
    const delay =
      step <= preambleEnd ? 350 : step <= processingEnd ? 25 : 250;
    demoTrainingTimer = setTimeout(tick, delay);
  };

  demoTrainingTimer = setTimeout(tick, 200);
};

const triggerTrainingWithLogs = () => {
  if (settingsStore.demoMode) {
    runDemoTraining();
    return;
  }
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

// ---- Dataset stats ----------------------------------------------------------
const folderImageCount = (folder: string): string => {
  const base = findDemoImageFolder(folder)?.images.length ?? 0;
  const extra = getDemoExtraImages(folder).length;
  const total = base + extra;
  return `${total} ${total === 1 ? 'photo' : 'photos'}`;
};

const identityCount = computed(() => folders.value.length);

const totalImageCount = computed(() => {
  if (settingsStore.demoMode) {
    const base = demoImageFolders.reduce((s, f) => s + f.images.length, 0);
    const extras = Object.values(demoState.extraImages).reduce(
      (s, arr) => s + arr.length,
      0
    );
    return base + extras;
  }
  return '—';
});

const lastTrainingLabel = computed(() => {
  const ts = demoState.lastTrainingAt;
  if (!ts) return 'Never';
  const diff = Date.now() - ts;
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return new Date(ts).toLocaleDateString();
});

// ---- Identity detail drawer -------------------------------------------------
const identityDetailOpen = ref(false);
const detailIdentity = ref<string>('');

const openIdentityDetail = (identity: string) => {
  detailIdentity.value = identity;
  identityDetailOpen.value = true;
};

const initialsFor = (name: string): string => {
  if (!name) return '?';
  return name
    .split(/\s+/)
    .map((s) => s.charAt(0).toUpperCase())
    .slice(0, 2)
    .join('');
};

const identityImageCount = (identity: string): number => {
  if (!identity) return 0;
  const base = findDemoImageFolder(identity)?.images.length ?? 0;
  const extras = getDemoExtraImages(identity).length;
  return base + extras;
};

const recentImagesFor = (identity: string) => {
  if (!identity) return [];
  const base = findDemoImageFolder(identity)?.images ?? [];
  const extras = getDemoExtraImages(identity);
  // Show the most recent uploads first if any, otherwise the first batch.
  return [...extras, ...base].slice(0, 6);
};

// Synthetic "last seen" derived from a hash of the identity name + the demo
// state's training timestamp. Stable per identity within a session.
const identityLastSeenLabel = (identity: string): string => {
  if (!identity) return 'Never';
  const ts = demoState.lastTrainingAt;
  if (!ts) return 'Never';
  let h = 2166136261;
  for (let i = 0; i < identity.length; i++) {
    h ^= identity.charCodeAt(i);
    h = Math.imul(h, 16777619) >>> 0;
  }
  const minutesAgo = (h % 600) + 1; // 1-600 min
  if (minutesAgo < 60) return `${minutesAgo}m ago`;
  return `${Math.floor(minutesAgo / 60)}h ago`;
};

// Score curve: 0-9 photos -> proportional, 10-29 -> 50-80, 30+ -> 85-98
const identityQualityScore = (identity: string): number => {
  const n = identityImageCount(identity);
  if (n === 0) return 0;
  if (n < 10) return Math.round((n / 10) * 50);
  if (n < 30) return 50 + Math.round(((n - 10) / 20) * 30);
  return 85 + Math.min(13, Math.floor((n - 30) / 4));
};

const identityTimeline = (identity: string) => {
  if (!identity) return [];
  const events: {
    title: string;
    when: string;
    icon: string;
    color: string;
  }[] = [];
  const baseCount = findDemoImageFolder(identity)?.images.length ?? 0;
  const extraCount = getDemoExtraImages(identity).length;

  events.push({
    title: 'Identity created',
    when: baseCount > 0 ? 'Seed dataset' : 'Just now',
    icon: 'person_add',
    color: 'accent',
  });
  if (baseCount > 0) {
    events.push({
      title: `${baseCount} seed photos imported`,
      when: 'Initial dataset',
      icon: 'photo_library',
      color: 'positive',
    });
  }
  if (extraCount > 0) {
    events.push({
      title: `${extraCount} new photos added`,
      when: 'This session',
      icon: 'add_a_photo',
      color: 'info',
    });
  }
  if (demoState.lastTrainingAt) {
    events.push({
      title: 'Model trained',
      when: lastTrainingLabel.value,
      icon: 'model_training',
      color: 'positive',
    });
  }
  events.push({
    title: `Last detection: ${identityLastSeenLabel(identity)}`,
    when: 'Synthetic',
    icon: 'visibility',
    color: 'grey',
  });
  return events;
};

const canDeleteIdentity = (identity: string): boolean => {
  // In demo mode we only allow deleting session-added (extraFolders) identities,
  // not the static seed ones — that keeps reload behavior coherent.
  if (settingsStore.demoMode) {
    return demoState.extraFolders.includes(identity);
  }
  return true;
};

const confirmDeleteIdentity = () => {
  const identity = detailIdentity.value;
  if (!canDeleteIdentity(identity)) return;
  $q.dialog({
    title: `Delete "${identity}"?`,
    message:
      'This removes the identity folder and all photos in this session. The dataset only resets fully on page reload.',
    cancel: true,
    persistent: true,
    color: 'negative',
  }).onOk(() => {
    demoState.extraFolders = demoState.extraFolders.filter(
      (n) => n !== identity
    );
    delete demoState.extraImages[identity];
    fetchFolders();
    identityDetailOpen.value = false;
    $q.notify({
      type: 'positive',
      message: `Identity "${identity}" removed.`,
    });
  });
};

const openIdentityFromDetail = () => {
  identityDetailOpen.value = false;
  openFolder(detailIdentity.value);
};

// ---- Test Recognition (demo theatre) ----------------------------------------
const testRecognitionDialog = ref(false);
const testFile = ref<File | null>(null);
const testFilePreview = ref<string | null>(null);
const testFileInput = ref<HTMLInputElement | null>(null);
const testRunning = ref(false);
const testResult = ref<{
  identity: string;
  confidence: number;
  matchPreviewUrl: string;
} | null>(null);

const setTestFile = (file: File) => {
  if (testFilePreview.value) {
    URL.revokeObjectURL(testFilePreview.value);
  }
  testFile.value = file;
  testFilePreview.value = URL.createObjectURL(file);
  testResult.value = null;
};

const onTestFileChange = (e: Event) => {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  if (file) setTestFile(file);
  input.value = '';
};

const onTestDrop = (e: DragEvent) => {
  const file = e.dataTransfer?.files?.[0];
  if (file && file.type.startsWith('image/')) {
    setTestFile(file);
  }
};

const resetTestRecognition = () => {
  if (testFilePreview.value) {
    URL.revokeObjectURL(testFilePreview.value);
  }
  testFile.value = null;
  testFilePreview.value = null;
  testResult.value = null;
  testRunning.value = false;
};

const runTestRecognition = async () => {
  if (!testFile.value) return;
  testRunning.value = true;
  // Brief delay so the spinner state registers — feels like work.
  await new Promise((r) => setTimeout(r, 850));

  // Deterministic identity pick: hash filename + size, mod folder count.
  const candidates = folders.value;
  if (!candidates.length) {
    testRunning.value = false;
    $q.notify({
      type: 'warning',
      message: 'No identity folders to match against.',
    });
    return;
  }
  const seedSrc = `${testFile.value.name}:${testFile.value.size}`;
  let h = 2166136261;
  for (let i = 0; i < seedSrc.length; i++) {
    h ^= seedSrc.charCodeAt(i);
    h = Math.imul(h, 16777619) >>> 0;
  }
  const identity = candidates[h % candidates.length];
  // Synthetic confidence in [0.85, 0.97]
  const confidence = 0.85 + ((h >>> 16) % 1200) / 10000;

  // Use the first image from that identity's dataset as the "match preview".
  const baseImages = findDemoImageFolder(identity)?.images ?? [];
  const extraImages = getDemoExtraImages(identity);
  const candidateImg = baseImages[0] ?? extraImages[0];
  const matchPreviewUrl =
    candidateImg?.url ?? '/icons/vigilant.png';

  testResult.value = { identity, confidence, matchPreviewUrl };
  testRunning.value = false;
};
</script>

<style lang="scss" scoped>
.face-page {
  max-width: 1280px;
  margin: 0 auto;
}

.dataset-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  align-items: stretch;
}

.dataset-stat {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 12px;
  background: rgba(156, 39, 176, 0.06);
  border: 1px solid rgba(156, 39, 176, 0.18);
}

.dataset-stat--action {
  justify-content: center;
}

.dataset-stat__value {
  font-size: 1.4rem;
  font-weight: 700;
  line-height: 1.1;
}

.dataset-stat__label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--vigilant-text-dim, rgba(0, 0, 0, 0.55));
}

.body--dark .dataset-stat__label {
  color: rgba(244, 238, 249, 0.65);
}

.folder-card,
.dataset-card {
  position: relative;
  transition: transform 0.2s ease, box-shadow 0.2s ease,
    border-color 0.2s ease;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.folder-card:hover,
.dataset-card:hover {
  transform: translateY(-2px);
  border-color: rgba(156, 39, 176, 0.4);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
}

.folder-name {
  font-size: 0.9rem;
  word-break: break-word;
  text-align: center;
  line-height: 1.2;
}

.folder-count-chip {
  font-weight: 600;
  font-size: 0.7rem;
}

.demo-pill {
  position: absolute;
  top: 6px;
  right: 6px;
  z-index: 2;
  letter-spacing: 0.05em;
}

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

.dataset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(160px, 100%), 1fr));
  gap: 12px;
}

.dataset-grid__cell {
  min-width: 0;
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

// ---- Identity detail card ----
.identity-detail-card {
  width: 460px;
  max-width: 100vw;
  height: 100vh;
  border-radius: 0;
  background: var(--vigilant-bg, #0c0218);
  color: #f3eafa;
}

.identity-detail__header {
  background: linear-gradient(
    135deg,
    var(--vigilant-purple-2, #4c065c),
    var(--vigilant-purple-1, #6a1b9a)
  );
  color: #fff;
}

.identity-stat-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}

.identity-stat {
  padding: 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  text-align: center;
}

.identity-stat__value {
  font-size: 1.2rem;
  font-weight: 700;
}

.identity-stat__label {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: rgba(244, 238, 249, 0.55);
}

.identity-section {
  margin-bottom: 24px;
}

.identity-section__title {
  text-transform: uppercase;
  font-size: 0.7rem;
  letter-spacing: 0.08em;
  color: rgba(244, 238, 249, 0.55);
  margin-bottom: 8px;
}

.identity-thumbs {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.identity-thumb {
  aspect-ratio: 1 / 1;
  background-size: cover;
  background-position: center;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

@media (max-width: 599px) {
  .identity-detail-card {
    width: 100vw;
  }
}

// ---- Test Recognition dialog ----
.test-recog-card {
  width: min(560px, 96vw);
  background: var(--vigilant-bg, #0c0218);
  color: #f3eafa;
}

.test-recog-drop {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 2px dashed rgba(156, 39, 176, 0.5);
  border-radius: 10px;
  padding: 24px;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease;
  min-height: 180px;
}

.test-recog-drop:hover {
  background: rgba(156, 39, 176, 0.08);
  border-color: rgba(156, 39, 176, 0.7);
}

.test-recog-drop--has {
  padding: 8px;
}

.test-recog-drop__preview {
  width: 100%;
  max-width: 220px;
  border-radius: 8px;
}

.test-recog-result {
  padding: 16px;
  border-radius: 10px;
  background: rgba(156, 39, 176, 0.12);
  border: 1px solid rgba(156, 39, 176, 0.3);
}

.test-recog-result__avatar {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  flex-shrink: 0;
  border: 2px solid rgba(255, 255, 255, 0.25);
}

@media (max-width: 599px) {
  .dataset-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  .dataset-stat--action {
    grid-column: span 2;
  }
  .folder-actions {
    flex-direction: row;
  }
}
</style>
