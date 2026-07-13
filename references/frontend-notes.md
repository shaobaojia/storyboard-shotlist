# 前端实现笔记

> 从 SKILL.md「关键经验」章节拆出。HTML/CSS/JS 实现细节，修改前端时查阅。

## HTML 布局与 CSS

### 列重排避坑
修改列序时必须同步更新：`<colgroup>` → CSS `col.cN{width}` → `<thead>` → `<tr>` 四处的顺序。常见翻车：只换 `<td>` 没换 `<colgroup>`，导致物理列 5 拿了 class c5 的宽度但 c5 实际绑定了旧列 5。

### 脚本定位 td
正则 `re.finditer(r'<td', rest)` 定位时，`c-num">XX</td>` 后的第一个 `<td` 是 col2（运镜），不是 col1。10 列：col3 = td_starts[2]，col4 = td_starts[3]，col7 = td_starts[6]，col9 = td_starts[8]。

### str.replace() 全局替换翻车
`content.replace(old_row, new_row)` 多镜相同内容时全部被替换。必须用位置索引：`content[:start] + new + content[end:]`，从后往前处理。

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

### patch 在 HTML JS 上静默失败
跨行 JS 含转义字符，`patch()` 匹配常失败或产碎代码。终端 `python3 -c '...'` 一行搞定。`execute_code` 的 `write_file` 多次不写盘，不可靠。

## 模板编辑铁律

- SKILL.md → `skill_manage(action='patch')`，禁裸 `patch()`
- feishu-backed.html → 终端 `python3 -c '...'`，避免 `/tmp/` 临时文件
- 每次编辑后验证括号平衡，重建用 `build_html.py`

## 飞书架构

`templates/feishu-backed.html` + `scripts/build_html.py`（静态再生）+ `scripts/shotlist_server.py`（多线程代理,8089）。飞书多维表格做数据库，HTML 带「🔄 从飞书刷新」。beat 分组在 JS 刷新中同步渲染。空间关系 `\n`→`<br>` + `<wbr>` 软换行。

## 右键菜单（ctx-menu）

`contextmenu` 事件弹出（`e.preventDefault()`），`position:fixed`。在 td 内插 textarea + 保存/取消按钮，按钮必须 `e.stopPropagation()`。

## 内联编辑器事件隔离

`td:has(textarea)` 选择器不可靠——取消按钮先删 textarea 再冒泡，选择器已不匹配。正确做法：按钮 onclick 中 `e.stopPropagation()`。

## 列宽拖拽

表头 `<th>` 右边缘 5px `cursor:col-resize`，跨 beat-section 同列同步。锁所有 colgroup 为像素宽，拖拽中只改目标列。

## 动态刷新 JS 同步

`refreshFromFeishu` 必须含 beat 分组渲染，不能只拼平板 `<tr>`。重建后调用 `attachPromptClicks()`。
