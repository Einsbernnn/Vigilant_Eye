import { onBeforeUnmount, onMounted } from 'vue';

export interface KeyboardShortcut {
  /** Single key or modifier combo, e.g. "?" / "g s" / "Shift+S". Case-insensitive. */
  key: string;
  /** Short, human-readable description for the help overlay. */
  description: string;
  /** Group label (e.g. "Navigation", "Live stream"). */
  group: string;
  /** Handler. Called only when no editable element has focus. */
  handler: (e: KeyboardEvent) => void;
}

const isEditable = (target: EventTarget | null): boolean => {
  if (!(target instanceof HTMLElement)) return false;
  if (target.isContentEditable) return true;
  const tag = target.tagName;
  return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT';
};

const matches = (e: KeyboardEvent, shortcut: string): boolean => {
  const parts = shortcut.toLowerCase().split('+');
  const key = parts[parts.length - 1];
  const wantsShift = parts.includes('shift');
  const wantsCtrl = parts.includes('ctrl');
  const wantsMeta = parts.includes('meta') || parts.includes('cmd');
  const wantsAlt = parts.includes('alt');

  if (wantsShift !== e.shiftKey) return false;
  if (wantsCtrl !== e.ctrlKey) return false;
  if (wantsMeta !== e.metaKey) return false;
  if (wantsAlt !== e.altKey) return false;

  // Normalize: "?" actually arrives as e.key === '?' (with shift on US layouts)
  // and as e.key === '/' with shift on some others. Accept either.
  if (key === '?' && (e.key === '?' || (e.key === '/' && e.shiftKey))) {
    return true;
  }
  return e.key.toLowerCase() === key;
};

export function useKeyboardShortcuts(shortcuts: KeyboardShortcut[]) {
  const onKeyDown = (e: KeyboardEvent) => {
    if (isEditable(e.target)) return;
    for (const s of shortcuts) {
      if (matches(e, s.key)) {
        e.preventDefault();
        s.handler(e);
        return;
      }
    }
  };

  onMounted(() => {
    window.addEventListener('keydown', onKeyDown);
  });

  onBeforeUnmount(() => {
    window.removeEventListener('keydown', onKeyDown);
  });
}
