# 分镜项目当前进度

> Agent 加载 storyboard-shotlist skill 后，必须先读此文件接续上下文。
> 用户说「保存进度」时才更新，平时不管。

## 凭证

飞书 API 凭证在 `feishu_config.json`（与本文件同目录）。Agent 和 `shotlist_server.py` 都读这个文件。

## 活跃项目

- **项目：** 电玩城的大小孩
- **数据源：** 飞书多维表格（飞书版是唯一活跃数据源，本地静态 HTML 已过期）
- **入口 URL：** http://192.168.3.65:8089/s010_feishu_backed.html
- **代理服务：** `shotlist_server.py`（8089 端口，serve HTML + 转发飞书 API）

## 场次状态

| 场次 | 模块0 价值弧线 | 模块1 分析 | 模块2 v1 骨架 | 模块2 v2 飞书 | 模块3 审计 | 模块4 提示词 |
|:---|:---|:---|:---|:---|:---|:---|
| s010 | ✅ | ✅ | ✅ | ✅ 34镜 1'49" | — | 部分（镜02-03✅） |
| s020–s080 | ✅ | — | — | — | — | — |

## 最近操作（2026-07-12）

- 建立 `feishu_config.json`——凭证从浏览器 localStorage 迁到 skill 目录，Agent 和 server 共享
- SKILL.md 模块4 更新：拉数据读 `feishu_config.json`，写回用 PUT（非 PATCH）
- 待做：镜 04-05 提示词写入飞书

## 接续规则

- 用户说「加载分镜」「看分镜」「打开分镜」「电玩城分镜」→ 直接 `browser_navigate` 飞书入口 URL，不搜本地文件
- 分镜数据改飞书表，不改 HTML 文件
- HTML 模板/样式改 `templates/feishu-backed.html`（`execute_code` + Python，禁裸 `patch()`）
- SKILL.md 改 `skill_manage(action='patch')`
