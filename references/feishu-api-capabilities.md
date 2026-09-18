# 飞书 API 能力速查

> 已验证的飞书多维表格 API 操作。当前应用 ID: `cli_aa9045b4afb85be9`，app_token: `OwBSbEQS5aY9HksVVBYcYUnVnlg`。

## 创建新应用

```bash
POST https://open.feishu.cn/open-apis/bitable/v1/apps
Body: {"name": "应用名", "folder_token": ""}
# folder_token 为空 = 个人空间
```

返回 `app_token`。实测通过，权限足够。

## 在现有应用下加表（推荐）

```bash
POST https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables
Body: {
    "table": {
        "name": "表名",
        "fields": [
            {"field_name": "字段名", "type": 1},   # 1=文本
            {"field_name": "状态", "type": 3},     # 3=单选
            {"field_name": "序号", "type": 2}      # 2=数字
        ]
    }
}
```

返回 `table_id`。实测通过。

## 删除表

```bash
DELETE https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}
```

## 字段类型速查

| type | 含义 |
|:---|:---|
| 1 | 文本 |
| 2 | 数字 |
| 3 | 单选 |
| 4 | 多选 |
| 5 | 日期 |
| 7 | 复选框 |
| 11 | 人员 |

## 双表架构（推荐模式）

当一种实体（如镜头）和另一种实体（如节拍）是 1:N 关系时，放两张表比塞进一张好：

- **分镜表**：每行一个镜头（镜号/运镜/动作调度/提示词...）
- **分析表**：每行一个节拍（场次/节拍序号/外界动作/人物反应/类型...）

前端按 `场次` 字段 JOIN。两张表共享同一 API 凭证，一次拉两张即可。

## 免费版限制

- 5000 行/表
- 当前分镜表 ~200 行全片，分析表 ~50 行全片 → 远未触及上限
