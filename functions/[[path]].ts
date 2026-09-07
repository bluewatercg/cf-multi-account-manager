type Env = { ADMIN?: string; ASSETS?: { fetch: (request: Request) => Promise<Response> }; cf_manager?: D1Database }
type Account = { id: number; alias: string; account_id: string; token: string; token_last4: string; token_status: string; enabled: number; daily_quota: number; notes: string; created_at: string; updated_at: string; last_error: string | null }

const state = globalThis as typeof globalThis & { __cfm?: { accounts: Account[]; nextId: number; resources: Record<string, any[]>; runs: any[]; db?: D1Database } }
if (!state.__cfm) state.__cfm = { accounts: [], nextId: 1, resources: { workers: [], pages: [], zones: [], 'dns-records': [], routes: [], 'usage/accounts': [], 'usage/workers': [], alerts: [] }, runs: [] }

function json(data: unknown, status = 200, headers: Record<string, string> = {}) {
  return new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', ...headers } })
}
function cookie(request: Request, name: string) {
  return (request.headers.get('Cookie') || '').split(';').map(v => v.trim()).find(v => v.startsWith(`${name}=`))?.slice(name.length + 1)
}
function authed(request: Request, env: Env) {
  return !!env.ADMIN && cookie(request, 'cfm_auth') === btoa(env.ADMIN).replace(/=/g, '')
}
function tokenOf(request: Request) { return request.headers.get('Authorization')?.replace(/^Bearer\s+/i, '') || '' }
async function body(request: Request) { try { return await request.json() as Record<string, any> } catch { return {} } }
function publicAccount(account: Account) { const { token, ...safe } = account; return safe }
async function cfGet(path: string, token: string, query = '') {
  const response = await fetch(`https://api.cloudflare.com/client/v4${path}${query}`, { headers: { Authorization: `Bearer ${token}`, Accept: 'application/json' } })
  const data = await response.json() as any
  if (!response.ok || data.success === false) throw new Error(data.errors?.[0]?.message || `Cloudflare HTTP ${response.status}`)
  return Array.isArray(data.result) ? data.result : []
}
async function syncAccount(account: Account, store: NonNullable<typeof state.__cfm>) {
  const prefix = { account_db_id: account.id, account_alias: account.alias }
  const warnings: string[] = []
  const collect = async (key: string, path: string, replace = true) => { try { const rows = await cfGet(path, account.token); const stamped = rows.map((r: any) => ({ ...r, ...(key === 'workers' ? { script_name: r.script_name || r.name || r.id } : {}), ...(key === 'pages' ? { project_name: r.project_name || r.name || r.id } : {}), ...prefix })); store.resources[key] = (replace ? store.resources[key].filter(r => r.account_db_id !== account.id) : store.resources[key]).concat(stamped); if (store.db) { if (replace) await store.db.prepare('DELETE FROM resources WHERE kind=? AND account_db_id=?').bind(key, account.id).run(); const statements = stamped.map((r: any) => store.db!.prepare('INSERT OR REPLACE INTO resources(kind,account_db_id,item_id,payload,updated_at) VALUES(?,?,?,?,?)').bind(key, account.id, String(r.id ?? r.name ?? r.script_name ?? r.project_name ?? JSON.stringify(r)), JSON.stringify(r), new Date().toISOString())); for (let i = 0; i < statements.length; i += 100) await store.db.batch(statements.slice(i, i + 100)); } return rows.length } catch (e) { warnings.push(`${key}: ${String(e)}`); return 0 } }
  const workers = await collect('workers', `/accounts/${encodeURIComponent(account.account_id)}/workers/scripts`)
  const pages = await collect('pages', `/accounts/${encodeURIComponent(account.account_id)}/pages/projects`)
  const zones = await collect('zones', `/zones?account.id=${encodeURIComponent(account.account_id)}`)
  let dns = 0, routes = 0
  for (const key of ['dns-records', 'routes']) { store.resources[key] = store.resources[key].filter(r => r.account_db_id !== account.id); if (store.db) await store.db.prepare('DELETE FROM resources WHERE kind=? AND account_db_id=?').bind(key, account.id).run() }
  for (const zone of store.resources.zones.filter(r => r.account_db_id === account.id)) {
    dns += await collect('dns-records', `/zones/${encodeURIComponent(zone.id)}/dns_records`, false)
    routes += await collect('routes', `/zones/${encodeURIComponent(zone.id)}/workers/routes`, false)
  }
  const usage = { account_db_id: account.id, account_alias: account.alias, date_utc: new Date().toISOString().slice(0, 10), requests: 0, subrequests: 0, errors: 0, workers_requests: 0, workers_subrequests: 0, workers_errors: 0, pages_requests: 0, pages_errors: 0, usage_percent: 0, quota: account.daily_quota, collected_at: new Date().toISOString() }
  store.resources['usage/accounts'] = store.resources['usage/accounts'].filter(r => r.account_db_id !== account.id).concat([usage])
  if (store.db) { await store.db.prepare('DELETE FROM resources WHERE kind=? AND account_db_id=?').bind('usage/accounts', account.id).run(); await store.db.prepare('INSERT OR REPLACE INTO resources(kind,account_db_id,item_id,payload,updated_at) VALUES(?,?,?,?,?)').bind('usage/accounts', account.id, usage.date_utc, JSON.stringify(usage), usage.collected_at).run() }
  account.token_status = warnings.length ? 'error' : 'ok'; account.last_error = warnings.join('; ') || null; account.updated_at = new Date().toISOString()
  return { workers, pages, zones, dns_records: dns, routes, warnings }
}

