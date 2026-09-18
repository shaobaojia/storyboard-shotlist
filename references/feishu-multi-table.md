# 飞书多表架构

> 飞书多维表格应用内多表协同，以及分析表的构建与集成。

## 应用结构

同一个飞书应用（`app_token`）下可有多张表。`app_id/app_secret` 授权整个应用，表内操作（建表、删表、加字段、读写记录）全在同一凭证下。

当前结构：
```
OwBSbEQS5aY9HksVVBYcYUnVnlg
├── 数据表 (tbl2gBoybDUPpPz2)  ← 分镜数据
└── 分析   (tbl9L7UG4kJ2nuSr)  ← 模块1分析
```

`feishu_config.json`：
```json
{
  "app_id": "cli_aa9045b4afb85be9",
  "app_secret": "***（真实值见 feishu_config.json，不入库）",
  "app_token": "OwBSbEQS5aY9HksVVBYcYUnVnlg",
  "table_id": "tbl2gBoybDUPpPz2",
  "analysis_table_id": "tbl9L7UG4kJ2nuSr"
}
```

## API 操作

### 创建应用（独立底座）
```
POST /bitable/v1/apps
Body: {"name": "xxx", "folder_token": ""}
→ 返回新的 app_token
```

### 在现有应用建表
```
POST /bitable/v1/apps/{app_token}/tables
Body: {"table": {"name": "xxx", "fields": [{"field_name":"...","type":1}, ...]}}
→ 返回 table_id
```

### 字段类型
| type | 含义 |
|:---|:---|
| 1 | text |
| 2 | number |
| 3 | single select（需 `property.options`） |

### 删表
```
DELETE /bitable/v1/apps/{app_token}/tables/{table_id}
```

## 分析表字段设计（18 字段）

```
场次 (text)          ← JOIN 键，与分镜表关联
场景价值 (text)        「压抑 → 释放」
起点极 (text)
终点极 (text)
翻转 (text)           是/否
视点角色 (text)
节拍序号 (number)      1, 2, 3...
节拍名称 (text)
外界动作 (text)
人物反应 (text)
类型 (select)         🔴戏点 / 🟡空间建立 / ⚪填充
闭环 (select)         ✅ / ⚠️未闭环
说明 (text)
节奏段落 (number)      节奏曲线段落编号
节奏描述 (text)
情绪温度 (number)      x/10
节奏密度 (select)      慢/中/快
预估总镜头数 (number)
```

## build_html.py 多表集成

1. `fetch_analysis_records(token, app_token, table_id)` — 拉分析表全量
2. `build_beat_analysis_html(records, scene_id)` — 渲染单个场次的节拍分析表
3. 主流程合并分析数据中的场次到 `scenes` dict（解决分析有数据但分镜表无记录时 Tab 不生成的问题）
4. 子 Tab 从 `['v2']` 扩展为 `['beat', 'v2']`

## 子 Tab 渲染

每个 scene section 下两个子 Tab：
- **节拍分析** (`#beat-{sid}`)：场景价值声明 + 7 列节拍表 + 节奏曲线 + 预估镜头数
- **v2 分镜** (`#v2-{sid}`)：分镜表（原有）

CSS 占位符 `{{SUB_TAB_CSS}}` 自动为 `['beat', 'v2']` 各生成一组 `#sub-{sub}-{sid}:checked` 规则。
