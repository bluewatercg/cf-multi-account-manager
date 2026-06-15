<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import api from '@/api'
import AccountGroupedTable from '@/components/AccountGroupedTable.vue'
import DomainTags from '@/components/DomainTags.vue'
import SyncButton from '@/components/SyncButton.vue'
import { formatBeijingTime } from '@/utils/time'
import type { UsageWorkerDaily, Worker } from '@/api/types'

type WorkerWithUsage = Worker & {
  usage_requests: number | null
  usage_subrequests: number | null
  usage_errors: number | null
  usage_cpu_time_p50: number | null
  usage_cpu_time_p99: number | null
  usage_collected_at: string | null
}

const workers = ref<Worker[]>([])
const workerUsage = ref<UsageWorkerDaily[]>([])
const loading = ref(false)

const currentUsageDate = computed(() => workerUsage.value[0]?.date_utc || '')

const usageByWorker = computed(() => {
  const map = new Map<string, UsageWorkerDaily>()

  for (const row of workerUsage.value) {
    if (row.date_utc !== currentUsageDate.value) continue
    map.set(`${row.account_db_id}:${row.script_name}`, row)
  }

  return map
})

const data = computed<WorkerWithUsage[]>(() => workers.value.map(worker => {
  const usage = usageByWorker.value.get(`${worker.account_db_id}:${worker.script_name}`)

  return {
    ...worker,
    usage_requests: usage?.requests ?? null,
    usage_subrequests: usage?.subrequests ?? null,
    usage_errors: usage?.errors ?? null,
    usage_cpu_time_p50: usage?.cpu_time_p50 ?? null,
    usage_cpu_time_p99: usage?.cpu_time_p99 ?? null,
    usage_collected_at: usage?.collected_at ?? null,
  }
}))

async function fetchData() {
  loading.value = true
  try {
    const [workerRes, usageRes] = await Promise.all([
      api.get<Worker[]>('/workers'),
      api.get<UsageWorkerDaily[]>('/usage/workers'),
    ])
    workers.value = workerRes.data
    workerUsage.value = usageRes.data
  } finally {
    loading.value = false
  }
}

function formatUsageNumber(value: number | null): string {
  return value == null ? '-' : Number(value).toLocaleString()
}

function formatCpu(value: number | null): string {
  return value == null ? '-' : value.toFixed(1)
}

onMounted(fetchData)
</script>

<template>
  <div class="page-view">
    <div class="page-topbar">
      <h2>Workers</h2>
      <div class="topbar-actions">
        <SyncButton kind="asset_sync" label="立即资产巡检" @synced="fetchData" />
        <SyncButton kind="usage_sync" label="立即用量巡检" @synced="fetchData" />
        <el-button @click="fetchData">刷新</el-button>
      </div>
    </div>

    <AccountGroupedTable :data="data" :loading="loading" empty-text="暂无 Workers" item-label="Workers">
      <el-table-column label="Worker" prop="script_name" min-width="200" sortable />
      <el-table-column label="自定义域名/路由" min-width="280">
        <template #default="{ row }">
          <DomainTags :value="row.custom_domains" />
        </template>
      </el-table-column>
      <el-table-column label="请求" width="100" align="right">
        <template #default="{ row }">{{ formatUsageNumber(row.usage_requests) }}</template>
      </el-table-column>
      <el-table-column label="子请求" width="100" align="right">
        <template #default="{ row }">{{ formatUsageNumber(row.usage_subrequests) }}</template>
      </el-table-column>
      <el-table-column label="错误" width="80" align="right">
        <template #default="{ row }">
          <span :class="{ 'danger-text': row.usage_errors > 0 }">{{ formatUsageNumber(row.usage_errors) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="CPU P50" width="100" align="right">
        <template #default="{ row }">{{ formatCpu(row.usage_cpu_time_p50) }}</template>
      </el-table-column>
      <el-table-column label="CPU P99" width="100" align="right">
        <template #default="{ row }">{{ formatCpu(row.usage_cpu_time_p99) }}</template>
      </el-table-column>
      <el-table-column label="采集" prop="usage_collected_at" width="180">
        <template #default="{ row }">{{ formatBeijingTime(row.usage_collected_at) }}</template>
      </el-table-column>
      <el-table-column label="修改时间" prop="modified_on" width="200" sortable>
        <template #default="{ row }">{{ formatBeijingTime(row.modified_on) }}</template>
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

.danger-text {
  color: var(--danger);
  font-weight: 600;
}
</style>
