<template>
  <q-page class="q-pa-lg">
    <div class="column items-center q-gutter-lg">
      <q-card class="upload-card q-pa-lg shadow-5">
        <q-form @submit.prevent="handleUpload" class="column q-gutter-y-md">
          <div class="row items-center justify-between q-mb-md">
            <q-file
              filled
              multiple
              accept="image/*"
              label="Select images"
              v-model="selectedFiles"
              @update:model-value="handleFileSelect"
              class="q-mr-md"
              style="width: 300px"
            >
              <template v-slot:prepend>
                <q-icon name="cloud_upload" color="accent" />
              </template>
            </q-file>

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
                spinner-color="primary"
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
                  <q-spinner-puff color="primary" />
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
          <q-btn
            color="accent"
            icon="refresh"
            label="Refresh"
            @click="fetchFolders"
            :loading="isFetchingFolders"
          />
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
                  spinner-color="primary"
                >
                  <template v-slot:loading>
                    <q-spinner-puff color="primary" />
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
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useQuasar } from 'quasar';
import { useSettingsStore } from 'stores/settingsStore';

const $q = useQuasar();
const settingsStore = useSettingsStore();

const API_BASE = ref(settingsStore.uploadApiUrl); // Ensure no trailing slash

const selectedFiles = ref<File[]>([]);
const previewImages = ref<string[]>([]);
const isUploading = ref(false);
const uploadSuccess = ref(false);

const handleFileSelect = (files: File[]) => {
  previewImages.value = files.map((file) => URL.createObjectURL(file));
  uploadSuccess.value = false;
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

  isUploading.value = true;

  try {
    const formData = new FormData();
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

    selectedFiles.value = [];
    previewImages.value = [];
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Upload failed. Please try again.',
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
    const res = await fetch(`${API_BASE.value}/api/folders`);
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
</style>
