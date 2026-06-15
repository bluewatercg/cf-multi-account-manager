# UI-SPEC.md — Cloudflare 多账号管理面板 UI 设计规范

> **版本:** v1.0  
> **日期:** 2026-06-13  
> **技术栈:** Vue 3 + TypeScript + Element Plus + ECharts + Pinia + VueUse  
> **后端:** Python http.server（零依赖，API 不变）

---

## 1. 全局设计语言

### 1.1 色彩体系

#### 亮色模式 (Light)

| 语义 | 色值 | 用途 |
|------|------|------|
| `--primary` | `#2563eb` | 主按钮、链接、激活态 |
| `--primary-light` | `#dbeafe` | 选中行背景、hover 态 |
| `--primary-dark` | `#1d4ed8` | 主按钮 hover |
| `--success` | `#16a34a` | 正常状态、ok badge |
| `--warning` | `#d97706` | 警告状态、80% 用量 |
| `--danger` | `#dc2626` | 错误状态、删除按钮、96%+ 用量 |
| `--info` | `#6366f1` | 信息提示 |
| `--bg-page` | `#f8fafc` | 页面背景 |
| `--bg-card` | `#ffffff` | 卡片/面板背景 |
| `--bg-sidebar` | `#0f172a` | 侧边栏背景（始终深色） |
| `--bg-table-header` | `#f1f5f9` | 表格表头背景 |
| `--text-primary` | `#0f172a` | 主文字 |
| `--text-secondary` | `#475569` | 次要文字 |
| `--text-muted` | `#94a3b8` | 占位符、禁用态 |
| `--border` | `#e2e8f0` | 边框、分割线 |
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,.05)` | 卡片微阴影 |
| `--shadow-md` | `0 4px 12px rgba(0,0,0,.08)` | 卡片标准阴影 |

#### 暗色模式 (Dark)

| 语义 | 色值 |
|------|------|
| `--bg-page` | `#0f172a` |
| `--bg-card` | `#1e293b` |
| `--bg-table-header` | `#1e293b` |
| `--text-primary` | `#f1f5f9` |
| `--text-secondary` | `#94a3b8` |
| `--border` | `#334155` |

### 1.2 字体

```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
             "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
```

| 级别 | 大小 | 粗细 | 用途 |
|------|------|------|------|
| H1 | 20px | 700 | 侧边栏标题 |
| H2 | 18px | 600 | 页面标题 |
| H3 | 15px | 600 | 区域标题 |
| Body | 14px | 400 | 正文 |
| Small | 13px | 400 | 表格内容、辅助文字 |
| Tiny | 12px | 600 | Badge、标签 |

### 1.3 圆角

| 元素 | 圆角 |
|------|------|
| 卡片 (Card) | 12px |
| 按钮 (Button) | 8px |
| 输入框 (Input) | 8px |
| Badge | 999px（胶囊） |
| 表格 (Table) | 12px |

### 1.4 间距系统

基于 4px 网格：4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48

| 用途 | 间距 |
|------|------|
| 卡片内边距 | 20px |
| 卡片间距 | 16px |
| 页面内边距 | 24px |
| 区块间距 | 24px |
| 表格行高 | 44px |
| 侧边栏内边距 | 12px |

---

## 2. 全局布局 — MainLayout.vue

### 2.1 布局结构

