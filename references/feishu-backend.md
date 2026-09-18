# Feishu-Backed Storyboard Architecture

## Architecture

```
飞书多维表格（数据库）
     ↑↓ REST API (direct curl from Agent)
     ↑↓ REST API (via proxy for browser)
  Agent (terminal curl)          shotlist_server.py (8089 端口)
     ↑ 读 feishu_config.json        ↑ 读 feishu_config.json
     └── SKILL.md 同级目录           └── (待实现：目前仍透传浏览器凭证)
```

**凭证存放：** `feishu_config.json`（与 SKILL.md 同目录）。Agent 和 server 共享这个文件，浏览器不存凭证。格式：

```json
{
  "app_id": "cli_...",
  "app_secret": "...",
  "app_token": "OwBSbEQS...",
  "table_id": "tbl..."
}
```

**Agent 直接调飞书 API：** Agent 从 `feishu_config.json` 读凭证 → `curl` 拿 token → `curl` 读写记录。不走代理——代理是给浏览器解决 CORS 用的，Agent 在 NAS 上不需要。

**提示词写回：** 使用 Feishu REST API 的 PUT（不是 PATCH）更新记录的 `提示词` 字段。镜号之间的继承用 `↑s010-NN` 标记，面板 JS 自动解析。

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

## 分析表（模块1 节拍分析）

同一应用内第二张表（`analysis_table_id`），与分镜表通过 `场次` 字段 JOIN。18 字段覆盖模块1 全部输出：节拍表 + 场景价值声明 + 节奏曲线 + 预估镜头数。

**表结构：** `场次`(text) / `场景价值`(text) / `起点极`(text) / `终点极`(text) / `翻转`(text) / `视点角色`(text) / `节拍序号`(number) / `节拍名称`(text) / `外界动作`(text) / `人物反应`(text) / `类型`(select: 🔴戏点/🟡空间建立/⚪填充) / `闭环`(select: ✅/⚠️未闭环) / `说明`(text) / `节奏段落`(number) / `节奏描述`(text) / `情绪温度`(number) / `节奏密度`(select: 慢/中/快) / `预估总镜头数`(number)

**前端渲染：** `build_html.py` 拉两张表 → 按场次 JOIN → 每场 scene section 下生成两个子 Tab：`节拍分析`（beat 子 Tab，默认不选中，手动切换）+ `v2 分镜`（默认选中）。CSS 占位符系统自动为 beat 子 Tab 生成 `#sub-beat-{sid}` 规则。

**建表能力：** 飞书 API `app_id/app_secret` 授权整个应用——可创建表（`POST /bitable/v1/apps/{app_token}/tables`）、加字段（`POST .../tables/{table_id}/fields`）、删表。无需额外权限。`feishu_config.json` 中的 `analysis_table_id` 记录分析表 ID。

## Why Proxy (Not Direct Fetch)

Feishu OpenAPI does NOT return CORS headers (confirmed via `curl -X OPTIONS`). Any browser JS call to `open.feishu.cn` is blocked. Proxy runs on NAS, same-origin for HTML, forwards server-side.

**Proxy HTTP method override:** The proxy defaults to forwarding requests with the same method. For Feishu record updates (which require PUT), browser JS passes `_method:'PUT'` in the JSON body, and the proxy uses it instead of the incoming POST method.

### `/api/generate-prompts` — 前端一键生成提示词

**请求：** `POST /api/generate-prompts` + `{"shots": ["13","14","15"]}`

**流程：** 读 `feishu_config.json` → 拉飞书全场数据 → 找上游提示词组的共享声明 → 读 `m4-prompt-template.md` 拼 system prompt → 调 DeepSeek API → PUT 写回飞书 → 返回结果。

**依赖：** `feishu_config.json` 中必须有 `deepseek_api_key` 字段。

**前端集成：** 每行左侧 checkbox（`.shot-chk`），info bar 中「⚡ 生成提示词」按钮（JS 动态注入）。勾选镜头 → 点按钮 → loading → 自动 🔄 刷新。复选框列通过 `buildRow` 中的 `<td class="c-sel">` 渲染。

## Server Persistence

Docker `nohup` dies on restart. Permanent: UGREEN NAS → Control Panel → Task Scheduler → Add startup task:
```
python3 /opt/data/skills/scriptwriting/storyboard-shotlist/scripts/shotlist_server.py
```

### Prompt Panel UX (2026-07-11: floating window; 2026-07-13: in-place edit)

**面板架构：浮动窗口（非右滑）。** `position:fixed` + 四条边四角 resize 手柄 + 标题栏 drag。

**面板布局：**
- 头部（drag handle）：左 `提示词` 静态标题 + 覆盖镜头号（`镜 02, 03`） + 右按钮行 `编辑` `💾保存` `复制` `✕`。按钮统一样式：`panel-btn` class，红底白字，hover 变空心红框红字。全中文全词，无 emoji。
- `.prompt-text` 正文区：微内阴影 + 暗底。编辑态：边框变琥珀色 `rgba(245,158,11,.5)`，背景微暖 `rgba(245,158,11,.04)`。

