<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import VChart from 'vue-echarts'
import '@/utils/echarts'
import api from '@/api'
import { formatBeijingTime } from '@/utils/time'
import type { UsageAccountDaily } from '@/api/types'

const accountUsage = ref<UsageAccountDaily[]>([])
const loading = ref(false)
const RESOURCE_LIMITS = {
  d1RowsRead: 5000000,
  d1RowsWritten: 100000,
  d1StorageBytes: 5 * 1024 * 1024 * 1024,
  kvReads: 100000,
  kvWrites: 1000,
  kvStorageBytes: 1 * 1024 * 1024 * 1024,
  r2ClassA: 1000000,
  r2ClassB: 10000000,
  r2StorageBytes: 10 * 1024 * 1024 * 1024,
}

async function loadUsage() {
  loading.value = true
  try {
    accountUsage.value = (await api.get<UsageAccountDaily[]>('/usage/accounts')).data
  } finally {
    loading.value = false
  }
}

async function runUsageSync() {
  await api.post('/sync/run-now', { kind: 'usage_sync', force: true }, { headers: { 'X-Silent': '1' } })
  window.setTimeout(loadUsage, 2500)
}

const currentUsageDate = computed(() => accountUsage.value[0]?.date_utc || '')

const currentAccountUsage = computed(() => {
  if (!currentUsageDate.value) return []
  return accountUsage.value.filter(row => row.date_utc === currentUsageDate.value)
})

function n(value: number | null | undefined): number {
  return Number(value || 0)
}

function d1Queries(row: UsageAccountDaily): number {
  return n(row.d1_read_queries) + n(row.d1_write_queries)
}

const requestTotals = computed(() => {
  const rows = currentAccountUsage.value
  const total = {
    requests: 0,
    workers: 0,
    pages: 0,
  }
  for (const row of rows) {
    total.requests += n(row.requests)
    total.workers += n(row.workers_requests)
    total.pages += n(row.pages_requests)
  }
  return [
    { label: '请求总量', value: total.requests, color: '#111827' },
    { label: 'Workers', value: total.workers, color: '#2563eb' },
    { label: 'Pages', value: total.pages, color: '#0891b2' },
  ]
})

const resourceCards = computed(() => {
  const rows = currentAccountUsage.value
  const accounts = Math.max(rows.length, 1)
  const totals = rows.reduce((acc, row) => {
    acc.d1Read += n(row.d1_rows_read)
    acc.d1Write += n(row.d1_rows_written)
    acc.d1Storage += n(row.d1_storage_bytes)
    acc.kvReads += n(row.kv_reads)
    acc.kvWrites += n(row.kv_writes)
    acc.kvStorage += n(row.kv_storage_bytes)
    acc.r2ClassA += n(row.r2_class_a)
    acc.r2ClassB += n(row.r2_class_b)
    acc.r2Storage += n(row.r2_storage_bytes)
    return acc
  }, { d1Read: 0, d1Write: 0, d1Storage: 0, kvReads: 0, kvWrites: 0, kvStorage: 0, r2ClassA: 0, r2ClassB: 0, r2Storage: 0 })
  return [
    { title: 'D1 读行', value: totals.d1Read, limit: RESOURCE_LIMITS.d1RowsRead * accounts, color: '#7c3aed' },
    { title: 'D1 写行', value: totals.d1Write, limit: RESOURCE_LIMITS.d1RowsWritten * accounts, color: '#8b5cf6' },
    { title: 'D1 存储', value: totals.d1Storage, limit: RESOURCE_LIMITS.d1StorageBytes * accounts, color: '#6d28d9', bytes: true },
    { title: 'KV 读取', value: totals.kvReads, limit: RESOURCE_LIMITS.kvReads * accounts, color: '#059669' },
    { title: 'KV 写入', value: totals.kvWrites, limit: RESOURCE_LIMITS.kvWrites * accounts, color: '#10b981' },
    { title: 'KV 存储', value: totals.kvStorage, limit: RESOURCE_LIMITS.kvStorageBytes * accounts, color: '#047857', bytes: true },
    { title: 'R2 Class A', value: totals.r2ClassA, limit: RESOURCE_LIMITS.r2ClassA * accounts, color: '#d97706' },
    { title: 'R2 Class B', value: totals.r2ClassB, limit: RESOURCE_LIMITS.r2ClassB * accounts, color: '#f59e0b' },
    { title: 'R2 存储', value: totals.r2Storage, limit: RESOURCE_LIMITS.r2StorageBytes * accounts, color: '#b45309', bytes: true },
  ]
})

