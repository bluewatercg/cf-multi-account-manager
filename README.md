# Cloudflare Multi-Account Manager

一个本地运行的 Cloudflare 多账号管理面板，用来统一巡检多个 Cloudflare Account 下的 Workers、Pages、Zone、DNS、Routes、用量和告警。

这个项目适合个人或内部运维使用：后端本地运行，数据存在本地 SQLite，Cloudflare API Token 由你自己填写并保存在本机。

## 功能

- 多账号管理：别名、Account ID、Token 尾号、Token 状态、额度、备注。
- 资产巡检：Workers、Worker 自定义域名、Pages、Pages 域名、Zones、DNS 记录、Worker Routes。
- 用量巡检：账号级 Workers/Pages 请求量、子请求、错误数、额度使用率，并采集 D1、KV、R2 的操作量和存储快照。
- Worker 实时用量：在 Workers 页面直接展示请求、子请求、错误、CPU P50/P99 和采集时间。
- Dashboard：账号数量、资产数量、今日用量、告警和最近巡检记录。
- 全局搜索：Workers、Pages、域名、Zone、DNS 记录、Routes。
- 定时巡检：默认创建资产巡检和用量巡检任务，也可以手动触发。
- Token 校验：新增或编辑账号时会校验 Token 是否能访问对应 Account ID。
- 北京时间显示：界面上的时间按北京时间显示，数据库仍保存 UTC 时间。
- 本地数据存储：数据库和本地密钥默认不提交到 Git。

## 技术栈

- Python 3.9+ 标准库后端
- SQLite 本地数据库
- Vue 3、TypeScript、Vite
- Element Plus、Pinia、Vue Router
- ECharts 图表

## Cloudflare Token 权限

只做只读巡检时，最省事的 Token 模板是：

- `Read all resources`

如果想用更细的自定义 Token，至少按需要授予这些读取权限：

- Account 读取权限，并且资源范围包含要添加的 Cloudflare Account
- Workers Scripts 读取
- Workers Routes 读取
- Pages 读取
- Zone 读取
- DNS 读取
- Analytics 读取

不建议为了这个工具选择 `Write all resources`。当前功能不写 Cloudflare 资源，除非以后增加 DNS 修改等写操作，否则也不需要 `Edit zone DNS`。

注意 Token 的资源范围要同时覆盖：

- 你在账号里填写的 Cloudflare Account ID
- 需要采集 DNS 或 Routes 的 Zone

如果账号校验成功，但资产巡检里出现 DNS 或 Routes 的 403 warning，通常表示 Token 能访问 Account，但没有对应 Zone 的读取权限。

## 快速启动

先安装并构建前端：

```powershell
cd frontend
npm install
npm run build
cd ..
```

启动本地后端：

```powershell
py -3 server.py
```

打开：

```text
http://127.0.0.1:8787
```

## Cloudflare Pages 部署

Pages 部署包含 Vue 静态前端、Pages Functions API 和 D1 数据库。首次部署按下面顺序执行；日常发布只需要重新构建和 `pages deploy`，不会重建或清空 D1。

### 1. 安装并登录 Wrangler

```powershell
npm install -g wrangler
wrangler login
wrangler whoami
```

### 2. 创建 Pages 项目和 D1

```powershell
npx wrangler pages project create <pages-project-name> --production-branch main
npx wrangler d1 create <d1-database-name>
```

将 `wrangler.toml.example` 复制为本地 `wrangler.toml`，填入 Pages 项目名和 D1 返回的 `database_id`。`wrangler.toml` 已被 `.gitignore` 排除，不要提交真实账号或数据库配置。

### 3. 初始化 D1（只执行一次）

```powershell
npx wrangler d1 migrations apply <d1-database-name> --remote
```

当前 migrations 会创建账号和资源表。以后新增表结构时只添加新的 migration 文件，再执行同一条命令；已应用的 migration 不会重复执行。不要删除数据库，也不要用裸 `d1 execute` 重放旧 migration。

### 4. 配置登录密码

密码只保存为 Pages Secret，不写入代码、`wrangler.toml` 或命令历史：

```powershell
npx wrangler pages secret put ADMIN --project-name <pages-project-name>
```

### 5. 构建并发布

```powershell
cd frontend
npm install
npm run build:pages
cd ..
npx wrangler pages deploy static/dist --project-name <pages-project-name> --branch main
```

访问 `https://<pages-project-name>.pages.dev/login`，使用刚配置的 `ADMIN` 密码登录。生产构建使用根资源路径；本地 Python 生产服务使用普通 `npm run build`。

### 6. 同步本地账号

同步脚本从本地 SQLite 读取并解密 Token，通过登录后的 HTTPS 请求写入 D1；Token 不会打印或写入临时文件。请保留本地数据库和 `.local_secret`，然后执行：

```powershell
py scripts/sync_accounts_to_pages.py --url https://<pages-project-name>.pages.dev
```

