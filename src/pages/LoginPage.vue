<template>
  <q-page class="row items-center justify-center bg-gradient">
    <q-card class="login-card q-pa-xl shadow-5">
      <div class="text-center q-mb-lg">
        <q-icon name="lock" color="accent" size="xl" class="q-mb-sm" />
        <h4 class="q-ma-none text-weight-bold">Login</h4>
        <div class="text-grey-6 q-mt-xs">Please sign in to continue</div>
      </div>

      <q-form @submit.prevent="handleLogin" class="q-gutter-y-md">
        <q-input
          v-model="username"
          label="Username"
          filled
          standout
          color="accent"
          dense
          lazy-rules
          :rules="[(val) => !!val || 'Username is required']"
        >
          <template v-slot:prepend>
            <q-icon name="person" color="accent" />
          </template>
        </q-input>

        <q-input
          v-model="password"
          label="Password"
          filled
          standout
          color="accent"
          dense
          :type="showPassword ? 'text' : 'password'"
          lazy-rules
          :rules="[(val) => !!val || 'Password is required']"
        >
          <template v-slot:prepend>
            <q-icon name="lock" color="accent" />
          </template>
          <template v-slot:append>
            <q-icon
              :name="showPassword ? 'visibility_off' : 'visibility'"
              class="cursor-pointer"
              @click="showPassword = !showPassword"
            />
          </template>
        </q-input>

        <div class="row items-center justify-between">
          <q-checkbox
            v-model="rememberMe"
            label="Remember me"
            color="accent"
            dense
          />
          <a href="#" class="text-accent text-caption">Forgot password?</a>
        </div>

        <q-btn
          type="submit"
          color="accent"
          label="Sign In"
          class="full-width q-mt-lg"
          size="lg"
          :loading="isLoading"
          push
        >
          <template v-slot:loading>
            <q-spinner-hourglass class="on-left" />
            Authenticating...
          </template>
        </q-btn>

        <q-banner
          v-if="errorMessage"
          class="bg-negative text-white q-mt-md"
          rounded
        >
          <template v-slot:avatar>
            <q-icon name="error" color="white" />
          </template>
          {{ errorMessage }}
        </q-banner>

        <div class="text-center q-mt-lg">
          <span class="text-grey-6">Don't have an account? </span>
          <a href="#" class="text-accent">Sign up</a>
        </div>
      </q-form>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useQuasar } from 'quasar';
import { useUserStore } from 'src/stores/userStore';
import { useRouter } from 'vue-router';

const $q = useQuasar();
const username = ref('');
const password = ref('');
const rememberMe = ref(false);
const showPassword = ref(false);
const errorMessage = ref('');
const isLoading = ref(false);
const userStore = useUserStore();
const router = useRouter();

const handleLogin: () => Promise<void> = async () => {
  isLoading.value = true;
  errorMessage.value = '';

  try {
    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 1500));

    if (userStore.login(username.value, password.value)) {
      $q.notify({
        type: 'positive',
        message: 'Login successful!',
        icon: 'check_circle',
      });
      router.push('/live-stream');
    } else {
      errorMessage.value = 'Invalid username or password';
    }
  } catch (error) {
    errorMessage.value = 'Login failed. Please try again.';
    $q.notify({
      type: 'negative',
      message: 'An error occurred during login',
      icon: 'error',
    });
  } finally {
    isLoading.value = false;
  }
};
</script>

<style lang="scss" scoped>
.login-card {
  width: 100%;
  max-width: 450px;
  border-radius: 16px;
}

.q-input {
  &::before,
  &::after {
    border-radius: 8px !important;
  }
}

.q-checkbox__label {
  font-size: 0.875rem;
}

a {
  text-decoration: none;
  transition: opacity 0.3s ease;

  &:hover {
    opacity: 0.8;
  }
}

.bg-gradient {
  background: linear-gradient(135deg, #341050, #4c065c);
}
</style>
