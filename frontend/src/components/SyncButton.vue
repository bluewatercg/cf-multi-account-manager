<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const props = defineProps<{
  kind: 'full_sync' | 'usage_sync' | 'asset_sync'
  label?: string
}>()

const emit = defineEmits<{
  synced: []
}>()

const loading = ref(false)

async function handleClick() {
  loading.value = true
  try {
    await api.post('/sync/run-now', { kind: props.kind }, { headers: { 'X-Silent': '1' } })
    ElMessage.success('已启动后台巡检，请稍后刷新')
    emit('synced')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <el-button type="primary" :loading="loading" @click="handleClick">
    {{ label || '立即巡检' }}
  </el-button>
</template>