```
┌──────────────────────────────────────────────────────┐
│ Sidebar (fixed) │         Main Content Area          │
│                 │  ┌─────────────────────────────┐   │
│  ┌───────────┐  │  │ TopBar (sticky)              │   │
│  │ Logo/Title│  │  │ [Page Title]    [Actions...] │   │
│  ├───────────┤  │  ├─────────────────────────────┤   │
│  │ Nav Items │  │  │                             │   │
│  │           │  │  │       <router-view />        │   │
│  │           │  │  │                             │   │
│  │           │  │  │                             │   │
│  │           │  │  │                             │   │
│  └───────────┘  │  └─────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

### 2.2 侧边栏 (Sidebar)

| 属性 | 桌面端 (≥768px) | 移动端 (<768px) |
|------|-----------------|-----------------|
| 宽度 | 220px（展开）/ 64px（收起） | 0px（默认隐藏） |
| 定位 | `position: fixed; left: 0` | `position: fixed` + 遮罩 overlay |
| 背景 | `--bg-sidebar` 始终深色 | 同左 |
| 交互 | 点击折叠按钮切换展开/收起 | 点击汉堡按钮弹出，点遮罩关闭 |

**导航项规范：**

```
┌──────────────────────┐
│ 📊 总览 Dashboard    │  ← 默认选中
│ 👤 账号 Accounts     │
│ 🔍 全局搜索          │
│ ⚙️  Workers         │
│ 📄 Pages            │
│ 🌐 域名 Zones       │
│ 📋 DNS 记录          │
│ 🔗 Routes           │
│ 📈 用量 Usage        │
│ 🔄 巡检 Jobs         │
│ 🔔 告警 Alerts      │
└──────────────────────┘
```

- 每项高度：44px，左侧图标 20px + 文字
- hover 态：背景 `rgba(255,255,255,.08)`
- 激活态：背景 `rgba(255,255,255,.12)`，左侧 3px `--primary` 色条
- 收起模式：仅显示图标，hover 时 tooltip 显示文字
- 图标使用 `@element-plus/icons-vue`

### 2.3 顶栏 (TopBar)

| 元素 | 说明 |
|------|------|
| 页面标题 | H2 级别，左侧 |
| 操作按钮组 | 右侧，主操作按钮用 `type="primary"` |
| 暗色模式开关 | 最右侧，太阳/月亮图标切换 |
| 面包屑 | 可选，二级页面时显示 |

### 2.4 响应式断点

| 断点 | 宽度 | 布局行为 |
|------|------|----------|
| Mobile | < 640px | 侧边栏隐藏，汉堡按钮触发抽屉；表格水平滚动；卡片单列 |
| Tablet | 640-1024px | 侧边栏收起为图标栏(64px)；卡片 2 列 |
| Desktop | ≥ 1024px | 侧边栏展开(220px)；卡片 3-4 列 |
| Wide | ≥ 1440px | 卡片 4-5 列；表格可显示更多列 |

---

## 3. 页面规范

### 3.1 Dashboard — 总览 (`/dashboard`)

**布局：**

```
┌─────────────────────────────────────────────────┐
│ 总览 Dashboard              [全量巡检] [诊断] [刷新] │
├─────────────────────────────────────────────────┤
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ │
│ │ 账号  │ │Workers│ │Pages │ │Zones │ │Routes│ │
│ │  3   │ │  12  │ │  5   │ │  8   │ │  20  │ │
│ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ │
│ ┌──────┐ ┌──────────────┐                      │
│ │DNS记录│ │  开放告警     │                      │
│ │ 156  │ │     2        │                      │
│ └──────┘ └──────────────┘                      │
├─────────────────────────────────────────────────┤
│ 📊 今日用量趋势                                  │
│ ┌─────────────────────────────────────────────┐ │
│ │         [ECharts 折线/面积图]                │ │
│ │   X轴: 账号名  Y轴: 请求数/使用率            │ │
│ └─────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────┤
│ 📋 最近巡检                                      │
│ ┌─────────────────────────────────────────────┐ │
│ │ el-table: 账号|类型|状态|开始|耗时|错误       │ │
│ │ 最多显示 10 行，分页不可见                     │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

**组件规格：**

| 组件 | Element Plus | 说明 |
|------|-------------|------|
| 统计卡片 | `el-card` | 7 个，Grid 布局 `repeat(auto-fit, minmax(150px, 1fr))` |
| 数字 | `<span class="stat-number">` | 28px, font-weight 800, 带计数动画 |
| 图表 | `echarts` 包裹 `v-chart` | 高度 280px，响应式宽度 |
| 巡检表格 | `el-table` + `el-table-column` | 不分页，max-height 限制滚动 |
| 操作按钮 | `el-button` | 全量巡检 `type="primary"`，诊断 `type="info"` |

**交互：**
- 进入页面自动调用 `GET /api/dashboard/summary`
- "全量巡检" 按钮点击 → `POST /api/sync/run-now {kind: 'full_sync'}` → ElMessage.success 通知 → 5 秒后自动刷新
- "网络诊断" → 弹出 `el-dialog` 显示诊断 JSON 结果
- "刷新" → 重新加载所有数据，按钮显示 loading 状态
- 用量图表：hover 显示 tooltip，点击图例可隐藏/显示系列
- 页面加载时卡片数字有 0 → N 的计数动画（约 600ms ease-out）

---

### 3.2 Accounts — 账号管理 (`/accounts`)

**布局：**

