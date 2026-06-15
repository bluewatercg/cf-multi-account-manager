<script setup lang="ts">
import { onMounted, ref } from 'vue'
import api from '@/api'
import { formatBeijingTime } from '@/utils/time'
import type { Alert } from '@/api/types'

const alerts = ref<Alert[]>([])
const loading = ref(false)

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

onMounted(loadAlerts)
</script>

<template>
  <div class="alerts-page" v-loading="loading">
    <div class="page-topbar">
      <h2>告警 Alerts</h2>
      <el-button @click="loadAlerts">刷新</el-button>
    </div>

    <el-table :data="alerts" stripe empty-text="暂无告警" style="width: 100%">
      <el-table-column label="等级" width="120" align="center">
        <template #default="{ row }">
          <el-tag :type="(levelConfig[row.level] || levelConfig.info).type" size="small" effect="dark">
            {{ (levelConfig[row.level] || levelConfig.info).icon }}
            {{ (levelConfig[row.level] || levelConfig.info).label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="账号" prop="account_alias" width="120" />
      <el-table-column label="目标" prop="target_name" width="150" />
      <el-table-column label="标题" prop="title" min-width="200" show-overflow-tooltip />
      <el-table-column label="内容" prop="message" min-width="250" show-overflow-tooltip />
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.status === 'open' ? 'danger' : 'success'" size="small">
            {{ row.status === 'open' ? '未处理' : '已解决' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="触发时间" prop="last_triggered_at" width="180">
        <template #default="{ row }">{{ formatBeijingTime(row.last_triggered_at) }}</template>
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
</style>
