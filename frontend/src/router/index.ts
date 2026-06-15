import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/dashboard', name: 'dashboard', component: () => import('@/views/DashboardView.vue'), meta: { title: '总览 Dashboard' } },
    { path: '/accounts', name: 'accounts', component: () => import('@/views/AccountsView.vue'), meta: { title: '账号 Accounts' } },
    { path: '/search', name: 'search', component: () => import('@/views/SearchView.vue'), meta: { title: '全局搜索' } },
    { path: '/workers', name: 'workers', component: () => import('@/views/WorkersView.vue'), meta: { title: 'Workers' } },
    { path: '/pages', name: 'pages', component: () => import('@/views/PagesView.vue'), meta: { title: 'Pages' } },
    { path: '/zones', name: 'zones', component: () => import('@/views/ZonesView.vue'), meta: { title: '域名 Zones' } },
    { path: '/dns', name: 'dns', component: () => import('@/views/DnsView.vue'), meta: { title: 'DNS 记录' } },
    { path: '/routes', name: 'routes', component: () => import('@/views/RoutesView.vue'), meta: { title: 'Routes' } },
    { path: '/usage', name: 'usage', component: () => import('@/views/UsageView.vue'), meta: { title: '用量 Usage' } },
    { path: '/jobs', name: 'jobs', component: () => import('@/views/JobsView.vue'), meta: { title: '巡检 Jobs' } },
    { path: '/alerts', name: 'alerts', component: () => import('@/views/AlertsView.vue'), meta: { title: '告警 Alerts' } },
  ],
})

// 页面标题
router.afterEach((to) => {
  document.title = `${(to.meta.title as string) || 'CF Manager'} — Cloudflare 多账号管理面板`
})

export default router
