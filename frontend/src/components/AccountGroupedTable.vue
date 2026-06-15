<script setup lang="ts" generic="T extends { account_alias?: string | null; account_db_id?: number | string | null }">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  data: T[]
  loading?: boolean
  emptyText?: string
  accountLabel?: string
  itemLabel?: string
  tableSize?: '' | 'default' | 'small' | 'large'
  maxHeight?: number | string
}>(), {
  loading: false,
  emptyText: '暂无数据',
  accountLabel: '账号',
  itemLabel: '条',
  tableSize: 'default',
})

const groups = computed(() => {
  const grouped = new Map<string, { key: string; account: string; items: T[] }>()

  for (const item of props.data) {
    const account = item.account_alias || '未设置账号'
    const key = String(item.account_db_id ?? account)

    if (!grouped.has(key)) {
      grouped.set(key, { key, account, items: [] })
    }

    grouped.get(key)!.items.push(item)
  }

  return Array.from(grouped.values()).sort((a, b) =>
    a.account.localeCompare(b.account, 'zh-Hans-CN'),
  )
})
</script>

<template>
  <div class="account-grouped-table" v-loading="loading">
    <el-empty
      v-if="!loading && data.length === 0"
      :description="emptyText"
      :image-size="96"
    />

    <div v-else class="account-groups">
      <section v-for="group in groups" :key="group.key" class="account-group">
        <div class="account-group__header">
          <div class="account-group__identity">
            <span class="account-group__label">{{ accountLabel }}</span>
            <span class="account-group__name">{{ group.account }}</span>
          </div>
          <el-tag size="small" type="info" effect="plain">
            {{ group.items.length }} {{ itemLabel }}
          </el-tag>
        </div>

        <el-table
          :data="group.items"
          :size="tableSize"
          :max-height="maxHeight"
          stripe
          style="width: 100%"
        >
          <slot />
        </el-table>
      </section>
    </div>
  </div>
</template>

<style scoped>
.account-grouped-table {
  min-height: 120px;
}

.account-groups {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.account-group {
  overflow: hidden;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.account-group__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  background: linear-gradient(180deg, rgba(37, 99, 235, 0.08), rgba(37, 99, 235, 0.02));
  border-bottom: 1px solid var(--border);
}

.account-group__identity {
  display: flex;
  align-items: baseline;
  gap: 10px;
  min-width: 0;
}

.account-group__label {
  flex: none;
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 600;
}

.account-group__name {
  overflow: hidden;
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
