<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import VChart from 'vue-echarts'
import '@/utils/echarts'
import api from '@/api'
import { formatBeijingTime } from '@/utils/time'
import type { UsageAccountDaily } from '@/api/types'

const accountUsage = ref<UsageAccountDaily[]>([])
const loading = ref(false)

async function loadUsage() {
  loading.value = true
  try {
    accountUsage.value = (await api.get<UsageAccountDaily[]>('/usage/accounts')).data
  } finally {
    loading.value = false
  }
}

async function runUsageSync() {
  await api.post('/sync/run-now', { kind: 'usage_sync' }, { headers: { 'X-Silent': '1' } })
}

const currentUsageDate = computed(() => accountUsage.value[0]?.date_utc || '')

const currentAccountUsage = computed(() => {
  if (!currentUsageDate.value) return []
  return accountUsage.value.filter(row => row.date_utc === currentUsageDate.value)
})

const usageBarOption = computed(() => {
  if (!currentAccountUsage.value.length) {
    return {
      graphic: { type: 'text', left: 'center', top: 'center', style: { text: '暂无用量数据', fontSize: 14, fill: '#94a3b8' } },
    }
  }
  const latest = currentAccountUsage.value.slice(0, 10)
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 80, right: 20, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: latest.map(u => u.account_alias), axisLabel: { fontSize: 12 } },
    yAxis: { type: 'value', axisLabel: { fontSize: 12 } },
    series: [{
      type: 'bar',
      data: latest.map(u => ({
        value: u.requests,
        itemStyle: {
          color: u.usage_percent >= 96 ? '#dc2626' : u.usage_percent >= 80 ? '#d97706' : '#2563eb',
          borderRadius: [4, 4, 0, 0],
        },
      })),
      barMaxWidth: 48,
    }],
  }
})

function usageColor(pct: number): 'exception' | 'warning' | undefined {
  if (pct >= 96) return 'exception'
  if (pct >= 80) return 'warning'
  return undefined
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
      <h3>用量趋势</h3>
      <v-chart class="usage-chart" :option="usageBarOption" autoresize />
    </div>

    <div class="section-card">
      <h3>账号实时</h3>
      <el-table :data="currentAccountUsage" stripe max-height="400" empty-text="暂无用量数据" style="width: 100%">
        <el-table-column label="账号" prop="account_alias" width="120" />
        <el-table-column label="日期" prop="date_utc" width="120" />
        <el-table-column label="请求" prop="requests" width="100" align="right" />
        <el-table-column label="子请求" prop="subrequests" width="100" align="right" />
        <el-table-column label="错误" prop="errors" width="80" align="right" />
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

.usage-chart {
  width: 100%;
  height: 280px;
}
</style>
