# Feishu-Backed Storyboard Architecture

## Architecture

```
飞书多维表格（数据库）
     ↑↓ REST API
  build_html.py（静态再生：读飞书 → 套模板 → 出 HTML）
     ↓
  HTML 前端（EDL 暗调主题）
     ← shotlist_server.py（动态代理，8089 端口）
        ↑↓ fetch('/api/feishu')
        → open.feishu.cn（无 CORS 问题的服务器端调用）
```

## v2 Field Schema (20 columns)

| # | 字段 | 类型 | 说明 |
|---|------|------|------|
| ★ | 镜号 | Text（主字段） | 主字段不可删/改类型 |
| 2 | 运镜 | Text | 固定/手持/拉跟/横移/上摇... |
| 3 | 空间关系 | Text | `[位置标签] + emoji` 格式 |
| 4 | 景别 | **Text** | 含 ★ 星级 + ↓ 过渡 + 焦段·景深，HTML 格式化后搬运 |
| 5 | 焦段 | Text | 50mm/35mm... |
| 6 | 景深 | SingleSelect | 浅/中/深 |
| 7 | 机位 | SingleSelect | 🔴 正打/🟡 反打/🟢 第三人称/🔵 空间环境/🟣 插入/切出 |
| 8 | 动作调度 | Text | |
| 9 | 台词 | Text | |
| 10 | 时长(秒) | Number | |
| 11 | 音频 | Text | |
| 12 | 导演备注 | Text | |
| 13 | 提示词 | Text | |
| 14 | **beat序号** | Text | `1`/`2`/`3`/`空间` |
| 15 | **beat类型** | SingleSelect | ⚪ 填充 / 🔴 戏点 |
| 16 | **beat标题** | Text | 纯名称：`被领导打压`（HTML 组装时加前缀 `beat N：` 和后缀 `(N 镜)`） |
| 17 | **节拍动作** | Text | 仅 beat 第一镜填写。`外界动作 → 人物反应`，`→` 分隔，HTML 按 `<br>` 分行 |
| 18 | **节拍属性** | SingleSelect | 触发 / 动作镜 / 反应镜 / 建立 / 插入。定义见模块2 v1 的「叙事角色 5 种」 |
| 19 | **视点角色** | Text | 本场戏通过谁的视角讲述（如 `👤男人`）。单场所有镜头通常相同 |
| 20 | **场次** | Text | 场景标识：`s010` / `s020` / ... 全表不拆表，靠此字段区分 |

### Beat Grouping

HTML 渲染时按 `beat序号` 分组：
- `空间` → 渲染为 `▸ 空间建立镜 (N 镜)` 标签，绿色
- 数字（1-6）→ 渲染为 beat 区块：类型标签（⚪ 灰底 / 🔴 红底高亮）+ 标题 + 可选节拍动作
- 设计意图从模块1分析报告引用，不存数据库

## Key Design Decisions

### 景别: Text vs SingleSelect

推拉摇移镜头有景别过渡（如 `近景 ★★★★ ↓ 中全 ★★`），单选只能存一个值。文本字段直接存完整描述（含 ★ 星级、↓ 过渡、焦段·景深），HTML 只搬运不加工。代价：失去飞书原生筛选/统计能力——但导演创作不需要。

### 机位简写映射

飞书存全称（🔵 空间环境），旧 HTML 用简写（🔵环）。`build_html.py` 中 `JIWEI_MAP` 做映射。

### 节拍动作 vs 节拍属性（不同层级）

- **节拍动作** — beat 级别的上下文，存**一个 beat 一份**（不是每个镜头一份）。独立于镜头表，存在节拍分析表中。外界动作 + 人物反应，`→` 分隔，HTML 渲染时分两行（`<br>`）。
- **节拍属性** — 镜头级别的标记，**每个镜头一个**。五种叙事角色（触发 / 动作镜 / 反应镜 / 建立 / 插入），定义见模块2 v1。

