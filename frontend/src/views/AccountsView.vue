<script setup lang="ts">
import { ref, onMounted, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, CircleCheckFilled, CircleCloseFilled } from '@element-plus/icons-vue'
import { useAccountStore } from '@/stores/account'
import StatusBadge from '@/components/StatusBadge.vue'
import { formatBeijingTime } from '@/utils/time'
import type { Account } from '@/api/types'
import type { FormInstance, FormRules } from 'element-plus'

const store = useAccountStore()

// 表单状态
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()
const formLoading = ref(false)
const verifyStatus = ref<'idle' | 'verifying' | 'ok' | 'error'>('idle')
const verifyError = ref('')

const form = reactive({
  id: 0,
  alias: '',
  account_id: '',
  email_hint: '',
  token: '',
  daily_quota: 100000,
  enabled: true,
  notes: '',
})

const rules: FormRules = {
  alias: [{ required: true, message: '请输入别名', trigger: 'blur' }],
  account_id: [{ required: true, message: '请输入 Account ID', trigger: 'blur' }],
  token: [{
    validator: (_rule: any, value: string, callback: any) => {
      if (!isEdit.value && !value) callback(new Error('新增时必填'))
      else callback()
    },
    trigger: 'blur',
  }],
  daily_quota: [{ required: true, message: '请输入每日额度', trigger: 'blur' }],
}

function openCreate() {
  isEdit.value = false
  verifyStatus.value = 'idle'
  verifyError.value = ''
  Object.assign(form, { id: 0, alias: '', account_id: '', email_hint: '', token: '', daily_quota: 100000, enabled: true, notes: '' })
  dialogVisible.value = true
}

function openEdit(row: Account) {
  isEdit.value = true
  verifyStatus.value = 'idle'
  verifyError.value = ''
  Object.assign(form, {
    id: row.id,
    alias: row.alias,
    account_id: row.account_id,
    email_hint: row.email_hint || '',
    token: '',
    daily_quota: row.daily_quota,
    enabled: !!row.enabled,
    notes: row.notes || '',
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  formLoading.value = true
  verifyStatus.value = 'verifying'
  verifyError.value = ''
  try {
    let res: { ok: boolean; token_status?: string } | undefined
    if (isEdit.value) {
      const payload: Record<string, any> = {
        alias: form.alias,
        account_id: form.account_id,
        email_hint: form.email_hint,
        daily_quota: form.daily_quota,
        enabled: form.enabled,
        notes: form.notes,
      }
      if (form.token) payload.token = form.token
      res = await store.updateAccount(form.id, payload)
    } else {
      res = await store.createAccount({
        alias: form.alias,
        account_id: form.account_id,
        email_hint: form.email_hint,
        token: form.token,
        daily_quota: form.daily_quota,
        enabled: form.enabled,
        notes: form.notes,
      })
    }
    verifyStatus.value = res?.token_status === 'ok' ? 'ok' : 'error'
    if (verifyStatus.value === 'error') {
      verifyError.value = 'Token 验证未通过，请检查 Account ID 和 Token 是否匹配'
      return
    }
    await new Promise(r => setTimeout(r, 600))
    dialogVisible.value = false
    ElMessage.success(isEdit.value ? '账号更新成功' : '账号创建成功')
  } catch (e: any) {
    verifyStatus.value = 'error'
    verifyError.value = e?.response?.data?.error || e?.message || '保存失败'
  } finally {
    formLoading.value = false
  }
}

async function handleDelete(id: number) {
  await store.deleteAccount(id)
}

async function handleTest(id: number) {
  await store.testToken(id)
}

onMounted(store.fetchAccounts)
</script>

<template>
  <div class="accounts-page">
    <div class="page-topbar">
      <h2>账号 Accounts</h2>
      <div class="topbar-actions">
        <el-button type="primary" @click="openCreate">新增账号</el-button>
        <el-button @click="store.fetchAccounts()">刷新</el-button>
      </div>
    </div>

    <el-table :data="store.accounts" v-loading="store.loading" stripe style="width: 100%" empty-text="暂无账号">
      <el-table-column label="ID" prop="id" width="70" />
      <el-table-column label="启用" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.enabled ? 'success' : 'info'" size="small">{{ row.enabled ? '是' : '否' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="别名" prop="alias" width="130" />
      <el-table-column label="Account ID" prop="account_id" min-width="180" show-overflow-tooltip />
      <el-table-column label="Token 尾号" width="100" align="center">
        <template #default="{ row }">
          <code v-if="row.token_last4">***{{ row.token_last4 }}</code>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>
      <el-table-column label="Token 状态" width="110" align="center">
        <template #default="{ row }">
          <StatusBadge :status="row.token_status" />
        </template>
      </el-table-column>
      <el-table-column label="额度" prop="daily_quota" width="100" align="right" />
      <el-table-column label="最后成功" prop="last_success_sync_at" width="180" show-overflow-tooltip>
        <template #default="{ row }">{{ formatBeijingTime(row.last_success_sync_at) }}</template>
      </el-table-column>
      <el-table-column label="错误" prop="last_error" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          <span v-if="row.last_error" class="error-text">{{ row.last_error }}</span>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right" align="center">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="info" @click="handleTest(row.id)">检测</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑账号' : '新增账号'"
      width="520px"
      destroy-on-close
      @close="formRef?.resetFields()"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" label-position="top">
        <el-form-item label="别名" prop="alias">
          <el-input v-model="form.alias" placeholder="cf-01" />
        </el-form-item>
        <el-form-item label="Account ID" prop="account_id">
          <el-input v-model="form.account_id" placeholder="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" />
        </el-form-item>
        <el-form-item label="Email / 备注">
          <el-input v-model="form.email_hint" placeholder="可选" />
        </el-form-item>
        <el-form-item label="API Token" prop="token">
          <el-input
            v-model="form.token"
            type="password"
            show-password
            :placeholder="isEdit ? '留空表示不修改 Token' : '请输入 API Token'"
          />
        </el-form-item>
        <el-form-item label="每日额度" prop="daily_quota">
          <el-input-number v-model="form.daily_quota" :min="1" :max="10000000" style="width: 100%" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.enabled" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <div class="verify-status">
            <template v-if="verifyStatus === 'verifying'">
              <el-icon class="is-loading spin"><Loading /></el-icon>
              <span class="status-text">正在验证 Token…</span>
            </template>
            <template v-else-if="verifyStatus === 'ok'">
              <el-icon color="#059669"><CircleCheckFilled /></el-icon>
              <span class="status-text success">Token 验证通过</span>
            </template>
            <template v-else-if="verifyStatus === 'error' && verifyError">
              <el-icon color="#dc2626"><CircleCloseFilled /></el-icon>
              <span class="status-text error">{{ verifyError }}</span>
            </template>
          </div>
          <div class="footer-actions">
            <el-button @click="dialogVisible = false">取消</el-button>
            <el-button type="primary" :loading="formLoading" @click="handleSubmit">
              {{ verifyStatus === 'verifying' ? '验证中…' : '保存' }}
            </el-button>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.accounts-page {
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
}

.error-text {
  color: var(--danger);
  font-size: 13px;
}

.muted {
  color: var(--text-muted);
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.verify-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.status-text { color: var(--text-secondary); }
.status-text.success { color: #059669; }
.status-text.error { color: #dc2626; }

.footer-actions {
  display: flex;
  gap: 8px;
}

.spin {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
