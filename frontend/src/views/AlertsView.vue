<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Check, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/api'
import { formatBeijingTime } from '@/utils/time'
import type { Alert } from '@/api/types'

const alerts = ref<Alert[]>([])
const loading = ref(false)
const resolvingId = ref<number | null>(null)

async function loadAlerts() {
  loading.value = true
  try {
    alerts.value = (await api.get<Alert[]>('/alerts')).data
  } finally {
    loading.value = false
  }
}

const levelConfig: Record<string, { type: 'danger' | 'warning' | 'info' | 'success'; label: string; icon: string }> = {
  critical: { type: 'danger', label: '严重', icon: '🔴' },
  danger: { type: 'danger', label: '危险', icon: '🟠' },
  warning: { type: 'warning', label: '警告', icon: '🟡' },
  info: { type: 'info', label: '信息', icon: '🔵' },
}
const levelRank: Record<string, number> = {
  critical: 0,
  danger: 1,
  warning: 2,
  info: 3,
}

const statusConfig: Record<string, { type: 'danger' | 'success' | 'info'; label: string }> = {
  open: { type: 'danger', label: '未处理' },
  resolved: { type: 'success', label: '已处理' },
}

const levelFilters = Object.entries(levelConfig).map(([value, config]) => ({ text: config.label, value }))
const statusFilters = computed(() => {
  const values = [...new Set(alerts.value.map(alertStatus).filter(Boolean))]
  return values.sort((a, b) => a.localeCompare(b)).map((value) => ({
    text: statusConfig[value]?.label || (value === 'unknown' ? '-' : value),
    value,
  }))
})
const accountFilters = computed(() => {
  const names = [...new Set(alerts.value.map(alertAccount).filter(Boolean))]
  return names.sort((a, b) => a.localeCompare(b)).map((value) => ({ text: value, value }))
})
const targetFilters = computed(() => {
  const names = [...new Set(alerts.value.map(alertTarget).filter(Boolean))]
  return names.sort((a, b) => a.localeCompare(b)).map((value) => ({ text: value, value }))
})
const titleFilters = computed(() => {
  const names = [...new Set(alerts.value.map(alertTitle).filter(Boolean))]
  return names.sort((a, b) => a.localeCompare(b)).map((value) => ({ text: value, value }))
})
const messageFilters = computed(() => {
  const names = [...new Set(alerts.value.map(alertMessage).filter(Boolean))]
  return names.sort((a, b) => a.localeCompare(b)).map((value) => ({ text: value, value }))
})
const triggeredTimeFilters = computed(() => {
  const values = [...new Set(alerts.value.map(alertTriggeredTime).filter(Boolean))]
  return values.sort((a, b) => b.localeCompare(a)).map((value) => ({ text: value, value }))
})

function alertAccount(row: Alert) {
  return row.account_alias || (row.target_type === 'account' ? row.target_name : '') || '-'
}

function alertTarget(row: Alert) {
  return row.target_name || '-'
}

function alertTitle(row: Alert) {
  return row.title || '-'
}

function alertMessage(row: Alert) {
  return row.message || '-'
}

function alertLevel(row: Alert): string {
  return row.level || 'info'
}

function alertLevelConfig(row: Alert) {
  return levelConfig[alertLevel(row)] || levelConfig.info
}

function alertStatus(row: Alert): string {
  return row.status || 'unknown'
}

function alertStatusConfig(row: Alert) {
  const status = alertStatus(row)
  return statusConfig[status] || { type: 'info' as const, label: status === 'unknown' ? '-' : status }
}

function alertTriggeredTime(row: Alert) {
  return formatBeijingTime(row.last_triggered_at)
}

function alertTimeValue(value: string | null | undefined) {
  if (!value) return 0
  const time = new Date(value).getTime()
  return Number.isNaN(time) ? 0 : time
}

function filterLevel(value: string, row: Alert) {
  return alertLevel(row) === value
}

function filterStatus(value: string, row: Alert) {
  return alertStatus(row) === value
}

function filterAccount(value: string, row: Alert) {
  return alertAccount(row) === value
}

function filterTarget(value: string, row: Alert) {
  return alertTarget(row) === value
}

function filterTitle(value: string, row: Alert) {
  return alertTitle(row) === value
}

function filterMessage(value: string, row: Alert) {
  return alertMessage(row) === value
}

function filterTriggeredTime(value: string, row: Alert) {
  return alertTriggeredTime(row) === value
}

function sortTriggeredTime(a: Alert, b: Alert) {
  return alertTimeValue(a.last_triggered_at) - alertTimeValue(b.last_triggered_at)
}

function sortLevel(a: Alert, b: Alert) {
  return (levelRank[alertLevel(a)] ?? 99) - (levelRank[alertLevel(b)] ?? 99)
}

async function resolveAlert(row: Alert) {
  resolvingId.value = row.id
  try {
    await api.post(`/alerts/${row.id}/resolve`)
    ElMessage.success('已标记为已处理')
    await loadAlerts()
  } finally {
    resolvingId.value = null
  }
}

onMounted(loadAlerts)
</script>

<template>
  <div class="alerts-page" v-loading="loading">
    <div class="page-topbar">
      <h2>告警 Alerts</h2>
      <el-button :icon="Refresh" @click="loadAlerts">刷新</el-button>
    </div>

    <el-table :data="alerts" row-key="id" stripe empty-text="暂无告警" style="width: 100%" :default-sort="{ prop: 'level', order: 'ascending' }">
      <el-table-column
        label="等级"
        prop="level"
        width="120"
        align="center"
        :filters="levelFilters"
        :filter-method="filterLevel"
        sortable
        :sort-method="sortLevel"
      >
        <template #default="{ row }">
          <el-tag :type="alertLevelConfig(row).type" size="small" effect="dark">
            {{ alertLevelConfig(row).icon }}
            {{ alertLevelConfig(row).label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="账号" width="140" :filters="accountFilters" :filter-method="filterAccount" show-overflow-tooltip>
        <template #default="{ row }">{{ alertAccount(row) }}</template>
      </el-table-column>
      <el-table-column label="目标" width="160" :filters="targetFilters" :filter-method="filterTarget" show-overflow-tooltip>
        <template #default="{ row }">{{ alertTarget(row) }}</template>
      </el-table-column>
      <el-table-column label="标题" min-width="200" :filters="titleFilters" :filter-method="filterTitle" show-overflow-tooltip>
        <template #default="{ row }">{{ alertTitle(row) }}</template>
      </el-table-column>
      <el-table-column label="内容" min-width="250" :filters="messageFilters" :filter-method="filterMessage" show-overflow-tooltip>
        <template #default="{ row }">{{ alertMessage(row) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="110" align="center" :filters="statusFilters" :filter-method="filterStatus">
        <template #default="{ row }">
          <el-tag :type="alertStatusConfig(row).type" size="small">
            {{ alertStatusConfig(row).label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        label="触发时间"
        width="180"
        :filters="triggeredTimeFilters"
        :filter-method="filterTriggeredTime"
        sortable
        :sort-method="sortTriggeredTime"
      >
        <template #default="{ row }">{{ alertTriggeredTime(row) }}</template>
      </el-table-column>
      <el-table-column label="处理时间" prop="resolved_at" width="180">
        <template #default="{ row }">{{ formatBeijingTime(row.resolved_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" fixed="right" width="110" align="center">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'open'"
            type="primary"
            link
            :icon="Check"
            :loading="resolvingId === row.id"
            @click="resolveAlert(row)"
          >
            处理
          </el-button>
          <span v-else class="resolved-text">已处理</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
.alerts-page {
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

.resolved-text {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
</style>
