import { boot } from 'quasar/wrappers';
import { Notify } from 'quasar';

// Single source of truth for toast positioning. Every $q.notify() and
// Notify.create() call across the app inherits this unless it explicitly
// overrides — so toasts are guaranteed to land in the same place no matter
// which page or component fires them.
//
// Position rationale: 'top' stays clear of the mobile bottom-nav, sits
// below the q-header, and is the first thing the eye lands on. Quasar
// auto-resizes top toasts to full width on narrow viewports and centers
// them at desktop widths, so it works for both layouts.

export default boot(() => {
  Notify.setDefaults({
    position: 'top',
    timeout: 2500,
    progress: true,
    actions: [{ icon: 'close', color: 'white', round: true, dense: true }],
  });
});
