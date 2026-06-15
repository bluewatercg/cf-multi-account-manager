<script setup lang="ts">
import { computed } from 'vue'
import { Check, Close, QuestionFilled, WarningFilled } from '@element-plus/icons-vue'

const props = defineProps<{
  status: string
}>()

const STATUS_MAP: Record<string, { type: 'success' | 'warning' | 'danger' | 'info'; label: string }> = {
  ok: { type: 'success', label: '正确' },
  partial: { type: 'warning', label: '部分成功' },
  error: { type: 'danger', label: '错误' },
}

const config = computed(() => STATUS_MAP[props.status] ?? { type: 'info' as const, label: '未检测' })

const icon = computed(() => {
  if (props.status === 'ok') return Check
  if (props.status === 'partial') return WarningFilled
  if (props.status === 'error') return Close
  return QuestionFilled
})
</script>

<template>
  <el-tag :type="config.type" size="small" effect="dark" round>
    <el-icon :size="12" style="margin-right: 2px">
      <component :is="icon" />
    </el-icon>
    {{ config.label }}
  </el-tag>
</template>
