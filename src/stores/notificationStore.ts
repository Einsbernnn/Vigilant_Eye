import { ref } from 'vue';
import { defineStore } from 'pinia';

export const useNotificationStore = defineStore('notification', () => {
  const notifications = ref<string[]>([]);

  function addNotification(message: string) {
    notifications.value.push(message);
    if (notifications.value.length > 100) {
      notifications.value.shift();
    }
  }

  function clearNotifications() {
    notifications.value = [];
  }

  return { notifications, addNotification, clearNotifications };
});
