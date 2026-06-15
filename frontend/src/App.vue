<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { ElConfigProvider } from 'element-plus'
import {
  Odometer, User, Search, Setting, Document, Location,
  Link, DataAnalysis, Clock, Bell,
  Fold, Expand, Sunny, Moon, Menu,
} from '@element-plus/icons-vue'

const route = useRoute()
const app = useAppStore()

interface NavItem { path: string; label: string; icon: any }
const navItems: NavItem[] = [
  { path: '/dashboard',  label: '总览 Dashboard',  icon: Odometer },
  { path: '/accounts',   label: '账号 Accounts',   icon: User },
  { path: '/search',     label: '全局搜索',         icon: Search },
  { path: '/workers',    label: 'Workers',          icon: Setting },
  { path: '/pages',      label: 'Pages',            icon: Document },
  { path: '/zones',      label: '域名 Zones',       icon: Location },
  { path: '/dns',        label: 'DNS 记录',         icon: DataAnalysis },
  { path: '/routes',     label: 'Routes',           icon: Link },
  { path: '/usage',      label: '用量 Usage',       icon: DataAnalysis },
  { path: '/jobs',       label: '巡检 Jobs',        icon: Clock },
  { path: '/alerts',     label: '告警 Alerts',      icon: Bell },
]

function isActive(p: string) { return route.path === p }
</script>

<template>
  <el-config-provider :z-index="3000" :size="'default'">
  <div class="app-layout">
    <div v-if="app.mobileOpen" class="sidebar-overlay" @click="app.closeMobile()" />

    <aside class="sidebar" :class="{ collapsed: app.sidebarCollapsed, 'mobile-open': app.mobileOpen }">
      <div class="sidebar-header">
        <span class="logo" v-if="!app.sidebarCollapsed">☁️ CF Manager</span>
        <span class="logo-mini" v-else>☁️</span>
        <button class="collapse-btn" @click="app.toggleSidebar()">
          <el-icon :size="18"><Fold v-if="!app.sidebarCollapsed" /><Expand v-else /></el-icon>
        </button>
      </div>
      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems" :key="item.path"
          :to="item.path" class="nav-item"
          :class="{ active: isActive(item.path) }"
          :title="app.sidebarCollapsed ? item.label : undefined"
          @click="app.closeMobile()"
        >
          <el-icon :size="18"><component :is="item.icon" /></el-icon>
          <span v-if="!app.sidebarCollapsed" class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>
    </aside>

    <main class="main-content" :class="{ expanded: app.sidebarCollapsed }">
      <header class="topbar">
        <button class="hamburger-btn" @click="app.toggleMobile()">
          <el-icon :size="20"><Menu /></el-icon>
        </button>
        <div style="flex: 1" />
        <button class="theme-toggle" @click="app.toggleDark()" :title="app.isDark ? '切换亮色' : '切换暗色'">
          <el-icon :size="18"><Sunny v-if="app.isDark" /><Moon v-else /></el-icon>
        </button>
      </header>
      <div class="page-container">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
  </div>
  </el-config-provider>
</template>

<style scoped>
.app-layout { display: flex; min-height: 100vh; }

.sidebar {
  position: fixed; left: 0; top: 0; bottom: 0;
  width: var(--sidebar-width);
  background: var(--bg-sidebar); color: var(--text-sidebar);
  display: flex; flex-direction: column;
  transition: width var(--transition-normal), transform var(--transition-normal);
  z-index: 100; overflow: hidden;
}
.sidebar.collapsed { width: var(--sidebar-collapsed-width); }

.sidebar-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px; min-height: 56px;
}
.logo { font-size: 18px; font-weight: 700; white-space: nowrap; }
.logo-mini { font-size: 22px; }
.collapse-btn {
  background: transparent; border: none; color: var(--text-sidebar);
  cursor: pointer; padding: 4px; border-radius: var(--radius-sm);
  display: flex; align-items: center; justify-content: center;
  transition: background var(--transition-fast);
}
.collapse-btn:hover { background: rgba(255,255,255,.1); }

.sidebar-nav { flex: 1; overflow-y: auto; padding: 8px; }
.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; border-radius: var(--radius-md);
  color: var(--text-sidebar); text-decoration: none; font-size: 14px;
  transition: background var(--transition-fast), color var(--transition-fast);
  cursor: pointer; white-space: nowrap;
}
.nav-item:hover { background: rgba(255,255,255,.08); color: var(--text-sidebar-active); text-decoration: none; }
.nav-item.active { background: rgba(255,255,255,.12); color: var(--text-sidebar-active); font-weight: 500; }
.nav-label { overflow: hidden; text-overflow: ellipsis; }

.sidebar-overlay { display: none; }

.main-content {
  margin-left: var(--sidebar-width); flex: 1; min-height: 100vh;
  transition: margin-left var(--transition-normal); display: flex; flex-direction: column;
}
.main-content.expanded { margin-left: var(--sidebar-collapsed-width); }

.topbar {
  display: flex; align-items: center; justify-content: flex-end;
  padding: 12px 24px; height: var(--topbar-height); gap: 12px;
}
.hamburger-btn {
  display: none; background: transparent; border: 1px solid var(--border);
  color: var(--text-secondary); cursor: pointer; padding: 6px;
  border-radius: var(--radius-sm); align-items: center; justify-content: center;
  transition: background var(--transition-fast);
}
.hamburger-btn:hover { background: var(--bg-hover); }
.theme-toggle {
  background: transparent; border: 1px solid var(--border); color: var(--text-secondary);
  cursor: pointer; padding: 6px; border-radius: var(--radius-sm);
  display: flex; align-items: center; justify-content: center;
  transition: background var(--transition-fast), color var(--transition-fast);
}
.theme-toggle:hover { background: var(--bg-hover); color: var(--text-primary); }
.page-container { flex: 1; padding: 0 24px 24px; }

.fade-enter-active, .fade-leave-active { transition: opacity 200ms ease, transform 200ms ease; }
.fade-enter-from { opacity: 0; transform: translateY(8px); }
.fade-leave-to { opacity: 0; transform: translateY(-4px); }

@media (max-width: 768px) {
  .sidebar { transform: translateX(-100%); width: var(--sidebar-width) !important; }
  .sidebar.mobile-open { transform: translateX(0); box-shadow: 4px 0 24px rgba(0,0,0,.3); }
  .sidebar-overlay { display: block; position: fixed; inset: 0; background: rgba(0,0,0,.4); z-index: 99; }
  .main-content, .main-content.expanded { margin-left: 0; }
  .hamburger-btn { display: flex; }
  .collapse-btn { display: none; }
  .page-container { padding: 0 16px 16px; }
}
</style>
