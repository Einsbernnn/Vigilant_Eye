import { boot } from 'quasar/wrappers';
import { createPinia } from 'pinia';
import { useSettingsStore } from 'src/stores/settingsStore';

export default boot(({ app }) => {
  const pinia = createPinia();
  app.use(pinia);

  // Apply the saved accent color to the root --q-accent CSS variable on boot
  // so existing color="accent" props pick up the user's preference.
  if (typeof document !== 'undefined') {
    const settings = useSettingsStore(pinia);
    settings.syncAccentToDom();
  }
});
