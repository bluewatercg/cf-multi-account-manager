<script setup lang="ts">
defineProps<{
  description?: string
  image?: string
}>()
</script>

<template>
  <div class="empty-state">
    <el-empty :description="description || '暂无数据'" :image-size="120">
      <template v-if="$slots.default">
        <slot />
      </template>
    </el-empty>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}
</style>
