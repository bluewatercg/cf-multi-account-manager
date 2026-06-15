<script setup lang="ts">
import { onMounted } from 'vue'
import { useTable } from '@/composables/useTable'
import AccountGroupedTable from '@/components/AccountGroupedTable.vue'
import DomainTags from '@/components/DomainTags.vue'
import SyncButton from '@/components/SyncButton.vue'
import { formatBeijingTime } from '@/utils/time'
import type { PagesProject } from '@/api/types'

const { data, loading, fetchData } = useTable<PagesProject>('/pages')

const statusType = (s: string | null) => {
  if (!s) return 'info'
  if (['active', 'deployed'].includes(s)) return 'success'
  if (['building', 'queued'].includes(s)) return ''
  if (s === 'failure') return 'danger'
  return 'info'
}

const statusLabel = (s: string | null) => {
  if (!s) return '未知'
  if (['active', 'deployed'].includes(s)) return '已部署'
  if (['building', 'queued'].includes(s)) return '构建中'
  if (s === 'failure') return '失败'
  return s
}

onMounted(fetchData)
</script>

<template>
  <div class="page-view">
    <div class="page-topbar">
      <h2>Pages</h2>
      <div class="topbar-actions">
        <SyncButton kind="asset_sync" label="立即资产巡检" @synced="fetchData" />
        <el-button @click="fetchData">刷新</el-button>
      </div>
    </div>

    <AccountGroupedTable :data="data" :loading="loading" empty-text="暂无 Pages" item-label="Pages">
      <el-table-column label="项目" prop="project_name" min-width="180" sortable>
        <template #default="{ row }">
          <span class="bold">{{ row.project_name }}</span>
        </template>
      </el-table-column>
      <el-table-column label="subdomain" prop="subdomain" width="160" />
      <el-table-column label="生产分支" prop="production_branch" width="130" />
      <el-table-column label="自定义域名" min-width="260">
        <template #default="{ row }">
          <DomainTags :value="row.custom_domains" />
        </template>
      </el-table-column>
      <el-table-column label="部署状态" width="120" align="center">
        <template #default="{ row }">
          <el-tag :type="statusType(row.latest_deployment_status)" size="small">
            {{ statusLabel(row.latest_deployment_status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="域名数" prop="domains_count" width="90" align="center" />
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
