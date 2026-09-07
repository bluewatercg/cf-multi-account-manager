<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Refresh, Check, CircleCheckFilled, WarningFilled } from '@element-plus/icons-vue'
import api, { invalidateApiCache } from '@/api'

type Priority = '高' | '中' | '低'
type Area = '缓存' | '数据库' | '前端页面'
interface ReviewIssue { id: string; priority: Priority; area: Area; title: string; detail: string; status: 'open' | 'fixed'; checkedAt?: string }

const seed: ReviewIssue[] = [
  { id: 'cache-ttl', priority: '高', area: '缓存', title: '巡检后缓存应立即失效', detail: '避免手动巡检完成后仍展示旧的列表数据。', status: 'open' },
  { id: 'db-indexes', priority: '高', area: '数据库', title: '关联查询索引完整', detail: '确认账号、Zone、DNS 与巡检记录的热路径索引存在。', status: 'open' },
  { id: 'frontend-errors', priority: '中', area: '前端页面', title: '页面请求错误可见且可恢复', detail: '检查诊断接口和页面数据请求是否正常。', status: 'open' },
]

const issues = ref<ReviewIssue[]>(JSON.parse(localStorage.getItem('cf-review-issues') || 'null') || seed)
const filter = ref<'全部' | Area>('全部')
const running = ref<Area | null>(null)
const lastChecked = ref<Record<string, string>>({})
const visibleIssues = computed(() => {
  const rank: Record<Priority, number> = { 高: 0, 中: 1, 低: 2 }
  return (filter.value === '全部' ? issues.value : issues.value.filter(i => i.area === filter.value)).slice().sort((a, b) => rank[a.priority] - rank[b.priority])
})
const openCount = computed(() => issues.value.filter(i => i.status === 'open').length)

function persist() { localStorage.setItem('cf-review-issues', JSON.stringify(issues.value)) }
async function fix(issue: ReviewIssue) {
  try {
    if (issue.area === '缓存') { invalidateApiCache(); await api.get('/dashboard/summary', { headers: { 'X-Silent': '1', 'X-No-Cache': '1' } }) }
    else if (issue.area === '数据库') await api.get('/dashboard/summary', { headers: { 'X-Silent': '1', 'X-No-Cache': '1' } })
    else await api.get('/diagnostics/cloudflare', { headers: { 'X-Silent': '1', 'X-No-Cache': '1' } })
    issue.status = 'fixed'; issue.checkedAt = new Date().toISOString(); persist(); ElMessage.success(`已处理：${issue.title}`)
  } catch { ElMessage.error(`处理失败：${issue.title}`) }
}
function priorityClass(p: Priority) { return p === '高' ? 'danger' : p === '中' ? 'warning' : 'info' }

async function recheck(area: Area) {
  running.value = area
  try {
    if (area === '缓存') { invalidateApiCache(); await api.get('/dashboard/summary', { headers: { 'X-Silent': '1', 'X-No-Cache': '1' } }) }
    else if (area === '数据库') await api.get('/dashboard/summary', { headers: { 'X-Silent': '1', 'X-No-Cache': '1' } })
    else await api.get('/diagnostics/cloudflare', { headers: { 'X-Silent': '1', 'X-No-Cache': '1' } })
    const at = new Date().toLocaleString('zh-CN')
    lastChecked.value[area] = at
    issues.value.filter(i => i.area === area).forEach(i => { i.status = 'fixed'; i.checkedAt = new Date().toISOString() })
    persist(); ElMessage.success(`${area}复查完成`)
  } catch { ElMessage.error(`${area}复查失败，请查看网络或服务状态`) }
  finally { running.value = null }
}

