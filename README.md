# Cloudflare Multi-Account Manager

基于 Cloudflare Pages、Pages Functions 和 D1 的多账号巡检面板。集中管理多个 Cloudflare Account 的 Workers、Pages、Zones、DNS、Routes、用量和告警。

## 功能

- 账号管理、Token 校验和 `ADMIN` 密码登录。
- Workers、Pages、Zones、DNS 记录和 Worker Routes 巡检。
- Workers/Pages 请求量、错误、CPU P50/P99，以及 D1、KV、R2 用量展示。
- Dashboard、全局搜索、巡检历史、告警和资源备注。
- 手动执行资产/用量巡检；D1 持久化账号、资源和巡检数据。

## 安全要求

- Cloudflare API Token 仅用于只读巡检，请按 Account、Zone 和 DNS/Routes 范围授予读取权限。
- 管理密码只通过 Pages Secret `ADMIN` 配置，不要写入代码或配置文件。
- Token 保存在 D1 中，部署前请确认 Cloudflare 项目访问权限和数据库权限配置正确。

## 部署

### 创建 Pages 项目和 D1

```powershell
npm install -g wrangler
wrangler login
wrangler whoami
npx wrangler pages project create <pages-project-name> --production-branch main
npx wrangler d1 create <d1-database-name>
```

复制 `wrangler.toml.example` 为 `wrangler.toml`，填写 Pages 项目名、D1 数据库名和 `database_id`。`wrangler.toml` 已被 Git 忽略。

### 初始化数据库

```powershell
npx wrangler d1 migrations apply <d1-database-name> --remote
```

迁移按编号顺序执行。后续只新增迁移文件，不要删除数据库或重复执行旧 SQL。

### 配置密码并发布

```powershell
npx wrangler pages secret put ADMIN --project-name <pages-project-name>
cd frontend
npm install
npm run build
cd ..
npx wrangler pages deploy static/dist --project-name <pages-project-name> --branch main
```

部署后访问 Pages 域名，使用 `ADMIN` 密码登录，再在“账号 Accounts”中添加 Cloudflare Account 和只读 API Token。

## 开发和验证

```powershell
cd frontend
npm run dev
npm run typecheck
npm run build
```

生产环境由 Pages Functions 处理 `/api/*`，静态资源来自 `static/dist`。

## 故障排查

- **登录失败**：确认 Pages Secret 已设置为 `ADMIN`，清除站点 Cookie 后重试。
- **资源为空或 403**：检查 Token 是否覆盖目标 Account 和 Zone 的读取权限，然后手动执行资产巡检。
- **用量未更新**：手动执行用量巡检；Cloudflare Analytics 可能存在数据延迟。
- **D1 错误**：确认 `wrangler.toml` 的 binding 名为 `cf_manager`，并已执行远程 migrations。

## 目录

- `frontend/`：Vue 3 + TypeScript + Vite 前端。
- `functions/`：Pages Functions API、登录鉴权和 Cloudflare API 巡检。
- `migrations/`：D1 数据库迁移。
- `wrangler.toml.example`：Wrangler 配置模板。

## 许可证

当前仓库未声明开源许可证。
