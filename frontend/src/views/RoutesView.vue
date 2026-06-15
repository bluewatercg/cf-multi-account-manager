<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useTable } from '@/composables/useTable'
import AccountGroupedTable from '@/components/AccountGroupedTable.vue'
import SyncButton from '@/components/SyncButton.vue'
import { formatBeijingTime } from '@/utils/time'
import type { WorkerRoute } from '@/api/types'

const route = useRoute()
const { data, loading, fetchData } = useTable<WorkerRoute>('/routes')
const filterZone = computed(() => (route.query.zone as string) || '')

const filteredData = computed(() => {
  if (!filterZone.value) return data.value
  return data.value.filter(r => r.zone_name === filterZone.value)
})

onMounted(fetchData)
</script>

<template>
  <div class="page-view">
    <div class="page-topbar">
      <h2>Worker Routes</h2>
      <div class="topbar-actions">
        <el-tag v-if="filterZone" closable @close="$router.push('/routes')">
          Zone: {{ filterZone }}
        </el-tag>
        <SyncButton kind="asset_sync" label="立即资产巡检" @synced="fetchData" />
        <el-button @click="fetchData">刷新</el-button>
      </div>
    </div>

    <AccountGroupedTable :data="filteredData" :loading="loading" empty-text="暂无 Routes" item-label="Routes">
      <el-table-column label="Zone" prop="zone_name" width="160" />
      <el-table-column label="Pattern" min-width="250">
        <template #default="{ row }">
          <code class="mono">{{ row.pattern }}</code>
        </template>
      </el-table-column>
      <el-table-column label="Script" prop="script_name" width="180" />
      <el-table-column label="last seen" prop="last_seen_at" width="200">
        <template #default="{ row }">{{ formatBeijingTime(row.last_seen_at) }}</template>
      </el-table-column>
    </AccountGroupedTable>
  </div>
</template>

<style scoped>
.page-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.page-topbar h2 {
  font-size: 20px;
  font-weight: 600;
}

.mono {
  font-family: 'SF Mono', Consolas, monospace;
  font-size: 13px;
}
</style>
