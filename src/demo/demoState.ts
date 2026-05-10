import { reactive } from 'vue';
import type { DemoImageEntry } from './demoData';

// In-memory, session-only mutations layered on top of the static demoData.
// Lets demoMode "uploads" and runtime-created folders feel persistent across
// page navigations without a real backend. Cleared on reload.
export type ClipTag =
  | 'visitor'
  | 'delivery'
  | 'family'
  | 'important'
  | 'review';

export const CLIP_TAGS: { value: ClipTag; label: string; color: string }[] = [
  { value: 'visitor', label: 'Visitor', color: 'blue' },
  { value: 'delivery', label: 'Delivery', color: 'orange' },
  { value: 'family', label: 'Family', color: 'green' },
  { value: 'important', label: 'Important', color: 'red' },
  { value: 'review', label: 'Review', color: 'purple' },
];

export const demoState = reactive({
  extraFolders: [] as string[],
  extraImages: {} as Record<string, DemoImageEntry[]>,
  // Epoch ms of the last simulated training run; null until first run.
  // Surfaced in the Face Recognition stats panel.
  lastTrainingAt: null as number | null,
  // Per-clip tags keyed by clip id. Persists across folder navigation.
  clipTags: {} as Record<string, ClipTag[]>,
});

export function resetDemoState() {
  // Releases the in-memory blob URLs we created for demo uploads / snapshots
  // before wiping them, so the browser can GC the underlying File data.
  for (const entries of Object.values(demoState.extraImages)) {
    for (const entry of entries) {
      if (entry.url.startsWith('blob:')) {
        try {
          URL.revokeObjectURL(entry.url);
        } catch {
          /* swallow — already revoked or invalid */
        }
      }
    }
  }
  demoState.extraFolders = [];
  demoState.extraImages = {};
  demoState.lastTrainingAt = null;
  demoState.clipTags = {};
}

export function markTrainingComplete() {
  demoState.lastTrainingAt = Date.now();
}

export function toggleClipTag(clipId: string, tag: ClipTag) {
  const current = demoState.clipTags[clipId] ?? [];
  if (current.includes(tag)) {
    demoState.clipTags[clipId] = current.filter((t) => t !== tag);
  } else {
    demoState.clipTags[clipId] = [...current, tag];
  }
}

export function getClipTags(clipId: string): ClipTag[] {
  return demoState.clipTags[clipId] ?? [];
}

export function addDemoFolder(name: string) {
  if (!name) return;
  if (!demoState.extraFolders.includes(name)) {
    demoState.extraFolders.push(name);
  }
  if (!demoState.extraImages[name]) {
    demoState.extraImages[name] = [];
  }
}

export function addDemoImages(folder: string, entries: DemoImageEntry[]) {
  if (!demoState.extraImages[folder]) {
    demoState.extraImages[folder] = [];
  }
  demoState.extraImages[folder].push(...entries);
}

export function getDemoExtraImages(folder: string): DemoImageEntry[] {
  return demoState.extraImages[folder] ?? [];
}
