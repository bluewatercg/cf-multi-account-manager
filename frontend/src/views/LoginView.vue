<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/api'
import { Lock } from '@element-plus/icons-vue'
const router = useRouter(), route = useRoute(), password = ref(''), loading = ref(false)
async function login() {
  if (!password.value) return
  loading.value = true
  try { await api.post('/auth/login', { password: password.value }); ElMessage.success('登录成功'); router.replace(String(route.query.redirect || '/dashboard')) }
  catch (e: any) { ElMessage.error(e?.response?.data?.error || '登录失败') }
  finally { loading.value = false }
}
</script>
<template><main class="login-page"><el-card class="login-card"><h1>CF Manager</h1><p>Cloudflare 多账号管理面板</p><el-form @submit.prevent="login"><el-form-item><el-input v-model="password" type="password" show-password autofocus placeholder="请输入管理密码" :prefix-icon="Lock" @keyup.enter="login" /></el-form-item><el-button type="primary" native-type="submit" :loading="loading" style="width:100%">登录</el-button></el-form></el-card></main></template>
<style scoped>.login-page{min-height:100vh;display:grid;place-items:center;background:var(--bg-page)}.login-card{width:min(92vw,380px)}h1{text-align:center;font-size:26px}.login-card p{text-align:center;color:var(--text-secondary);margin:6px 0 24px}</style>