```
┌─────────────────────────────────────────────────┐
│ 账号 Accounts               [新增账号] [刷新]     │
├─────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────┐ │
│ │ el-table                                     │ │
│ │ ID | 启用 | 别名 | Account ID | Token尾号    │ │
│ │ Token状态 | 额度 | 最后成功 | 错误 | 操作     │ │
│ │                                              │ │
│ │ [行1] ● cf-01  acct_xxx  ***8832  ✅正确  ...│ │
│ │ [行2] ○ cf-02  acct_yyy  ***1234  ⚠未检测 ...│ │
│ │                                              │ │
│ │ 分页: [< 1 2 3 ... >]  共 N 条              │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

**新增/编辑弹窗 (`el-dialog`)：**

```
┌─────────────────────────────────────────┐
│ 新增账号                           [✕]  │
├─────────────────────────────────────────┤
│                                         │
│  别名 *        ┌─────────────────────┐  │
│                │ cf-01               │  │
│                └─────────────────────┘  │
│  Account ID *  ┌─────────────────────┐  │
│                │ acct_xxxxxxxxx      │  │
│                └─────────────────────┘  │
│  Email/备注    ┌─────────────────────┐  │
│                │                     │  │
│                └─────────────────────┘  │
│  API Token *   ┌─────────────────────┐  │
│                │ ••••••••••••••••    │  │
│                └─────────────────────┘  │
│  每日额度      ┌─────────────────────┐  │
│                │ 100000              │  │
│                └─────────────────────┘  │
│  ☑ 启用                              │
│  备注          ┌─────────────────────┐  │
│                │                     │  │
│                └─────────────────────┘  │
│                                         │
│              [取消]  [保存]              │
└─────────────────────────────────────────┘
```

**组件规格：**

| 组件 | Element Plus | 说明 |
|------|-------------|------|
| 表格 | `el-table` | stripe, border, 按钮列 fixed="right" |
| 分页 | `el-pagination` | layout: "total, prev, pager, next"，每页 20 条 |
| 弹窗 | `el-dialog` | width 520px, destroy-on-close |
| 表单 | `el-form` | label-width="100px", rules 验证 |
| 输入框 | `el-input` | 带 placeholder |
| 复选框 | `el-switch` | 替代 checkbox，更现代 |
| 按钮 | `el-button` | 编辑=默认, 检测=info, 删除=danger + 确认 |

**表单校验规则：**

```typescript
rules = {
  alias:     [{ required: true, message: '请输入别名', trigger: 'blur' }],
  account_id: [{ required: true, message: '请输入 Account ID', trigger: 'blur' }],
  token:     [{ required: true, message: '请输入 API Token', trigger: 'blur',
                validator: (rule, value, callback) => {
                  if (isEdit && !value) callback() // 编辑时可选
                  else if (!value) callback(new Error('必填'))
                  else callback()
                }
              }],
}
```

**交互：**
- 新增：打开空白弹窗，token 必填
- 编辑：打开预填弹窗，token 留空表示不修改
- 检测：`POST /api/accounts/:id/test-token` → 表格该行 token_status 实时更新
- 删除：`ElMessageBox.confirm('确定删除？只删除本地缓存...')` → 确认后删除
- 启用/禁用：`el-switch` 直接切换，调用 `PUT /api/accounts/:id`

---

### 3.3 Search — 全局搜索 (`/search`)

**布局：**

```
┌─────────────────────────────────────────────────┐
│ 全局搜索                                         │
├─────────────────────────────────────────────────┤
│ ┌─────────────────────────────────┐ [搜索]      │
│ │ 输入域名 / Worker / Pages / DNS │              │
│ └─────────────────────────────────┘              │
├─────────────────────────────────────────────────┤
│ Workers (3)                                      │
│ ┌─────────────────────────────────────────────┐ │
│ │ el-table: 账号 | Worker | 修改时间           │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Zones (2)                                       │
│ ┌─────────────────────────────────────────────┐ │
│ │ el-table: 账号 | Zone | 状态 | 类型          │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ DNS Records (5)                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ el-table: 账号 | Zone | 类型 | 名称 | 内容   │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Routes (1)                                      │
│ ┌─────────────────────────────────────────────┐ │
│ │ el-table: 账号 | Zone | Pattern | Script     │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Pages Domains (2)                               │
│ ┌─────────────────────────────────────────────┐ │
│ │ el-table: 账号 | 域名 | 状态 | 项目名        │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

**组件规格：**

