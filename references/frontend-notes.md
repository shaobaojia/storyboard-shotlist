# 前端实现笔记

> 从 SKILL.md「关键经验」章节拆出。HTML/CSS/JS 实现细节，修改前端时查阅。

## HTML 布局与 CSS

### 列重排避坑
修改列序时必须同步更新：`<colgroup>` → CSS `col.cN{width}` → `<thead>` → `<tr>` 四处的顺序。常见翻车：只换 `<td>` 没换 `<colgroup>`，导致物理列 5 拿了 class c5 的宽度但 c5 实际绑定了旧列 5。

### 脚本定位 td
正则 `re.finditer(r'<td', rest)` 定位时，`c-num">XX</td>` 后的第一个 `<td` 是 col2（运镜），不是 col1。10 列：col3 = td_starts[2]，col4 = td_starts[3]，col7 = td_starts[6]，col9 = td_starts[8]。

### str.replace() 全局替换翻车
`content.replace(old_row, new_row)` 多镜相同内容时全部被替换。必须用位置索引：`content[:start] + new + content[end:]`，从后往前处理。

### str.replace() 多位置匹配 → 括号错乱（致命）

**症状：** 用 `str.replace('});\n})();', ...)` 改 JS 模板后，node --check 报 syntax error，且错误行号和实际修改位置不匹配。反复修补后仍有新错误。

**根因：** JS 模板中多处使用相同的闭合模式（IIFE 结尾 `});\n})();`、forEach 嵌套等）。`str.replace()` 全局匹配所有位置，一次改动同时破坏多处括号平衡。并且 `count=1` 不能解决问题——因为两处歧义交替出现，每次修复一处就重新破坏另一处。

**正确做法：** 
- 用**唯一上下文**定位：搜前后 3-4 行的独特组合作为 old_string，确保只匹配目标位置
- 或直接用**行号数组切片**：`lines = c.split('\n'); lines[1006:1008] = new_lines; c = '\n'.join(lines)`
- 改动后**立即 `node --check`** 验证（不要等到 build 后才发现）

### Radio 按钮隐藏
`input[name=scene],input[name^=sub-]{display:none}`，否则 Tab 上方裸露小圆点。

### Tab 对比度
选中态和未选中态文字颜色必须不同。未选中 `#888`，选中 `var(--head)`。

### table width:100%
不能移除——是防止横向溢出的关键。配合 `min-width:900px`，`.table-wrap{overflow-x:auto}` 仅在超宽时启用滚动。

### 列隐藏方案
`col` 元素的 `display:none`/`visibility:collapse` 浏览器兼容性不稳定。可靠方案：零宽折叠 `width:0;padding:0;overflow:hidden` + `col.cX{width:0}`。

### c11 提示词列操作
1. CSS `col.c11{width:160px}` → 2. `<colgroup>` 加 `<col class="c11">` → 3. `<thead>` 加 `<th>` → 4. 每行 `</tr>` 前加 `<td></td>` → 5. 填内容时 `rowspan="N"`。

### .c-prompt 文字排版
必须 `white-space:pre-line`，禁用 `word-break:break-word`（导致一字一行竖排）。

## 提示词面板

### 浮动窗口架构
`position:fixed`，默认 500×60vh。头部 drag handle + 右按钮行（钉住/右贴附/下贴附/复制/✕）。正文区 `overflow-y:auto`，徽标 C 风格彩色圆点（场景=琥珀#f59e0b、空间锚=蓝#3b82f6、人物=翠绿#10b981、镜头=紫#a78bfa；动作表演/拍摄方式/画面呈现=石板灰#94a3b8）。

### ↑ 继承链
`↑s010-NN` 格式，面板跟随 ↑ 链向上查找源镜头。支持简写（`↑02`，同场次）和全称（`↑s010-02`，跨场次）。`visited` 集合防循环引用。

### 面板关闭
X 按钮 onclick 写 `closePrompt()`（不要复杂 inline）。`closePrompt()` 内先 unpin 再关闭。钉住时 overlay 隐藏，点遮罩不关面板。

## JS 避坑

### 括号纪律
每次 JS 编辑后验证 `{` 和 `}` 数量相等。间隙 ≠ 0 → 整页交互静默失效（行失去点击、面板不弹）。

