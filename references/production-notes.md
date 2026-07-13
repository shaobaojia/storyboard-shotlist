# 生产笔记 — 分镜实战经验

## 运镜术语（非标准但实用）

| 术语 | 含义 | 适用场景 |
|------|------|------|
| 拉跟 | dolly back + tracking，镜头在前方后退，人物朝镜头走 | 正面跟拍行走中的人物 |
| 拉+微摇 | dolly back + slight pan，后退同时微调角度 | OTS绕到正面，景别从松到紧 |
| 上摇 | tilt up，从下往上摇 | 手机屏幕元素的垂直浏览 |
| 拉跟→停 | dolly back tracking 然后停下 | 人物边走边接电话→停下，镜头随之停 |

## 镜头合并判断逻辑

当两个相邻镜头满足以下条件时，优先考虑合并为一个长镜头：
1. 动作/情绪是一个连续流，中间没有明显的节拍断点
2. 景别变化可以通过运镜（拉/推/摇）自然过渡
3. 合并后时长合理（≤10s），不会变成拖沓长镜

**合并优势：**
- 减少切镜次数，观众不被打断
- 情绪更连贯——不切 = 不给观众喘息
- 减少总镜数，表更紧凑

**s010 合并实例：**
- 04+05: 拉跟→停，特写→中景。被骂→挂断→停下，一气呵成
- 08+09: 上摇，拇指→账单。两个威胁在一个镜内完成
- 14+15: 拉+微摇，中景→近景。从"看到小孩哭"过渡到"意识到自己完蛋了"

## AI 生图/生视频的提示词安全规则

**核心原则：动作调度列只写画面内可见的内容。画外的视线目标、声源、空间参照物一律不入动作列。**

### 问题

当镜头的机位是正打（画面中有角色的脸）时，如果动作列写了"他看着电玩城门口"，AI 模型会试图往画面里塞电玩城门口——即使这个镜头根本不该看到它。

**根因：** AI 模型不区分"角色在看着什么"和"画面里有什么"。任何被命名的名词都可能被渲染进画面。

### 规则

| 机位 | 动作列可以写 | 动作列禁止写 |
|------|------|------|
| 🔴正打 | 角色自身的表情、眼神变化、面部肌肉动作 | 他所看的目标物/人/空间 |
| 🟡反打 | POV 所见的具体内容 | 角色自身的表情（脸不在画面里） |
| 🟢三 | 角色动作+环境中的元素 | —（相对安全） |

**正打画外视线写法：**
- ❌ `他看着电玩城门口。霓虹灯的红蓝紫光轮流打在他脸上。`
- ✅ `眼神从空变成定——泄气 → 被吸引。嘴唇微张。`
- 视线目标由**空间关系列**和**导演备注列**交代（如备注写`画外霓虹灯光源`）

**反打POV写法：**
- ✅ 写所见的景物、光效、人物
- ❌ 写观看者自身的表情反应

### 台词列空值

无台词的镜头，台词列留空 `<td></td>`，不用 `—` 占位符。AI 提示词中空值不会被误解为"空白台词"。

## 新增运镜术语

| 术语 | 含义 |
|------|------|
| 滑动变焦 | dolly in + zoom out（或反向），背景压缩/扩展，主体大小不变。希区柯克变焦 |
| 后跟→侧跟 | 从后方跟拍绕到侧面跟拍，镜头绕主体做弧形运动 |
| 拉+微摇 | dolly back + 轻微 pan，后退同时微调角度

当镜头内景别发生变化时，景别列使用叠层格式：

```
起幅景别 ★★★★★
    ↓
落幅景别 ★★★
```

HTML: `<td>起幅 ★★★★★<br>↓<br>落幅 ★★★</td>`

星数用落幅景别（最终状态），起幅也标注星以供参考。

> `<br>` 显式换行在 nowrap 列中依然生效。

## 插入镜（Insert Shot）用子编号

在已有镜号之间插入新镜头时，使用子编号（如 11A 插入在 11 和 12 之间），避免下游全部重排。

## 表情写作：若有所思 vs 平静

"若有所思"与"平静"是不同的表演状态，动作调度列必须区分：

| | 平静 | 若有所思 |
|------|------|------|
| 眼神 | 松弛，焦点存在 | **虚焦**——瞳孔不对准任何东西 |
| 视线 | 像在看 | 像在"穿过" |
| 嘴唇 | 自然闭合 | 微张，**停在那里忘了闭上** |

