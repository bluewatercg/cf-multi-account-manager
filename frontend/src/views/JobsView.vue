<script setup lang="ts">
import { onMounted, ref } from 'vue'
import api from '@/api'
import { formatBeijingTime } from '@/utils/time'
import type { SyncJob, SyncRun } from '@/api/types'

const jobs = ref<SyncJob[]>([])
const runs = ref<SyncRun[]>([])
const loading = ref(false)

function runStatusType(status: SyncRun['status']): 'success' | 'warning' | 'danger' | 'info' {
  if (status === 'success') return 'success'
  if (status === 'partial') return 'warning'
  if (status === 'failed') return 'danger'
  return 'info'
}

function runStatusLabel(status: SyncRun['status']): string {
  if (status === 'success') return '成功'
  if (status === 'partial') return '部分成功'
  if (status === 'failed') return '失败'
  return '运行中'
}

async function loadData() {
  loading.value = true
  try {
    const [j, r] = await Promise.all([
      api.get<SyncJob[]>('/sync/jobs'),
      api.get<SyncRun[]>('/sync/runs'),
    ])
    jobs.value = j.data
    runs.value = r.data
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div class="jobs-page" v-loading="loading">
    <div class="page-topbar">
      <h2>巡检 Jobs</h2>
      <el-button @click="loadData">刷新</el-button>
    </div>

    <div class="section-card">
      <h3>巡检任务配置</h3>
      <el-table :data="jobs" stripe empty-text="暂无巡检任务" style="width: 100%">
        <el-table-column label="ID" prop="id" width="70" />
        <el-table-column label="名称" prop="name" min-width="160" />
        <el-table-column label="类型" prop="job_type" width="120" />
        <el-table-column label="启用" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'" size="small">{{ row.enabled ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="间隔(分)" prop="interval_minutes" width="100" align="center" />
        <el-table-column label="时间段" width="160">
          <template #default="{ row }">
            {{ row.time_window_start }} - {{ row.time_window_end }}
          </template>
        </el-table-column>
        <el-table-column label="最后运行" prop="last_run_at" width="200">
          <template #default="{ row }">{{ formatBeijingTime(row.last_run_at) }}</template>
        </el-table-column>
      </el-table>
    </div>

    <div class="section-card">
      <h3>执行记录</h3>
      <el-table :data="runs" stripe empty-text="暂无执行记录" max-height="500" style="width: 100%">
        <el-table-column label="ID" prop="id" width="70" />
        <el-table-column label="账号" prop="account_alias" width="120" />
        <el-table-column label="类型" prop="run_type" width="120" />
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="runStatusType(row.status)" size="small">
              {{ runStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="开始" prop="started_at" width="180">
          <template #default="{ row }">{{ formatBeijingTime(row.started_at) }}</template>
        </el-table-column>
        <el-table-column label="耗时" width="100" align="right">
          <template #default="{ row }">
            {{ row.duration_ms != null ? (row.duration_ms < 1000 ? row.duration_ms + 'ms' : (row.duration_ms / 1000).toFixed(1) + 's') : '—' }}
          </template>
        </el-table-column>
        <el-table-column label="API 调用" prop="api_calls_count" width="100" align="right" />
        <el-table-column label="错误" prop="error_message" min-width="200" show-overflow-tooltip />
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.jobs-page {
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
</style>
