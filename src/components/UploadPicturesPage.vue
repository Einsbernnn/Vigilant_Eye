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
          <h5 class="q-ma-none text-weight-bold">Gallery</h5>
          <q-btn
            color="accent"
            icon="refresh"
            label="Refresh"
            @click="fetchImages"
            :loading="isFetching"
          />
        </div>

        <div v-if="isFetching" class="text-center q-pa-lg">
          <q-spinner color="accent" size="3em" />
          <div class="q-mt-sm text-grey">Loading images...</div>
        </div>

        <q-banner
          v-else-if="fetchError"
          class="bg-negative text-white q-mb-md"
          rounded
        >
          <template v-slot:avatar>
            <q-icon name="error" color="white" />
          </template>
          Error loading images: {{ fetchError }}
        </q-banner>

        <div v-else class="row q-col-gutter-md">
          <div
            v-for="(image, index) in fetchedImages"
            :key="index"
            class="col-xs-6 col-sm-4 col-md-3 col-lg-2"
          >
            <q-card class="image-card">
              <q-img
                :src="image.url"
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
                  {{ image.name }}
                  <div class="text-caption opacity-70">
                    {{ formatDate(image.timestamp) }}
                  </div>
                </div>
              </q-img>

              <q-menu touch-position context-menu>
                <q-list dense style="min-width: 150px">
                  <q-item clickable @click="downloadImage(image)">
                    <q-item-section avatar>
                      <q-icon name="download" />
                    </q-item-section>
                    <q-item-section>Download</q-item-section>
                  </q-item>
                  <q-item
                    clickable
                    @click="deleteImage(image)"
                    class="text-negative"
                  >
                    <q-item-section avatar>
                      <q-icon name="delete" color="negative" />
                    </q-item-section>
                    <q-item-section class="text-negative"
                      >Delete</q-item-section
                    >
                  </q-item>
                </q-list>
              </q-menu>
            </q-card>
          </div>

          <div
            v-if="!fetchedImages.length && !isFetching"
            class="text-grey text-center q-pa-lg full-width"
          >
            No images found in storage
          </div>
        </div>
      </q-card>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useQuasar, date } from 'quasar';

const $q = useQuasar();

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
    await new Promise((resolve) => setTimeout(resolve, 2000));

    uploadSuccess.value = true;
    $q.notify({
      type: 'positive',
      message: `${selectedFiles.value.length} images uploaded successfully!`,
      icon: 'check_circle',
    });

    // Clear the success message after 5 seconds
    setTimeout(() => {
      uploadSuccess.value = false;
    }, 1000);

    await fetchImages();

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

interface GalleryImage {
  url: string;
  name: string;
  timestamp: number;
  size?: number;
}

const fetchedImages = ref<GalleryImage[]>([]);
const isFetching = ref(true);
const fetchError = ref<string | null>(null);

const formatDate = (timestamp: number) => {
  return date.formatDate(timestamp, 'YYYY-MM-DD HH:mm');
};

const fetchImages = async () => {
  isFetching.value = true;
  fetchError.value = null;

  try {
    await new Promise((resolve) => setTimeout(resolve, 1000));

    fetchedImages.value = Array.from({ length: 18 }).map((_, i) => ({
      url: `https://picsum.photos/300/300?random=${i}`,
      name: `image-${i + 1}.jpg`,
      timestamp: Date.now() - Math.random() * 1000000000,
      size: Math.floor(Math.random() * 5000000) + 1000000,
    }));
  } catch (error) {
    fetchError.value =
      error instanceof Error ? error.message : 'Failed to load images';
    $q.notify({
      type: 'negative',
      message: 'Failed to load gallery',
      icon: 'error',
    });
  } finally {
    isFetching.value = false;
  }
};

const downloadImage = (image: GalleryImage) => {
  $q.notify({
    message: `Downloading ${image.name}`,
    color: 'info',
    icon: 'download',
  });
};

const deleteImage = (image: GalleryImage) => {
  $q.dialog({
    title: 'Confirm Delete',
    message: `Delete ${image.name} permanently?`,
    cancel: true,
    persistent: true,
  }).onOk(async () => {
    try {
      await new Promise((resolve) => setTimeout(resolve, 500));
      $q.notify({
        type: 'positive',
        message: `${image.name} deleted successfully`,
        icon: 'check_circle',
      });
      await fetchImages();
    } catch (error) {
      $q.notify({
        type: 'negative',
        message: `Failed to delete ${image.name}`,
        icon: 'error',
      });
    }
  });
};

onMounted(() => {
  fetchImages();
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
