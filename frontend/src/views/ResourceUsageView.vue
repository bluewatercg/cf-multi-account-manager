<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import api, { invalidateApiCache } from '@/api'
import AccountGroupedTable from '@/components/AccountGroupedTable.vue'
import DomainTags from '@/components/DomainTags.vue'
import SyncButton from '@/components/SyncButton.vue'
import { formatBeijingTime } from '@/utils/time'
import type { PagesProject, UsageWorkerDaily, Worker } from '@/api/types'

type ResourceKind = 'Worker' | 'Pages'

type ResourceRow = {
  id: string
  resource_id: number
  usage_key: string
  account_db_id: number
  account_alias: string
  kind: ResourceKind
  name: string
  secondary: string | null
  status: string | null
  custom_domains: string | null
  domains_count: number
  usage_requests: number | null
  usage_subrequests: number | null
  usage_errors: number | null
  usage_cpu_time_p50: number | null
  usage_cpu_time_p99: number | null
  usage_collected_at: string | null
  last_seen_at: string | null
  updated_at: string | null
  notes: string | null
}

const route = useRoute()
const workers = ref<Worker[]>([])
const pages = ref<PagesProject[]>([])
const workerUsage = ref<UsageWorkerDaily[]>([])
const loading = ref(false)
const savingNotes = ref(new Set<string>())

const activeKind = ref<'all' | ResourceKind>(
  route.path === '/pages' ? 'Pages' : route.path === '/workers' ? 'Worker' : 'all',
)

watch(() => route.path, (path) => {
  activeKind.value = path === '/pages' ? 'Pages' : path === '/workers' ? 'Worker' : 'all'
})

const currentUsageDate = computed(() => workerUsage.value[0]?.date_utc || '')

const usageByWorker = computed(() => {
  const map = new Map<string, UsageWorkerDaily>()

  for (const row of workerUsage.value) {
    if (row.date_utc !== currentUsageDate.value) continue
    map.set(`${row.account_db_id}:${row.script_name}`, row)
  }

  return map
})

const rows = computed<ResourceRow[]>(() => {
  const workerRows = workers.value.map((worker): ResourceRow => {
    const usage = usageByWorker.value.get(`${worker.account_db_id}:${worker.script_name}`)

    return {
      id: `worker:${worker.account_db_id}:${worker.script_name}`,
      resource_id: worker.id,
      usage_key: `worker:${worker.account_db_id}:${worker.script_name}`,
      account_db_id: worker.account_db_id,
      account_alias: worker.account_alias,
      kind: 'Worker',
      name: worker.script_name,
      secondary: null,
      status: null,
      custom_domains: worker.custom_domains ?? null,
      domains_count: worker.custom_domains_count ?? countLines(worker.custom_domains),
      usage_requests: usage?.requests ?? null,
      usage_subrequests: usage?.subrequests ?? null,
      usage_errors: usage?.errors ?? null,
      usage_cpu_time_p50: usage?.cpu_time_p50 ?? null,
      usage_cpu_time_p99: usage?.cpu_time_p99 ?? null,
      usage_collected_at: usage?.collected_at ?? null,
      last_seen_at: worker.last_seen_at,
      updated_at: worker.modified_on || worker.updated_at,
      notes: worker.notes,
    }
  })

  const pageRows = pages.value.map((page): ResourceRow => ({
    id: `pages:${page.account_db_id}:${page.project_name}`,
    resource_id: page.id,
    usage_key: `pages-account:${page.account_db_id}`,
    account_db_id: page.account_db_id,
    account_alias: page.account_alias,
    kind: 'Pages',
    name: page.project_name,
    secondary: page.subdomain || page.production_branch || null,
    status: page.latest_deployment_status,
    custom_domains: page.custom_domains ?? null,
    domains_count: page.domains_count ?? countLines(page.custom_domains),
    usage_requests: page.usage_requests ?? null,
    usage_subrequests: null,
    usage_errors: page.usage_errors ?? null,
    usage_cpu_time_p50: null,
    usage_cpu_time_p99: null,
    usage_collected_at: page.usage_collected_at ?? null,
    last_seen_at: page.last_seen_at,
    updated_at: page.updated_at,
    notes: page.notes,
  }))

  return [...workerRows, ...pageRows].sort((a, b) => {
    const account = a.account_alias.localeCompare(b.account_alias, 'zh-Hans-CN')
    if (account !== 0) return account
    const kind = a.kind.localeCompare(b.kind)
    if (kind !== 0) return kind
    return a.name.localeCompare(b.name, 'zh-Hans-CN')
  })
})

