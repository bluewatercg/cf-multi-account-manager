
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import base64, datetime as dt, hashlib, json, os, sqlite3, threading, time, urllib.parse, urllib.request, urllib.error, traceback, webbrowser, ssl, http.client
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
APP=Path(__file__).resolve().parent; DATA=APP/'data'; STATIC=APP/'static'; DB=DATA/'cloudflare-manager.db'; SECRET=DATA/'.local_secret'
CF='https://api.cloudflare.com/client/v4'; HOST=os.getenv('CFM_HOST','127.0.0.1'); PORT=int(os.getenv('CFM_PORT','8787')); DATA.mkdir(exist_ok=True)
def now(): return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def today(): return dt.datetime.now(dt.timezone.utc).date().isoformat()
def key():
    if not SECRET.exists(): SECRET.write_bytes(os.urandom(32))
    return SECRET.read_bytes()
def stream(n):
    k=key(); out=b''; i=0
    while len(out)<n: out+=hashlib.sha256(k+i.to_bytes(8,'big')).digest(); i+=1
    return out[:n]
def enc(s):
    b=s.encode(); return base64.urlsafe_b64encode(bytes(x^y for x,y in zip(b,stream(len(b))))).decode()
def dec(s):
    b=base64.urlsafe_b64decode(s.encode()); return bytes(x^y for x,y in zip(b,stream(len(b)))).decode()
def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON'); return c
SCHEMA=[
"CREATE TABLE IF NOT EXISTS accounts(id INTEGER PRIMARY KEY AUTOINCREMENT,alias TEXT NOT NULL,account_id TEXT NOT NULL UNIQUE,email_hint TEXT,token_encrypted TEXT NOT NULL,token_last4 TEXT,token_status TEXT DEFAULT 'unknown',daily_quota INTEGER DEFAULT 100000,enabled INTEGER DEFAULT 1,notes TEXT,last_success_sync_at TEXT,last_failed_sync_at TEXT,last_error TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL)",
"CREATE TABLE IF NOT EXISTS sync_jobs(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,job_type TEXT NOT NULL,enabled INTEGER DEFAULT 1,schedule_mode TEXT DEFAULT 'interval',interval_minutes INTEGER DEFAULT 30,time_window_start TEXT DEFAULT '00:00',time_window_end TEXT DEFAULT '23:59',high_usage_threshold INTEGER DEFAULT 80,high_usage_interval_minutes INTEGER DEFAULT 10,critical_usage_threshold INTEGER DEFAULT 96,critical_interval_minutes INTEGER DEFAULT 5,last_run_at TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL)",
"CREATE TABLE IF NOT EXISTS sync_runs(id INTEGER PRIMARY KEY AUTOINCREMENT,account_db_id INTEGER,run_type TEXT,status TEXT,started_at TEXT,finished_at TEXT,duration_ms INTEGER,workers_count INTEGER DEFAULT 0,pages_count INTEGER DEFAULT 0,zones_count INTEGER DEFAULT 0,dns_records_count INTEGER DEFAULT 0,routes_count INTEGER DEFAULT 0,api_calls_count INTEGER DEFAULT 0,error_message TEXT,raw_summary_json TEXT)",
"CREATE TABLE IF NOT EXISTS workers(id INTEGER PRIMARY KEY AUTOINCREMENT,account_db_id INTEGER,script_name TEXT,modified_on TEXT,raw_json TEXT,last_seen_at TEXT,created_at TEXT,updated_at TEXT,UNIQUE(account_db_id,script_name))",
"CREATE TABLE IF NOT EXISTS pages_projects(id INTEGER PRIMARY KEY AUTOINCREMENT,account_db_id INTEGER,project_name TEXT,subdomain TEXT,production_branch TEXT,latest_deployment_status TEXT,raw_json TEXT,last_seen_at TEXT,created_at TEXT,updated_at TEXT,UNIQUE(account_db_id,project_name))",
"CREATE TABLE IF NOT EXISTS pages_domains(id INTEGER PRIMARY KEY AUTOINCREMENT,account_db_id INTEGER,pages_project_id INTEGER,name TEXT,status TEXT,raw_json TEXT,last_seen_at TEXT,created_at TEXT,updated_at TEXT,UNIQUE(account_db_id,pages_project_id,name))",
"CREATE TABLE IF NOT EXISTS worker_domains(id INTEGER PRIMARY KEY AUTOINCREMENT,account_db_id INTEGER,domain_id TEXT,hostname TEXT,service TEXT,environment TEXT,zone_id TEXT,zone_name TEXT,raw_json TEXT,last_seen_at TEXT,created_at TEXT,updated_at TEXT,UNIQUE(account_db_id,hostname))",
"CREATE TABLE IF NOT EXISTS zones(id INTEGER PRIMARY KEY AUTOINCREMENT,account_db_id INTEGER,zone_id TEXT,name TEXT,status TEXT,type TEXT,raw_json TEXT,last_seen_at TEXT,created_at TEXT,updated_at TEXT,UNIQUE(account_db_id,zone_id))",
"CREATE TABLE IF NOT EXISTS dns_records(id INTEGER PRIMARY KEY AUTOINCREMENT,account_db_id INTEGER,zone_db_id INTEGER,record_id TEXT,type TEXT,name TEXT,content TEXT,ttl INTEGER,proxied INTEGER,raw_json TEXT,last_seen_at TEXT,created_at TEXT,updated_at TEXT,UNIQUE(zone_db_id,record_id))",
"CREATE TABLE IF NOT EXISTS worker_routes(id INTEGER PRIMARY KEY AUTOINCREMENT,account_db_id INTEGER,zone_db_id INTEGER,route_id TEXT,pattern TEXT,script_name TEXT,raw_json TEXT,last_seen_at TEXT,created_at TEXT,updated_at TEXT,UNIQUE(zone_db_id,route_id))",
"CREATE TABLE IF NOT EXISTS usage_account_daily(id INTEGER PRIMARY KEY AUTOINCREMENT,account_db_id INTEGER,date_utc TEXT,requests INTEGER DEFAULT 0,subrequests INTEGER DEFAULT 0,errors INTEGER DEFAULT 0,usage_percent REAL DEFAULT 0,quota INTEGER DEFAULT 100000,collected_at TEXT,raw_json TEXT,UNIQUE(account_db_id,date_utc))",
"CREATE TABLE IF NOT EXISTS usage_worker_daily(id INTEGER PRIMARY KEY AUTOINCREMENT,account_db_id INTEGER,script_name TEXT,date_utc TEXT,requests INTEGER DEFAULT 0,subrequests INTEGER DEFAULT 0,errors INTEGER DEFAULT 0,cpu_time_p50 REAL,cpu_time_p99 REAL,collected_at TEXT,raw_json TEXT,UNIQUE(account_db_id,script_name,date_utc))",
"CREATE TABLE IF NOT EXISTS alerts(id INTEGER PRIMARY KEY AUTOINCREMENT,alert_key TEXT UNIQUE,account_db_id INTEGER,target_type TEXT,target_name TEXT,level TEXT,title TEXT,message TEXT,current_value REAL,threshold_value REAL,status TEXT DEFAULT 'open',first_triggered_at TEXT,last_triggered_at TEXT,resolved_at TEXT,raw_json TEXT)",
"CREATE INDEX IF NOT EXISTS idx_workers_name ON workers(script_name)","CREATE INDEX IF NOT EXISTS idx_dns_name ON dns_records(name)","CREATE INDEX IF NOT EXISTS idx_dns_content ON dns_records(content)","CREATE INDEX IF NOT EXISTS idx_routes_pattern ON worker_routes(pattern)"
]
USAGE_ACCOUNT_COLUMNS=[
('workers_requests','INTEGER DEFAULT 0'),('workers_subrequests','INTEGER DEFAULT 0'),('workers_errors','INTEGER DEFAULT 0'),
('pages_requests','INTEGER DEFAULT 0'),('pages_errors','INTEGER DEFAULT 0'),
('d1_read_queries','INTEGER DEFAULT 0'),('d1_write_queries','INTEGER DEFAULT 0'),('d1_rows_read','INTEGER DEFAULT 0'),('d1_rows_written','INTEGER DEFAULT 0'),('d1_storage_bytes','INTEGER DEFAULT 0'),('d1_databases','INTEGER DEFAULT 0'),
('kv_requests','INTEGER DEFAULT 0'),('kv_reads','INTEGER DEFAULT 0'),('kv_writes','INTEGER DEFAULT 0'),('kv_deletes','INTEGER DEFAULT 0'),('kv_lists','INTEGER DEFAULT 0'),('kv_storage_bytes','INTEGER DEFAULT 0'),('kv_keys','INTEGER DEFAULT 0'),('kv_namespaces','INTEGER DEFAULT 0'),
('r2_requests','INTEGER DEFAULT 0'),('r2_class_a','INTEGER DEFAULT 0'),('r2_class_b','INTEGER DEFAULT 0'),('r2_free','INTEGER DEFAULT 0'),('r2_other','INTEGER DEFAULT 0'),('r2_storage_bytes','INTEGER DEFAULT 0'),('r2_objects','INTEGER DEFAULT 0'),('r2_buckets','INTEGER DEFAULT 0'),
('cache_status','TEXT DEFAULT "unknown"'),
('usage_details_json','TEXT'),('usage_errors_json','TEXT')
]
USAGE_CACHE_TTL_SECONDS=max(0,int(os.getenv('CFM_USAGE_CACHE_TTL_SECONDS','1200') or 0))
R2_CLASS_A_ACTIONS={'listbuckets','putbucket','listobjects','listobjectsv2','putobject','copyobject','completemultipartupload','createmultipartupload','lifecyclestoragetiertransition','listmultipartuploads','uploadpart','uploadpartcopy','listparts','putbucketencryption','putbucketcors','putbucketlifecycleconfiguration'}
R2_CLASS_B_ACTIONS={'headbucket','headobject','getobject','usagesummary','getbucketencryption','getbucketlocation','getbucketcors','getbucketlifecycleconfiguration'}
R2_FREE_ACTIONS={'deleteobject','deleteobjects','deletebucket','abortmultipartupload'}
def init_db():
    with db() as c:
        for s in SCHEMA: c.execute(s)
        cols={r['name'] for r in c.execute('PRAGMA table_info(usage_account_daily)')}
        for name,ddl in USAGE_ACCOUNT_COLUMNS:
            if name not in cols: c.execute(f'ALTER TABLE usage_account_daily ADD COLUMN {name} {ddl}')
        c.execute('UPDATE usage_account_daily SET workers_requests=requests,workers_subrequests=subrequests,workers_errors=errors WHERE usage_details_json IS NULL AND workers_requests=0 AND (requests<>0 OR subrequests<>0 OR errors<>0)')
        if c.execute('SELECT COUNT(*) c FROM sync_jobs').fetchone()['c']==0:
            t=now(); c.execute('INSERT INTO sync_jobs(name,job_type,interval_minutes,created_at,updated_at) VALUES(?,?,?,?,?)',('默认资产巡检','asset_sync',360,t,t)); c.execute('INSERT INTO sync_jobs(name,job_type,interval_minutes,created_at,updated_at) VALUES(?,?,?,?,?)',('默认用量巡检','usage_sync',30,t,t))
