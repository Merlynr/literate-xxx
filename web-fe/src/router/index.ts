import { createRouter, createWebHistory } from 'vue-router'
import { getAccessToken } from '@/api/request'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/app/dashboard' },
    {
      path: '/app/login',
      name: 'app-login',
      component: () => import('@/views/app/LoginView.vue'),
      meta: { guest: true, portal: 'app' },
    },
    {
      path: '/app',
      component: () => import('@/layouts/AppShell.vue'),
      meta: { auth: true, portal: 'app' },
      children: [
        { path: '', redirect: '/app/dashboard' },
        {
          path: 'dashboard',
          name: 'app-dashboard',
          component: () => import('@/views/app/DashboardView.vue'),
        },
        {
          path: 'generate',
          name: 'app-generate',
          component: () => import('@/views/app/GenerateView.vue'),
        },
        {
          path: 'works',
          name: 'app-works',
          component: () => import('@/views/app/WorksView.vue'),
        },
        {
          path: 'works/tasks',
          name: 'app-tasks',
          component: () => import('@/views/app/WorksView.vue'),
          props: { tab: 'tasks' },
        },
        {
          path: 'modules',
          name: 'app-modules',
          component: () => import('@/views/app/ModulesView.vue'),
        },
        {
          path: 'account',
          name: 'app-account',
          component: () => import('@/views/app/AccountView.vue'),
        },
      ],
    },
    {
      path: '/admin/login',
      name: 'admin-login',
      component: () => import('@/views/admin/LoginView.vue'),
      meta: { guest: true, portal: 'admin' },
    },
    {
      path: '/admin',
      component: () => import('@/layouts/AdminShell.vue'),
      meta: { auth: true, portal: 'admin' },
      children: [
        { path: '', redirect: '/admin/dashboard' },
        {
          path: 'dashboard',
          name: 'admin-dashboard',
          component: () => import('@/views/admin/DashboardView.vue'),
        },
        {
          path: 'catalog/categories',
          name: 'admin-categories',
          component: () => import('@/views/admin/CategoriesView.vue'),
        },
        {
          path: 'catalog/styles',
          name: 'admin-styles',
          component: () => import('@/views/admin/StylesView.vue'),
        },
        {
          path: 'content/terms',
          name: 'admin-terms',
          component: () => import('@/views/admin/TermsView.vue'),
        },
        {
          path: 'content/promo-rules',
          name: 'admin-promo-rules',
          component: () => import('@/views/admin/PromoRulesView.vue'),
        },
        {
          path: 'billing/pricing-plans',
          name: 'admin-pricing',
          component: () => import('@/views/admin/PricingPlansView.vue'),
        },
        {
          path: 'billing/quota-ledger',
          name: 'admin-ledger',
          component: () => import('@/views/admin/QuotaLedgerView.vue'),
        },
        {
          path: 'jobs',
          name: 'admin-jobs',
          component: () => import('@/views/admin/JobsView.vue'),
        },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/app/dashboard' },
  ],
})

router.beforeEach((to) => {
  const token = getAccessToken()
  if (to.meta.auth && !token) {
    return to.meta.portal === 'admin' ? '/admin/login' : '/app/login'
  }
  if (to.meta.guest && token) {
    return to.meta.portal === 'admin' ? '/admin/dashboard' : '/app/dashboard'
  }
  return true
})

export default router
