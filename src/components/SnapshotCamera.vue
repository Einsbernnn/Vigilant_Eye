<template>
  <div class="photobooth-container">
    <div v-if="!firstName" class="name-prompt">
      <label for="firstName">Enter your first name:</label>
      <input
        id="firstName"
        v-model="nameInput"
        @keyup.enter="setFirstName"
        autofocus
      />
      <button @click="setFirstName">Start</button>
      <div v-if="folderError" style="color: red; margin-top: 0.5rem">
        {{ folderError }}
      </div>
      <div v-if="videoDevices.length > 1" style="margin-top: 1rem">
        <label for="cameraSelect">Select Camera:</label>
        <select id="cameraSelect" v-model="selectedDeviceId">
          <option
            v-for="d in videoDevices"
            :key="d.deviceId"
            :value="d.deviceId"
          >
            {{ d.label || 'Camera ' + d.deviceId }}
          </option>
        </select>
      </div>
    </div>
    <div v-else>
      <div v-if="cameraError" style="color: red; margin-bottom: 1rem">
        {{ cameraError }}
      </div>
      <div class="photobooth-frame">
        <video ref="video" autoplay playsinline class="camera-preview"></video>
        <div class="photobooth-overlay">
          <span class="photobooth-title">Photo Booth - {{ firstName }}</span>
        </div>
      </div>
      <div class="controls">
        <span class="counter">Photos: {{ photos.length }}</span>
        <button class="done-btn" @click="doneSession">Done</button>
        <button class="redo-btn" @click="redoSession">Redo</button>
      </div>
      <div class="thumbnails">
        <img
          v-for="(img, idx) in photos"
          :key="idx"
          :src="img"
          class="thumbnail"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';

const video = ref<HTMLVideoElement | null>(null);
const photos = ref<string[]>([]);
const firstName = ref<string | null>(null);
const nameInput = ref('');
const photoCount = ref(0);
let stream: MediaStream | null = null;
let takingPhotos = false;
let photoInterval: number | null = null;
const videoDevices = ref<MediaDeviceInfo[]>([]);
const selectedDeviceId = ref<string | null>(null);
const cameraError = ref<string | null>(null);
const folderError = ref<string | null>(null);

async function getVideoDevices() {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    videoDevices.value = devices.filter((d) => d.kind === 'videoinput');
    if (videoDevices.value.length > 0) {
      selectedDeviceId.value = videoDevices.value[0].deviceId;
    }
  } catch (err) {
    cameraError.value = 'Could not list video devices.';
  }
}

async function setFirstName() {
  folderError.value = null;
  if (nameInput.value.trim()) {
    const folderName = nameInput.value.trim();
    // Try to create folder in backend
    const res = await fetch('http://localhost:5000/api/create-folder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folder: folderName }),
    });
    if (res.status === 409) {
      folderError.value = 'Folder already exists. Please choose a new name.';
      return;
    }
    if (!res.ok) {
      folderError.value = 'Error creating folder. Please try again.';
      return;
    }
    firstName.value = folderName;
    // startCamera will be called by the watcher below
  }
}

