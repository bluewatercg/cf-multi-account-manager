import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useDark, useToggle } from '@vueuse/core'

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const mobileOpen = ref(false)
  const isDark = useDark({ storageKey: 'cfm-theme' })
  const toggleDark = useToggle(isDark)

  function toggleSidebar() { sidebarCollapsed.value = !sidebarCollapsed.value }
  function openMobile() { mobileOpen.value = true }
  function closeMobile() { mobileOpen.value = false }
  function toggleMobile() { mobileOpen.value = !mobileOpen.value }

  return {
    sidebarCollapsed, mobileOpen, isDark,
    toggleSidebar, openMobile, closeMobile, toggleMobile, toggleDark,
  }
})