写法：`眼神虚焦——看着镜头方向，瞳孔没有对准任何东西，像在算一道没有答案的题。嘴唇微张，停在那里忘了闭上。` "像在算一道没有答案的题"比"若有所思"更可演。

## 空间关系列"没有深度层不硬凹"

仅当画面确实分了前中后三层（或至少两层有明确遮挡/虚化关系）时才用 `[前]` `[后]`。简单并置的左右直接用 `[左]` `[右]`。

## 合并镜头后统计更新

合并或插入镜头后，必须同步更新：
- 顶部 stats 中的总镜数
- 对应 beat 标题中的 "(X 镜)"

## s010 字段排列最终版（写入 SKILL.md）

```
镜号 → 运镜 → 空间关系 → 景别 → 机位 → 动作调度 → 台词 → 焦段 → 景深 → 时长 → 音乐 → 音效 → 导演备注
```

阅读流：运镜+空间="画面里有什么，动不动" → 景别+机位="什么镜头" → 动作+台词="干什么说什么"

## 2026-07-11: Feishu-Backed Architecture

Frontend/backend separation achieved. Feishu Bitable as database, HTML as presentation layer.

### Architecture
```
Feishu Bitable (DB) → Agent read-bridge (JSON) → build_html.py (assembly) → HTML (browser)
```

Five steps: (1) Migrate shots into bitable, (2) Read bridge normalizes rich-text → JSON, (3) Template with slots, (4) Assembly script one-command, (5) Browser verification.

### Key Files

| File | Purpose |
|------|---------|
| `templates/feishu-backed.html` | Template with CSS + JS refresh + settings panel |
| `scripts/build_html.py` | Fetch records → normalize → build HTML |

### Browser Refresh

HTML has 🔄 button. First use: click ⚙ to enter App ID/Secret/Token/Table ID (saved to localStorage). Subsequent clicks fetch Feishu API via JS fetch(), rebuild table body, update stats. Zero dependencies.

### Field Mapping (Feishu → v2 11-column)

13 Feishu fields (景别/焦段/景深 split; 摄影机 reconstructed at assembly):
镜号, 运镜, 空间关系, 景别, 焦段, 景深, 机位, 动作调度, 台词, 时长(秒), 音频, 导演备注, 提示词

### MCP Limitation

lark-mcp has no "add field to existing table" tool. Use REST API:
```bash
curl -X POST "https://open.feishu.cn/open-apis/bitable/v1/apps/{token}/tables/{id}/fields" ...
```

### User Preference

Browser-based refresh over CLI commands. Tools must work without Hermes running. file:// may have CORS issues; serve via python3 -m http.server or Hermes dashboard 9119.

## 2026-07-12: 飞书 API 批量修改陷阱

### 多次 GET→PUT 互相覆盖

**症状：** 连续修改同一记录的不同字段时，先改的内容被后改的操作覆盖丢失。例如：改了台词 → 改了前缀格式 → 台词丢了。

**根因：** 每次 GET→修改→PUT 是一个独立事务。两次 PUT 间隔太短时，第二次 GET 可能拿到第一次 PUT 前的旧版本，第二次 PUT 把第一次的改动盖回去了。

**正确做法：** 一次 GET → 攒齐所有修改 → 一次 PUT。绝不做「改一处 PUT 一次，再改再 PUT」的连环操作。

### 静默失败陷阱

`replace()` 匹配失败时静默返回原文，PUT 仍返回 `code=0`。Agent 误以为改成功了，实际数据没变。

**防范：** 每次 PUT 后立即 GET 验证，确认改动已落地再进入下一步。

## 2026-07-12: 右键菜单编辑 + 模板编辑终局

### 右键菜单（contextmenu）
- `contextmenu` 事件不触发 `click`，与提示词面板零冲突。
- 固定定位 `<div>` 在鼠标位置弹出，点空白处自动消失。
- 编辑时用 `textarea` 替换 `td` 内容，保存走代理 PUT（同提示词面板的 `_method:'PUT'` 模式）。
- `data-record-id` 必须在行上，否则编辑时拿不到 record_id。

