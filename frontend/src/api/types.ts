/** 账号 */
export interface Account {
  id: number
  alias: string
  account_id: string
  email_hint: string | null
  token_last4: string | null
  token_status: 'ok' | 'error' | 'unknown'
  daily_quota: number
  enabled: boolean
  notes: string | null
  last_success_sync_at: string | null
  last_failed_sync_at: string | null
  last_error: string | null
  created_at: string
  updated_at: string
}

/** Worker */
export interface Worker {
  id: number
  account_db_id: number
  script_name: string
  modified_on: string
  raw_json: string | null
  last_seen_at: string | null
  created_at: string | null
  updated_at: string | null
  account_alias: string
  custom_domains?: string | null
  custom_domains_count?: number
}

/** Pages 项目 */
export interface PagesProject {
  id: number
  account_db_id: number
  project_name: string
  subdomain: string
  production_branch: string
  latest_deployment_status: string | null
  raw_json: string | null
  last_seen_at: string | null
  created_at: string | null
  updated_at: string | null
  account_alias: string
  domains_count?: number
  custom_domains?: string | null
}

/** Pages 自定义域名 */
export interface PagesDomain {
  name: string
  status: string | null
  project_name: string
  account_alias: string
  account_db_id?: number
}

/** Zone 域名 */
export interface Zone {
  id: number
  account_db_id: number
  zone_id: string
  name: string
  status: string
  type: string
  raw_json: string | null
  last_seen_at: string | null
  created_at: string | null
  updated_at: string | null
  account_alias: string
  dns_count?: number
  routes_count?: number
}

/** DNS 记录 */
export interface DnsRecord {
  id: number
  account_db_id: number
  zone_db_id: number
  record_id: string
  type: string
  name: string
  content: string
  ttl: number
  proxied: boolean
  raw_json: string | null
  last_seen_at: string | null
  created_at: string | null
  updated_at: string | null
  account_alias: string
  zone_name?: string
}

/** Worker Route */
export interface WorkerRoute {
  id: number
  account_db_id: number
  zone_db_id: number
  route_id: string
  pattern: string
  script_name: string
  raw_json: string | null
  last_seen_at: string | null
  created_at: string | null
  updated_at: string | null
  account_alias: string
  zone_name?: string
}

/** 账号每日用量 */
export interface UsageAccountDaily {
  account_db_id: number
  date_utc: string
  requests: number
  subrequests: number
  errors: number
  usage_percent: number
  quota: number
  collected_at: string
  account_alias: string
}

/** Worker 每日用量 */
export interface UsageWorkerDaily {
  account_db_id: number
  script_name: string
  date_utc: string
  requests: number
  subrequests: number
  errors: number
  cpu_time_p50: number | null
  cpu_time_p99: number | null
  collected_at: string
  account_alias: string
}

/** 巡检任务 */
export interface SyncJob {
  id: number
  name: string
  job_type: string
  enabled: boolean
  schedule_mode: string
  interval_minutes: number
  time_window_start: string
  time_window_end: string
  high_usage_threshold: number
  high_usage_interval_minutes: number
  critical_usage_threshold: number
  critical_interval_minutes: number
  last_run_at: string | null
  created_at: string
  updated_at: string
}

/** 巡检执行记录 */
export interface SyncRun {
  id: number
  account_db_id: number | null
  run_type: string
  status: 'success' | 'partial' | 'failed' | 'running'
  started_at: string
  finished_at: string | null
  duration_ms: number | null
  workers_count: number
  pages_count: number
  zones_count: number
  dns_records_count: number
  routes_count: number
  api_calls_count: number
  error_message: string | null
  raw_summary_json: string | null
  account_alias: string | null
}

/** 告警 */
export interface Alert {
  id: number
  alert_key: string
  account_db_id: number | null
  target_type: string
  target_name: string
  level: 'critical' | 'danger' | 'warning' | 'info'
  title: string
  message: string
  current_value: number | null
  threshold_value: number | null
  status: 'open' | 'resolved'
  first_triggered_at: string | null
  last_triggered_at: string | null
  resolved_at: string | null
  raw_json: string | null
  account_alias?: string
}

/** Dashboard 汇总 */
export interface DashboardSummary {
  accounts: number
  workers: number
  pages: number
  zones: number
  dns_records: number
  routes: number
  today_usage: UsageAccountDaily[]
  open_alerts: Alert[]
  recent_runs: SyncRun[]
}

/** 全局搜索结果 */
export interface SearchResult {
  q: string
  results: {
    workers: Worker[]
    pages: PagesProject[]
    pages_domains: PagesDomain[]
    zones: Zone[]
    dns_records: DnsRecord[]
    routes: WorkerRoute[]
  }
}

/** 网络诊断结果 */
export interface DiagnosticsResult {
  dns: string | null
  https: string | null
  error: string | null
}
