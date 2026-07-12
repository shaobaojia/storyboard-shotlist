# 提示词面板实现参考

浮动窗口 + 拖拽 + 调整大小 + 继承链 + 按钮行 + 徽标解析。

## 架构

面板 ID `prompt-panel`，CSS `position:fixed` + JS 动态定位。数据源：c11 列（`td:nth-child(11)`）零宽隐藏，`textContent` 供面板 JS 读取。飞书里填提示词，HTML 组装时填入 c11 td，面板打开时 JS 从 td 读取。

## 核心 CSS

```css
.prompt-panel{position:fixed;top:40px;right:40px;width:500px;max-width:90vw;height:calc(100vh - 80px);
  max-height:calc(100vh - 80px);background:var(--card);border:1px solid var(--accent);
  z-index:100;display:none;flex-direction:column;box-shadow:-4px 0 20px rgba(0,0,0,.4);
  border-radius:6px}
.prompt-panel.open{display:flex;animation:panelIn .35s cubic-bezier(.34,1.56,.64,1)}
@keyframes panelIn{from{opacity:0;transform:scale(.95)}to{opacity:1;transform:scale(1)}}

.prompt-header{cursor:grab;user-select:none}
.prompt-header:active{cursor:grabbing}

.prompt-panel.dragging{box-shadow:-4px 0 30px rgba(0,0,0,.6)!important}
```

## 状态持久化 (_saveState/_restoreState)

```js
p._saveState = function(){
  this._left=this.style.left||''; this._right=this.style.right||'';
  this._top=this.style.top||''; this._width=this.style.width||''; this._height=this.style.height||'';
};
p._restoreState = function(){
  if(this._left){
    // ⚠️ 右对齐态：left='auto' 是 truthy，必须单独判断
    if(this._left==='auto'){this.style.right=this._right||'8px';this.style.left='auto';}
    else{this.style.left=this._left;this.style.right='auto';}
    this.style.top=this._top||'40px';
  }
  if(this._width)this.style.width=this._width;
  if(this._height)this.style.height=this._height;
};
```

**调用时机：**
- 关面板前：`panel._saveState()` — **必须在 `classList.remove('open')` 之前**
- 开面板后：`panel._restoreState()` — 在 `classList.add('open')` 之后

## 拖拽逻辑

按住标题栏 → `mousedown` 记录偏移（`dX=e.clientX-p.offsetLeft`）→ `mousemove` 更新 `left/top` → `mouseup` 调 `_saveState()`。跳过按钮点击（`e.target.closest('button')`）。

**底部边界：** `y = Math.max(0, Math.min(window.innerHeight - p.offsetHeight - 10, y))`。用 `p.offsetHeight` 动态计算，不硬编码常数。

## 四边四角调整大小

8 个 `<div class="resize-handle DIR">` 绝对定位于面板四边和四角：

| 手柄 | 样式 | cursor |
|------|------|--------|
| n/s | 边条 6px 高 | n/s-resize |
| e/w | 边条 6px 宽 | e/w-resize |
| ne/nw/se/sw | 方块 12×12 | *-resize |

mousedown 记录 `resizeStart = {x, y, l, t, w, h}` → mousemove 按方向更新。最小 320×200，最大 90vw×90vh。

## 面板默认尺寸

```
top:40px; right:40px; width:500px; height:calc(100vh - 80px); max-width:90vw
```

## 贴靠按钮

两个快捷定位按钮（统一 11px，与其他按钮一致）：

- **右贴附：** `style.left='auto'; style.right='8px'; style.top='40px'; height=window.innerHeight-80; w=500`
- **下贴附：** `style.left='40px'; style.right='40px'; style.top='auto'; style.bottom='8px'; width='auto'; height=45vh`

贴靠后调 `_saveState()`。点下时加 `snap-bounce` class（0.25s 回弹动画）。

## 钉住功能

📌 按钮切换 `.pinned` class。按钮 class 同步 `toggle('pinned')`。

- 钉住时：`closePrompt()` 检测 `.pinned` → `return` 不关（遮罩点击无效）
- 钉住时：`openPrompt()` 不显示 overlay（`if (!panel.classList.contains('pinned'))`）
- 钉住时：点击其他镜头行 → `openPrompt` 切换内容，钉住保持
- ✕ 按钮：**必须先解钉再关**——`panel.classList.remove('pinned'); btnPin.classList.remove('pinned'); closePrompt()`

## 按钮行

五颗按钮统一 `panel-btn` CSS class：

```css
.panel-btn{font-size:11px;padding:4px 8px;border:1px solid var(--accent);
  border-radius:4px;background:var(--accent);color:#fff;cursor:pointer;
  transition:all .15s ease;line-height:1.4}
.panel-btn:hover{background:transparent;color:var(--accent);border-color:var(--accent);
  transform:translateY(-1px)}
.panel-btn.pinned{opacity:.7}
.btn-close{border-color:var(--accent);background:var(--accent);color:#fff;font-size:16px;padding:2px 6px}
.btn-close:hover{background:transparent;color:var(--accent);border-color:var(--accent);transform:scale(1.1)}
```

从左到右：钉住 | 右贴附 | 下贴附 | 复制 | ✕。**全部 11px 统一字号，中文全词，红底白字，hover 变空心红框+红字。** 所有按钮 class 统一为 `panel-btn`。✕ 关闭按钮额外加 `btn-close`。

## 提示词徽标解析