脚本会交互式要求输入 `ADMIN` 密码，默认同步启用账号；追加 `--all` 可包含停用账号。按 Account ID 去重，重复执行不会重复添加。

### 7. 手动巡检

登录后在 Dashboard、Workers、Pages 或 Usage 页面点击巡检按钮。巡检由 Pages Function 直接访问 Cloudflare API，不依赖本机代理；账号和巡检资源写入 D1，重新发布不会丢失。

### 日常更新

```powershell
cd frontend
npm run build:pages
cd ..
npx wrangler pages deploy static/dist --project-name <pages-project-name> --branch main
```

不要在日常更新中重新创建 D1、删除 D1，或重复执行旧 migration。

macOS 或 Linux 可以用：

```bash
python3 server.py
```

## 开发模式

启动 Python 后端：

```powershell
py -3 server.py
```

另开一个终端启动 Vite：

```powershell
cd frontend
npm install
npm run dev
```

开发地址：

```text
http://127.0.0.1:5173
```

开发服务会把 `/api` 请求代理到本地 Python 后端的 `8787` 端口。

## 运行配置

后端读取这些环境变量：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `CFM_HOST` | `127.0.0.1` | Python 服务监听地址 |
| `CFM_PORT` | `8787` | Python 服务端口 |
| `CFM_NO_BROWSER` | `0` | 设为 `1` 时启动后不自动打开浏览器 |
| `CFM_USAGE_CACHE_TTL_SECONDS` | `1200` | 用量巡检本地缓存 TTL；定时巡检在 TTL 内复用 SQLite 缓存，手动立即巡检会强制刷新 |

示例：

```powershell
$env:CFM_HOST = '127.0.0.1'
$env:CFM_PORT = '8787'
$env:CFM_NO_BROWSER = '1'
py -3 server.py
```

## 数据和密钥

首次启动后会在本地生成：

- SQLite 数据库
- 本地加密密钥

这两类文件必须一起保留。Token 是用本地密钥加密后写入数据库的，如果只复制数据库、不复制本地密钥，已经保存的 Token 将无法解密。

这个加密方式用于本地使用场景，不等同于专业密钥管理系统。不要把数据库、密钥、日志或本机配置提交到 GitHub。

## 常用流程

### 添加账号

1. 在 Cloudflare 创建 API Token。
2. 打开 `账号 Accounts` 页面。
3. 填写别名、Cloudflare Account ID 和 API Token。
4. 保存。系统会校验 Token 是否能访问该 Account ID。

### 资产巡检

在 Dashboard、Workers、Pages、Zones、DNS 或 Routes 页面点击资产巡检按钮。

资产巡检会同步 Workers、Pages、Zones、DNS 记录、Routes 以及相关自定义域名。DNS 或 Routes 权限不足时，巡检记录会显示 `partial`，账号 Token 状态不会因为局部 Zone 权限问题被误判为错误。

### 用量巡检

在 Usage 或 Workers 页面点击用量巡检按钮。

Usage 页面展示最新日期的请求额度趋势和 D1/KV/R2 资源额度明细。定时巡检会优先复用 TTL 内的本地缓存，减少 Cloudflare GraphQL 请求；点击“立即用量巡检”会强制刷新。

## 故障排查

### Cloudflare API HTTP 403 Authentication Error

先判断失败位置：

- 账号级接口失败：通常是 Token 和 Account ID 不匹配，或者 Token 没有访问该 Account 的权限。
- DNS 或 Routes 失败：通常是 Token 有 Account 权限，但缺少某些 Zone 的读取权限。

如果只是 DNS 或 Routes 报错，给对应 Zone 增加 DNS 或 Worker Routes 读取权限即可。

### 页面打不开

生产模式下后端会加载构建后的前端文件。先重新构建前端，再启动后端：

```powershell
cd frontend
npm install
npm run build
cd ..
py -3 server.py
```

### Cloudflare 网络诊断

启动后端后访问诊断接口：

```text
http://127.0.0.1:8787/api/diagnostics/cloudflare
```

也可以在同一台机器上测试 Cloudflare API 连通性：

```powershell
curl -v https://api.cloudflare.com/client/v4/user/tokens/verify
```

能收到 HTTP 响应说明网络路径基本可达。超时、连接重置或 DNS 失败通常和代理、VPN、防火墙或 DNS 有关。

## GitHub 提交排除项

可以提交：

- Python 后端源码
- Vue 前端源码
- 包管理清单和锁文件
- README、设计文档、示例配置

不要提交：

- 本地数据库
- 本地加密密钥
- 本机配置文件
- 日志
- 前端依赖目录
- 前端构建输出
- TypeScript 构建缓存
- Python 缓存文件

`.gitignore` 已覆盖这些常见文件。提交前建议运行：

```powershell
git status --short
```

确认没有数据库、密钥、日志、构建产物或依赖目录被加入暂存区。

## 发布前注意

当前仓库还没有声明 License。如果准备公开到 GitHub，并希望别人可以使用、复制或修改代码，需要先选择并添加 License。
