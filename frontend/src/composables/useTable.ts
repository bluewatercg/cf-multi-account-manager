import { ref } from 'vue'
import api from '@/api'

/**
 * 通用表格数据获取 composable
 * @param url API 地址
 */
export function useTable<T>(url: string) {
  const data = ref<T[]>([])
  const loading = ref(false)

  async function fetchData() {
    loading.value = true
    try {
      data.value = (await api.get<T[]>(url)).data
    } finally {
      loading.value = false
    }
  }

  return { data, loading, fetchData }
}