| 组件 | 说明 |
|------|------|
| 搜索框 | `el-input` size="large"，带搜索图标前缀，Enter 键触发搜索 |
| 搜索按钮 | `el-button` type="primary"，搜索中显示 loading |
| 结果分组 | 每组用 `el-card` 包裹，标题带计数 badge |
| 空结果 | `el-empty` 组件，描述 "无搜索结果" |

**交互：**
- 按 Enter 或点击搜索按钮触发
- 搜索中：搜索按钮 loading，结果显示区显示 `el-skeleton`
- 每个结果组可独立折叠（`el-collapse`）
- URL 参数同步：`/search?q=xxx`，支持分享搜索链接

---

### 3.4 Workers (`/workers`)

**布局：**

```
┌─────────────────────────────────────────────────┐
│ Workers                           [刷新]         │
├─────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────┐ │
│ │ el-table                                     │ │
│ │ 账号 | Worker 名称 | 修改时间 | last seen     │ │
│ │                                              │ │
│ │ cf-01 | my-worker       | 2026-06-10 14:30  │ │
│ │ cf-02 | api-gateway     | 2026-06-12 09:15  │ │
│ │ cf-01 | cron-handler    | 2026-06-11 22:00  │ │
│ │                                              │ │
│ │ [< 1 2 ... >] 共 12 条                      │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

**表格列定义：**

| 列名 | 字段 | 宽度 | 排序 | 筛选 |
|------|------|------|------|------|
| 账号 | account_alias | 120px | ✅ | ✅ 按账号筛选 |
| Worker 名称 | script_name | auto | ✅ | — |
| 修改时间 | modified_on | 180px | ✅ | — |
| last seen | last_seen_at | 180px | ✅ | — |

**交互：**
- 默认按账号 → Worker 名称排序
- 表头筛选器：按账号筛选（多选）
- 支持列宽拖拽调整

---

### 3.5 Pages (`/pages`)

**布局：** 同 Workers 模式

**表格列定义：**

| 列名 | 字段 | 宽度 | 特殊渲染 |
|------|------|------|----------|
| 账号 | account_alias | 120px | — |
| 项目 | project_name | auto | 加粗 |
| subdomain | subdomain | 150px | — |
| 生产分支 | production_branch | 120px | — |
| 部署状态 | latest_deployment_status | 120px | StatusBadge 颜色 |
| 域名数 | domains_count | 80px | 居中 |
| last seen | last_seen_at | 180px | — |

**部署状态映射：**

| 状态值 | Badge 颜色 | 文字 |
|--------|-----------|------|
| `active` / `deployed` | 绿色 `success` | 已部署 |
| `building` / `queued` | 蓝色 `primary` | 构建中 |
| `failure` | 红色 `danger` | 失败 |
| 其他 | 灰色 `info` | 未知 |

---

### 3.6 Zones — 域名 (`/zones`)

**表格列定义：**

| 列名 | 字段 | 宽度 |
|------|------|------|
| 账号 | account_alias | 120px |
| Zone | name | auto, 加粗 |
| 状态 | status | 100px, StatusBadge |
| 类型 | type | 100px |
| DNS 数 | dns_count | 80px, 居中, 可点击查看 |
| Routes 数 | routes_count | 80px, 居中, 可点击查看 |
| last seen | last_seen_at | 180px |

**Zone 状态映射：**

| 状态 | Badge |
|------|-------|
| `active` | 绿色 |
| `pending` | 黄色 |
| `initializing` | 蓝色 |
| `deleted` / `deactivated` | 灰色 |

**交互：**
- DNS 数点击 → 跳转 `/dns` 并筛选该 Zone
- Routes 数点击 → 跳转 `/routes` 并筛选该 Zone

---

### 3.7 DNS 记录 (`/dns`)

**表格列定义：**

| 列名 | 字段 | 宽度 | 特殊渲染 |
|------|------|------|----------|
| 账号 | account_alias | 100px | — |
| Zone | zone_name | 150px | — |
| 类型 | type | 70px | Tag 样式（A/AAAA/CNAME/MX/TXT 等） |
| 名称 | name | auto | `font-family: monospace` |
| 内容 | content | auto | `font-family: monospace`，长内容截断+tooltip |
| 代理 | proxied | 60px | 橙色云朵图标 (proxy) / 灰色 (DNS only) |
| TTL | ttl | 80px | 数字，0 显示 "自动" |

**DNS 类型 Tag 颜色：**

| 类型 | 颜色 |
|------|------|
| A / AAAA | 蓝色 |
| CNAME | 紫色 |
| MX | 绿色 |
| TXT | 橙色 |
| NS | 红色 |
| SRV / CAA / 其他 | 灰色 |

**交互：**
- 大数据量场景（可能 500+ 条），使用虚拟滚动 `el-table-v2` 或分页（每页 50 条）
- 内容列 hover 显示完整值 tooltip
- 支持按类型/名称筛选

---

### 3.8 Routes (`/routes`)

**表格列定义：**

| 列名 | 字段 | 宽度 |
|------|------|------|
| 账号 | account_alias | 120px |
| Zone | zone_name | 150px |
| Pattern | pattern | auto, `font-family: monospace` |
| Script | script_name | 150px |
| last seen | last_seen_at | 180px |

---

### 3.9 Usage — 用量 (`/usage`)

**布局：**

```
┌─────────────────────────────────────────────────┐
│ 用量 Usage              [用量巡检] [刷新]         │
├─────────────────────────────────────────────────┤
│ 📊 用量趋势图                                    │
│ ┌─────────────────────────────────────────────┐ │
│ │         [ECharts 多系列折线图]                │ │
│ │   X轴: 日期  Y轴: 请求数                      │ │
│ │   每个账号一个系列，可点击图例切换              │ │
│ └─────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────┤
│ 📋 账号每日用量                                   │
│ ┌─────────────────────────────────────────────┐ │
│ │ el-table: 账号 | 日期 | 请求 | 错误 | 额度    │ │
│ │         | 使用率 | 采集时间                    │ │
│ │                                              │ │
│ │ 使用率列: <80% 绿色 | 80-96% 黄色 | >96% 红色│ │
│ └─────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────┤
│ 📋 Worker 每日用量                               │
│ ┌─────────────────────────────────────────────┐ │
│ │ el-table: 账号 | Worker | 日期 | 请求 | 错误  │ │
│ │         | CPU P50 | CPU P99                   │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