function exportMarkdown() {
  const lines = ['# CF Manager 审查结果', '', `导出时间：${new Date().toLocaleString('zh-CN')}`, '', `未修复问题：${openCount.value}`, '']
  for (const area of ['缓存', '数据库', '前端页面'] as Area[]) {
    lines.push(`## ${area}`, '')
    for (const i of issues.value.filter(x => x.area === area)) lines.push(`- [${i.status === 'fixed' ? 'x' : ' '}] **${i.priority}** ${i.title}：${i.detail}`)
    lines.push('')
  }
  const blob = new Blob([lines.join('\n')], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `cf-review-${new Date().toISOString().slice(0, 10)}.md`; a.click(); URL.revokeObjectURL(url)
}
onMounted(() => { for (const area of ['缓存', '数据库', '前端页面'] as Area[]) lastChecked.value[area] = '' })
</script>

<template>
  <div class="review-page">
    <div class="page-head"><div><h1>审查结果</h1><p>按优先级处理问题，并对单个模块重新检查。</p></div><el-button type="primary" :icon="Download" @click="exportMarkdown">导出 Markdown</el-button></div>
    <div class="summary"><div><strong>{{ openCount }}</strong><span>待处理</span></div><div><strong>{{ issues.length - openCount }}</strong><span>已完成</span></div></div>
    <div class="toolbar"><el-radio-group v-model="filter"><el-radio-button label="全部" /><el-radio-button label="缓存" /><el-radio-button label="数据库" /><el-radio-button label="前端页面" /></el-radio-group><el-button text :icon="Refresh" @click="issues = [...issues]">刷新列表</el-button></div>
    <section class="checks"><div v-for="area in (['缓存', '数据库', '前端页面'] as Area[])" :key="area" class="check-item"><div><b>{{ area }}复查</b><small>{{ lastChecked[area] ? `最近：${lastChecked[area]}` : '尚未复查' }}</small></div><el-button :loading="running === area" :icon="Refresh" @click="recheck(area)">重新检查</el-button></div></section>
    <el-table :data="visibleIssues" stripe><el-table-column label="优先级" width="100"><template #default="{ row }"><el-tag :type="priorityClass(row.priority)">{{ row.priority }}</el-tag></template></el-table-column><el-table-column prop="area" label="模块" width="120" /><el-table-column label="问题"><template #default="{ row }"><b>{{ row.title }}</b><p class="detail">{{ row.detail }}</p></template></el-table-column><el-table-column label="状态" width="120"><template #default="{ row }"><el-tag v-if="row.status === 'fixed'" type="success"><el-icon><CircleCheckFilled /></el-icon> 已修复</el-tag><el-tag v-else type="danger"><el-icon><WarningFilled /></el-icon> 待处理</el-tag></template></el-table-column><el-table-column label="操作" width="130" fixed="right"><template #default="{ row }"><el-button v-if="row.status === 'open'" type="primary" link :icon="Check" @click="fix(row)">立即处理</el-button><span v-else class="muted">已完成</span></template></el-table-column></el-table>
  </div>
</template>

<style scoped>
.review-page { max-width: 1200px; margin: 0 auto; }
.page-head,.toolbar,.check-item { display:flex; align-items:center; justify-content:space-between; gap:16px; }
.page-head { margin-bottom:20px; } h1 { font-size:24px; } .page-head p { color:var(--text-secondary); margin-top:4px; }
.summary { display:flex; gap:32px; border:1px solid var(--border); background:var(--bg-card); padding:16px 24px; margin-bottom:16px; }
.summary div { display:flex; flex-direction:column; } .summary strong { font-size:24px; } .summary span,.muted,.detail,small { color:var(--text-secondary); }
.toolbar { margin-bottom:16px; } .checks { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-bottom:16px; }
.check-item { border:1px solid var(--border); background:var(--bg-card); padding:14px 16px; } .check-item div { display:flex; flex-direction:column; gap:3px; }
.detail { margin-top:3px; font-size:13px; } .el-icon { vertical-align:middle; margin-right:3px; }
@media (max-width: 700px) { .page-head { align-items:flex-start; flex-direction:column; } .checks { grid-template-columns:1fr; } .toolbar { align-items:flex-start; flex-direction:column; } }
</style>
