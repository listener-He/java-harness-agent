---
title: events.jsonl 事件流 schema
date: 2026-05-31
category: architecture
status: active
origin: human-design
---

# events.jsonl — 统一事件流 schema

## 用途

承接 hook 三层分离架构（Sensor / Policy / Enforce）的 **L1 Sensor 层**输出。所有 Claude Code hook 退化为传感器后，把事件 append 到此文件；agent 通过 `events_query.py` 按需查询。

替代旧 push 模型（hook 直接 inject inline context block 给 agent）。新模型：hook 写流，agent 拉取。

## 文件位置

```
.claude/runs/local_intel/events.jsonl
```

- gitignored（隶属 `.claude/runs/`）
- append-only JSONL（一行一事件，UTF-8 无 BOM）
- 单文件 > 10MB 时按当日日期 rotate 为 `events.jsonl.YYYY-MM-DD`，新文件接力

## 通用字段（每条事件必有）

| 字段 | 类型 | 说明 |
|---|---|---|
| `ts` | string | ISO 8601 timestamp（含时区），如 `2026-05-31T14:23:01+0800` |
| `kind` | string | 事件类型，见下 |

其余字段按 `kind` 自由扩展，writer 不校验额外字段，query 按需投影。

## 8 类事件 schema

### `prompt` — 用户提交 prompt
| 字段 | 类型 | 必有 | 说明 |
|---|---|---|---|
| `text` | string | ✓ | 原始 prompt 文本（截断到 2000 字符） |
| `session_id` | string | — | Claude Code session 标识（若 payload 含） |

### `edit_pre` — Edit/Write 工具调用前
| 字段 | 类型 | 必有 | 说明 |
|---|---|---|---|
| `file_path` | string | ✓ | 目标文件绝对/相对路径 |
| `tool` | string | — | "Edit" 或 "Write"（若可推断） |
| `secrets_check` | string | — | "PASS"/"WARN"/"FAIL"/"SKIP"（secrets pre-check 结果） |
| `blocked` | bool | — | true = secrets FAIL 阻断 |

### `edit_post` — Edit/Write 工具调用后
| 字段 | 类型 | 必有 | 说明 |
|---|---|---|---|
| `file_path` | string | ✓ | 已落盘的文件路径 |
| `tool` | string | — | "Edit" 或 "Write" |
| `success` | bool | — | 工具调用是否成功（默认 true） |

### `read` — Read 工具调用后
| 字段 | 类型 | 必有 | 说明 |
|---|---|---|---|
| `file_path` | string | ✓ | 已读文件路径 |
| `tracked` | bool | — | 是否落进 usage_tracker（仅 `.claude/wiki/**` / `.claude/skills/**`） |

### `subagent_return` — 子 agent 一轮结束
| 字段 | 类型 | 必有 | 说明 |
|---|---|---|---|
| `text` | string | ✓ | 子 agent 最终返回文本（截断到 4000 字符） |
| `transcript_path` | string | — | 原始 transcript JSONL 路径（如可获取） |

### `turn_end` — main agent 一轮结束
| 字段 | 类型 | 必有 | 说明 |
|---|---|---|---|
| `branch` | string | — | 当前 git branch |
| `head` | string | — | 当前 short HEAD commit |
| `dirty_files` | int | — | `git diff --name-only` 行数 |

### `notification` — Claude Code UI 通知
| 字段 | 类型 | 必有 | 说明 |
|---|---|---|---|
| `message` | string | ✓ | 通知文本（来自 payload.notification / .message / .title） |
| `notif_type` | string | — | payload 携带的 type 字段（如 "permission" / "idle"） |
| `session_id` | string | — | Claude Code session 标识 |

### `compact` — Claude Code 上下文压缩前
| 字段 | 类型 | 必有 | 说明 |
|---|---|---|---|
| `branch` | string | — | 当时 branch |
| `head` | string | — | 当时 short HEAD |
| `active_task_brief` | string | — | active task_brief 路径 |
| `in_progress_slugs` | list[string] | — | launch_spec 中 IN_PROGRESS 的 slug 列表 |

## 字段命名约定

- 蛇形：`file_path`, `dirty_files`, `session_id`
- 路径：原样写入（不做 abspath 转换，保留 agent 传入形态便于追溯）
- 时间戳：仅 `ts` 字段，ISO 8601，写入时取本地时区
- 大文本：超长 truncate 到 schema 注明上限（避免 jsonl 单行膨胀）

## Writer API（event_writer.py）

```python
from event_writer import append

append("edit_post", file_path="src/foo/Bar.java", tool="Edit", success=True)
# 等价于在 events.jsonl 追加一行:
#   {"ts": "2026-05-31T14:23:01+0800", "kind": "edit_post",
#    "file_path": "src/foo/Bar.java", "tool": "Edit", "success": true}
```

- `kind` 为 positional required
- 其余字段任意 kwargs，writer 不校验 schema
- IO 错误一律 silent（hook 安全）
- 不返回值

## Query CLI（events_query.py）

支持的查询：

| 命令 | 用途 |
|---|---|
| `events-query --kind edit_post --since 30m` | 最近 30 分钟所有 edit_post |
| `events-query --file src/Foo.java --last 50` | 指定文件最近 50 条事件 |
| `events-query --kind subagent_return --last 5` | 最近 5 次子 agent 返回 |
| `events-query --aggregate-failures --days 30` | 按 gate 聚合最近 30 天失败次数 |
| `events-query --kind edit_post --since 1h --json` | 输出 JSON 数组（machine-readable） |

默认输出 human-readable text（一行一事件）。`--json` 切换为 JSON 数组。

## Rotation 规则

| 触发 | 动作 |
|---|---|
| `events.jsonl` 文件大小 > 10MB（写入前检查） | `mv events.jsonl events.jsonl.YYYY-MM-DD`；新空文件接力 |
| 当日已存在 rotate 文件 | 追加序号 `events.jsonl.YYYY-MM-DD.1`、`.2` …… |

不主动 GC 旧 rotate 文件（手动 / cron 处理）。

## 何时不该写 events.jsonl

- secrets HIGH-confidence 阻断时 → 也写 event（`edit_pre` with `blocked=true`），便于 agent 复盘
- 但绝不写**任何**内容到 jsonl，如内容含 secret（避免日志泄漏） —— writer 不做内容扫描，由调用方负责脱敏

## 与现有 sidecar 的关系

| Sidecar | 命运 |
|---|---|
| `failure_memory.json` | **保留**（已有用法稳定）；events_query `--aggregate-failures` 内部可调它 |
| `notifications.jsonl` | **保留**（继续作为 notification 专属沉淀）；同时 emit 一份 `notification` event |
| `last_compact_snapshot.json` + `compact_snapshots/*` | **保留**（PreCompact 专属，结构和 events 不同） |
| `.usage/` | **保留**（usage_tracker 专属计数） |

新架构里 events.jsonl 是**新加的统一上下文流**，不替代上述专门 sink；只是把它们的"通知给 agent"职能集中起来由 agent 按需 pull。