**使用率进度条：**

| 范围 | 颜色 | 展示 |
|------|------|------|
| 0-60% | 绿色 | `el-progress` 正常 |
| 60-80% | 蓝色 | `el-progress` 正常 |
| 80-96% | 橙色 | `el-progress` warning |
| 96-100% | 红色 | `el-progress` exception + 脉冲动画 |

**交互：**
- 用量巡检按钮 → `POST /api/sync/run-now {kind: 'usage_sync'}`
- 图表支持缩放（dataZoom）和区域选择
- 表格支持按日期范围筛选

---

### 3.10 Jobs — 巡检 (`/jobs`)

**布局：**

```
┌─────────────────────────────────────────────────┐
│ 巡检 Jobs                          [刷新]         │
├─────────────────────────────────────────────────┤
│ 📋 巡检任务配置                                   │
│ ┌─────────────────────────────────────────────┐ │
│ │ el-table: ID | 名称 | 类型 | 启用 | 间隔     │ │
│ │         | 时间段 | 最后运行                    │ │
│ └─────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────┤
│ 📋 执行记录                                      │
│ ┌─────────────────────────────────────────────┐ │
│ │ el-table: ID | 账号 | 类型 | 状态 | 开始     │ │
│ │         | 耗时 | API调用 | 错误               │ │
│ │                                              │ │
│ │ 状态列: success=绿色 ✅ | failed=红色 ❌     │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

---

### 3.11 Alerts — 告警 (`/alerts`)

**布局：**

```
┌─────────────────────────────────────────────────┐
│ 告警 Alerts                          [刷新]       │
├─────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────┐ │
│ │ el-table                                     │ │
│ │ 等级 | 账号 | 目标 | 标题 | 状态 | 触发时间   │ │
│ │                                              │ │
│ │ 🔴 critical | cf-01 | cf-01 用量 97% | ...   │ │
│ │ 🟡 warning  | cf-02 | cf-02 用量 85% | ...   │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

**告警等级颜色：**

| 等级 | 颜色 | 图标 |
|------|------|------|
| `critical` | 红色 | 🔴 |
| `danger` | 橙红色 | 🟠 |
| `warning` | 黄色 | 🟡 |
| `info` | 蓝色 | 🔵 |

---

## 4. 公共组件规范

### 4.1 StatusBadge.vue

```vue
<!-- 状态标签组件 -->
<!-- Props: status: 'ok' | 'error' | 'unknown' | string -->
<!-- 自动映射: ok → 绿色, error → 红色, 其他 → 灰色 -->

<template>
  <el-tag :type="tagType" size="small" effect="dark" round>
    <el-icon v-if="status === 'ok'"><Check /></el-icon>
    <el-icon v-else-if="status === 'error'"><Close /></el-icon>
    {{ label }}
  </el-tag>
</template>
```