`parsePromptBlocks(text)` 识别子标题正则：
`/^(@图片\\d+|场景|空间锚|人物|镜头[一二三四五六七八九十\\d]+|动作表演|拍摄方式|画面呈现|视角|光线|调色|氛围|风格|时长|景别|焦段|景深|机位|运镜)[：:]/`

**C 风格（默认）：** 场景描述字段使用 `●` 彩色圆点前缀。
**D 风格：** 动作表演/拍摄方式/画面呈现 仅彩色加粗，无圆点前缀，统一石板灰 #94a3b8。

颜色映射：场景#f59e0b / 空间锚#3b82f6 / 人物#10b981 / 镜头#a78bfa / 风格#8b5cf6 / 动作表演/拍摄方式/画面呈现 #94a3b8 / 其余#6b7280。

## 动效（全 CSS 层，零 layout recalc）

- 面板打开：弹性淡入（opacity 0→1 + scale 0.95→1）
- 按钮 hover：scale(1.08) + translateY(-1px)
- 拖拽阴影：`.dragging`
- 贴靠回弹：`snapBounce` 0.25s
- 滚动条渐显：`scrollbar-color:transparent` → hover `rgba(255,255,255,.15)`

## 左侧侧边栏

`position:fixed;left:0;top:50%` 红色竖条 `▶`（12×36px，呼吸脉冲光晕动画）。展开后 48px 宽面板，内含 🔄 和 ⚙ 两个 32×32 方形按钮。状态 localStorage 持久化。

## 页面加载自动刷新

`DOMContentLoaded` 后 800ms，若 `readFeishuConfig()` 返回有效凭证 → 自动调用 `refreshFromFeishu()`。F5 即实时数据。

## 提示词注释 [镜02] 格式

飞书提示词正文中可用 `[...]` 方括号添加注释——用于标注提示词内局部镜头编号与实际 v2 镜号的映射关系（如 `镜头一：[镜02]`）。面板渲染时自动转换为红色同号注释显示，复制时过滤掉 `[...]` 不进入剪贴板。

**飞书写法：** `镜头一：[镜02]` / `镜头二：[镜03]`

**面板显示：** 注释以红色 `var(--accent)` 同号字体显示，`[` `]` 保留。

**复制行为：** `copyBtn.onclick` 和 `fallbackCopy` 中均执行 `.replace(/\[.*?\]/g, '')` 过滤掉注释块。\n\n表头 `<th>` 右边缘 5px 拖拽区域（`cursor:col-resize`）。每张 table 独立绑定。\n\n```js\ndocument.querySelectorAll('#v2-s010 table thead').forEach(function(thead){\n  var ths = thead.querySelectorAll('th');\n  var table = thead.closest('table');\n  var cols = table.querySelector('colgroup').querySelectorAll('col');\n  ths.forEach(function(th, i){\n    if (i === ths.length - 1) return; // skip last col\n    var handle = document.createElement('div');\n    handle.className = 'col-resize';\n    th.appendChild(handle);\n    handle.addEventListener('mousedown', function(e){\n      var startW = parseFloat(cols[i].style.width || getComputedStyle(cols[i]).width);\n      // mousemove: cols[i].style.width = Math.max(30, startW + dx) + 'px'\n    });\n  });\n});\n```\n\n表头右分隔线：`thead th{border-right:1px solid rgba(255,255,255,.12)}`，确保暗底可见。\n\n## ⚠️ 致命坑合集

### 1. 空提示词镜头打不开面板

根因：无提示词时 `document.getElementById('prompt-copy')` 返回 null，`.onclick = ...` 抛 TypeError。

修复：
```js
var copyBtn = document.getElementById('prompt-copy');
if (copyBtn) { copyBtn.onclick = function(){ ... }; }
// ⚠️ 别忘了闭合 if 的 }
```

### 2. coveredLabel 用后定义

根因：`document.getElementById('prompt-shot-num').textContent = coveredLabel` 在 coveredShots 收集循环之前。`coveredLabel` = undefined → setter 静默中断。

修复顺序：收集 `coveredShots` → 算 `coveredLabel` → 再用。

### 3. 已删除元素的 getElementById → 面板不弹

根因：HTML 去掉 `<h3 id="prompt-shot-title">` 但 JS 保留下面的引用。null → `.textContent` 报错。

### 4. closePrompt 缺 _saveState → 位置丢失

根因：旧版 `closePrompt` 只移除 class，不调 `_saveState()`。关了再开 `_restoreState` 用过期值。

### 5. if (copyBtn) 缺闭合 } → 整页 JS 静默

症状：`{:128  }:127  diff:1` → 页面视觉正常但零交互（行无 cursor:pointer、面板不弹）。

每次 JS 编辑后校验 brace 平衡。

### 6. 按钮行重构后功能全崩

根因：按钮从 header HTML 移到 JS 动态创建后，class 名变更（`btn-pin` → `panel-btn`）但 `querySelector` 仍用旧名。

### 7. 拖拽后底部溢出

修复：`Math.min(window.innerHeight - p.offsetHeight - 10, y)`，不硬编码 40。

### 8. ✕ 按钮的 inline onclick 处理

关闭按钮的 onclick 写为 inline HTML 属性（非 JS 事件绑定）：

```html
<button class="panel-btn btn-close" onclick="
  var p=document.getElementById('prompt-panel');
  p.classList.remove('pinned');
  var b=p.querySelector('.panel-btn.pinned');
  if(b)b.classList.remove('pinned');
  closePrompt()
">✕</button>
```

必须先解钉再调 `closePrompt()`——因为 `closePrompt` 第一行 `if(pinned)return`，在内部解钉逻辑永远走不到。
