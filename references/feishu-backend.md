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

## v2 Field Schema (13 columns)

| # | 字段 | 类型 | 说明 |
|---|------|------|------|
| ★ | 镜号 | Text（主字段） | 主字段不可删/改类型 |
| 2 | 运镜 | Text | 固定/手持/拉跟/横移/上摇... |
| 3 | 空间关系 | Text | `[位置标签] + emoji` 格式 |
| 4 | 景别 | **Text** | 含 ★ 星级 + ↓ 过渡 + 焦段·景深，HTML 直接搬运 |
| 5 | 焦段 | Text | 50mm/35mm... |
| 6 | 景深 | SingleSelect | 浅/中/深 |
| 7 | 机位 | SingleSelect | 🔴 正打/🟡 反打/🟢 第三人称/🔵 空间环境/🟣 插入/切出 |
| 8 | 动作调度 | Text | |
| 9 | 台词 | Text | |
| 10 | 时长(秒) | Number | |
| 11 | 音频 | Text | |
| 12 | 导演备注 | Text | |
| 13 | 提示词 | Text | |

## Key Design Decisions

### 景别: Text vs SingleSelect

推拉摇移镜头有景别过渡（如 `近景 ★★★★ ↓ 中全 ★★`），单选只能存一个值。文本字段直接存完整描述（含 ★ 星级、↓ 过渡、焦段·景深），HTML 只搬运不加工。代价：失去飞书原生筛选/统计能力——但导演创作不需要。

### 机位简写映射

飞书存全称（🔵 空间环境），旧 HTML 用简写（🔵环）。`build_html.py` 中 `JIWEI_MAP` 做映射。

## Why Proxy (Not Direct Fetch)

Feishu OpenAPI does NOT return CORS headers (confirmed via `curl -X OPTIONS`). Any browser JS call to `open.feishu.cn` is blocked. Proxy runs on NAS, same-origin for HTML, forwards server-side.

## Server Persistence

Docker `nohup` dies on restart. Permanent: UGREEN NAS → Control Panel → Task Scheduler → Add startup task:
```
python3 /opt/data/skills/scriptwriting/storyboard-shotlist/scripts/shotlist_server.py
```

## Common Pitfalls

- **URL params in credentials** (MOST COMMON): `OwBSbEQS...?table=...&view=...` instead of pure IDs → API returns `code=0` with 0 records → empty table with no error.
- **`file://` doesn't work**: open via `http://192.168.3.65:8089/...` not SMB double-click.
- **景别 was SingleSelect**: old version forced single value, losing ↓ transitions. Now changed to Text.
- **Primary field**: can't delete or change type of the first column. Rename instead.
- **Field rename**: breaks `build_html.py` field name mapping. Update script if renaming.
- **Records fetch needs GET**: Feishu token endpoint uses POST, records endpoint uses GET. Proxy detects method by presence/absence of body.
