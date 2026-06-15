import axios from 'axios'
import { ElMessage, ElLoading } from 'element-plus'

type LoadingInstance = ReturnType<typeof ElLoading.service>

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

/** 全局 loading 管理 — 300ms 延迟避免闪烁 */
let pending = 0
let loadingInst: LoadingInstance | null = null
let timer: ReturnType<typeof setTimeout> | null = null

function showLoading() {
  if (pending === 0) {
    timer = setTimeout(() => {
      loadingInst = ElLoading.service({ lock: false, text: '加载中...', background: 'rgba(0,0,0,.05)' })
    }, 300)
  }
  pending++
}

function hideLoading() {
  pending = Math.max(0, pending - 1)
  if (pending === 0) {
    if (timer) { clearTimeout(timer); timer = null }
    loadingInst?.close()
    loadingInst = null
  }
}

api.interceptors.request.use((config) => {
  if (!config.headers['X-Silent']) showLoading()
  return config
})

api.interceptors.response.use(
  (res) => { if (!res.config.headers['X-Silent']) hideLoading(); return res },
  (err) => {
    if (!err.config?.headers?.['X-Silent']) hideLoading()
    if (err.response) {
      const s = err.response.status
      if (s === 404) ElMessage.error('资源不存在')
      else if (s >= 500) ElMessage.error('服务器错误，请稍后重试')
      else ElMessage.error(err.response.data?.error || `请求失败 (${s})`)
    } else if (err.message?.includes('timeout')) {
      ElMessage.error('请求超时')
    } else if (err.message?.includes('Network')) {
      ElMessage.error('网络连接失败，请检查代理/VPN/防火墙')
    } else {
      ElMessage.error(err.message || '请求失败')
    }
    return Promise.reject(err)
  },
)

export default api
