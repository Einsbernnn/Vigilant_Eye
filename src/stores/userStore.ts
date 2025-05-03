import { defineStore } from 'pinia';

export const useUserStore = defineStore('user', {
  state: () => ({
    username: '',
    isAuthenticated: false,
  }),
  actions: {
    login(username: string, password: string) {
      if (username === 'admin' && password === 'admin') {
        this.username = username;
        this.isAuthenticated = true;
        return true;
      }
      return false;
    },
    logout() {
      this.username = '';
      this.isAuthenticated = false;
    },
  },
});