### 4.2 SyncButton.vue

```vue
<!-- 同步按钮组件 -->
<!-- Props: kind: 'full_sync' | 'usage_sync' | 'asset_sync' -->
<!-- Props: label: string -->
<!-- 点击后自动管理 loading 状态 + 成功/失败通知 -->

<template>
  <el-button
    type="primary"
    :loading="loading"
    @click="handleSync"
  >
    {{ label }}
  </el-button>
</template>
```

### 4.3 EmptyState.vue

```vue
<!-- 空状态组件 -->
<!-- Props: description?: string -->
<!-- Props: icon?: string -->

<template>
  <el-empty :description="description" :image-size="120" />
</template>
```

### 4.4 DataTable.vue

```vue
<!-- 通用数据表格封装 -->
<!-- Props: data, columns, loading, pagination -->
<!-- 自动处理: 加载态骨架屏、空状态、分页、排序 -->

<template>
  <el-table
    v-loading="loading"
    :data="paginatedData"
    stripe
    border
    style="width: 100%"
  >
    <el-table-column
      v-for="col in columns"
      :key="col.prop"
      v-bind="col"
    />
  </el-table>
  <el-pagination
    v-if="pagination"
    v-model:current-page="currentPage"
    v-model:page-size="pageSize"
    :total="data.length"
    layout="total, prev, pager, next"
    :page-sizes="[20, 50, 100]"
    style="margin-top: 16px; justify-content: flex-end"
  />
</template>
```

---

## 5. 交互模式

### 5.1 全局 Loading 状态

| 层级 | 方式 | 触发时机 |
|------|------|----------|
| 路由切换 | `NProgress` 顶部进度条 | 每次路由跳转 |
| 页面数据 | `el-table v-loading` / `el-skeleton` | API 请求中 |
| 按钮操作 | `el-button loading` prop | POST/PUT/DELETE 请求中 |
| 全局 | `ElLoading.service()` | 极少使用，仅全量同步时 |

### 5.2 用户通知

| 类型 | 方法 | 场景 |
|------|------|------|
| 成功 | `ElMessage.success(msg)` | 保存成功、删除成功、同步启动 |
| 警告 | `ElMessage.warning(msg)` | Token 即将过期 |
| 错误 | `ElMessage.error(msg)` | API 失败、网络错误 |
| 确认 | `ElMessageBox.confirm(msg, title)` | 删除操作、危险操作 |
| 信息 | `ElMessage.info(msg)` | 操作提示 |

### 5.3 错误处理

```typescript
// 全局 Axios 拦截器
axios.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 404) {
      ElMessage.error('资源不存在')
    } else if (error.response?.status >= 500) {
      ElMessage.error('服务器错误，请稍后重试')
    } else if (error.message?.includes('Network')) {
      ElMessage.error('网络连接失败，请检查代理/VPN/防火墙')
    } else {
      ElMessage.error(error.response?.data?.error || error.message || '请求失败')
    }
    return Promise.reject(error)
  }
)
```

### 5.4 表格通用交互

- **排序:** 点击表头切换 升序 → 降序 → 取消
- **筛选:** 部分列支持表头筛选器（账号列、状态列）
- **分页:** 默认每页 20 条，可切换 50/100
- **空状态:** 无数据时显示 `el-empty`
- **加载态:** 请求中显示骨架屏 `el-skeleton`（3 行占位）

---

## 6. 动画规范

| 场景 | 动画 | 时长 | 缓动 |
|------|------|------|------|
| 页面切换 | 淡入 `opacity 0→1` + 轻微上移 `translateY(8px→0)` | 200ms | ease-out |
| 弹窗打开 | ElDialog 默认 | 300ms | ease |
| 卡片数字 | 数字滚动 0→N | 600ms | ease-out |
| 侧边栏折叠 | 宽度 220→64px + 文字 opacity | 250ms | ease-in-out |
| 暗色模式切换 | CSS 变量过渡 | 300ms | ease |
| 按钮 hover | background 颜色 | 150ms | ease |
| Badge 状态变更 | 颜色渐变 | 200ms | ease |

---

## 7. 暗色模式规范

### 7.1 实现方式

