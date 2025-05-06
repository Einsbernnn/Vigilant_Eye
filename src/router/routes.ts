import { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/login',
  },
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: 'live-stream',
        component: () => import('components/LiveStreamPage.vue'),
      },
      {
        path: 'saved-videos',
        component: () => import('components/SavedVideosPage.vue'),
      },
      {
        path: 'upload-pictures',
        component: () => import('components/UploadPicturesPage.vue'),
      },
      {
        path: 'snapshot-camera',
        component: () => import('components/SnapshotCamera.vue'),
      },
    ],
  },
  {
    path: '/',
    component: () => import('layouts/AuthLayout.vue'),
    children: [
      {
        path: 'login',
        component: () => import('pages/LoginPage.vue'),
      },
    ],
  },
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
];

export default routes;