export const onRequest: PagesFunction<Env> = async ({ request, env, next }) => {
  const url = new URL(request.url), path = url.pathname
  if (!path.startsWith('/api/')) return next()
  if (path === '/api/auth/login' && request.method === 'POST') {
    const input = await body(request)
    if (!env.ADMIN) return json({ error: '未配置 ADMIN 环境变量' }, 503)
    if (String(input.password || '') !== env.ADMIN) return json({ error: '密码错误' }, 401)
    const value = btoa(env.ADMIN).replace(/=/g, '')
    const secure = url.protocol === 'https:' ? '; Secure' : ''
    return json({ ok: true }, 200, { 'Set-Cookie': `cfm_auth=${value}; Path=/; Max-Age=86400; HttpOnly${secure}; SameSite=Lax` })
  }
  if (path === '/api/auth/logout' && request.method === 'POST') return json({ ok: true }, 200, { 'Set-Cookie': 'cfm_auth=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax' })
  if (path === '/api/auth/me') return authed(request, env) ? json({ authenticated: true }) : json({ authenticated: false }, 401)
  if (!authed(request, env) && !tokenOf(request)) return json({ error: '未登录' }, 401)

  const store = state.__cfm!
  if (env.cf_manager) {
    store.db = env.cf_manager
    const result = await env.cf_manager.prepare('SELECT id,alias,account_id,token,token_last4,token_status,enabled,daily_quota,notes,email_hint,last_error,created_at,updated_at FROM accounts ORDER BY id DESC').all<Account>()
    store.accounts = result.results || []; store.nextId = Math.max(0, ...store.accounts.map(a => a.id)) + 1
    for (const key of Object.keys(store.resources)) store.resources[key] = []
    const resourceRows = await env.cf_manager.prepare('SELECT kind,payload FROM resources').all<{ kind: string; payload: string }>()
    for (const row of resourceRows.results || []) if (store.resources[row.kind]) { try { store.resources[row.kind].push(JSON.parse(row.payload)) } catch { /* skip malformed rows */ } }
  }
  if (path === '/api/accounts' && request.method === 'GET') return json(store.accounts.map(publicAccount))
  if (path === '/api/accounts' && request.method === 'POST') {
    const d = await body(request); if (!d.alias || !d.account_id || !d.token) return json({ error: 'alias/account_id/token required' }, 400)
    const now = new Date().toISOString(), account: Account = { id: store.nextId++, alias: String(d.alias), account_id: String(d.account_id), token: String(d.token), token_last4: String(d.token).slice(-4), token_status: 'unknown', enabled: d.enabled === false ? 0 : 1, daily_quota: Number(d.daily_quota || 100000), notes: String(d.notes || ''), created_at: now, updated_at: now, last_error: null }
    if (env.cf_manager) await env.cf_manager.prepare('INSERT INTO accounts (alias,account_id,token,token_last4,token_status,enabled,daily_quota,notes,email_hint,last_error,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)').bind(account.alias,account.account_id,account.token,account.token_last4,account.token_status,account.enabled,account.daily_quota,account.notes,d.email_hint || '',null,account.created_at,account.updated_at).run()
    else store.accounts.push(account)
    return json({ ok: true, id: account.id, token_status: account.token_status })
  }
  const match = path.match(/^\/api\/accounts\/(\d+)(?:\/(test-token))?$/)
  if (match && request.method === 'POST' && match[2] === 'test-token') {
    const account = store.accounts.find(a => a.id === Number(match[1])); if (!account) return json({ error: 'account not found' }, 404)
    try { const response = await fetch(`https://api.cloudflare.com/client/v4/accounts/${encodeURIComponent(account.account_id)}`, { headers: { Authorization: `Bearer ${account.token}`, Accept: 'application/json' } }); const data = await response.json() as any; account.token_status = response.ok && data.success ? 'ok' : 'error'; account.last_error = account.token_status === 'ok' ? null : (data.errors?.[0]?.message || `HTTP ${response.status}`); account.updated_at = new Date().toISOString(); if (env.cf_manager) await env.cf_manager.prepare('UPDATE accounts SET token_status=?,last_error=?,updated_at=? WHERE id=?').bind(account.token_status,account.last_error,account.updated_at,account.id).run(); return json({ success: account.token_status === 'ok', error: account.last_error }) } catch (e) { account.token_status = 'error'; account.last_error = String(e); return json({ success: false, error: account.last_error }) }
  }
  if (match && request.method === 'PUT') {
    const account = store.accounts.find(a => a.id === Number(match[1])); if (!account) return json({ error: 'account not found' }, 404)
    const d = await body(request); Object.assign(account, { alias: d.alias ?? account.alias, account_id: d.account_id ?? account.account_id, daily_quota: Number(d.daily_quota ?? account.daily_quota), enabled: d.enabled === undefined ? account.enabled : (d.enabled ? 1 : 0), notes: d.notes ?? account.notes, updated_at: new Date().toISOString() }); if (d.token) { account.token = String(d.token); account.token_last4 = account.token.slice(-4); account.token_status = 'unknown' }; if (env.cf_manager) await env.cf_manager.prepare('UPDATE accounts SET alias=?,account_id=?,token=?,token_last4=?,token_status=?,enabled=?,daily_quota=?,notes=?,updated_at=? WHERE id=?').bind(account.alias,account.account_id,account.token,account.token_last4,account.token_status,account.enabled,account.daily_quota,account.notes,account.updated_at,account.id).run(); return json({ ok: true, token_status: account.token_status })
  }
  if (match && request.method === 'DELETE') { if (env.cf_manager) await env.cf_manager.prepare('DELETE FROM accounts WHERE id=?').bind(Number(match[1])).run(); store.accounts = store.accounts.filter(a => a.id !== Number(match[1])); return json({ ok: true }) }
  if (path === '/api/dashboard/summary') return json({ accounts: store.accounts.length, workers: store.resources.workers.length, pages: store.resources.pages.length, zones: store.resources.zones.length, dns_records: store.resources['dns-records'].length, routes: store.resources.routes.length, today_usage: store.resources['usage/accounts'], open_alerts: store.resources.alerts, recent_runs: store.runs.slice(-10).reverse() })
  if (path === '/api/search') { const q = url.searchParams.get('q')?.toLowerCase() || ''; const all = Object.entries(store.resources).flatMap(([kind, rows]) => rows.filter(row => JSON.stringify(row).toLowerCase().includes(q)).map(row => ({ ...row, kind }))); return json({ query: q, total: all.length, results: all }) }
  for (const key of ['workers', 'pages', 'zones', 'dns-records', 'routes', 'usage/accounts', 'usage/workers', 'sync/jobs', 'sync/runs', 'alerts']) { if (path === `/api/${key}` && request.method === 'GET') return json(key === 'sync/jobs' ? [] : key === 'sync/runs' ? store.runs : (key === 'alerts' ? store.resources.alerts : store.resources[key] || [])) }
  const notes = path.match(/^\/api\/(workers|pages)\/(\d+)\/notes$/)
  if (notes && request.method === 'PUT') { const row = store.resources[notes[1]].find(r => r.id === Number(notes[2])); if (!row) return json({ error: 'resource not found' }, 404); const d = await body(request); row.notes = String(d.notes || ''); return json({ ok: true, notes: row.notes }) }
  const resolve = path.match(/^\/api\/alerts\/(\d+)\/resolve$/)
  if (resolve && request.method === 'POST') { const row = store.resources.alerts.find(r => r.id === Number(resolve[1])); if (!row) return json({ error: 'alert not found' }, 404); row.status = 'resolved'; return json({ ok: true }) }
  if (path === '/api/diagnostics/cloudflare') return json({ runtime: 'cloudflare-pages-functions', dns: 'edge', https: 'available', proxy: 'not required' })
  if (path === '/api/sync/run-now' && request.method === 'POST') { const started = new Date().toISOString(); const summaries: any[] = []; for (const account of store.accounts.filter(a => a.enabled)) { try { summaries.push({ account_id: account.id, ...(await syncAccount(account, store)) }) } catch (e) { summaries.push({ account_id: account.id, error: String(e) }) } } const run = { run_type: 'manual', status: summaries.some(s => s.error || s.warnings?.length) ? 'partial' : 'success', started_at: started, finished_at: new Date().toISOString(), summaries }; store.runs.push(run); return json({ ok: true, started: true, summaries }) }
  return json({ error: 'not found' }, 404)
}