```typescript
// 使用 VueUse
import { useDark, useToggle } from '@vueuse/core'
const isDark = useDark({ storageKey: 'cfm-theme' })
const toggleDark = useToggle(isDark)
```

### 7.2 切换机制

- 顶栏右侧：太阳/月亮图标按钮
- 首次访问：跟随系统 `prefers-color-scheme`
- 持久化：`localStorage` key `cfm-theme`
- 过渡：`<html>` 元素添加 `transition: background-color 300ms, color 300ms`

### 7.3 Element Plus 暗色主题

```typescript
// 使用 Element Plus 内置暗色模式
import 'element-plus/theme-chalk/dark/css-vars.css'
// 在 <html> 上切换 class="dark"
```

---

## 8. 路由规范

```typescript
const routes: RouteRecordRaw[] = [
  { path: '/',           redirect: '/dashboard' },
  { path: '/dashboard',  component: () => import('@/views/DashboardView.vue') },
  { path: '/accounts',   component: () => import('@/views/AccountsView.vue') },
  { path: '/search',     component: () => import('@/views/SearchView.vue') },
  { path: '/workers',    component: () => import('@/views/WorkersView.vue') },
  { path: '/pages',      component: () => import('@/views/PagesView.vue') },
  { path: '/zones',      component: () => import('@/views/ZonesView.vue') },
  { path: '/dns',        component: () => import('@/views/DnsView.vue') },
  { path: '/routes',     component: () => import('@/views/RoutesView.vue') },
  { path: '/usage',      component: () => import('@/views/UsageView.vue') },
  { path: '/jobs',       component: () => import('@/views/JobsView.vue') },
  { path: '/alerts',     component: () => import('@/views/AlertsView.vue') },
]
```

- 所有路由使用 **懒加载** `() => import(...)`
- 路由切换时自动加载数据（在组件 `onMounted` 或 `watch` 路由）
- URL 参数同步搜索/筛选状态（如 `/dns?zone=xxx`）

---

## 9. API 对接规范

### 9.1 Axios 实例

```typescript
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})
```

### 9.2 API 映射

| 前端方法 | HTTP | 路径 | 说明 |
|----------|------|------|------|
| `getDashboardSummary()` | GET | `/api/dashboard/summary` | 仪表盘汇总 |
| `getAccounts()` | GET | `/api/accounts` | 账号列表 |
| `createAccount(data)` | POST | `/api/accounts` | 新增账号 |
| `updateAccount(id, data)` | PUT | `/api/accounts/:id` | 编辑账号 |
| `deleteAccount(id)` | DELETE | `/api/accounts/:id` | 删除账号 |
| `testAccountToken(id)` | POST | `/api/accounts/:id/test-token` | 检测 Token |
| `getWorkers()` | GET | `/api/workers` | Workers 列表 |
| `getPages()` | GET | `/api/pages` | Pages 列表 |
| `getZones()` | GET | `/api/zones` | Zones 列表 |
| `getDnsRecords()` | GET | `/api/dns-records` | DNS 记录列表 |
| `getRoutes()` | GET | `/api/routes` | Routes 列表 |
| `getUsageAccounts()` | GET | `/api/usage/accounts` | 账号用量 |
| `getUsageWorkers()` | GET | `/api/usage/workers` | Worker 用量 |
| `getSyncJobs()` | GET | `/api/sync/jobs` | 巡检任务 |
| `getSyncRuns()` | GET | `/api/sync/runs` | 执行记录 |
| `getAlerts()` | GET | `/api/alerts` | 告警列表 |
| `runSync(kind)` | POST | `/api/sync/run-now` | 手动触发巡检 |
| `search(q)` | GET | `/api/search?q=xxx` | 全局搜索 |
| `diagnose()` | GET | `/api/diagnostics/cloudflare` | 网络诊断 |

### 9.3 Pinia Store 设计

```typescript
// stores/account.ts
export const useAccountStore = defineStore('account', () => {
  const accounts = ref<Account[]>([])
  const loading = ref(false)

  async function fetchAccounts() {
    loading.value = true
    try {
      accounts.value = await accountApi.list()
    } finally {
      loading.value = false
    }
  }

  return { accounts, loading, fetchAccounts }
})

// stores/dashboard.ts
export const useDashboardStore = defineStore('dashboard', () => {
  const summary = ref<DashboardSummary | null>(null)
  const loading = ref(false)

  async function fetchSummary() { /* ... */ }

  return { summary, loading, fetchSummary }
})

// stores/app.ts
export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const isDark = useDark({ storageKey: 'cfm-theme' })
  const toggleSidebar = () => { sidebarCollapsed.value = !sidebarCollapsed.value }
  const toggleDark = useToggle(isDark)

  return { sidebarCollapsed, isDark, toggleSidebar, toggleDark }
})
```

