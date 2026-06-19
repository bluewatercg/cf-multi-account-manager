<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import '@/utils/echarts'
import { useDashboardStore } from '@/stores/dashboard'
import StatusBadge from '@/components/StatusBadge.vue'
import { formatBeijingTime } from '@/utils/time'

const store = useDashboardStore()

// 统计卡片
const cards = computed(() => {
  const d = store.summary
  if (!d) return []
  return [
    { label: '账号', value: d.accounts, color: '#2563eb' },
    { label: 'Workers', value: d.workers, color: '#7c3aed' },
    { label: 'Pages', value: d.pages, color: '#0891b2' },
    { label: 'Zones', value: d.zones, color: '#059669' },
    { label: 'DNS 记录', value: d.dns_records, color: '#d97706' },
    { label: 'Routes', value: d.routes, color: '#dc2626' },
    { label: '开放告警', value: d.open_alerts.length, color: '#e11d48' },
  ]
})

// ECharts 用量趋势配置
const usageChartOption = computed(() => {
  const usage = store.summary?.today_usage
  if (!usage?.length) {
    return {
      graphic: {
        type: 'text', left: 'center', top: 'center',
        style: { text: '今日暂无用量数据', fontSize: 14, fill: '#94a3b8' },
      },
    }
  }
  const quotaLimit = Math.max(...usage.map((u) => n(u.quota)), 100000)
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
    tooltip: {
      trigger: 'axis',
      formatter: (params: any[]) => {
        const lines = params.map((item) => `${item.marker}${item.seriesName}: ${Number(item.value || 0).toLocaleString()}`)
        return `<b>${params[0]?.name ?? ''}</b><br/>${lines.join('<br/>')}`
      },
    },
    legend: { top: 0, type: 'scroll' },
    grid: { left: 60, right: 20, top: 42, bottom: 40 },
    xAxis: {
      type: 'category',
      data: usage.map((u) => u.account_alias),
      axisLabel: { fontSize: 12 },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        fontSize: 12,
        formatter: (v: number) => (v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v)),
      },
    },
    series: [
      { name: 'Workers', type: 'bar', stack: 'usage', data: usage.map((u) => n(u.workers_requests)), itemStyle: { color: '#2563eb' }, barMaxWidth: 48, markLine: limitLine },
      { name: 'Pages', type: 'bar', stack: 'usage', data: usage.map((u) => n(u.pages_requests)), itemStyle: { color: '#0891b2' }, barMaxWidth: 48 },
    ],
  }
})

// 最近巡检表格列
const recentRunColumns = [
  { label: '账号', prop: 'account_alias', width: 120 },
  { label: '类型', prop: 'run_type', width: 120 },
  { label: '状态', prop: 'status', width: 100, slot: 'status' },
  { label: '开始', prop: 'started_at', width: 180, slot: 'time' },
  { label: '耗时', prop: 'duration_ms', width: 100, slot: 'duration' },
  { label: '错误', prop: 'error_message', minWidth: 200, showOverflowTooltip: true },
]