const usageBarOption = computed(() => {
  if (!currentAccountUsage.value.length) {
    return {
      graphic: { type: 'text', left: 'center', top: 'center', style: { text: '暂无用量数据', fontSize: 14, fill: '#94a3b8' } },
    }
  }
  const latest = currentAccountUsage.value.slice(0, 10)
  const quotaLimit = Math.max(...latest.map(u => n(u.quota)), 100000)
  const limitLine = {
    silent: true,
    symbol: 'none',
    lineStyle: { color: '#dc2626', type: 'dashed', width: 2 },
    label: {
      formatter: `Limit ${quotaLimit.toLocaleString()}`,
      color: '#dc2626',
      fontWeight: 700,
      position: 'insideEndTop',
    },
    data: [{ yAxis: quotaLimit }],
  }
  return {
    tooltip: { trigger: 'axis' },
    legend: { top: 0, type: 'scroll' },
    grid: { left: 80, right: 20, top: 42, bottom: 40 },
    xAxis: { type: 'category', data: latest.map(u => u.account_alias), axisLabel: { fontSize: 12 } },
    yAxis: { type: 'value', axisLabel: { fontSize: 12 } },
    series: [
      { name: 'Workers', type: 'bar', stack: 'usage', data: latest.map(u => n(u.workers_requests)), itemStyle: { color: '#2563eb' }, barMaxWidth: 48, markLine: limitLine },
      { name: 'Pages', type: 'bar', stack: 'usage', data: latest.map(u => n(u.pages_requests)), itemStyle: { color: '#0891b2' }, barMaxWidth: 48 },
    ],
  }
})

function usageColor(pct: number): 'exception' | 'warning' | undefined {
  if (pct >= 96) return 'exception'
  if (pct >= 80) return 'warning'
  return undefined
}

function formatNumber(value: number | null | undefined): string {
  return n(value).toLocaleString()
}

function formatBytes(value: number | null | undefined): string {
  const bytes = n(value)
  if (bytes >= 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(2)} MB`
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(2)} KB`
  return `${bytes.toLocaleString()} B`
}

function formatMetric(value: number, bytes?: boolean): string {
  return bytes ? formatBytes(value) : formatNumber(value)
}

function percent(value: number, limit: number): number {
  return limit > 0 ? Math.min(Number(((value * 100) / limit).toFixed(1)), 100) : 0
}

onMounted(loadUsage)
</script>