二者关系：先确定视点角色 → 外界动作是视点角色无法选择的事件 → 人物反应是视点角色的应对 → 每个镜头从这个 beat 动作中切割出一个具体叙事角色（谁在动？外界还是角色？）。

### 数据 vs 装饰文本

外界动作和人物反应是一个完整叙述（`领导咆哮 → 他移开手机绷紧`），拆成两列反而割裂。一个「节拍动作」文本字段，用 `→` 分隔，HTML 里自然渲染成两段。设计意图不存数据库，从模块1分析报告引用。

## Why Proxy (Not Direct Fetch)

Feishu OpenAPI does NOT return CORS headers (confirmed via `curl -X OPTIONS`). Any browser JS call to `open.feishu.cn` is blocked. Proxy runs on NAS, same-origin for HTML, forwards server-side.

## Server Persistence

Docker `nohup` dies on restart. Permanent: UGREEN NAS → Control Panel → Task Scheduler → Add startup task:
```
python3 /opt/data/skills/scriptwriting/storyboard-shotlist/scripts/shotlist_server.py
```

### Prompt Panel UX (2026-07-11)

**面板布局：**
- 头部：左 `提示词` 标题 + 右 `📋 复制` `📌 钉住` `✕`
- `.prompt-toggle` 绿色行：`镜 02, 03`（覆盖镜头列表，横排）
- `.prompt-inherit` 红色行：`↑ 继承自 镜02`（仅继承时显示）
- `.prompt-text` 正文区：白色文字，微内阴影 + 暗底（像纸浮在面板上）

**标题徽标（badge headings）：**
- 提示词正文中的子标题自动识别为彩色小徽标：`场景`、`空间锚`、`镜头一`、`镜头二`、`演`、`拍`、`呈`、`@图片N` 等
- 徽标用 1px 彩色边框 + 小号加粗字体：场景=黄、空间锚=蓝、镜头=紫、演=金、拍=蓝、呈=红
- 解析函数 `parsePromptBlocks()` 自动拆分行 → 匹配标题 → 生成 `<span class="prompt-badge" style="border-color:...">`

**交互增强：**
- 头部 `sticky` 固顶，长提示词滚动不丢上下文
- 左边缘拖拽柄调宽度（320–900px）。`closePrompt()` 必须重置 `panel.style.width = ''`——否则拖宽后面板 `right:-540px` + 自设宽度 > 540 会露出一截
- 📌 钉住按钮：钉住后面板不随点击关闭，遮罩自动隐藏。`closePrompt()` 同时清除钉住状态
- 面板滑出弹性缓动 `cubic-bezier(.25,.8,.25,1)`
- 正文切换淡入动画 `fadeIn .3s`
- 复制按钮弹跳 `copyBounce` 动画。HTTP 环境用 textarea fallback（`document.execCommand('copy')`）

点击任意镜头行 → 右侧滑出面板。所有共享同一提示词的镜头同时高亮（`.clicked` 类，仅背景色 `rgba(244,63,94,.12)`）。关闭时 `.clicked` 全清。

### 提示词继承（↑ 上线模式）

提示词字段三种写法，面板自动解析：

| 飞书里填 | 面板显示 |
|----------|---------|
| 正文 | 直接显示 |
| `↑s010-02` | `↑ 继承自 镜02` + 02 的完整正文 |
| 空 | 暂无提示词 |

- 支持链式继承：`↑05` → 05 写 `↑02` → 最终显示 02
- 支持简写（`↑02`，同场次内）和全称（`↑s010-02`，跨场次可读）
- JS 用 `visited` 集合防止循环引用死循环
- `attachPromptClicks()` 在页面加载、Tab 切换、刷新后自动调用

### Multi-Scene Single Table

整个剧本的所有场次存在**同一个**多维表格里，不拆表。通过「场次」字段区分：

| 字段 | 类型 | 说明 |
|------|------|------|
| 场次 | Text | `s010` / `s020` / ... 全表唯一场景标识 |

