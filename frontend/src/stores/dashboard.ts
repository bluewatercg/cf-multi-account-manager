import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'
import type { DashboardSummary } from '@/api/types'

export const useDashboardStore = defineStore('dashboard', () => {
  const summary = ref<DashboardSummary | null>(null)
  const loading = ref(false)
  const syncing = ref(false)

  async function fetchSummary() {
    loading.value = true
    try {
      summary.value = (await api.get<DashboardSummary>('/dashboard/summary')).data
    } finally {
      loading.value = false
    }
  }

  async function runFullSync() {
    syncing.value = true
    try {
      await api.post('/sync/run-now', { kind: 'full_sync' }, { headers: { 'X-Silent': '1' } })
      ElMessage.success('已启动后台巡检，请稍后刷新')
    } finally {
      syncing.value = false
    }
  }

  return { summary, loading, syncing, fetchSummary, runFullSync }
})