---

## 10. 构建与部署

### 10.1 开发模式

```bash
# 终端 1: Python 后端
python server.py  # 运行在 localhost:8787

# 终端 2: Vite 前端
cd frontend && npm run dev  # 运行在 localhost:5173
# Vite 代理 /api → http://localhost:8787
```

### 10.2 生产构建

```bash
cd frontend && npm run build
# 输出到 frontend/dist/
# 复制到 static/dist/ 供 Python 服务
```

### 10.3 vite.config.ts 代理配置

```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8787',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: '../static/dist',
    emptyOutDir: true,
  },
})
```

---

## 附录 A: 原有页面 → 新页面映射

| 原 HTML section | 新路由 | 新视图组件 |
|-----------------|--------|-----------|
| `#dashboard` | `/dashboard` | `DashboardView.vue` |
| `#accounts` | `/accounts` | `AccountsView.vue` |
| `#search` | `/search` | `SearchView.vue` |
| `#workers` | `/workers` | `WorkersView.vue` |
| `#pages` | `/pages` | `PagesView.vue` |
| `#zones` | `/zones` | `ZonesView.vue` |
| `#dns` | `/dns` | `DnsView.vue` |
| `#routes` | `/routes` | `RoutesView.vue` |
| `#usage` | `/usage` | `UsageView.vue` |
| `#jobs` | `/jobs` | `JobsView.vue` |
| `#alerts` | `/alerts` | `AlertsView.vue` |

## 附录 B: 文件大小预算

| 资源 | 目标 | 说明 |
|------|------|------|
| JS 总包 (gzipped) | < 200KB | Element Plus 按需引入 |
| CSS (gzipped) | < 50KB | Element Plus 主题 |
| 首屏加载 | < 1.5s | 懒加载 + 代码分割 |
| 图表库 | < 100KB | ECharts 按需引入 |

## 附录 C: TypeScript 类型定义

```typescript
// api/types.ts

interface Account {
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

interface Worker {
  id: number
  account_db_id: number
  script_name: string
  modified_on: string
  last_seen_at: string | null
  account_alias: string
}

interface PagesProject {
  id: number
  account_db_id: number
  project_name: string
  subdomain: string
  production_branch: string
  latest_deployment_status: string | null
  domains_count: number
  last_seen_at: string | null
  account_alias: string
}

interface Zone {
  id: number
  account_db_id: number
  zone_id: string
  name: string
  status: string
  type: string
  dns_count: number
  routes_count: number
  last_seen_at: string | null
  account_alias: string
}

interface DnsRecord {
  id: number
  account_db_id: number
  zone_db_id: number
  record_id: string
  type: string
  name: string
  content: string
  ttl: number
  proxied: boolean
  last_seen_at: string | null
  zone_name: string
  account_alias: string
}

interface WorkerRoute {
  id: number
  account_db_id: number
  zone_db_id: number
  route_id: string
  pattern: string
  script_name: string
  last_seen_at: string | null
  zone_name: string
  account_alias: string
}

interface UsageAccountDaily {
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

interface UsageWorkerDaily {
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

interface SyncJob {
  id: number
  name: string
  job_type: string
  enabled: boolean
  interval_minutes: number
  time_window_start: string
  time_window_end: string
  high_usage_interval_minutes: number
  critical_interval_minutes: number
  last_run_at: string | null
}

interface SyncRun {
  id: number
  account_db_id: number | null
  run_type: string
  status: 'success' | 'failed' | 'running'
  started_at: string
  duration_ms: number | null
  api_calls_count: number
  error_message: string | null
  account_alias: string | null
}

interface Alert {
  id: number
  account_db_id: number | null
  target_type: string
  target_name: string
  level: 'critical' | 'danger' | 'warning' | 'info'
  title: string
  message: string
  current_value: number | null
  threshold_value: number | null
  status: 'open' | 'resolved'
  last_triggered_at: string | null
  account_alias: string | null
}

interface DashboardSummary {
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

interface SearchResult {
  q: string
  results: {
    workers: Worker[]
    pages: PagesProject[]
    pages_domains: any[]
    zones: Zone[]
    dns_records: DnsRecord[]
    routes: WorkerRoute[]
  }
}
```
