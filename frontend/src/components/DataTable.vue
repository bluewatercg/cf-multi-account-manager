<script setup lang="ts" generic="T extends Record<string, any>">
import { computed, ref, watch } from 'vue'

export interface Column<T> {
  label: string
  prop?: string
  width?: number | string
  minWidth?: number | string
  fixed?: 'left' | 'right'
  sortable?: boolean | 'custom'
  showOverflowTooltip?: boolean
  slot?: string
  align?: 'left' | 'center' | 'right'
}

const props = withDefaults(defineProps<{
  data: T[]
  columns: Column<T>[]
  loading?: boolean
  stripe?: boolean
  border?: boolean
  maxHeight?: number | string
  emptyText?: string
  pageSize?: number
  pageSizes?: number[]
  showPagination?: boolean
}>(), {
  loading: false,
  stripe: true,
  border: false,
  emptyText: '暂无数据',
  pageSize: 20,
  pageSizes: () => [20, 50, 100],
  showPagination: true,
})

const currentPage = ref(1)
const size = ref(props.pageSize)

const paginatedData = computed(() => {
  if (!props.showPagination) return props.data
  const start = (currentPage.value - 1) * size.value
  return props.data.slice(start, start + size.value)
})

const total = computed(() => props.data.length)

// 当数据变化时重置到第一页
watch(() => props.data.length, () => { currentPage.value = 1 })
</script>

<template>
  <div class="data-table-wrapper">
    <el-table
      :data="paginatedData"
      v-loading="loading"
      :stripe="stripe"
      :border="border"
      :max-height="maxHeight"
      :empty-text="emptyText"
      style="width: 100%"
    >
      <el-table-column
        v-for="col in columns"
        :key="col.prop || col.label"
        :label="col.label"
        :prop="col.prop"
        :width="col.width"
        :min-width="col.minWidth"
        :fixed="col.fixed"
        :sortable="col.sortable"
        :show-overflow-tooltip="col.showOverflowTooltip"
        :align="col.align"
      >
        <template v-if="col.slot" #default="scope">
          <slot :name="col.slot" v-bind="scope" />
        </template>
      </el-table-column>
    </el-table>

    <div v-if="showPagination && total > 0" class="pagination-bar">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="size"
        :total="total"
        :page-sizes="pageSizes"
        layout="total, prev, pager, next, sizes"
        background
      />
    </div>
  </div>
</template>

<style scoped>
.data-table-wrapper {
  display: flex;
  flex-direction: column;
}

.pagination-bar {
  display: flex;
  justify-content: flex-end;
  padding: 16px 0 4px;
}
</style>
