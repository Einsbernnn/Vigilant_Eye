import { reactive } from 'vue';
import type { DemoImageEntry } from './demoData';

// In-memory, session-only mutations layered on top of the static demoData.
// Lets demoMode "uploads" and runtime-created folders feel persistent across
// page navigations without a real backend. Cleared on reload.
export const demoState = reactive({
  extraFolders: [] as string[],
  extraImages: {} as Record<string, DemoImageEntry[]>,
});

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
