# AGENTS.md

> 给下一个 Agent（或下一个自己）的交接备忘录。**收工推送前必须更新「刚做完 / 正在做 / 下一步 / 坑」四个字段。**
> 2026-09-18：v1 封存入库（重做前冻结点）。

## 接手前必读（环境/前置条件）

- 运行环境：Python 3（Hermes 容器内）；脚本全部 stdlib，零第三方依赖
- 依赖服务：`scripts/shotlist_server.py` :8089（serve 生成的 HTML + 代理飞书 API）——**无常驻，手动拉起**
- 前置操作：先读 `CURRENT_STATE.md` 接续进度；凭证在 `feishu_config.json`（同目录，不入库）

## 这个项目是干什么的

分镜列表 v1（Hermes skill `storyboard-shotlist`）：剧本 → 价值弧线 / 节拍分析 → 镜头表（v1 骨架 / v2 全量）→ AI 提示词；数据存飞书多维表格，前端为生成式 HTML（经 :8089 浏览）。

## 刚做完

- 2026-09-18 封存入库：7 月中下旬 ~ 8 月初全部迭代（多表架构、一键生成提示词、build_html 多表集成、前端系列修复）
- SKILL.md 增补两条定案：「v1 数据存储规则」「飞书批量写入陷阱（逐条 POST）」
- references 新增 `feishu-api-capabilities.md`、`feishu-multi-table.md`

## 正在做

- 无（v1 封存）

## 下一步

- 重做分镜列表 v2（2026-09-18 拍板；方案讨论中）

## 坑（已踩过的雷）

- `build_html.py` 输出文件名硬编码（`s010_feishu_backed.html`）≠ 浏览器入口名（`电玩城的大小孩_feishu_backed.html`）→ 重建后忘 cp 就「刷不出来」
- `shotlist_server.py` 无常驻机制（挂会话进程下）→ 页面打不开先查 :8089；永久方案（NAS 任务计划）未做
- 凭证红线：`feishu_config.json` / `.env` 永不入库（已进 .gitignore）；app_secret 在任何文档中一律占位
- 飞书 `batch_create` 对中英文引号嵌套敏感（报 9499）→ 写回全部逐条 POST
- 改 HTML 模板 / 样式禁裸 `patch()`（大括号计数会碎）→ 走 execute_code + Python；SKILL.md 改动走 skill_manage patch

## 细节指针

- 方法论全文：`SKILL.md` + `references/`（16 个文件）
- 当前进度：`CURRENT_STATE.md`
- 生成管线：`scripts/build_html.py` + `scripts/shotlist_server.py`
