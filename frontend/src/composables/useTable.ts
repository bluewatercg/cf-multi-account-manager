import { ref } from 'vue'
import api, { invalidateApiCache } from '@/api'

/**
 * 通用表格数据获取 composable
 * @param url API 地址
 */
export function useTable<T>(url: string) {
  const data = ref<T[]>([])
  const loading = ref(false)

  /**
   * @param force 为 true 时绕过 API 缓存强制重新拉取（刷新按钮用）
   */
  async function fetchData(force = false) {
    if (force) invalidateApiCache(url)
    loading.value = true
    try {
      data.value = (await api.get<T[]>(url)).data
    } finally {
      loading.value = false
    }
  }

  return { data, loading, fetchData }
}
