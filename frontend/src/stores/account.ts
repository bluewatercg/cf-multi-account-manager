import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'
import type { Account } from '@/api/types'

export const useAccountStore = defineStore('account', () => {
  const accounts = ref<Account[]>([])
  const loading = ref(false)

  async function fetchAccounts() {
    loading.value = true
    try {
      accounts.value = (await api.get<Account[]>('/accounts')).data
    } finally {
      loading.value = false
    }
  }

  async function createAccount(d: {
    alias: string; account_id: string; email_hint?: string;
    token: string; daily_quota?: number; enabled?: boolean; notes?: string;
  }) {
    const res = (await api.post<{ ok: boolean; id: number; token_status: string }>('/accounts', d)).data
    await fetchAccounts()
    return res
  }

  async function updateAccount(id: number, d: Partial<Account> & { token?: string }) {
    const res = (await api.put<{ ok: boolean; token_status: string }>(`/accounts/${id}`, d)).data
    await fetchAccounts()
    return res
  }

  async function deleteAccount(id: number) {
    await ElMessageBox.confirm('确定删除这个账号？只删除本地缓存，不会删除 Cloudflare 线上资源。', '确认删除', {
      confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning',
    })
    await api.delete(`/accounts/${id}`)
    ElMessage.success('账号已删除')
    await fetchAccounts()
  }

  async function testToken(id: number) {
    const r = (await api.post(`/accounts/${id}/test-token`, {}, { headers: { 'X-Silent': '1' } })).data
    await fetchAccounts()
    if (r.success) {
      ElMessage.success('Token 检测通过')
    } else {
      ElMessage.error('Token 检测失败：' + (r.error || 'Account Read 检测未通过'))
    }
    return r
  }

  return { accounts, loading, fetchAccounts, createAccount, updateAccount, deleteAccount, testToken }
})