function formatDuration(ms: number | null): string {
  if (ms == null) return '-'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

function formatNumber(value: number): string {
  return Number(value || 0).toLocaleString()
}

function n(value: number | null | undefined): number {
  return Number(value || 0)
}

function d1Queries(row: any): number {
  return n(row.d1_read_queries) + n(row.d1_write_queries)
}

function formatPercent(value: number): string {
  return `${Number(value || 0).toFixed(2)}%`
}

function runBadgeStatus(status: string): string {
  if (status === 'success') return 'ok'
  if (status === 'partial') return 'partial'
  return 'error'
}

onMounted(store.fetchSummary)
</script>

<template>
  <div class="dashboard" v-loading="store.loading">
    <div class="topbar">
      <h2>总览 Dashboard</h2>
      <div class="topbar-actions">
        <el-button type="primary" :loading="store.syncing" @click="store.runFullSync()">
          立即全量巡检
        </el-button>
        <el-button :icon="Refresh" @click="store.fetchSummary()">刷新</el-button>
      </div>
    </div>

    <div class="cards-grid">
      <div v-for="card in cards" :key="card.label" class="stat-card">
        <div class="stat-label">{{ card.label }}</div>
        <div class="stat-value" :style="{ color: card.color }">{{ card.value }}</div>
      </div>
    </div>

    <div v-if="store.summary?.open_alerts?.length" class="alert-banner">
      <el-alert
        :title="`有 ${store.summary.open_alerts.length} 条未处理告警`"
        type="warning" show-icon :closable="false"
        style="border-radius: var(--radius-md)"
      />
    </div>

    <div class="section-card">
      <h3>今日账号用量</h3>
      <v-chart class="usage-chart" :option="usageChartOption" autoresize />
      <el-table
        v-if="store.summary?.today_usage?.length"
        :data="store.summary.today_usage"
        class="usage-table"
        stripe
        size="small"
        style="width: 100%"
      >
        <el-table-column label="账号" prop="account_alias" min-width="180" />
        <el-table-column label="请求" width="110" align="right">
          <template #default="{ row }">{{ formatNumber(row.requests) }}</template>
        </el-table-column>
        <el-table-column label="Workers" width="100" align="right">
          <template #default="{ row }">{{ formatNumber(row.workers_requests) }}</template>
        </el-table-column>
        <el-table-column label="Pages" width="100" align="right">
          <template #default="{ row }">{{ formatNumber(row.pages_requests) }}</template>
        </el-table-column>
        <el-table-column label="D1" width="90" align="right">
          <template #default="{ row }">{{ formatNumber(d1Queries(row)) }}</template>
        </el-table-column>
        <el-table-column label="KV" width="90" align="right">
          <template #default="{ row }">{{ formatNumber(row.kv_requests) }}</template>
        </el-table-column>
        <el-table-column label="R2" width="90" align="right">
          <template #default="{ row }">{{ formatNumber(row.r2_requests) }}</template>
        </el-table-column>
        <el-table-column label="子请求" width="120" align="right">
          <template #default="{ row }">{{ formatNumber(row.subrequests) }}</template>
        </el-table-column>
        <el-table-column label="错误" width="90" align="right">
          <template #default="{ row }">{{ formatNumber(row.errors) }}</template>
        </el-table-column>
        <el-table-column label="使用率" width="100" align="right">
          <template #default="{ row }">{{ formatPercent(row.usage_percent) }}</template>
        </el-table-column>
        <el-table-column label="采集时间" prop="collected_at" width="180">
          <template #default="{ row }">{{ formatBeijingTime(row.collected_at) }}</template>
        </el-table-column>
      </el-table>
    </div>

    <div class="section-card">
      <h3>最近巡检</h3>
      <el-table :data="store.summary?.recent_runs ?? []" stripe style="width: 100%" max-height="400" empty-text="暂无巡检记录">
        <el-table-column
          v-for="col in recentRunColumns" :key="col.prop"
          :label="col.label" :prop="col.prop" :width="col.width"
          :min-width="(col as any).minWidth" :show-overflow-tooltip="(col as any).showOverflowTooltip"
        >
          <template v-if="col.slot === 'status'" #default="{ row }">
            <StatusBadge :status="runBadgeStatus(row.status)" />
          </template>
          <template v-else-if="col.slot === 'duration'" #default="{ row }">
            {{ formatDuration(row.duration_ms) }}
          </template>
          <template v-else-if="col.slot === 'time'" #default="{ row }">
            {{ formatBeijingTime(row[col.prop]) }}
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.dashboard { display: flex; flex-direction: column; gap: 20px; }
.topbar { display: flex; align-items: center; justify-content: space-between; }
.topbar h2 { font-size: 20px; font-weight: 600; }
.topbar-actions { display: flex; gap: 8px; }

.cards-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 14px;
}
.stat-card {
  background: var(--bg-card); border-radius: var(--radius-lg);
  padding: 18px 20px; box-shadow: var(--shadow-md);
  transition: transform var(--transition-fast), box-shadow var(--transition-fast);
}
.stat-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg); }
.stat-label { font-size: 13px; color: var(--text-secondary); margin-bottom: 6px; }
.stat-value { font-size: 28px; font-weight: 800; line-height: 1.2; font-variant-numeric: tabular-nums; }

.alert-banner { margin-bottom: 4px; }

.section-card {
  background: var(--bg-card); border-radius: var(--radius-lg);
  padding: 20px; box-shadow: var(--shadow-md);
}
.section-card h3 { font-size: 15px; font-weight: 600; margin-bottom: 16px; color: var(--text-primary); }
.usage-chart { width: 100%; height: 280px; }
.usage-table { margin-top: 12px; }
</style>