async function startCamera() {
  cameraError.value = null;
  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
    stream = null;
  }
  try {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error('getUserMedia is not supported in this browser.');
    }
    const constraints: MediaStreamConstraints = {
      video: selectedDeviceId.value
        ? { deviceId: { exact: selectedDeviceId.value } }
        : true,
    };
    stream = await navigator.mediaDevices.getUserMedia(constraints);
    if (video.value) {
      video.value.srcObject = stream;
    }
  } catch (err: unknown) {
    if (err instanceof Error) {
      cameraError.value = 'Camera error: ' + (err.message || err.name);
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
  if (ctx) {
    ctx.drawImage(video.value, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL('image/jpeg');
    photos.value.push(dataUrl);
    photoCount.value += 1;
    // Send to backend for saving with incremented filename
    savePhotoToBackend(dataUrl, photoCount.value);
  }
}

function dataURLtoBlob(dataurl: string) {
  const arr = dataurl.split(','),
    mime = arr[0].match(/:(.*?);/)?.[1] || '',
    bstr = atob(arr[1]),
    n = bstr.length,
    u8arr = new Uint8Array(n);
  for (let i = 0; i < n; i++) {
    u8arr[i] = bstr.charCodeAt(i);
  }
  return new Blob([u8arr], { type: mime });
}

function savePhotoToBackend(dataUrl: string, count: number) {
  if (!firstName.value) return;
  const formData = new FormData();
  formData.append('folder', firstName.value);
  const blob = dataURLtoBlob(dataUrl);
  const filename = `${firstName.value}${count}.jpg`;
  formData.append('images', blob, filename);
  fetch('http://localhost:5000/api/upload', {
    method: 'POST',
    body: formData,
  });
}

function handleKeyDown(e: KeyboardEvent) {
  if (e.code === 'Space' && !takingPhotos) {
    takingPhotos = true;
    photoInterval = window.setInterval(takePhoto, 300);
  }
}
function handleKeyUp(e: KeyboardEvent) {
  if (e.code === 'Space') {
    takingPhotos = false;
    if (photoInterval) {
      clearInterval(photoInterval);
      photoInterval = null;
    }
  }
}

function doneSession() {
  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
    stream = null;
  }
  alert('Session complete! Photos saved to your Desktop.');
}

function redoSession() {
  photos.value = [];
  photoCount.value = 0;
  // Optionally, notify backend to clear folder (not implemented here)
}

onMounted(() => {
  getVideoDevices();
  window.addEventListener('keydown', handleKeyDown);
  window.addEventListener('keyup', handleKeyUp);
});
onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeyDown);
  window.removeEventListener('keyup', handleKeyUp);
  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
  }
});
</script>

<style scoped>
.photobooth-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: linear-gradient(135deg, #ece9e6, #ffffff);
  min-height: 100vh;
  font-family: 'Arial', sans-serif;
}
.name-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  background: #f9f9f9;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
.name-prompt label {
  font-size: 1.2rem;
  font-weight: bold;
  color: #333;
}
.name-prompt input {
  padding: 0.5rem 1rem;
  border: 2px solid #ccc;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s;
}
.name-prompt input:focus {
  border-color: #9c27b0;
  outline: none;
}
.name-prompt button {
  background: #9c27b0;
  color: #fff;
  border: none;
  border-radius: 50px;
  padding: 0.5rem 1.5rem;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.3s, transform 0.2s;
}
.name-prompt button:hover {
  background: #388e3c;
  transform: scale(1.05);
}
.photobooth-frame {
  position: relative;
  border: 8px solid #fff;
  border-radius: 24px;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  width: 360px;
  height: 270px;
  background: #222;
  margin-bottom: 1rem;
}
.camera-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.photobooth-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  pointer-events: none;
}
.photobooth-title {
  margin-top: 12px;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  padding: 6px 18px;
  border-radius: 12px;
  font-size: 1.3rem;
  font-weight: bold;
  letter-spacing: 2px;
}
.controls {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 1rem;
}
.counter {
  font-size: 1.1rem;
  font-weight: bold;
  color: #333;
}
.done-btn,
.redo-btn {
  background: #607d8b;
  color: #fff;
  border: none;
  border-radius: 50px;
  padding: 0.5rem 1.5rem;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.3s, transform 0.2s;
}
.done-btn:hover {
  background: #388e3c;
  transform: scale(1.05);
}
.redo-btn:hover {
  background: #c62828;
  transform: scale(1.05);
}
.thumbnails {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 1rem;
  max-width: 360px;
}
.thumbnail {
  width: 60px;
  height: 45px;
  object-fit: cover;
  border: 2px solid #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.12);
  transition: transform 0.2s, box-shadow 0.2s;
}
.thumbnail:hover {
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}
</style>