# Build a proxy-aware opener that respects system proxy settings on Windows/Linux/Mac
def _build_opener():
    proxies=urllib.request.getproxies()
    if proxies:
        return urllib.request.build_opener(urllib.request.ProxyHandler(proxies))
    return urllib.request.build_opener()
_proxy_opener=None
def _get_opener():
    global _proxy_opener
    if _proxy_opener is None: _proxy_opener=_build_opener()
    return _proxy_opener
class CFClient:
    def __init__(self,token): self.token=token; self.calls=0
    def req(self,method,path,data=None,qs=None):
        self.calls+=1; url=CF+path+(('?' + urllib.parse.urlencode(qs)) if qs else '')
        body=json.dumps(data).encode('utf-8') if data is not None else None
        headers={'Authorization':'Bearer '+self.token,'Accept':'application/json','User-Agent':'CF-Multi-Account-Manager/2.0 Python-urllib','Connection':'close'}
        if body: headers['Content-Type']='application/json'
        last=None
        for i in range(3):
            try:
                with _get_opener().open(urllib.request.Request(url,data=body,headers=headers,method=method),timeout=60) as r:
                    raw=r.read().decode('utf-8'); return json.loads(raw) if raw else {}
            except urllib.error.HTTPError as e:
                raise RuntimeError('Cloudflare API HTTP %s: %s'%(e.code,e.read().decode(errors='replace')[:1200]))
            except (http.client.RemoteDisconnected, ConnectionResetError, urllib.error.URLError, TimeoutError, ssl.SSLError) as e:
                last=e; time.sleep(1.5*(i+1))
        raise RuntimeError('Cloudflare API 网络连接失败：%s；请检查代理/VPN/防火墙/DNS'%last)
    def all(self,path,qs=None,per=50):
        out=[]; page=1
        while True:
            q=dict(qs or {}); q.update({'page':page,'per_page':per})
            try:
                d=self.req('GET',path,qs=q)
            except RuntimeError as e:
                if page==1 and 'Invalid list options' in str(e):
                    d=self.req('GET',path,qs=qs); part=d.get('result') or []
                    return part if isinstance(part,list) else []
                raise
            part=d.get('result') or []; out+=part
            if page>=((d.get('result_info') or {}).get('total_pages') or 1) or not part: break
            page+=1
        return out
    def gql(self,q,v): return self.req('POST','/graphql',{'query':q,'variables':v})
