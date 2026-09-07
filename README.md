# Cloudflare Multi-Account Manager

一个本地运行、也可以部署到 Cloudflare Pages 的 Cloudflare 多账号巡检面板。它把多个 Account 的 Workers、Pages、Zones、DNS、Routes、用量和告警集中到一个界面中，并将数据保存到本地 SQLite 或 Cloudflare D1。

## 能做什么

- 管理多个 Cloudflare 账号：别名、Account ID、Token 尾号、状态、额度和备注。
- 巡检 Workers、Pages、Zones、DNS 记录和 Worker Routes。
- 采集 Workers/Pages 请求量、子请求、错误、CPU P50/P99，以及 D1、KV、R2 的用量快照（Cloudflare API 提供数据时）。
- Dashboard 汇总账号、资产、今日用量、告警和最近巡检记录。
- 全局搜索资源，查看巡检历史，并对 Worker/Pages 资源保存备注。
- 按间隔自动执行资产巡检和用量巡检，也可以在页面中手动触发。
- 根据额度阈值生成告警；界面时间统一显示为北京时间，数据库时间保存为 UTC。

## 安全边界

这是面向个人或内部运维的工具。Cloudflare Token 只用于只读 API 巡检，不会修改 Cloudflare 资源。

- 本地模式将 Token 加密后保存到 `data/cloudflare-manager.db`，密钥保存在 `data/.local_secret`。
- `config.yaml`、数据库、密钥、`.env` 和 `wrangler.toml` 均默认被 Git 忽略；不要把它们提交到仓库。
- Token 至少需要覆盖目标 Account 的读取权限，以及需要巡检的 Zone、DNS 和 Routes 读取权限。推荐使用 Cloudflare 的 `Read all resources` 模板。
- Pages 部署通过 Pages Secret `ADMIN` 保护管理界面和 API。不要把密码写入代码或 `wrangler.toml`。
- 本地服务默认只监听 `127.0.0.1`。如果要让其他机器访问，请显式设置监听地址，并自行配置网络访问控制。

## 本地运行

### 环境要求

- Python 3.9 或更高版本
- Node.js 18 或更高版本及 npm

### 安装和启动

```powershell
cd frontend
npm install
npm run build
cd ..
py -3 server.py
```

然后打开 `http://127.0.0.1:8787`。Windows 也可以直接运行 `start.bat`；它会启动后端，前提是前端已经构建到 `static/dist`。

首次启动会自动创建数据库、加密密钥和默认的资产/用量巡检任务。复制 `config.example.yaml` 为 `config.yaml` 可保留项目配置模板；当前后端主要通过环境变量读取运行参数。

常用环境变量：

| 变量 | 默认值 | 作用 |
| --- | --- | --- |
| `CFM_HOST` | `127.0.0.1` | HTTP 监听地址 |
| `CFM_PORT` | `8787` | HTTP 监听端口 |
| `CFM_FETCH_WORKERS` | `8` | 资产并发抓取数，范围 1–16 |
| `CFM_USAGE_CACHE_TTL_SECONDS` | `1200` | 用量缓存时长；设为 `0` 禁用 |
| `CFM_HTTP_PROXY` | 空 | Cloudflare API 使用的 HTTP/HTTPS 代理 |
| `CFM_NO_PROXY` | 空 | 设为 `1`、`true` 或 `yes` 禁用系统代理 |
| `CFM_GZIP_MIN_BYTES` | `1024` | 响应启用 gzip 的最小大小 |
| `CFM_GZIP_LEVEL` | `4` | gzip 压缩级别 |
| `CFM_NO_BROWSER` | `0` | 设为 `1` 时启动后不自动打开浏览器 |

### 添加第一个账号

打开“账号 Accounts”，填写显示别名、Cloudflare Account ID、API Token、每日额度（用于计算用量百分比）和可选备注。保存后点击“校验 Token”，再在 Dashboard 或资源页面执行巡检。

## Cloudflare Pages + D1 部署

Pages 部署使用静态前端、Pages Functions API 和 D1。D1 只初始化一次，后续发布不会清空数据。

### 1. 创建资源

```powershell
npm install -g wrangler
wrangler login
wrangler whoami
npx wrangler pages project create <pages-project-name> --production-branch main
npx wrangler d1 create <d1-database-name>
```

复制 `wrangler.toml.example` 为 `wrangler.toml`，填写 Pages 项目名、D1 数据库名和 `database_id`。`wrangler.toml` 已被忽略，不要提交真实配置。

### 2. 初始化 D1

```powershell
npx wrangler d1 migrations apply <d1-database-name> --remote
```

迁移文件按顺序执行。以后只新增迁移文件，再重复执行同一条命令；不要删除数据库，也不要用裸 `d1 execute` 重放旧迁移。

### 3. 设置管理密码并发布

```powershell
npx wrangler pages secret put ADMIN --project-name <pages-project-name>
cd frontend
npm install
npm run build:pages
cd ..
npx wrangler pages deploy static/dist --project-name <pages-project-name> --branch main
```

`ADMIN` 只保存在 Pages Secret。部署后访问站点会先进入登录页，登录 Cookie 默认有效 24 小时。

### 从本地 SQLite 同步账号到 Pages

同步脚本不会打印 Token，会跳过远端已有的 Account ID，并默认只同步启用账号：

```powershell
py -3 scripts/sync_accounts_to_pages.py --url https://<pages-project>.pages.dev
```

脚本会交互读取 Pages `ADMIN` 密码。需要同步已停用账号时追加 `--all`；同步前确认本地数据库和 `data/.local_secret` 存在。

## 开发和验证

```powershell
cd frontend
npm run dev
npm run typecheck
npm run build
cd ..
py -3 -m py_compile server.py
```

后端 API 默认位于 `/api`，包括账号、Dashboard、Workers、Pages、Zones、DNS、Routes、用量、巡检记录、告警、搜索和 Cloudflare 诊断接口。前端使用 history 路由，生产环境需将非 API 路径回退到 `static/dist/index.html`。

## 故障排查

- **资源为空**：检查 Token 状态并执行资产巡检；DNS/Routes 403 通常表示缺少对应 Zone 的读取权限。
- **API 请求失败**：检查网络和代理，或设置 `CFM_HTTP_PROXY`；诊断接口可查看运行环境和代理信息。
- **端口占用**：设置 `CFM_PORT` 使用其他端口，或停止占用 8787 的旧 Python 进程。
- **用量未变化**：手动执行“立即用量巡检”强制刷新；Cloudflare Analytics 本身可能存在延迟。
- **Pages 未登录**：确认已设置 `ADMIN` Secret，清除站点 Cookie 后重新登录。

## 目录说明

- `server.py`：本地 HTTP 服务、SQLite、Cloudflare API、巡检调度器和 API。
- `frontend/`：Vue 3 + TypeScript + Vite 前端。
- `functions/`：Cloudflare Pages Functions API。
- `migrations/`：D1 数据库迁移。
- `scripts/`：本地 SQLite 到 Pages 的账号同步工具。
- `config.example.yaml`、`wrangler.toml.example`：不含敏感信息的配置模板。

## 许可证

当前仓库未声明开源许可证。如需对外分发，请先补充许可证和部署责任说明。