**提示词就地编辑（2026-07-13）：**
- 点击「编辑」→ 正文变 `contentEditable` → 按钮切换为「💾 保存」→ 边框琥珀色
- 保存：`fetch('/api/feishu')` → 拿 token → PUT 写回飞书 `提示词` 字段
- 继承链（↑s010-02）：保存到源镜头的 `targetRecordId`
- `data-record-id`：`build_html.py` 和 `refreshFromFeishu` 都在 `<tr>` 上挂此属性，编辑功能依赖它定位 Feishu 记录
- 保存成功：按钮显示「✅ 已保存」2 秒后隐藏
- `.prompt-covered` 绿色行：`镜 02, 03`（覆盖镜头列表，横排）
- `.prompt-inherit` 红色行：`↑ 继承自 镜02`（仅继承时显示）
- `.prompt-text` 正文区：微内阴影 + 暗底（像纸浮在面板上），右上角 `📋 复制` 按钮
- `.prompt-body` `overflow-y:auto`，头部不 sticky（浮动窗口不需要）

**交互：**
- **拖动**：按住标题栏拖到任意位置。约束在视口内（上下左右四边碰撞）。
- **调整大小**：四条边 + 四角共 8 个不可见手柄（`cursor:n-resize` 等），320×200 最小。
- **贴靠**：`⏭` 吸到右边缘撑全高 / `⏬` 吸到底边缘撑全宽。
- **📌 钉住**：切镜头面板不动。遮罩自动隐藏。
- **状态持久化**：`_saveState()` 在 `closePrompt()` 前保存 `left/top/width/height`，`_restoreState()` 在 `openPrompt()` 后恢复。支持 `left:auto`（右贴靠态）。浏览器刷新前一直记忆。
- **复制按钮**：在头部按钮行，`panel-btn` 同款样式。HTTP 环境 textarea fallback，复制成功弹跳动画。
- 正文切换淡入 `fadeIn .3s`。
- 无提示词的镜头也弹面板（显示「暂无提示词」，无复制按钮）。`document.getElementById('prompt-copy')` 可能为 null，必须判空。
- 点击行 → 群组高亮（`.clicked` 类，仅 `rgba(244,63,94,.12)` 背景）。关闭清空。

**标题徽标（C 风格彩色圆点）：**
- 提示词正文子标题：`● ` 彩色前缀 + 标题文字同色。覆盖 `@图片N` `场景` `空间锚` `人物` `镜头一/二/X` `视角` `光线` `调色` `氛围` 等 — **不标注演/拍/呈**。
- 所有标题统一 C 风格（`styleMap = {}`），无 A/B 混用。
- 解析函数 `parsePromptBlocks()` 按行拆分 → 正则匹配标题 → 生成 `<div class="prompt-line-c"><span class="prompt-badge-c">`。
- 字体：提示词正文用**无衬线**（继承全局），不用衬线。用户认为衬线体在面板中杂乱。

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

### 标题徽标（badge headings）— 已确定 C 风格

用户选择 **C 彩色圆点**，全标题统一。`● ` 彩色前缀 + 标题文字同色。覆盖：`@图片N`、`场景`、`空间锚`、`人物`、`镜头一/二/X`、`视角`、`光线`、`调色`、`氛围`等。演/拍/呈 不标注。`parsePromptBlocks()` 在模板 JS 中，`prompt-badge-c` class 渲染。

### 字体

提示词正文用**无衬线**（继承全局 font），不用 Georgia/serif。用户认为衬线体在面板中杂乱。

## Common Pitfalls