### HTML 模板文件编辑终局
- **`skill_manage(action='patch')`** → SKILL.md 专属，有防清空保护，禁止用裸 `patch()` 或 `execute_code` 操作 SKILL.md。
- **`execute_code` + `write_file`** → 对 `feishu-backed.html` 不可靠，多次静默失败（文件内容不落地）。
- **终端 `python3 -c` 一行命令** → `feishu-backed.html` 唯一可靠编辑方式。用 Python 读文件、`str.replace()`、写回。
- 模板中 JS 字符串含 `'` 时，文件内以 `\'` 字面量保存。Python 匹配需用单引号包裹的字符串里写双引号避开转义地狱，或者直接匹配不含引号的子串。

### textContent vs innerText 陷阱

**症状：** 编辑保存后，提示词格式全部丢失——冒号消失、换行消失、所有内容连成一段。

**根因：** `.prompt-text` 内容由 `parsePromptBlocks()` 渲染为 HTML（含 badge span 等元素）。`textContent` 在包含子元素的节点上会丢弃换行并可能打乱冒号位置。

**修复：** 
1. `savePrompt()` 用 `innerText`（保留 `<br>` 换行）替代 `textContent`
2. `toggleEdit()` 进入编辑态时先将 HTML 替换为 `currentShotData.promptText` 纯文本，避免用户编辑 badge 标签内的文字

### X 按钮 onclick 转义地狱

**症状：** ✕ 按钮点击无效，面板不关。

**根因：** 模板中 onclick 使用了 `\'` 转义单引号，HTML 解析后 `\'` 变成字面量反斜杠+引号，JS 内虽能正确解析为 `'`，但极长的 inline onclick 极易因各种格式问题静默失效。

**修复：** 把 X 按钮 onclick 简化为 `onclick="closePrompt()"`，将 unpin 逻辑移入 `closePrompt` 内部。一行调用，零转义。

### 编辑态点击拦：td:has(textarea)

**症状：** 右键编辑动作调度时，点击 textarea 或保存/取消按钮会触发行 click → 弹出提示词面板。

**误解：** 最初以为需要拦所有 `.panel-btn`，结果把 X 按钮也拦了。

**正确做法：** 只拦 `textarea`、`.ctx-menu`、`td:has(textarea)`——后者覆盖了编辑格内所有子元素（textarea + 按钮），但不影响面板上的 X 按钮。

### 保存按钮文字跳变

**症状：** 保存成功时按钮从「💾 保存」变成「✓ 已保存」，宽度微增导致整排按钮布局跳动。

**修复：** `.panel-btn` 加 `white-space:nowrap;flex-shrink:0`，禁止换行和压缩。

### 模板编辑终局（补充）

- `execute_code` + `read_file(limit=900)` 后 `write_file` 写回时，超过 limit 的内容会被截断。读取和写入内容不一致导致静默失败。
- **唯一可靠方式：终端 `python3 -c` 一行**，用 Python 原生 `open/read/replace/write`，不设 limit，不绕中间文件。

**症状：** 编辑中点空白区域关面板，再打开时「编辑」按钮消失、「💾 保存」还露着，但正文不可编辑。

**根因：** `closePrompt` 不清 `_isEditing` 和按钮状态。`openPrompt` 重渲染 body.innerHTML 但不重渲染 header 按钮。

**修复：** `openPrompt` 开头重置 `_isEditing = false`，编辑按钮 display=`""`，保存按钮 display=`"none"`。

### 代理 PUT 支持

**症状：** 保存提示词时请求挂起。代理 `shotlist_server.py` 的 `_proxy_request` 处理 POST 请求时，`method` 固定为 `"POST"`，而飞书更新记录需要 PUT。

**修复：** 代理检查请求 body 中的 `_method` 参数覆盖默认 method。前端保存时传 `_method:'PUT'`。

### data-record-id 缺失

**症状：** 保存时弹「缺少记录ID」。

**根因：** `buildRow` 生成的行没有 `data-record-id` 属性。需在 `refreshFromFeishu` 的 shot 对象中加 `rid: r.record_id`，并在 `buildRow` 返回的 `<tr>` 中插入 `data-record-id`。`build_html.py` 的静态行也需同步。

### has-prompt 绿点双路径同步

**症状：** 浏览器刷新（F5）后绿点消失，点 🔄 又出现。

**根因：** `has-prompt` 类只在 JS `refreshFromFeishu` 的 `buildRow` 中添加，静态 HTML（`build_html.py`）未同步。

**修复：** `build_html.py` 的 `build_shot_row` 中检查 `提示词` 字段，有内容时加 `class="has-prompt"`。
