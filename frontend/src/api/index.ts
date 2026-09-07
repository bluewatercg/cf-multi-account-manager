import axios, { getAdapter } from 'axios'
import type { AxiosAdapter, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { ElMessage, ElLoading } from 'element-plus'

type LoadingInstance = ReturnType<typeof ElLoading.service>

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

/* ------------------------------------------------------------------ *
 * GET 响应缓存
 *
 * 巡检数据只会在巡检后变化，但原先每次切换页面都会重新拉取全量列表
 * （DNS 列表单就 250KB）。这里对 GET 做短 TTL 缓存，切换页面直接命中
 * 内存；巡检或手动刷新时显式失效。
 * ------------------------------------------------------------------ */
const CACHE_TTL = Number(import.meta.env.VITE_API_CACHE_TTL ?? 30_000)
const cacheStore = new Map<string, { at: number; data: unknown }>()

function cacheKey(config: InternalAxiosRequestConfig): string {
  const params = config.params ? JSON.stringify(config.params) : ''
  return `${config.baseURL ?? ''}${config.url ?? ''}?${params}`
}

/** 失效指定前缀（或全部）的缓存条目。巡检、手动刷新时调用。 */
export function invalidateApiCache(prefix?: string) {
  if (!prefix) {
    cacheStore.clear()
    return
  }
  for (const key of cacheStore.keys()) {
    if (key.includes(prefix)) cacheStore.delete(key)
  }
}

// 包一层 adapter 实现透明缓存：GET 命中则直接返回，否则请求后写入缓存。
// 注意：axios v1 的 defaults.adapter 是适配器「名称数组」（如 ['xhr','http','fetch']），
// 不是函数——必须用 getAdapter() 解析成真实实现后才能调用，否则会抛
// “... is not a function”，所有请求都会失败。
const baseAdapter = getAdapter(api.defaults.adapter)
api.defaults.adapter = async (config) => {
  const method = (config.method ?? 'get').toLowerCase()
  const key = cacheKey(config)
  if (method !== 'get' || (config as any).__noCache || !baseAdapter) {
    return baseAdapter!(config)
  }
  const hit = cacheStore.get(key)
  if (hit && Date.now() - hit.at < CACHE_TTL) {
    return {
      data: hit.data,
      status: 200,
      statusText: 'OK (cache)',
      headers: {},
      config,
    } as AxiosResponse
  }
  const res = await baseAdapter(config)
  if (res.status === 200) cacheStore.set(key, { at: Date.now(), data: res.data })
  return res
}

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
  // 带 X-No-Cache 的请求穿透缓存
  if (config.headers['X-No-Cache'] === '1' || (config.headers as any)['x-no-cache'] === '1') {
    ;(config as any).__noCache = true
  }
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