def verify_account_token(token,account_id):
    return bool(CFClient(token).req('GET','/accounts/%s'%account_id).get('success'))
def rows(sql,p=()):
    with db() as c: return [dict(r) for r in c.execute(sql,p)]
def one(sql,p=()):
    with db() as c:
        r=c.execute(sql,p).fetchone(); return dict(r) if r else None
def accounts(): return rows('SELECT * FROM accounts WHERE enabled=1')
def sync_assets(a):
    cf=CFClient(dec(a['token_encrypted'])); t=now(); st=time.time(); s={'workers':0,'pages':0,'zones':0,'dns_records':0,'routes':0,'api_calls':0,'warnings':[]}
    with db() as c:
        try:
            for w in cf.all('/accounts/%s/workers/scripts'%a['account_id']):
                name=w.get('id') or w.get('name'); c.execute('INSERT INTO workers(account_db_id,script_name,modified_on,raw_json,last_seen_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(account_db_id,script_name) DO UPDATE SET modified_on=excluded.modified_on,raw_json=excluded.raw_json,last_seen_at=excluded.last_seen_at,updated_at=excluded.updated_at',(a['id'],name,w.get('modified_on'),json.dumps(w),t,t,t)); s['workers']+=1
            try: wdoms=cf.all('/accounts/%s/workers/domains'%a['account_id'])
            except Exception as e:
                s['warnings'].append('Worker Domains: %s'%str(e)); wdoms=[]
            for d in wdoms:
                host=d.get('hostname') or d.get('domain') or d.get('name')
                service=d.get('service') or d.get('script') or d.get('script_name')
                if host: c.execute('INSERT INTO worker_domains(account_db_id,domain_id,hostname,service,environment,zone_id,zone_name,raw_json,last_seen_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(account_db_id,hostname) DO UPDATE SET domain_id=excluded.domain_id,service=excluded.service,environment=excluded.environment,zone_id=excluded.zone_id,zone_name=excluded.zone_name,raw_json=excluded.raw_json,last_seen_at=excluded.last_seen_at,updated_at=excluded.updated_at',(a['id'],d.get('id'),host,service,d.get('environment'),d.get('zone_id'),d.get('zone_name'),json.dumps(d),t,t,t))
            for p in cf.all('/accounts/%s/pages/projects'%a['account_id']):
                latest=p.get('latest_deployment') or p.get('canonical_deployment') or {}; stage=latest.get('latest_stage') or {}
                c.execute('INSERT INTO pages_projects(account_db_id,project_name,subdomain,production_branch,latest_deployment_status,raw_json,last_seen_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(account_db_id,project_name) DO UPDATE SET subdomain=excluded.subdomain,latest_deployment_status=excluded.latest_deployment_status,raw_json=excluded.raw_json,last_seen_at=excluded.last_seen_at,updated_at=excluded.updated_at',(a['id'],p.get('name'),p.get('subdomain'),p.get('production_branch'),stage.get('status'),json.dumps(p),t,t,t)); s['pages']+=1
                pr=c.execute('SELECT id FROM pages_projects WHERE account_db_id=? AND project_name=?',(a['id'],p.get('name'))).fetchone()
                try: doms=cf.req('GET','/accounts/%s/pages/projects/%s/domains'%(a['account_id'],urllib.parse.quote(p.get('name')))).get('result') or []
                except Exception: doms=[]
                for d in doms: c.execute('INSERT INTO pages_domains(account_db_id,pages_project_id,name,status,raw_json,last_seen_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(account_db_id,pages_project_id,name) DO UPDATE SET status=excluded.status,raw_json=excluded.raw_json,last_seen_at=excluded.last_seen_at,updated_at=excluded.updated_at',(a['id'],pr['id'],d.get('name'),d.get('status'),json.dumps(d),t,t,t))
            for z in cf.all('/zones',{'account.id':a['account_id']},50):
                c.execute('INSERT INTO zones(account_db_id,zone_id,name,status,type,raw_json,last_seen_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(account_db_id,zone_id) DO UPDATE SET name=excluded.name,status=excluded.status,raw_json=excluded.raw_json,last_seen_at=excluded.last_seen_at,updated_at=excluded.updated_at',(a['id'],z.get('id'),z.get('name'),z.get('status'),z.get('type'),json.dumps(z),t,t,t)); s['zones']+=1
                zr=c.execute('SELECT id FROM zones WHERE account_db_id=? AND zone_id=?',(a['id'],z.get('id'))).fetchone()
                try: dns=cf.all('/zones/%s/dns_records'%z.get('id'),per=50)
                except Exception as e:
                    s['warnings'].append('DNS %s: %s'%(z.get('name'),str(e))); dns=[]
                for r in dns: c.execute('INSERT INTO dns_records(account_db_id,zone_db_id,record_id,type,name,content,ttl,proxied,raw_json,last_seen_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(zone_db_id,record_id) DO UPDATE SET name=excluded.name,content=excluded.content,raw_json=excluded.raw_json,last_seen_at=excluded.last_seen_at,updated_at=excluded.updated_at',(a['id'],zr['id'],r.get('id'),r.get('type'),r.get('name'),r.get('content'),r.get('ttl'),int(bool(r.get('proxied'))),json.dumps(r),t,t,t))
                s['dns_records']+=len(dns)
                try: routes=cf.req('GET','/zones/%s/workers/routes'%z.get('id')).get('result') or []
                except Exception as e:
                    s['warnings'].append('Routes %s: %s'%(z.get('name'),str(e))); routes=[]
                for rr in routes: c.execute('INSERT INTO worker_routes(account_db_id,zone_db_id,route_id,pattern,script_name,raw_json,last_seen_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(zone_db_id,route_id) DO UPDATE SET pattern=excluded.pattern,script_name=excluded.script_name,raw_json=excluded.raw_json,last_seen_at=excluded.last_seen_at,updated_at=excluded.updated_at',(a['id'],zr['id'],rr.get('id'),rr.get('pattern'),rr.get('script'),json.dumps(rr),t,t,t))
                s['routes']+=len(routes)
            s['api_calls']=cf.calls; warn='; '.join(s['warnings'][:5]) if s['warnings'] else None; status='partial' if warn else 'success'
            c.execute('UPDATE accounts SET token_status="ok",last_success_sync_at=?,last_error=?,updated_at=? WHERE id=?',(t,warn,t,a['id']))
            c.execute('INSERT INTO sync_runs(account_db_id,run_type,status,started_at,finished_at,duration_ms,workers_count,pages_count,zones_count,dns_records_count,routes_count,api_calls_count,error_message,raw_summary_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(a['id'],'asset_sync',status,t,now(),int((time.time()-st)*1000),s['workers'],s['pages'],s['zones'],s['dns_records'],s['routes'],s['api_calls'],warn,json.dumps(s)))
        except Exception as e:
            c.execute('UPDATE accounts SET token_status="error",last_failed_sync_at=?,last_error=?,updated_at=? WHERE id=?',(t,str(e),t,a['id'])); c.execute('INSERT INTO sync_runs(account_db_id,run_type,status,started_at,finished_at,duration_ms,error_message,raw_summary_json) VALUES(?,?,?,?,?,?,?,?)',(a['id'],'asset_sync','failed',t,now(),int((time.time()-st)*1000),str(e),json.dumps(s))); c.commit(); raise
    return s
USAGE_GQL='''query GetUsageAnalytics($accountTag: string, $datetimeStart: string, $datetimeEnd: string, $dateStart: Date, $dateEnd: Date, $monthStart: Time) {
  viewer { accounts(filter: {accountTag: $accountTag}) {
    workersInvocationsAdaptive(limit: 10000, filter: { datetime_geq: $datetimeStart, datetime_leq: $datetimeEnd }) { sum { requests subrequests errors } quantiles { cpuTimeP50 cpuTimeP99 } dimensions { scriptName status } }
    pagesFunctionsInvocationsAdaptiveGroups(limit: 10000, filter: { datetime_geq: $datetimeStart, datetime_leq: $datetimeEnd }) { sum { requests errors } }
    d1AnalyticsAdaptiveGroups(limit: 10000, filter: { date_geq: $dateStart, date_leq: $dateEnd }) { sum { readQueries writeQueries rowsRead rowsWritten } dimensions { date databaseId } }
    d1StorageAdaptiveGroups(limit: 10000, filter: { date_geq: $dateStart, date_leq: $dateEnd }, orderBy: [date_DESC]) { max { databaseSizeBytes } dimensions { date databaseId } }
    kvOperationsAdaptiveGroups(limit: 10000, filter: { date_geq: $dateStart, date_leq: $dateEnd }) { sum { requests } dimensions { actionType } }
    kvStorageAdaptiveGroups(limit: 10000, filter: { date_geq: $dateStart, date_leq: $dateEnd }, orderBy: [date_DESC]) { max { keyCount byteCount } dimensions { date namespaceId } }
    r2OperationsAdaptiveGroups(limit: 10000, filter: { datetime_geq: $monthStart, datetime_leq: $datetimeEnd }) { sum { requests } dimensions { actionType actionStatus bucketName } }
    r2StorageAdaptiveGroups(limit: 10000, filter: { datetime_geq: $monthStart, datetime_leq: $datetimeEnd }, orderBy: [datetime_DESC]) { max { objectCount uploadCount payloadSize metadataSize } dimensions { datetime bucketName } }
  } }
}'''
def gql_account_rows(data,key):
    return ((((data.get('data') or {}).get('viewer') or {}).get('accounts') or [{}])[0].get(key) or []) if data else []
def sum_field(rows_,field):
    return sum(int((r.get('sum') or {}).get(field) or 0) for r in rows_ if isinstance(r,dict))
def account_node(data):
    return (((data.get('data') or {}).get('viewer') or {}).get('accounts') or [{}])[0] if data else {}
def latest_groups(groups,id_field,time_field):
    out={}
    for g in groups or []:
        d=g.get('dimensions') or {}; k=d.get(id_field) or '__account'; tm=str(d.get(time_field) or '')
        if k not in out or tm>=out[k][0]: out[k]=(tm,g)
    return [v[1] for v in out.values()]
def normalized_action(action):
    return ''.join(ch for ch in str(action or '').lower() if ch.isalnum())
def usage_window():
    n=dt.datetime.now(dt.timezone.utc); day=n.date().isoformat(); month=dt.datetime(n.year,n.month,1,tzinfo=dt.timezone.utc)
    return {'now':n.replace(microsecond=0).isoformat().replace('+00:00','Z'),'day':day,'day_start':day+'T00:00:00Z','month_start':month.isoformat().replace('+00:00','Z')}
def fresh_usage_row(row,ttl=USAGE_CACHE_TTL_SECONDS):
    if not row or ttl<=0 or not row['collected_at']: return False
    try: collected=dt.datetime.fromisoformat(row['collected_at'].replace('Z','+00:00'))
    except Exception: return False
    return (dt.datetime.now(dt.timezone.utc)-collected).total_seconds()<ttl
def build_usage_metrics(account):
    s={'requests':0,'subrequests':0,'errors':0,'workers_requests':0,'workers_subrequests':0,'workers_errors':0,'pages_requests':0,'pages_errors':0,'d1_read_queries':0,'d1_write_queries':0,'d1_rows_read':0,'d1_rows_written':0,'d1_storage_bytes':0,'d1_databases':0,'kv_requests':0,'kv_reads':0,'kv_writes':0,'kv_deletes':0,'kv_lists':0,'kv_storage_bytes':0,'kv_keys':0,'kv_namespaces':0,'r2_requests':0,'r2_class_a':0,'r2_class_b':0,'r2_free':0,'r2_other':0,'r2_storage_bytes':0,'r2_objects':0,'r2_buckets':0}
    workers_by={}
    for row in account.get('workersInvocationsAdaptive') or []:
        nm=(row.get('dimensions') or {}).get('scriptName') or '(unknown)'; sm=row.get('sum') or {}; qu=row.get('quantiles') or {}; x=workers_by.setdefault(nm,{'requests':0,'subrequests':0,'errors':0,'p50':None,'p99':None,'raw':[]})
        x['requests']+=int(sm.get('requests') or 0); x['subrequests']+=int(sm.get('subrequests') or 0); x['errors']+=int(sm.get('errors') or 0); x['p50']=qu.get('cpuTimeP50'); x['p99']=qu.get('cpuTimeP99'); x['raw'].append(row)
    for x in workers_by.values():
        s['workers_requests']+=x['requests']; s['workers_subrequests']+=x['subrequests']; s['workers_errors']+=x['errors']
    s['pages_requests']=sum_field(account.get('pagesFunctionsInvocationsAdaptiveGroups') or [],'requests'); s['pages_errors']=sum_field(account.get('pagesFunctionsInvocationsAdaptiveGroups') or [],'errors')
    for row in account.get('d1AnalyticsAdaptiveGroups') or []:
        sm=row.get('sum') or {}; s['d1_read_queries']+=int(sm.get('readQueries') or 0); s['d1_write_queries']+=int(sm.get('writeQueries') or 0); s['d1_rows_read']+=int(sm.get('rowsRead') or 0); s['d1_rows_written']+=int(sm.get('rowsWritten') or 0)
    d1_storage=latest_groups(account.get('d1StorageAdaptiveGroups') or [],'databaseId','date'); s['d1_databases']=len(d1_storage); s['d1_storage_bytes']=sum(int((g.get('max') or {}).get('databaseSizeBytes') or 0) for g in d1_storage)
    for row in account.get('kvOperationsAdaptiveGroups') or []:
        req=int((row.get('sum') or {}).get('requests') or 0); action=str((row.get('dimensions') or {}).get('actionType') or '').lower(); s['kv_requests']+=req
        if 'read' in action: s['kv_reads']+=req
        elif 'write' in action: s['kv_writes']+=req
        elif 'delete' in action: s['kv_deletes']+=req
        elif 'list' in action: s['kv_lists']+=req
    kv_storage=latest_groups(account.get('kvStorageAdaptiveGroups') or [],'namespaceId','date'); s['kv_namespaces']=len(kv_storage); s['kv_keys']=sum(int((g.get('max') or {}).get('keyCount') or 0) for g in kv_storage); s['kv_storage_bytes']=sum(int((g.get('max') or {}).get('byteCount') or 0) for g in kv_storage)
    for row in account.get('r2OperationsAdaptiveGroups') or []:
        dims=row.get('dimensions') or {}; status=str(dims.get('actionStatus') or 'success').lower()
        if status and status!='success': continue
        req=int((row.get('sum') or {}).get('requests') or 0); action=normalized_action(dims.get('actionType')); s['r2_requests']+=req
        if action in R2_CLASS_A_ACTIONS: s['r2_class_a']+=req
        elif action in R2_CLASS_B_ACTIONS: s['r2_class_b']+=req
        elif action in R2_FREE_ACTIONS: s['r2_free']+=req
        else: s['r2_other']+=req
    r2_storage=latest_groups(account.get('r2StorageAdaptiveGroups') or [],'bucketName','datetime'); s['r2_buckets']=len(r2_storage); s['r2_objects']=sum(int((g.get('max') or {}).get('objectCount') or 0) for g in r2_storage); s['r2_storage_bytes']=sum(int((g.get('max') or {}).get('payloadSize') or 0)+int((g.get('max') or {}).get('metadataSize') or 0) for g in r2_storage)
    s['requests']=s['workers_requests']+s['pages_requests']; s['subrequests']=s['workers_subrequests']; s['errors']=s['workers_errors']+s['pages_errors']
    return s,workers_by
USAGE_ALERT_LEVELS=(('critical',96),('danger',90),('warning',80))
def sync_usage_alert(c,a,s,pct,t):
    active=next(((level,thr) for level,thr in USAGE_ALERT_LEVELS if pct>=thr),None)
    key=f'account_usage:{a["id"]}'; legacy=f'account_usage:{a["id"]}:%'
    if not active:
        c.execute('UPDATE alerts SET status="resolved",resolved_at=COALESCE(resolved_at,?) WHERE status="open" AND (alert_key=? OR alert_key LIKE ?)',(t,key,legacy))
        return
    level,thr=active
    c.execute('UPDATE alerts SET status="resolved",resolved_at=COALESCE(resolved_at,?) WHERE status="open" AND alert_key LIKE ?',(t,legacy))
    c.execute('INSERT INTO alerts(alert_key,account_db_id,target_type,target_name,level,title,message,current_value,threshold_value,status,first_triggered_at,last_triggered_at,raw_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(alert_key) DO UPDATE SET level=excluded.level,title=excluded.title,message=excluded.message,current_value=excluded.current_value,threshold_value=excluded.threshold_value,status="open",last_triggered_at=excluded.last_triggered_at,resolved_at=NULL,raw_json=excluded.raw_json',(key,a['id'],'account',a['alias'],level,f'{a["alias"]} 用量 {pct}%',f'今日总用量 {s["requests"]}，使用率 {pct}%，超过 {thr}%',pct,thr,'open',t,t,json.dumps(s)))
def sync_usage(a,force=False):
    cf=CFClient(dec(a['token_encrypted'])); t=now(); d=today(); st=time.time(); s={'requests':0,'subrequests':0,'errors':0,'api_calls':0}
    with db() as c:
        try:
            cached=c.execute('SELECT * FROM usage_account_daily WHERE account_db_id=? AND date_utc=?',(a['id'],d)).fetchone()
            if not force and fresh_usage_row(cached):
                s=dict(cached); s.update({'api_calls':0,'cache_status':'fresh','cached':True})
                c.execute('INSERT INTO sync_runs(account_db_id,run_type,status,started_at,finished_at,duration_ms,api_calls_count,raw_summary_json) VALUES(?,?,?,?,?,?,?,?)',(a['id'],'usage_sync','success',t,now(),int((time.time()-st)*1000),0,json.dumps(s)))
                return s
            w=usage_window(); vars_={'accountTag':a['account_id'],'datetimeStart':w['day_start'],'datetimeEnd':w['now'],'dateStart':w['day'],'dateEnd':w['day'],'monthStart':w['month_start']}
            raw={}; usage_errors={}
            data=cf.gql(USAGE_GQL,vars_); raw['combined']=data
            if data.get('errors'): usage_errors['combined']=data.get('errors')
            account=account_node(data)
            if data.get('errors') and not account:
                raise RuntimeError('; '.join(str((e or {}).get('message') or e) for e in data.get('errors') or []))
            s,by=build_usage_metrics(account)
            for nm,x in by.items():
                c.execute('INSERT INTO usage_worker_daily(account_db_id,script_name,date_utc,requests,subrequests,errors,cpu_time_p50,cpu_time_p99,collected_at,raw_json) VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(account_db_id,script_name,date_utc) DO UPDATE SET requests=excluded.requests,subrequests=excluded.subrequests,errors=excluded.errors,cpu_time_p50=excluded.cpu_time_p50,cpu_time_p99=excluded.cpu_time_p99,collected_at=excluded.collected_at,raw_json=excluded.raw_json',(a['id'],nm,d,x['requests'],x['subrequests'],x['errors'],x['p50'],x['p99'],t,json.dumps(x['raw']))); s['requests']+=x['requests']; s['subrequests']+=x['subrequests']; s['errors']+=x['errors']
            s['requests']=s['workers_requests']+s['pages_requests']; s['subrequests']=s['workers_subrequests']; s['errors']=s['workers_errors']+s['pages_errors']; s.update({'usage_errors':usage_errors,'cache_status':'refreshed'})
            quota=int(a.get('daily_quota') or 100000); pct=round(s['requests']*100/quota,2) if quota else 0
            c.execute('INSERT INTO usage_account_daily(account_db_id,date_utc,requests,subrequests,errors,usage_percent,quota,collected_at,raw_json,workers_requests,workers_subrequests,workers_errors,pages_requests,pages_errors,d1_read_queries,d1_write_queries,d1_rows_read,d1_rows_written,d1_storage_bytes,d1_databases,kv_requests,kv_reads,kv_writes,kv_deletes,kv_lists,kv_storage_bytes,kv_keys,kv_namespaces,r2_requests,r2_class_a,r2_class_b,r2_free,r2_other,r2_storage_bytes,r2_objects,r2_buckets,cache_status,usage_details_json,usage_errors_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(account_db_id,date_utc) DO UPDATE SET requests=excluded.requests,subrequests=excluded.subrequests,errors=excluded.errors,usage_percent=excluded.usage_percent,quota=excluded.quota,collected_at=excluded.collected_at,raw_json=excluded.raw_json,workers_requests=excluded.workers_requests,workers_subrequests=excluded.workers_subrequests,workers_errors=excluded.workers_errors,pages_requests=excluded.pages_requests,pages_errors=excluded.pages_errors,d1_read_queries=excluded.d1_read_queries,d1_write_queries=excluded.d1_write_queries,d1_rows_read=excluded.d1_rows_read,d1_rows_written=excluded.d1_rows_written,d1_storage_bytes=excluded.d1_storage_bytes,d1_databases=excluded.d1_databases,kv_requests=excluded.kv_requests,kv_reads=excluded.kv_reads,kv_writes=excluded.kv_writes,kv_deletes=excluded.kv_deletes,kv_lists=excluded.kv_lists,kv_storage_bytes=excluded.kv_storage_bytes,kv_keys=excluded.kv_keys,kv_namespaces=excluded.kv_namespaces,r2_requests=excluded.r2_requests,r2_class_a=excluded.r2_class_a,r2_class_b=excluded.r2_class_b,r2_free=excluded.r2_free,r2_other=excluded.r2_other,r2_storage_bytes=excluded.r2_storage_bytes,r2_objects=excluded.r2_objects,r2_buckets=excluded.r2_buckets,cache_status=excluded.cache_status,usage_details_json=excluded.usage_details_json,usage_errors_json=excluded.usage_errors_json',(a['id'],d,s['requests'],s['subrequests'],s['errors'],pct,quota,t,json.dumps(data),s['workers_requests'],s['workers_subrequests'],s['workers_errors'],s['pages_requests'],s['pages_errors'],s['d1_read_queries'],s['d1_write_queries'],s['d1_rows_read'],s['d1_rows_written'],s['d1_storage_bytes'],s['d1_databases'],s['kv_requests'],s['kv_reads'],s['kv_writes'],s['kv_deletes'],s['kv_lists'],s['kv_storage_bytes'],s['kv_keys'],s['kv_namespaces'],s['r2_requests'],s['r2_class_a'],s['r2_class_b'],s['r2_free'],s['r2_other'],s['r2_storage_bytes'],s['r2_objects'],s['r2_buckets'],s['cache_status'],json.dumps(raw),json.dumps(usage_errors)))
            sync_usage_alert(c,a,s,pct,t)
            s['api_calls']=cf.calls; c.execute('UPDATE accounts SET last_success_sync_at=?,updated_at=? WHERE id=?',(t,t,a['id'])); c.execute('INSERT INTO sync_runs(account_db_id,run_type,status,started_at,finished_at,duration_ms,api_calls_count,raw_summary_json) VALUES(?,?,?,?,?,?,?,?)',(a['id'],'usage_sync','success',t,now(),int((time.time()-st)*1000),cf.calls,json.dumps(s)))
        except Exception as e:
            c.execute('UPDATE accounts SET token_status="error",last_failed_sync_at=?,last_error=?,updated_at=? WHERE id=?',(t,str(e),t,a['id'])); c.execute('INSERT INTO sync_runs(account_db_id,run_type,status,started_at,finished_at,duration_ms,error_message,raw_summary_json) VALUES(?,?,?,?,?,?,?,?)',(a['id'],'usage_sync','failed',t,now(),int((time.time()-st)*1000),str(e),json.dumps(s))); c.commit(); raise
lock=threading.Lock()
def run(kind,lock_acquired=False,force=False):
    acquired=lock_acquired or lock.acquire(False)
    if not acquired: return False
    try:
        for a in accounts():
            try:
                if kind in ('full_sync','asset_sync'): sync_assets(a)
                if kind in ('full_sync','usage_sync'): sync_usage(a,force=force)
            except Exception as e: print('sync failed',a.get('alias'),e)
        return True
    finally: lock.release()
def start_run(kind,force=False):
    if not lock.acquire(False): return False
    try:
        threading.Thread(target=lambda:run(kind,True,force),daemon=True).start()
        return True
    except Exception:
        lock.release()
        raise
def scheduler():
    while True:
        try:
            for j in rows('SELECT * FROM sync_jobs WHERE enabled=1 AND schedule_mode="interval"'):
                n=dt.datetime.now().strftime('%H:%M'); a=j['time_window_start'] or '00:00'; b=j['time_window_end'] or '23:59'; ok=(a<=n<=b) if a<=b else (n>=a or n<=b)
                if not ok: continue
                due=True
                if j['last_run_at']: due=(dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(j['last_run_at'].replace('Z','+00:00'))).total_seconds()>=int(j['interval_minutes'] or 30)*60
                if due:
                    if start_run(j['job_type']):
                        with db() as c: c.execute('UPDATE sync_jobs SET last_run_at=?,updated_at=? WHERE id=?',(now(),now(),j['id']))
            time.sleep(30)
        except Exception: traceback.print_exc(); time.sleep(60)
def resp(h,o,code=200):
    b=json.dumps(o,ensure_ascii=False,default=str).encode(); h.send_response(code); h.send_header('Content-Type','application/json; charset=utf-8'); h.send_header('Content-Length',str(len(b))); h.end_headers(); h.wfile.write(b)
def body(h):
    n=int(h.headers.get('Content-Length') or 0); return json.loads(h.rfile.read(n).decode()) if n else {}
def summary(): return {'accounts':one('SELECT COUNT(*) c FROM accounts')['c'],'workers':one('SELECT COUNT(*) c FROM workers')['c'],'pages':one('SELECT COUNT(*) c FROM pages_projects')['c'],'zones':one('SELECT COUNT(*) c FROM zones')['c'],'dns_records':one('SELECT COUNT(*) c FROM dns_records')['c'],'routes':one('SELECT COUNT(*) c FROM worker_routes')['c'],'today_usage':rows('SELECT u.*,a.alias account_alias FROM usage_account_daily u JOIN accounts a ON a.id=u.account_db_id WHERE date_utc=? ORDER BY usage_percent DESC',(today(),)),'open_alerts':rows('SELECT * FROM alerts WHERE status="open" ORDER BY last_triggered_at DESC LIMIT 20'),'recent_runs':rows('SELECT r.*,a.alias account_alias FROM sync_runs r LEFT JOIN accounts a ON a.id=r.account_db_id ORDER BY r.id DESC LIMIT 10')}
def worker_custom_domains(account_db_id,script_name):
    vals=[r['hostname'] for r in rows('SELECT hostname FROM worker_domains WHERE account_db_id=? AND service=? ORDER BY hostname',(account_db_id,script_name))]
    vals += [r['pattern'] for r in rows('SELECT pattern FROM worker_routes WHERE account_db_id=? AND script_name=? ORDER BY pattern',(account_db_id,script_name))]
    return [v for v in vals if v]
def page_custom_domains(project_id):
    return [r['name'] for r in rows('SELECT name FROM pages_domains WHERE pages_project_id=? ORDER BY name',(project_id,)) if r['name']]
def list_workers():
    data=rows('SELECT w.*,a.alias account_alias FROM workers w JOIN accounts a ON a.id=w.account_db_id ORDER BY a.alias,w.script_name')
    for w in data:
        domains=worker_custom_domains(w['account_db_id'],w['script_name'])
        w['custom_domains']='\n'.join(domains); w['custom_domains_count']=len(domains)
    return data
def list_pages():
    data=rows('SELECT p.*,a.alias account_alias,(SELECT COUNT(*) FROM pages_domains d WHERE d.pages_project_id=p.id) domains_count FROM pages_projects p JOIN accounts a ON a.id=p.account_db_id ORDER BY a.alias,p.project_name')
    for p in data: p['custom_domains']='\n'.join(page_custom_domains(p['id']))
    return data
def search(s):
    like='%'+s+'%'
    worker_items=rows("""SELECT w.script_name,w.account_db_id,a.alias account_alias,w.modified_on
      FROM workers w JOIN accounts a ON a.id=w.account_db_id
      WHERE w.script_name LIKE ?
         OR EXISTS(SELECT 1 FROM worker_routes wr WHERE wr.account_db_id=w.account_db_id AND wr.script_name=w.script_name AND wr.pattern LIKE ?)
         OR EXISTS(SELECT 1 FROM worker_domains wd WHERE wd.account_db_id=w.account_db_id AND wd.service=w.script_name AND wd.hostname LIKE ?)
      LIMIT 50""",(like,like,like))
    for w in worker_items: w['custom_domains']='\n'.join(worker_custom_domains(w['account_db_id'],w['script_name']))
    page_items=rows("""SELECT p.id,p.project_name,p.subdomain,p.account_db_id,a.alias account_alias,
      (SELECT COUNT(*) FROM pages_domains d WHERE d.pages_project_id=p.id) domains_count
      FROM pages_projects p JOIN accounts a ON a.id=p.account_db_id
      WHERE p.project_name LIKE ? OR p.subdomain LIKE ? OR EXISTS(SELECT 1 FROM pages_domains d WHERE d.pages_project_id=p.id AND d.name LIKE ?)
      LIMIT 50""",(like,like,like))
    for p in page_items: p['custom_domains']='\n'.join(page_custom_domains(p['id']))
    return {'q':s,'results':{
        'workers':worker_items,
        'pages':page_items,
        'pages_domains':rows('SELECT d.name,d.status,d.account_db_id,p.project_name,a.alias account_alias FROM pages_domains d JOIN pages_projects p ON p.id=d.pages_project_id JOIN accounts a ON a.id=d.account_db_id WHERE d.name LIKE ? LIMIT 50',(like,)),
        'zones':rows('SELECT z.name,z.status,z.account_db_id,a.alias account_alias FROM zones z JOIN accounts a ON a.id=z.account_db_id WHERE z.name LIKE ? LIMIT 50',(like,)),
        'dns_records':rows('SELECT r.type,r.name,r.content,r.account_db_id,z.name zone_name,a.alias account_alias FROM dns_records r JOIN zones z ON z.id=r.zone_db_id JOIN accounts a ON a.id=r.account_db_id WHERE r.name LIKE ? OR r.content LIKE ? LIMIT 100',(like,like)),
        'routes':rows('SELECT wr.pattern,wr.script_name,wr.account_db_id,z.name zone_name,a.alias account_alias FROM worker_routes wr JOIN zones z ON z.id=wr.zone_db_id JOIN accounts a ON a.id=wr.account_db_id WHERE wr.pattern LIKE ? OR wr.script_name LIKE ? LIMIT 100',(like,like))}}
class H(BaseHTTPRequestHandler):
    def log_message(self,fmt,*args): print('[%s] '%self.log_date_time_string()+fmt%args)
    def do_GET(self):
        p=urllib.parse.urlparse(self.path); path=p.path; qs=urllib.parse.parse_qs(p.query)
        try:
            route={'/api/dashboard/summary':lambda:summary(),'/api/accounts':lambda:rows('SELECT id,alias,account_id,email_hint,token_last4,token_status,daily_quota,enabled,notes,last_success_sync_at,last_failed_sync_at,last_error,created_at,updated_at FROM accounts ORDER BY id DESC'),'/api/workers':list_workers,'/api/pages':list_pages,'/api/zones':lambda:rows('SELECT z.*,a.alias account_alias,(SELECT COUNT(*) FROM dns_records r WHERE r.zone_db_id=z.id) dns_count,(SELECT COUNT(*) FROM worker_routes wr WHERE wr.zone_db_id=z.id) routes_count FROM zones z JOIN accounts a ON a.id=z.account_db_id ORDER BY a.alias,z.name'),'/api/dns-records':lambda:rows('SELECT r.*,z.name zone_name,a.alias account_alias FROM dns_records r JOIN zones z ON z.id=r.zone_db_id JOIN accounts a ON a.id=r.account_db_id ORDER BY z.name,r.name'),'/api/routes':lambda:rows('SELECT wr.*,z.name zone_name,a.alias account_alias FROM worker_routes wr JOIN zones z ON z.id=wr.zone_db_id JOIN accounts a ON a.id=wr.account_db_id ORDER BY z.name,wr.pattern'),'/api/usage/accounts':lambda:rows('SELECT u.*,a.alias account_alias FROM usage_account_daily u JOIN accounts a ON a.id=u.account_db_id ORDER BY date_utc DESC,usage_percent DESC'),'/api/usage/workers':lambda:rows('SELECT u.*,a.alias account_alias FROM usage_worker_daily u JOIN accounts a ON a.id=u.account_db_id ORDER BY date_utc DESC,requests DESC'),'/api/sync/jobs':lambda:rows('SELECT * FROM sync_jobs ORDER BY id'),'/api/sync/runs':lambda:rows('SELECT r.*,a.alias account_alias FROM sync_runs r LEFT JOIN accounts a ON a.id=r.account_db_id ORDER BY r.id DESC LIMIT 200'),'/api/alerts':lambda:rows('SELECT al.*,a.alias account_alias FROM alerts al LEFT JOIN accounts a ON a.id=al.account_db_id ORDER BY al.last_triggered_at DESC LIMIT 200')}
            if path=='/api/search': return resp(self,search((qs.get('q') or [''])[0].strip()))
            if path=='/api/diagnostics/cloudflare':
                import socket; out={'dns':None,'https':None,'error':None}
                try:
                    out['dns']=socket.gethostbyname('api.cloudflare.com')
                    try: urllib.request.urlopen(urllib.request.Request(CF+'/user/tokens/verify',headers={'User-Agent':'CF-Multi-Account-Manager/1.4','Connection':'close'}),timeout=15).read(); out['https']='reachable_200'
                    except urllib.error.HTTPError as e: out['https']='reachable_http_%s'%e.code
                    return resp(self,out)
                except Exception as e: out['error']=str(e); return resp(self,out,500)
            if path in route: return resp(self,route[path]())
            if path=='/': return self.file('dist/index.html')
            if path.startswith('/static/'): return self.file(path[8:])
            # SPA fallback: non-API, non-static routes -> serve index.html
            if not path.startswith('/api/') and not '.' in path.split('/')[-1]:
                return self.file('dist/index.html')
            return resp(self,{'error':'not found'},404)
        except Exception as e: traceback.print_exc(); return resp(self,{'error':str(e)},500)
    def do_POST(self):
        p=urllib.parse.urlparse(self.path); path=p.path
        try:
            if path=='/api/accounts':
                d=body(self); t=now()
                if not d.get('alias') or not d.get('account_id') or not d.get('token'): return resp(self,{'error':'alias/account_id/token required'},400)
                # Verify token against Cloudflare API before saving
                token_status='unknown'
                try:
                    token_status='ok' if verify_account_token(d['token'],d['account_id']) else 'error'
                except Exception as e:
                    return resp(self,{'error':'Token 验证失败: %s'%str(e)},400)
                with db() as c:
                    cur=c.execute('INSERT INTO accounts(alias,account_id,email_hint,token_encrypted,token_last4,token_status,daily_quota,enabled,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(d['alias'],d['account_id'],d.get('email_hint'),enc(d['token']),d['token'][-4:],token_status,int(d.get('daily_quota') or 100000),int(bool(d.get('enabled',1))),d.get('notes'),t,t)); nid=cur.lastrowid
                return resp(self,{'ok':True,'id':nid,'token_status':token_status})
            if path=='/api/sync/run-now':
                d=body(self); kind=d.get('kind') or 'full_sync'; force=bool(d.get('force'))
                if not start_run(kind,force=force): return resp(self,{'ok':False,'error':'已有巡检正在运行，请稍后再试'},409)
                return resp(self,{'ok':True,'started':True})
            parts=path.strip('/').split('/')
            if len(parts)==4 and parts[0]=='api' and parts[1]=='alerts' and parts[3]=='resolve':
                aid=int(parts[2]); t=now()
                with db() as c:
                    cur=c.execute('UPDATE alerts SET status="resolved",resolved_at=? WHERE id=?',(t,aid))
                    if cur.rowcount==0: return resp(self,{'error':'alert not found'},404)
                return resp(self,{'ok':True})
            if path.startswith('/api/accounts/') and path.endswith('/test-token'):
                aid=int(path.split('/')[3]); a=one('SELECT * FROM accounts WHERE id=?',(aid,))
                if not a: return resp(self,{'success':False,'error':'account not found'},404)
                ok=False; err=None
                try: ok=verify_account_token(dec(a['token_encrypted']),a['account_id'])
                except Exception as e: err=str(e)
                with db() as c: c.execute('UPDATE accounts SET token_status=?,last_error=?,updated_at=? WHERE id=?',('ok' if ok else 'error',None if ok else err,now(),aid))
                return resp(self,{'success':ok,'error':err})
            return resp(self,{'error':'not found'},404)
        except Exception as e: traceback.print_exc(); return resp(self,{'error':str(e)},500)
    def do_PUT(self):
        p=urllib.parse.urlparse(self.path); path=p.path
        try:
            if path.startswith('/api/accounts/'):
                aid=int(path.split('/')[3]); d=body(self); t=now(); a=one('SELECT * FROM accounts WHERE id=?',(aid,))
                if not a: return resp(self,{'error':'account not found'},404)
                te=a['token_encrypted']; tl=a['token_last4']; token_changed=bool(d.get('token'))
                if token_changed: te=enc(d['token']); tl=d['token'][-4:]
                aid_changed=d.get('account_id') and d['account_id']!=a['account_id']
                # Verify token when token or account_id changes
                status=a['token_status']; clear_error=False
                if token_changed or aid_changed:
                    status='unknown'
                    try:
                        vtoken=d['token'] if token_changed else dec(a['token_encrypted'])
                        vacct=d.get('account_id') or a['account_id']
                        status='ok' if verify_account_token(vtoken,vacct) else 'error'
                        clear_error=status=='ok'
                    except Exception as e:
                        return resp(self,{'error':'Token 验证失败: %s'%str(e)},400)
                with db() as c: c.execute('UPDATE accounts SET alias=?,account_id=?,email_hint=?,token_encrypted=?,token_last4=?,daily_quota=?,enabled=?,notes=?,token_status=?,last_error=?,updated_at=? WHERE id=?',(d.get('alias') or a['alias'],d.get('account_id') or a['account_id'],d.get('email_hint'),te,tl,int(d.get('daily_quota') or a['daily_quota'] or 100000),int(bool(d.get('enabled',a['enabled']))),d.get('notes'),status,None if clear_error else a['last_error'],t,aid))
                return resp(self,{'ok':True,'token_status':status})
            return resp(self,{'error':'not found'},404)
        except Exception as e: traceback.print_exc(); return resp(self,{'error':str(e)},500)
    def do_DELETE(self):
        p=urllib.parse.urlparse(self.path); path=p.path
        try:
            if path.startswith('/api/accounts/'):
                aid=int(path.split('/')[3])
                with db() as c:
                    for tb in ['alerts','usage_worker_daily','usage_account_daily','worker_routes','worker_domains','dns_records','zones','pages_domains','pages_projects','workers','sync_runs']: c.execute(f'DELETE FROM {tb} WHERE account_db_id=?',(aid,))
                    c.execute('DELETE FROM accounts WHERE id=?',(aid,))
                return resp(self,{'ok':True})
            return resp(self,{'error':'not found'},404)
        except Exception as e: traceback.print_exc(); return resp(self,{'error':str(e)},500)
    def file(self,n):
        fp=(STATIC/n).resolve()
        if not str(fp).startswith(str(STATIC.resolve())) or not fp.exists(): return resp(self,{'error':'not found'},404)
        raw=fp.read_bytes(); ct='text/html; charset=utf-8' if fp.suffix=='.html' else 'text/css; charset=utf-8' if fp.suffix=='.css' else 'application/javascript; charset=utf-8'
        self.send_response(200); self.send_header('Content-Type',ct); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
if __name__=='__main__':
    init_db(); threading.Thread(target=scheduler,daemon=True).start(); url=f'http://{HOST}:{PORT}'; print('CF Manager v1.4 running:',url)
    if os.getenv('CFM_NO_BROWSER','0')!='1': threading.Timer(1,lambda:webbrowser.open(url)).start()
    ThreadingHTTPServer((HOST,PORT),H).serve_forever()
