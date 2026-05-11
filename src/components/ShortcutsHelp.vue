<template>
  <q-dialog v-model="model" :maximized="$q.screen.lt.sm">
    <q-card class="shortcuts-card">
      <q-card-section class="row items-center vigilant-demo-banner q-pa-md">
        <q-icon name="keyboard" size="sm" class="q-mr-sm" />
        <div class="text-h6">Keyboard shortcuts</div>
        <q-space />
        <q-btn flat round dense icon="close" v-close-popup />
      </q-card-section>

      <q-scroll-area style="max-height: 70vh">
        <div
          v-for="(group, name) in groupedShortcuts"
          :key="name"
          class="shortcuts-group"
        >
          <div class="shortcuts-group__name">{{ name }}</div>
          <div class="shortcuts-group__list">
            <div
              v-for="s in group"
              :key="s.key + s.description"
              class="shortcut-row"
            >
              <span class="shortcut-row__desc">{{ s.description }}</span>
              <span class="shortcut-row__keys">
                <kbd
                  v-for="part in keyParts(s.key)"
                  :key="part"
                  class="shortcut-key"
                >
                  {{ part }}
                </kbd>
              </span>
            </div>
          </div>
        </div>
        <div class="shortcuts-footer text-caption text-grey-5 q-pa-md">
          Tip: shortcuts ignore key presses while typing in inputs.
        </div>
      </q-scroll-area>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import type { KeyboardShortcut } from 'src/composables/useKeyboardShortcuts';

const props = defineProps<{
  modelValue: boolean;
  shortcuts: KeyboardShortcut[];
}>();
const emit = defineEmits<{ (e: 'update:modelValue', v: boolean): void }>();

const model = ref(props.modelValue);
watch(
  () => props.modelValue,
  (v) => {
    model.value = v;
  }
);
watch(model, (v) => emit('update:modelValue', v));

const groupedShortcuts = computed(() => {
  const out: Record<string, KeyboardShortcut[]> = {};
  for (const s of props.shortcuts) {
    if (!out[s.group]) out[s.group] = [];
    out[s.group].push(s);
  }
  return out;
});

const keyParts = (key: string): string[] => {
  return key.split('+').map((k) => {
    const lower = k.toLowerCase();
    if (lower === 'meta' || lower === 'cmd') return '⌘';
    if (lower === 'shift') return 'Shift';
    if (lower === 'ctrl') return 'Ctrl';
    if (lower === 'alt') return 'Alt';
    if (lower === ' ') return 'Space';
    if (k.length === 1) return k.toUpperCase();
    return k;
  });
};
</script>

<style lang="scss" scoped>
.shortcuts-card {
  width: min(560px, 96vw);
  background: var(--vigilant-bg);
  color: var(--vigilant-text);
}

.shortcuts-group {
  padding: 16px 24px 8px;
}

.shortcuts-group__name {
  text-transform: uppercase;
  font-size: 0.7rem;
  letter-spacing: 0.08em;
  color: var(--vigilant-text-dim);
  margin-bottom: 8px;
}

.shortcuts-group__list {
  display: flex;
  flex-direction: column;
}

.shortcut-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--vigilant-border);
  font-size: 0.9rem;
}

.shortcut-row:last-child {
  border-bottom: 0;
}

.shortcut-row__keys {
  display: inline-flex;
  gap: 4px;
}

.shortcut-key {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 5px;
  padding: 2px 8px;
  font-family: 'SFMono-Regular', Menlo, Consolas, monospace;
  font-size: 0.8rem;
  min-width: 22px;
  text-align: center;
}

.shortcuts-footer {
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}
</style>