### 变量定义顺序
`var coveredLabel = ...` 必须先定义再使用。hoisting 下值为 `undefined`，用于 `textContent` setter 时静默中断。

### HTML 元素删除后清理引用
删除带 id 元素后，必须 grep 所有 `getElementById` 并删除。null.setter → TypeError。

### 粘贴按钮读旧值（闭包捕获过期变量）

症状：面板编辑提示词 → 保存成功 → 点复制 → 复制的是编辑前的旧文本。

根因：`openPrompt()` 内 `copyBtn.onclick` 闭包捕获了局部变量 `promptText`。`savePrompt()` 只更新了 `currentShotData.promptText`，没更新闭包里的局部变量。

修复：复制按钮改为读 `currentShotData && currentShotData.promptText`，不读局部变量。

### readFeishuConfig 未定义 → 页面加载不自动刷新

症状：F5 后页面显示旧静态数据，800ms 自动刷新不触发。

根因：`DOMContentLoaded` 回调调用了 `readFeishuConfig()`，但该函数从未定义（只有 `getSettings()` 存在）。JS 静默报错，自动刷新跳过。

修复：添加别名 `function readFeishuConfig(){ return getSettings(); }`。

### F5 后数据回退到旧版（静态 HTML 未同步）

症状：🔄 从飞书刷新后数据正确，但 F5 刷新浏览器数据回到旧版。

根因：`refreshFromFeishu()` 只更新内存 DOM，不更新磁盘上的静态 HTML 文件。F5 重新加载静态文件，看到的仍是旧数据。

修复：两处改动——
1. `shotlist_server.py` 加 `/api/rebuild` 端点，读取 `feishu_config.json` 凭证后运行 `build_html.py` 重建静态 HTML
2. `refreshFromFeishu()` 末尾加 `fetch('/api/rebuild')` 异步触发重建

注意：`build_html.py` 需 `FEISHU_APP_SECRET` 环境变量——`_rebuild()` 从 `feishu_config.json` 读 `app_secret` 传入 subprocess env。
跨行 JS 含转义字符，`patch()` 匹配常失败或产碎代码。终端 `python3 -c '...'` 一行搞定。`execute_code` 的 `write_file` 多次不写盘，不可靠。

## 模板编辑铁律

- SKILL.md → `skill_manage(action='patch')`，禁裸 `patch()`
- feishu-backed.html → 终端 `python3 -c '...'` 一行搞定。`execute_code` 的 `write_file` **反复证明不可靠**——多次静默不写盘
- `patch(mode='replace')` 在 HTML 模板上几乎必失败（跨行 JS、转义字符、缩进差异）
- Shell 转义地狱：Python 单引号嵌套时用 `'"'"'` 拼接法；复杂编辑先写 `.py` 文件再执行
- 所有前端修改后必须重建：`python3 scripts/build_html.py`
- **模板改了 build_html.py 也必须同步**——按钮、列、CSS 只在模板 JS 里加了但 build_html.py 没更新，静态 HTML 不会有
- 避免往 `/tmp/` 写临时文件——被安全策略拦截
- 每次 JS 编辑后验证 `{` 和 `}` 数量相等
- 浏览器缓存顽固——重启服务后用 `curl` 先验证文件已更新，再让用户 `Ctrl+Shift+R`

## 一键生成提示词

`shotlist_server.py` 端点 `/api/generate-prompts`：前端多选镜头 → POST 镜号列表 → 代理拉飞书数据 + 读 `m4-prompt-template.md` → 调 DeepSeek API → PUT 写回飞书。`feishu_config.json` 需含 `deepseek_api_key`。

**前端实现：** `buildRow()` 每行左侧加 checkbox（`.c-sel` + `.shot-chk`），`generateSelected()` 收集已勾选镜头号 → fetch `/api/generate-prompts` → 自动调用 `refreshFromFeishu()`。按钮通过 JS 动态注入 info bar（比改 build_html.py 更可靠）。`<colgroup>` 需加 `col style="width:28px"` 为 checkbox 列留空间，`<thead>` 需加空 `<th>`。

## 飞书架构

`templates/feishu-backed.html` + `scripts/build_html.py`（静态再生）+ `scripts/shotlist_server.py`（多线程代理,8089）。飞书多维表格做数据库，HTML 带「🔄 从飞书刷新」。beat 分组在 JS 刷新中同步渲染。空间关系 `\n`→`<br>` + `<wbr>` 软换行。

