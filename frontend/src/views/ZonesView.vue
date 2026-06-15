<script setup lang="ts">
import { onMounted } from 'vue'
import { useTable } from '@/composables/useTable'
import AccountGroupedTable from '@/components/AccountGroupedTable.vue'
import SyncButton from '@/components/SyncButton.vue'
import { formatBeijingTime } from '@/utils/time'
import type { Zone } from '@/api/types'

const { data, loading, fetchData } = useTable<Zone>('/zones')

onMounted(fetchData)
</script>

<template>
  <div class="page-view">
    <div class="page-topbar">
      <h2>域名 Zones</h2>
      <div class="topbar-actions">
        <SyncButton kind="asset_sync" label="立即资产巡检" @synced="fetchData" />
        <el-button @click="fetchData">刷新</el-button>
      </div>
    </div>

    <AccountGroupedTable :data="data" :loading="loading" empty-text="暂无 Zones" item-label="Zones">
      <el-table-column label="Zone" prop="name" min-width="200" sortable>
        <template #default="{ row }">
          <span class="bold">{{ row.name }}</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="120" align="center">
        <template #default="{ row }">
          <el-tag
            :type="row.status === 'active' ? 'success' : row.status === 'pending' ? 'warning' : 'info'"
            size="small"
          >{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="类型" prop="type" width="100" />
      <el-table-column label="DNS 数" prop="dns_count" width="100" align="center">
        <template #default="{ row }">
          <router-link :to="{ path: '/dns', query: { zone: row.name } }">
            {{ row.dns_count }}
          </router-link>
        </template>
      </el-table-column>
      <el-table-column label="Routes 数" prop="routes_count" width="110" align="center">
        <template #default="{ row }">
          <router-link :to="{ path: '/routes', query: { zone: row.name } }">
            {{ row.routes_count }}
          </router-link>
        </template>
      </el-table-column>
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

.topbar-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.bold {
  font-weight: 600;
}
</style>
