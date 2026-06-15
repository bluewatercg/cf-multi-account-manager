<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import '@/utils/echarts'
import api from '@/api'
import AccountGroupedTable from '@/components/AccountGroupedTable.vue'
import DomainTags from '@/components/DomainTags.vue'
import { formatBeijingTime } from '@/utils/time'
import type { SearchResult } from '@/api/types'

type AccountGroupedSearchItem = {
  account_alias?: string | null
  account_db_id?: number | string | null
}

const router = useRouter()
const query = ref('')
const result = ref<SearchResult | null>(null)
const loading = ref(false)

async function doSearch() {
  const q = query.value.trim()
  if (!q) return
  loading.value = true
  try {
    result.value = (await api.get<SearchResult>('/search', { params: { q } })).data
  } finally {
    loading.value = false
  }
}

function navigateTo(path: string) {
  router.push(path)
}

function isAccountGroupedKey(key: string | number) {
  return ['workers', 'pages', 'pages_domains', 'zones', 'dns_records', 'routes'].includes(String(key))
}

function resultItemLabel(key: string | number) {
  const labels: Record<string, string> = {
    workers: 'Workers',
    pages: 'Pages',
    pages_domains: '域名',
    zones: 'Zones',
    dns_records: 'DNS',
    routes: 'Routes',
  }

  return labels[String(key)] || '条'
}

function accountGroupedItems(items: unknown[]) {
  return items as AccountGroupedSearchItem[]
}
</script>

<template>
  <div class="search-page">
    <h2>全局搜索</h2>

    <div class="search-box">
      <el-input
        v-model="query"
        placeholder="输入域名 / Worker / Pages / DNS / Route"
        size="large"
        clearable
        @keyup.enter="doSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-button type="primary" size="large" :loading="loading" @click="doSearch">搜索</el-button>
    </div>

    <div v-if="result" class="search-results">
      <template v-for="(items, key) in result.results" :key="key">
        <div v-if="items && items.length" class="result-group">
          <div class="group-header">
            <h3>{{ key }} <el-tag size="small" type="info">{{ items.length }}</el-tag></h3>
          </div>
          <AccountGroupedTable
            v-if="isAccountGroupedKey(key)"
            :data="accountGroupedItems(items)"
            :item-label="resultItemLabel(key)"
            table-size="small"
          >
            <template v-if="key === 'workers'">
              <el-table-column label="Worker" prop="script_name" />
              <el-table-column label="自定义域名/路由" min-width="240">
                <template #default="{ row }">
                  <DomainTags :value="row.custom_domains" />
                </template>
              </el-table-column>
              <el-table-column label="修改时间" prop="modified_on" width="180">
                <template #default="{ row }">{{ formatBeijingTime(row.modified_on) }}</template>
              </el-table-column>
            </template>
            <template v-else-if="key === 'zones'">
              <el-table-column label="Zone" prop="name" />
              <el-table-column label="状态" prop="status" width="120" />
            </template>
            <template v-else-if="key === 'dns_records'">
              <el-table-column label="类型" prop="type" width="80" />
              <el-table-column label="名称" prop="name" />
              <el-table-column label="内容" prop="content" show-overflow-tooltip />
              <el-table-column label="Zone" prop="zone_name" width="150" />
            </template>
            <template v-else-if="key === 'routes'">
              <el-table-column label="Pattern" prop="pattern" />
              <el-table-column label="Script" prop="script_name" width="150" />
              <el-table-column label="Zone" prop="zone_name" width="150" />
            </template>
            <template v-else-if="key === 'pages'">
              <el-table-column label="项目" prop="project_name" />
              <el-table-column label="subdomain" prop="subdomain" width="150" />
              <el-table-column label="自定义域名" min-width="220">
                <template #default="{ row }">
                  <DomainTags :value="row.custom_domains" />
                </template>
              </el-table-column>
            </template>
            <template v-else-if="key === 'pages_domains'">
              <el-table-column label="域名" prop="name" min-width="220" />
              <el-table-column label="项目" prop="project_name" min-width="160" />
              <el-table-column label="状态" prop="status" width="120" />
            </template>
          </AccountGroupedTable>

          <el-table v-else :data="items" stripe size="small" style="width: 100%">
            <el-table-column
              v-for="col in Object.keys(items[0] || {})"
              :key="col"
              :label="col"
              :prop="col"
            />
          </el-table>
        </div>
      </template>

      <el-empty
        v-if="!Object.values(result.results).some(arr => arr && arr.length)"
        description="无搜索结果"
        :image-size="100"
      />
    </div>
  </div>
</template>

<style scoped>
.search-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.search-page h2 {
  font-size: 20px;
  font-weight: 600;
}

.search-box {
  display: flex;
  gap: 12px;
}

.search-box .el-input {
  flex: 1;
}

.result-group {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px 20px;
  box-shadow: var(--shadow-sm);
}

.group-header {
  margin-bottom: 12px;
}

.group-header h3 {
  font-size: 15px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
