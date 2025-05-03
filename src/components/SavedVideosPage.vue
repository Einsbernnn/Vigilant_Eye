<template>
  <q-page class="q-px-xl q-pt-xl">
    <div class="gallery-wrapper">
      <div class="header-row q-mb-lg">
        <q-input
          v-model="dateRangeString"
          outlined
          placeholder="Select date range"
          color="accent"
          class="date-picker"
          dense
          emit-value
          clearable
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
          color="accent"
          icon="cloud_download"
          label="Export All"
          rounded
          class="export-btn"
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
}
</style>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';

interface Video {
  id: string;
  title: string;
  timestamp: Date;
  duration: number;
  thumbnail: string;
  url: string;
}

const searchQuery = ref('');
const dateRange = ref<{ from: string | null; to: string | null }>({
  from: null,
  to: null,
});
const dateRangeString = ref<string | null>(null);

const updateDateRangeString = (range: {
  from: string | null;
  to: string | null;
}) => {
  if (range.from && range.to) {
    dateRangeString.value = `${range.from} to ${range.to}`;
  } else {
    dateRangeString.value = null;
  }
};

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
</script>
