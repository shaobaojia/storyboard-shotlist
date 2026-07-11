# v2 表格 CSS 避坑指南

> s010 分镜表实战中踩过的 CSS 坑。

---

## 当前列显隐状态（提示词面板取代 toggle）

| 列 | 显示 | 说明 |
|:---|:---|:---|
| c1-c8 | ✅ | 镜号～时长 |
| c9 | ✅ | 音频 |
| c10 | ✅ | 导演备注 |
| c11 | 隐藏 | 提示词（数据供面板读取） |

```css
col.c11{width:0}
th:nth-child(11),td:nth-child(11){width:0!important;padding:0!important;overflow:hidden!important;border:none!important;font-size:0!important;max-width:0!important}
```

> **⚠️ 不要再用 hide-c11 toggle。** 旧的「隐藏提示词/显示提示词」切换功能已删除。提示词面板替代了它的作用。c9/c10 始终可见。

---

## nth-child 翻车记录

修改列数时**所有 nth-child 规则失效**——选择器绑定的列号变了，出现字体倒挂、宽度错乱、边框消失。每次加减列必须全量 grep + 逐条校对 nth-child 选择器。最典型的一次：删掉 c11 后 thead 的 `nth-child(9)` 从音频变成了导演备注，字体大小 0 把导演备注吞了。

---

## 列隐藏：方案对比（历史参考）

| 方案 | 结果 | 原因 |
|:---|:---|:---|
| `col{display:none}` | ✗ | `<col>` 不支持 |
| `col{visibility:collapse}` | ✗ | headless Chromium 无效 |
| `col{width:0}` 单独 | ✗ 内容溢出 | 单元格穿透 col 宽度限制 |
| `td:nth-child(N){display:none}` | ✗ | rowspan 打乱计数，prompt 列被挤出表外 |

**唯一可靠：零宽折叠。** col 宽度和 th/td 样式必须同步操作：

### 默认状态（显示提示词，隐藏音频+备注）

```css
/* col 归零释放 table-layout:fixed 空间 */
col.c9{width:0}
col.c10{width:0}
col.c6{width:auto;max-width:300px}
col.c11{width:auto}

/* 单元格零宽折叠 */
th:nth-child(9),th:nth-child(10),td:nth-child(9),td:nth-child(10){
  width:0!important;
  padding:0!important;
  overflow:hidden!important;
  border:none!important;
  font-size:0!important;
  max-width:0!important;
}
```

### `.hide-c11` 状态（隐藏提示词，恢复音频+备注）

```css
/* col 恢复原始宽度 */
.hide-c11 col.c9{width:120px}
.hide-c11 col.c10{width:180px}
.hide-c11 col.c11{width:0}

/* th 恢复：2px accent 底部线 */
.hide-c11 th:nth-child(9),.hide-c11 th:nth-child(10){
  width:auto!important;
  padding:10px 6px!important;
  overflow:visible!important;
  border-bottom:2px solid var(--accent)!important;
  font-size:12px!important;
  max-width:none!important;
}

/* td 恢复：1px border 底部线 */
.hide-c11 td:nth-child(9),.hide-c11 td:nth-child(10){
  width:auto!important;
  padding:8px 6px!important;
  overflow:visible!important;
  border-bottom:1px solid var(--border)!important;
  font-size:inherit!important;
  max-width:none!important;
}

/* 提示词单元格和表头隐藏 */
.hide-c11 th:nth-child(11){display:none!important}
.hide-c11 td.c-prompt{display:none!important}
```

**关键：th 和 td 恢复规则不同。** th 底线是 `2px solid var(--accent)`（表头红色分隔线），td 底线是 `1px solid var(--border)`（表体灰色分隔线）。混用会导致线断开。

---

## 提示词单元格排版

`word-break:break-word` 是头号杀手——320px 列宽下每个汉字单独一行。

```css
.c-prompt{
  word-break:normal;     /* 必须 */
  white-space:pre-line;  /* 保留<br>的同时正常换行 */
  font-size:12px;
  line-height:1.5;
}
```

---

## `!important` 堆叠

零宽折叠靠 `!important` 覆盖默认样式。新增规则时如不加 `!important` 可能被已有规则静默覆盖。

---

## 验证方法

不要只靠 `browser_vision`——经常判断错。用：

```js
// 列宽
getComputedStyle(document.querySelector('col.c11')).width
// 单元格宽度
document.querySelector('.c-prompt').offsetWidth
// 文字排版
getComputedStyle(document.querySelector('.c-prompt')).wordBreak
```