<template>
  <div class="usage-page" v-loading="loading">
    <div class="page-topbar">
      <h2>用量 Usage</h2>
      <div class="topbar-actions">
        <el-button type="primary" @click="runUsageSync">立即用量巡检</el-button>
        <el-button @click="loadUsage">刷新</el-button>
      </div>
    </div>

    <div class="section-card">
      <h3>请求额度趋势</h3>
      <div class="usage-summary">
        <div v-for="item in requestTotals" :key="item.label" class="usage-summary-item">
          <div class="usage-summary-label">{{ item.label }}</div>
          <div class="usage-summary-value" :style="{ color: item.color }">{{ formatNumber(item.value) }}</div>
        </div>
      </div>
      <v-chart class="usage-chart" :option="usageBarOption" autoresize />
    </div>

    <div class="section-card">
      <h3>资源额度</h3>
      <div class="resource-grid">
        <div v-for="item in resourceCards" :key="item.title" class="resource-card">
          <div class="resource-card-head">
            <span>{{ item.title }}</span>
            <strong :style="{ color: item.color }">{{ percent(item.value, item.limit) }}%</strong>
          </div>
          <div class="resource-card-value">{{ formatMetric(item.value, item.bytes) }}</div>
          <el-progress
            :percentage="percent(item.value, item.limit)"
            :color="item.color"
            :show-text="false"
            :stroke-width="8"
          />
          <div class="resource-card-limit">额度 {{ formatMetric(item.limit, item.bytes) }}</div>
        </div>
      </div>
    </div>

    <div class="section-card">
      <h3>账号实时</h3>
      <el-table :data="currentAccountUsage" stripe max-height="400" empty-text="暂无用量数据" style="width: 100%">
        <el-table-column type="expand" width="48">
          <template #default="{ row }">
            <div class="resource-detail-grid">
              <div class="resource-detail">
                <div class="resource-detail-title">D1</div>
                <div>读行 {{ formatNumber(row.d1_rows_read) }}</div>
                <div>写行 {{ formatNumber(row.d1_rows_written) }}</div>
                <div>查询 {{ formatNumber(d1Queries(row)) }}</div>
                <div>存储 {{ formatBytes(row.d1_storage_bytes) }} / {{ formatNumber(row.d1_databases) }} DB</div>
              </div>
              <div class="resource-detail">
                <div class="resource-detail-title">KV</div>
                <div>读取 {{ formatNumber(row.kv_reads) }}</div>
                <div>写入 {{ formatNumber(row.kv_writes) }}</div>
                <div>删除/列表 {{ formatNumber(n(row.kv_deletes) + n(row.kv_lists)) }}</div>
                <div>存储 {{ formatBytes(row.kv_storage_bytes) }} / {{ formatNumber(row.kv_namespaces) }} NS</div>
              </div>
              <div class="resource-detail">
                <div class="resource-detail-title">R2</div>
                <div>Class A {{ formatNumber(row.r2_class_a) }}</div>
                <div>Class B {{ formatNumber(row.r2_class_b) }}</div>
                <div>免费/其他 {{ formatNumber(n(row.r2_free) + n(row.r2_other)) }}</div>
                <div>存储 {{ formatBytes(row.r2_storage_bytes) }} / {{ formatNumber(row.r2_buckets) }} 桶</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="账号" prop="account_alias" min-width="160" />
        <el-table-column label="日期" prop="date_utc" width="120" />
        <el-table-column label="请求" width="110" align="right">
          <template #default="{ row }">{{ formatNumber(row.requests) }}</template>
        </el-table-column>
        <el-table-column label="Workers" width="100" align="right">
          <template #default="{ row }">{{ formatNumber(row.workers_requests) }}</template>
        </el-table-column>
        <el-table-column label="Pages" width="100" align="right">
          <template #default="{ row }">{{ formatNumber(row.pages_requests) }}</template>
        </el-table-column>
        <el-table-column label="D1 查询" width="100" align="right">
          <template #default="{ row }">{{ formatNumber(d1Queries(row)) }}</template>
        </el-table-column>
        <el-table-column label="KV" width="90" align="right">
          <template #default="{ row }">{{ formatNumber(row.kv_requests) }}</template>
        </el-table-column>
        <el-table-column label="R2" width="90" align="right">
          <template #default="{ row }">{{ formatNumber(row.r2_requests) }}</template>
        </el-table-column>
        <el-table-column label="缓存" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.cache_status === 'fresh' ? 'info' : 'success'">
              {{ row.cache_status === 'fresh' ? '缓存' : '已刷新' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="子请求" width="100" align="right">
          <template #default="{ row }">{{ formatNumber(row.subrequests) }}</template>
        </el-table-column>
        <el-table-column label="错误" width="80" align="right">
          <template #default="{ row }">{{ formatNumber(row.errors) }}</template>
        </el-table-column>
        <el-table-column label="额度" prop="quota" width="100" align="right" />
        <el-table-column label="使用率" width="180">
          <template #default="{ row }">
            <el-progress
              :percentage="Math.min(row.usage_percent, 100)"
              :status="usageColor(row.usage_percent)"
              :stroke-width="14"
              :text-inside="true"
            />
          </template>
        </el-table-column>
        <el-table-column label="采集" prop="collected_at" width="180">
          <template #default="{ row }">{{ formatBeijingTime(row.collected_at) }}</template>
        </el-table-column>
      </el-table>
    </div>

  </div>
</template>

<style scoped>
.usage-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
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
}

.section-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-md);
}

.section-card h3 {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--text-primary);
}

.usage-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.usage-summary-item {
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 10px 12px;
  background: var(--bg-table-header);
}

.usage-summary-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.usage-summary-value {
  margin-top: 4px;
  font-size: 20px;
  font-weight: 800;
  line-height: 1.15;
  font-variant-numeric: tabular-nums;
}

.resource-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.resource-card {
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 12px;
  background: var(--bg-table-header);
}

.resource-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}

.resource-card-value {
  margin: 8px 0;
  font-size: 18px;
  font-weight: 800;
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
}

.resource-card-limit {
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-muted);
}

.resource-detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  padding: 12px 48px;
}

.resource-detail {
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 10px 12px;
  background: var(--bg-page);
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.8;
}

.resource-detail-title {
  margin-bottom: 4px;
  color: var(--text-primary);
  font-weight: 700;
}

.usage-chart {
  width: 100%;
  height: 280px;
}
</style>
