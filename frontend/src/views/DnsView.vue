<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useTable } from '@/composables/useTable'
import AccountGroupedTable from '@/components/AccountGroupedTable.vue'
import SyncButton from '@/components/SyncButton.vue'
import type { DnsRecord } from '@/api/types'

const route = useRoute()
const { data, loading, fetchData } = useTable<DnsRecord>('/dns-records')
const filterZone = computed(() => (route.query.zone as string) || '')

const filteredData = computed(() => {
  if (!filterZone.value) return data.value
  return data.value.filter(r => r.zone_name === filterZone.value)
})

const typeColors: Record<string, string> = {
  A: '', AAAA: '', CNAME: 'success', MX: 'warning', TXT: 'info', NS: 'danger',
}

onMounted(fetchData)
</script>

<template>
  <div class="page-view">
    <div class="page-topbar">
      <h2>DNS 记录</h2>
      <div class="topbar-actions">
        <el-tag v-if="filterZone" closable @close="$router.push('/dns')">
          Zone: {{ filterZone }}
        </el-tag>
        <SyncButton kind="asset_sync" label="立即资产巡检" @synced="fetchData" />
        <el-button @click="fetchData">刷新</el-button>
      </div>
    </div>

    <AccountGroupedTable
      :data="filteredData"
      :loading="loading"
      empty-text="暂无 DNS 记录"
      item-label="DNS"
      max-height="600"
    >
      <el-table-column label="Zone" prop="zone_name" width="160" />
      <el-table-column label="类型" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="typeColors[row.type] || 'info'" size="small" effect="dark" round>
            {{ row.type }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="名称" prop="name" min-width="200">
        <template #default="{ row }">
          <code class="mono">{{ row.name }}</code>
        </template>
      </el-table-column>
      <el-table-column label="内容" prop="content" min-width="250" show-overflow-tooltip>
        <template #default="{ row }">
          <code class="mono">{{ row.content }}</code>
        </template>
      </el-table-column>
      <el-table-column label="代理" width="80" align="center">
        <template #default="{ row }">
          <span v-if="row.proxied" class="proxy-on">☁️</span>
          <span v-else class="proxy-off">DNS</span>
        </template>
      </el-table-column>
      <el-table-column label="TTL" width="80" align="center">
        <template #default="{ row }">
          {{ row.ttl === 0 ? '自动' : row.ttl }}
        </template>
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

.mono {
  font-family: 'SF Mono', Consolas, monospace;
  font-size: 13px;
}

.proxy-on {
  font-size: 16px;
}

.proxy-off {
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 600;
}
</style>
