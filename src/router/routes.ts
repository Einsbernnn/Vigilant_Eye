import { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/live-stream',
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
    ],
  },

  // Always leave this as last one,
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
];

export default routes;
