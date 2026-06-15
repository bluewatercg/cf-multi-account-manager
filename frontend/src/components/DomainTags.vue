<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  value?: string | null
  emptyText?: string
  maxVisible?: number
}>(), {
  emptyText: '未绑定',
  maxVisible: 3,
})

const domains = computed(() => {
  if (!props.value) return []

  return props.value
    .split(/\r?\n|,/)
    .map((item) => item.trim())
    .filter(Boolean)
})

const visibleDomains = computed(() => domains.value.slice(0, props.maxVisible))
const hiddenCount = computed(() => Math.max(domains.value.length - props.maxVisible, 0))
</script>

<template>
  <div v-if="domains.length" class="domain-tags">
    <el-tag
      v-for="domain in visibleDomains"
      :key="domain"
      size="small"
      type="info"
      effect="plain"
      round
    >
      {{ domain }}
    </el-tag>
    <el-tooltip v-if="hiddenCount" placement="top">
      <template #content>
        <div class="domain-tags__tooltip">
          <div v-for="domain in domains" :key="domain">{{ domain }}</div>
        </div>
      </template>
      <el-tag size="small" type="info" effect="plain" round>
        +{{ hiddenCount }}
      </el-tag>
    </el-tooltip>
  </div>
  <span v-else class="domain-tags__empty">{{ emptyText }}</span>
</template>

<style scoped>
.domain-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  min-width: 0;
}

.domain-tags :deep(.el-tag) {
  max-width: 220px;
}

.domain-tags :deep(.el-tag__content) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.domain-tags__empty {
  color: var(--text-muted);
  font-size: 12px;
}

.domain-tags__tooltip {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 360px;
}
</style>