const filteredRows = computed(() => {
  if (activeKind.value === 'all') return rows.value
  return rows.value.filter(row => row.kind === activeKind.value)
})

const totals = computed(() => {
  let requests = 0
  let subrequests = 0
  let errors = 0
  const seen = new Set<string>()

  for (const row of filteredRows.value) {
    if (seen.has(row.usage_key)) continue
    seen.add(row.usage_key)
    requests += row.usage_requests ?? 0
    subrequests += row.usage_subrequests ?? 0
    errors += row.usage_errors ?? 0
  }

  return { requests, subrequests, errors }
})

async function fetchData(force = false) {
  if (force) invalidateApiCache()
  loading.value = true
  try {
    const [workerRes, pageRes, usageRes] = await Promise.all([
      api.get<Worker[]>('/workers'),
      api.get<PagesProject[]>('/pages'),
      api.get<UsageWorkerDaily[]>('/usage/workers'),
    ])
    workers.value = workerRes.data
    pages.value = pageRes.data
    workerUsage.value = usageRes.data
  } finally {
    loading.value = false
  }
}

function countLines(value?: string | null): number {
  return value ? value.split('\n').filter(Boolean).length : 0
}

function formatUsageNumber(value: number | null): string {
  // 无用量记录时显示 0 而非 '-'，避免同一账号下"有的有数、有的没数"造成困惑
  return value == null ? '0' : Number(value).toLocaleString()
}

function formatCpu(value: number | null): string {
  return value == null ? '-' : value.toFixed(1)
}

function kindTagType(kind: ResourceKind) {
  return kind === 'Worker' ? 'primary' : 'success'
}

function statusType(s: string | null) {
  if (!s) return 'info'
  if (['active', 'deployed'].includes(s)) return 'success'
  if (['building', 'queued'].includes(s)) return ''
  if (s === 'failure') return 'danger'
  return 'info'
}

function statusLabel(s: string | null) {
  if (!s) return '-'
  if (['active', 'deployed'].includes(s)) return '已部署'
  if (['building', 'queued'].includes(s)) return '构建中'
  if (s === 'failure') return '失败'
  return s
}

async function saveNote(row: ResourceRow) {
  const key = row.id
  if (savingNotes.value.has(key)) return
  savingNotes.value = new Set(savingNotes.value).add(key)
  try {
    const collection = row.kind === 'Worker' ? workers : pages
    const item = collection.value.find((entry) => entry.id === row.resource_id)
    const notes = row.notes?.trim() || null
    if (item) item.notes = notes
    await api.put(`/${row.kind === 'Worker' ? 'workers' : 'pages'}/${row.resource_id}/notes`, { notes })
    row.notes = notes
  } finally {
    const next = new Set(savingNotes.value)
    next.delete(key)
    savingNotes.value = next
  }
}

onMounted(fetchData)
</script>