## 右键菜单（ctx-menu）

`contextmenu` 事件弹出（`e.preventDefault()`），`position:fixed`。在 td 内插 textarea + 保存/取消按钮，按钮必须 `e.stopPropagation()`。

## 内联编辑器事件隔离

`td:has(textarea)` 选择器不可靠——取消按钮先删 textarea 再冒泡，选择器已不匹配。正确做法：按钮 onclick 中 `e.stopPropagation()`。

## 自动生成提示词（/api/generate-prompts）

### 架构
前端多选镜头 → POST `{shots}` → `shotlist_server.py` 端点：
1. 读 `feishu_config.json`（含 `deepseek_api_key`）→ 拉飞书数据
2. 读 `m4-prompt-template.md` 为 system prompt
3. 找上游提示词组继承共享声明
4. 调 DeepSeek API → PUT 写回飞书
5. 前端自动 `refreshFromFeishu()`

### nth-child 全面翻车（加列必现）
加 checkbox 列后，所有 nth-child 索引 +1——c11 零宽隐藏失效（提示词撑爆表格）、c9/c10 消失。修复：
- 关键隐藏改用 class 选择器（`th.c-prompt-head, td.c-prompt`）不依赖列号
- colgroup class 编号需同步移位（`c1→c2, c2→c3...c11→c12`）
- 静态 HTML（build_html.py）和动态 JS（buildRow）列数必须一致

## 列宽拖拽

表头 `<th>` 右边缘 5px `cursor:col-resize`，跨 beat-section 同列同步。锁所有 colgroup 为像素宽，拖拽中只改目标列。

## 动态刷新 JS 同步

`refreshFromFeishu` 必须含 beat 分组渲染，不能只拼平板 `<tr>`。重建后调用 `attachPromptClicks()`。

## 多场景支持（单页多场）

页面通过两层 Tab 切换场次（价值弧线 + s010/s020/...）。CSS 和 JS 均需场景化，禁止硬编码 `s010`。

### CSS 占位符系统

模板内不再硬编码场景 CSS 规则，改为三个占位符在 `build_html.py` 构建时动态生成：

| 占位符 | 生成内容 |
|:---|:---|
| `{{SCENE_CSS}}` | `#scene-{sid}:checked~#{sid}-section{display:block}` 每场一行 |
| `{{SCENE_TAB_ACTIVE_CSS}}` | 场景 Tab 选中高亮规则（含 arc Tab） |
| `{{SUB_TAB_CSS}}` | 子 Tab（v2）显示/隐藏规则 |

表样式选择器从 `#v2-s010 table` 改为 `.scene-section table`（类选择器，不依赖场景 ID）。

### JS 场景选择

- **`activeScene`** 全局变量（默认 `"s010"`）+ **`getActiveScene()`** 从当前选中 radio 读取
- 所有 `#v2-s010` 硬编码替换为动态拼接：`'#v2-' + getActiveScene()`
- `attachPromptClicks` 和列宽拖拽改为 `.scene-section .sub-content tbody tr` 类选择器

### 场次切换事件

`input[name=scene]` 的 `change` 事件 → 更新 `activeScene` → 重新 `attachPromptClicks()` + `bindColResize()`

### refreshFromFeishu 场次分组

JS 端新增 `scene` 字段（从飞书 `场次` 列读取），`refreshFromFeishu()` 按场次分组后分别写入 `#v2-{sid}` 容器。状态栏统计仅显示当前活跃场次。

### build_html.py 多场构建

`records_to_shots()` 新增 `场次` 字段 → `group_by_scene()` 按场次分组 → `build_html()` 接受 `OrderedDict{scene_id: [shots]}` → 循环生成所有场次的 Tab、CSS、Section。`SCENE_NAMES` 字典映射 scene_id 到中文名。

### 列宽拖拽重构

从 IIFE 改为命名函数 `bindColResize(thead)`，支持场次切换后重新绑定。同步锁定范围从 `#v2-s010 colgroup` 改为 `table.closest('.scene-section') colgroup`。

### 文件名保持兼容

输出文件名仍为 `s010_feishu_backed.html`（历史 URL 不变），内容已支持多场次。