`build_html.py` 组装时按场次筛选，每场产出一个独立的 HTML 文件。提示词跨镜继承 `↑s010-02` 格式自描述，飞书里肉眼可读。

### 标题徽标（badge headings）— 当前状态

三方案对比中（2026-07-11）：
- **A 实心小药丸** — `场景`、`人物`：彩色椭圆底 + 深色字
- **B 左侧竖条** — `空间锚`、`镜头一/二/X`：`border-left` 覆盖整段
- **C 彩色圆点** — 其余标题：`● ` 彩色前缀
- **演/拍/呈 不带色标**（用户明确排除）

用户尚未选定，当前三方案并存对照。`parsePromptBlocks()` 在模板 JS 中。

### 字体

提示词正文用**无衬线**（继承全局 font），不用 Georgia/serif。用户认为衬线体在面板中杂乱。

## Common Pitfalls

- **URL params in credentials** (MOST COMMON): `OwBSbEQS...?table=...&view=...` instead of pure IDs → API returns `code=0` with 0 records → empty table with no error.
- **`file://` doesn't work**: open via `http://192.168.3.65:8089/...` not SMB double-click.
- **Server hangs on refresh**: Python `http.server.HTTPServer` is single-threaded. A slow Feishu API call blocks ALL other requests. Fix: use `socketserver.ThreadingMixIn` (already applied in `shotlist_server.py` v2). Symptom: page loads blank, health check times out, refresh spins forever.
- **Row highlight**: `tbody tr:hover` = background only, no box-shadow/transition. Clicked = same style via `.clicked` class. `closePrompt()` removes `.clicked` from all rows. User rejected multi-color scheme.
- **Refresh beat grouping**: JS `refreshFromFeishu()` rebuilds beat-section blocks (not flat table). Must call `attachPromptClicks()` after refresh.
- **coveredLabel used before definition**: JS computes `coveredLabel` from highlight loop → MUST place this BEFORE the `document.getElementById('prompt-shot-num').textContent = coveredLabel` line. Failure: panel silently breaks (no error thrown, just doesn't open).
- **copy button on HTTP**: `navigator.clipboard.writeText` requires HTTPS/localhost. Use textarea fallback (`document.execCommand('copy')`) for `http://192.168.x.x` origins.
- **JS brace discipline in HTML templates**: When using `patch` to edit JavaScript inside HTML, stray `};` from incomplete replacements silently break all JS on the page (rows lose click handlers, panel won't open, cursor:pointer gone). Symptom: page loads fine visually but zero interactivity. Verify with `{count} - }count = 0` after every JS edit.
- **`if (sn === shotNum) return` kills highlight**: Skipping the clicked row in the highlight loop prevents its own `.clicked` from being added. Fix: `if (sn === shotNum) { r.classList.add('clicked'); return; }` — highlight self but skip double-count.
- **closePrompt must reset panel.style.width**: After user drags panel wider, closing leaves a visible sliver because `right:-540px` + custom width > 540px. Fix: `panel.style.width = ''` in closePrompt.
- **Drag + pin + close interaction**: `closePrompt()` must handle all three states: remove `.open`, remove `.pinned`, reset `style.width`, reset pin button class. Any one missing → visible glitch.
- **景别 was SingleSelect**: old version forced single value, losing ↓ transitions. Now changed to Text.
- **Primary field**: can't delete or change type of the first column. Rename instead.
- **Field rename**: breaks `build_html.py` field name mapping. Update script if renaming.
- **Records fetch needs GET**: Feishu token endpoint uses POST, records endpoint uses GET. Proxy detects method by presence/absence of body.
- **Column visibility**: Only c11 (提示词) is zero-width hidden. c9/c10 always visible. Old hide-c11 toggle removed.
- **nth-child fragility**: Adding/removing columns shifts all nth-child indices. Must grep + verify all selectors after any column change.