<template>
  <div class="page-view">
    <div class="page-topbar">
      <div>
        <h2>Workers / Pages</h2>
        <p class="page-subtitle">统一查看资源、域名和当天请求统计</p>
      </div>
      <div class="topbar-actions">
        <el-segmented
          v-model="activeKind"
          :options="[
            { label: '全部', value: 'all' },
            { label: 'Workers', value: 'Worker' },
            { label: 'Pages', value: 'Pages' },
          ]"
        />
        <SyncButton kind="asset_sync" label="立即资产巡检" @synced="fetchData(true)" />
        <SyncButton kind="usage_sync" label="立即用量巡检" @synced="fetchData(true)" />
        <el-button @click="fetchData(true)">刷新</el-button>
      </div>
    </div>

    <div class="summary-bar">
      <div>
        <span class="summary-label">资源</span>
        <strong>{{ filteredRows.length.toLocaleString() }}</strong>
      </div>
      <div>
        <span class="summary-label">请求</span>
        <strong>{{ totals.requests.toLocaleString() }}</strong>
      </div>
      <div>
        <span class="summary-label">子请求</span>
        <strong>{{ totals.subrequests.toLocaleString() }}</strong>
      </div>
      <div>
        <span class="summary-label">错误</span>
        <strong :class="{ 'danger-text': totals.errors > 0 }">{{ totals.errors.toLocaleString() }}</strong>
      </div>
    </div>

    <AccountGroupedTable
      :data="filteredRows"
      :loading="loading"
      empty-text="暂无 Workers / Pages"
      item-label="资源"
    >
      <el-table-column label="类型" prop="kind" width="92" sortable>
        <template #default="{ row }">
          <el-tag :type="kindTagType(row.kind)" effect="plain" size="small">{{ row.kind }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="名称" prop="name" min-width="210" sortable show-overflow-tooltip>
        <template #default="{ row }">
          <div class="resource-name">
            <span class="bold">{{ row.name }}</span>
            <span v-if="row.secondary" class="muted">{{ row.secondary }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="备注" min-width="220">
        <template #default="{ row }">
          <el-input
            v-model="row.notes"
            type="textarea"
            :rows="2"
            resize="vertical"
            maxlength="500"
            show-word-limit
            placeholder="输入备注"
            :disabled="savingNotes.has(row.id)"
            @blur="saveNote(row)"
          />
        </template>
      </el-table-column>
      <el-table-column label="域名/路由" min-width="260">
        <template #default="{ row }">
          <DomainTags :value="row.custom_domains" />
        </template>
      </el-table-column>
      <el-table-column label="请求" width="110" align="right" sortable prop="usage_requests">
        <template #default="{ row }">{{ formatUsageNumber(row.usage_requests) }}</template>
      </el-table-column>
      <el-table-column label="子请求" width="100" align="right" sortable prop="usage_subrequests">
        <template #default="{ row }">{{ formatUsageNumber(row.usage_subrequests) }}</template>
      </el-table-column>
      <el-table-column label="错误" width="90" align="right" sortable prop="usage_errors">
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
      <el-table-column label="状态" width="110" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.kind === 'Pages'" :type="statusType(row.status)" size="small">
            {{ statusLabel(row.status) }}
          </el-tag>
          <span v-else class="muted">-</span>
        </template>
      </el-table-column>
      <el-table-column label="采集时间" prop="usage_collected_at" width="180">
        <template #default="{ row }">{{ formatBeijingTime(row.usage_collected_at) }}</template>
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
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.page-topbar h2 {
  font-size: 20px;
  font-weight: 600;
}

.page-subtitle {
  color: var(--text-secondary);
  font-size: 13px;
}

.topbar-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  justify-content: flex-end;
}

.summary-bar {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.summary-bar > div {
  min-width: 0;
  padding: 12px 14px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: var(--shadow-sm);
}

.summary-label {
  display: block;
  color: var(--text-muted);
  font-size: 12px;
  line-height: 1.2;
}

.summary-bar strong {
  display: block;
  margin-top: 4px;
  font-size: 18px;
  line-height: 1.2;
}

.resource-name {
  display: flex;
  min-width: 0;
  flex-direction: column;
  line-height: 1.35;
}

.bold {
  overflow: hidden;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.muted {
  overflow: hidden;
  color: var(--text-muted);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.danger-text {
  color: var(--danger);
  font-weight: 600;
}

@media (max-width: 900px) {
  .page-topbar {
    flex-direction: column;
  }

  .topbar-actions {
    justify-content: flex-start;
  }

  .summary-bar {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