- **URL params in credentials** (MOST COMMON): `OwBSbEQS...?table=...&view=...` instead of pure IDs → API returns `code=0` with 0 records → empty table with no error.
- **Agent scrapes browser DOM for Feishu data (反模式)**: 飞书数据唯一来源是 REST API。Agent 不应通过 `browser_console` / `browser_snapshot` 抓取渲染后的 DOM 来获取分镜数据——慢、不可靠、且拿不到 record_id。正确做法：读 `feishu_config.json` → `curl` 直接调飞书 API。
- **Agent generates prompt but doesn't write back**: 模块4 生成提示词后必须 PUT 写回飞书 `提示词` 字段。只输出文本不写回 → 数据丢失，浏览器 🔄 刷新后消失。
- **`file://` doesn't work**: open via `http://192.168.3.65:8089/...` not SMB double-click.
- **Server hangs on refresh**: Python `http.server.HTTPServer` is single-threaded. A slow Feishu API call blocks ALL other requests. Fix: use `socketserver.ThreadingMixIn` (already applied in `shotlist_server.py` v2). Symptom: page loads blank, health check times out, refresh spins forever.
- **Row highlight**: `tbody tr:hover` = background only, no box-shadow/transition. Clicked = same style via `.clicked` class. `closePrompt()` removes `.clicked` from all rows. User rejected multi-color scheme.
- **Refresh beat grouping**: JS `refreshFromFeishu()` rebuilds beat-section blocks (not flat table). Must call `attachPromptClicks()` after refresh.
- **coveredLabel used before definition**: JS computes `coveredLabel` from highlight loop → MUST place this BEFORE the `document.getElementById('prompt-shot-num').textContent = coveredLabel` line. Failure: panel silently breaks (no error thrown, just doesn't open).
- **copy button on HTTP**: `navigator.clipboard.writeText` requires HTTPS/localhost. Use textarea fallback (`document.execCommand('copy')`) for `http://192.168.x.x` origins.
- **JS brace discipline in HTML templates**: When using `patch` to edit JavaScript inside HTML, stray `};` from incomplete replacements silently break all JS on the page (rows lose click handlers, panel won't open, cursor:pointer gone). Symptom: page loads fine visually but zero interactivity. Verify with `{count} - }count = 0` after every JS edit.
- **`if (sn === shotNum) return` kills highlight**: Skipping the clicked row in the highlight loop prevents its own `.clicked` from being added. Fix: `if (sn === shotNum) { r.classList.add('clicked'); return; }` — highlight self but skip double-count.
- **Drag width persistence**: After user drags panel wider, the width persists across open/close (until browser refresh). `closePrompt()` does NOT reset width — it sets `panel.style.right = panel._closeOffset` (computed from current width) to slide fully off screen. `_closeOffset` stored in `openPrompt()` when panel opens.
- **Drag + pin + close interaction**: `closePrompt()` handles: remove `.open` and `.pinned`, set `panel.style.right` (dynamic close offset, preserves width), hide overlay, clear `.clicked`. Pin button class reset separately.
- **景别 was SingleSelect**: old version forced single value, losing ↓ transitions. Now changed to Text.
- **Primary field**: can't delete or change type of the first column. Rename instead.
- **Field rename**: breaks `build_html.py` field name mapping. Update script if renaming.
- **Records fetch needs GET**: Feishu token endpoint uses POST, records endpoint uses GET. Proxy detects method by presence/absence of body.
- **Column visibility**: Only c11 (提示词) is zero-width hidden. c9/c10 always visible. Old hide-c11 toggle removed.
- **`nth-child` fragility**: Adding/removing columns shifts all nth-child indices. Must grep + verify all selectors after any column change.
- **closePrompt must call `_saveState()` before removing `.open`**: Floating window model. Omit → next `openPrompt()` can't restore dragged position. Panel either snaps to default or silently fails.
- **Null-safe copy button**: `document.getElementById('prompt-copy')` is null when prompt text is empty (button not in DOM). `if (copyBtn) { ... }` mandatory — null.onclick = TypeError kills entire `openPrompt`.
- **`_restoreState` must handle `left:auto`**: After right-snap (`right:8px; left:auto`), `_left='auto'`. Must branch: auto → restore `right`; else → restore `left`. Failure → right-snapped panel reopens on left.
- **Drag bottom boundary**: `window.innerHeight - panel.offsetHeight - 10`, not fixed `-40`. Failure → drag below viewport.
- **Brace balance after EVERY JS edit**: `{count} - }count = 0` verification mandatory. Even 1-brace mismatch (e.g., missing `}` after `if (copyBtn) { ... ;}`) kills ALL page interactivity silently.

- **`\n` in Feishu text → `<br>` in HTML**: Feishu API returns multi-line text fields with real `\n` characters. HTML renders `\n` as whitespace, not line break. Fields like 空间关系 that use multi-line formatting MUST convert `\n` → `<br>` in BOTH `build_html.py` AND JS `refreshFromFeishu`. 景别 uses `↓` as separator instead — handled by `format_sheyingji()`, no `\n` conversion needed.

- **`<wbr>` for bracket boundaries**: 空间关系 field uses `[位置标签]` format. Insert `<wbr>` before `[` to create soft line-break opportunities so text wraps naturally at bracket boundaries when the column narrows.

- **Inline style cleanup**: After changing button classes via `execute_code`, grep the output for leftover inline `fontSize`/`padding` styles from previous iterations. Inline styles override CSS classes and produce size inconsistencies that are invisible in template diffs. Snap buttons carried `fontSize='14px'` for multiple sessions undetected.

- **Column resize cross-beat sync**: Each beat-section has its own `<table>` with its own `<colgroup>`. On `mousedown`, lock ALL colgroups to current computed pixel widths. On `mousemove`, set the target column width and sync that same column index across ALL colgroups. Without cross-sync, only the table being dragged changes.

- **Column width model**: `table-layout:fixed` + `width:100%`. Most columns use fixed pixel widths (42–180px). Only c6（动作调度）uses `width:auto;max-width:300px` — it absorbs all remaining space. This is NOT proportional — only one elastic column. If resizing narrows c6 below 300px, table overflows with horizontal scrollbars.
