# 使用指南（中文）— 在不同 CLI / IDE 中加载规则并跑完整闭环

**导航：**[English](USAGE.md) · [README_zh.md](README_zh.md) · [AGENTS.md](AGENTS.md) · [ENGINEERING_MANUAL_zh.md](ENGINEERING_MANUAL_zh.md)

> 这份文档写给第一次接触“编码 Agent 规则/工作流”的同学：尽量少黑话、可复制粘贴、一步一步来。  
> 目标：让你在 Trae / Cursor / Claude Code / Codex / Gemini CLI / Qoder / CodeBuddy / Copilot / Windsurf / Aider 等工具里，都能稳定加载本仓库的规则，并用同一套“闭环流程”完成：需求 → 设计 → 实现 → 测试 → 归档。

---

## TL;DR（先看这个就够用）

1. 把这两个东西放进你的项目根目录：
   - `.agents/`（工作流引擎、技能、Wiki、脚本）
   - `AGENTS.md`（规则入口，“给 Agent 的 README”）
2. 让你用的工具“读到”`AGENTS.md`：
   - 有些工具原生就会读（比如 Codex、Cursor、Windsurf、Qoder 等）
   - 有些工具读别的文件名（比如 `GEMINI.md`、`CLAUDE.md`、`.github/copilot-instructions.md`），就用“适配文件/软链接/设置项”解决
3. 开始提需求：
   - 你可以直接用自然语言，Agent 会自动判断是“只读解释 / 小修复 / 完整闭环”
   - 也可以用 `@learn` / `@patch` / `@standard` 当快捷方式（不是必须）

---

## 1. 这套东西到底是什么？（一句话）

把它当成“**给 AI 编程助手戴的安全带 + 操作流程**”。

- 安全带：防止它乱改、改超范围、无限重试烧 Token
- 操作流程：不管你要“看懂代码、修 Bug、做新功能”，都能按同一套节奏把事情做完，并且留下可追溯的记录

---

## 2. 规则加载：一套内容，多种工具

不同工具叫法不一样，但本质都在做同一件事：**每次会话开始前，把你的项目约定塞进模型上下文**。

本仓库选择用 `AGENTS.md` 作为“跨工具通用格式”。`AGENTS.md` 生态说明见：<https://agents.md/>。

### 2.1 推荐的“单一真相来源”（Strongly Recommended）

把 `AGENTS.md` 当作唯一真相来源。其它工具需要不同文件名时，用以下方式之一“指向它”，避免复制粘贴维护两份：

- 方式 A：软链接（macOS/Linux 推荐）
- 方式 B：复制一份同内容（Windows/受限环境最稳）
- 方式 C：工具设置项里把“规则文件名”改成 `AGENTS.md`（若工具支持）

Windows 如果也想用软链接（需要管理员权限或开启“开发者模式”），常见命令是：
```powershell
New-Item -ItemType SymbolicLink -Path CLAUDE.md -Target AGENTS.md
```

---

## 3. 各工具怎么加载规则（多种方案）

下面每个工具我都给 2–4 种方案，你挑最顺手的用。  
（提示：如果你在公司电脑/Windows 上软链接麻烦，就直接用“复制一份同内容”最省事。）

### 3.1 Trae（IDE）

Trae 支持“用户规则 / 项目规则”，并会把规则存到项目里的 `.trae/rules/`。官方规则说明：<https://docs.trae.ai/ide/rules?_lang=en>。

推荐做法（稳、团队可共享）：
1. 在 Trae 里创建 Project Rule（会自动生成 `.trae/rules/<name>.md`）
2. 在规则文件里写一句“把 `AGENTS.md` 当宪法”，并把你们最关键的约束放进去（比如不要越权改文件、需要测试等）
3. 让 `AGENTS.md` 继续作为仓库里的主入口（跨工具兼容）

可选做法（更省维护）：
- 如果你确认 Trae 版本可以直接识别项目根 `AGENTS.md`，那就不额外建 `.trae/rules/`；但团队协作时，建议至少保留一个“Always Apply”的 Trae 规则，写上最低限度的团队共识。

### 3.2 Cursor（IDE）

Cursor 支持两种方式：`.cursor/rules/*` 或 `AGENTS.md`。官方说明：<https://cursor.com/docs/rules>。

方案 A（最省事）：只放 `AGENTS.md` 在项目根目录  
方案 B（更精细）：同时加 `.cursor/rules/*.mdc`
- 适合你想按目录/文件类型分规则（比如 `src/**` 一套、`docs/**` 一套）
- 注意：Cursor 的 rule 文件支持 `.md` 和 `.mdc`（带 frontmatter）

### 3.3 Codex CLI（Terminal）

Codex 会自动按目录向下构建“指令链”，优先 `AGENTS.override.md` 再 `AGENTS.md`。官方说明：<https://developers.openai.com/codex/guides/agents-md>。

方案 A（推荐）：项目根放 `AGENTS.md`  
方案 B：需要本地临时覆盖时放 `AGENTS.override.md`（记得别提交）  
方案 C：在 Codex 配置里加 fallback 文件名（当你不想叫 `AGENTS.md` 时）

### 3.4 Claude Code（Terminal / VS Code / JetBrains）

Claude Code 官方文档说明它会读取项目根的 `CLAUDE.md` 作为会话启动指令：<https://code.claude.com/docs/en/overview>。

为了兼容“AGENTS.md 作为单一真相来源”，推荐你选一个：

方案 A（软链接，macOS/Linux 推荐）：
```bash
ln -s AGENTS.md CLAUDE.md
```

方案 B（复制同内容，最稳）：
```bash
cp AGENTS.md CLAUDE.md
```

方案 C（最小适配文件）：
创建 `CLAUDE.md`，写清楚两句：
- “本仓库规则以 AGENTS.md 为准”
- “开始任何任务前请先阅读 AGENTS.md 并遵循其中的流程/预算/门禁”

### 3.5 Gemini CLI（Terminal）

Gemini CLI 默认使用 `GEMINI.md`，并支持在 `settings.json` 里改“context 文件名”，也支持 `@file.md` 导入。官方说明：
- `GEMINI.md` 机制：<https://geminicli.com/docs/cli/gemini-md/>
- `context.fileName` 设置：<https://geminicli.com/docs/reference/configuration/>

方案 A（推荐：改设置，让它直接找 AGENTS.md）：
在项目根创建 `.gemini/settings.json`：
```json
{
  "context": {
    "fileName": ["AGENTS.md", "GEMINI.md"]
  }
}
```

方案 B（兼容旧习惯：保留 GEMINI.md，但内容不重复）：
创建 `GEMINI.md`：
```md
# Project instructions

@./AGENTS.md
```

方案 C（软链接）：
```bash
ln -s AGENTS.md GEMINI.md
```

### 3.6 Windsurf / Cascade（IDE）

Windsurf 支持 `AGENTS.md`（或 `agents.md`），并且会根据文件所在目录自动决定作用域：根目录相当于 always-on，子目录相当于 `<dir>/**` 的规则。官方说明：<https://docs.windsurf.com/windsurf/cascade/agents-md>。

方案 A（推荐）：项目根放 `AGENTS.md`  
方案 B：在子目录放更细的 `AGENTS.md`（比如 `backend/AGENTS.md`、`docs/AGENTS.md`）  

### 3.7 GitHub Copilot（IDE / Copilot CLI / Cloud Agent）

Copilot 支持：
- `.github/copilot-instructions.md`（仓库级）
- `.github/instructions/*.instructions.md`（路径级）
- `AGENTS.md`（给 Agent 用的指令，按目录树就近生效）

官方说明：
- 仓库自定义指令：<https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot>
- Copilot CLI 自定义指令：<https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions>

推荐做法（兼容性最好）：
1. 项目根保留 `AGENTS.md`
2. 再加一个 `.github/copilot-instructions.md`，写一句话：  
   “This repo uses AGENTS.md as the primary agent instructions. Please follow it.”

### 3.8 Qoder（IDE / CLI）

Qoder 的规则系统放在 `.qoder/rules`，并且官方明确写了“兼容 AGENTS.md，复制到项目里就能用”。官方说明：<https://docs.qoder.com/user-guide/rules>。

方案 A（推荐）：项目根放 `AGENTS.md`（Qoder 会识别）  
方案 B（更强约束）：把关键规则再写到 `.qoder/rules` 里，做“Always Apply”  

### 3.9 CodeBuddy Code（CLI）

CodeBuddy 的“可配置入口”主要是：
- 项目/用户级 Sub-Agent 文件：`.codebuddy/agents/*.md`（带 YAML frontmatter）官方说明：<https://www.codebuddy.ai/docs/cli/sub-agents>
- CLI 参数里可以加载/追加 system prompt（包括从文件读取）：<https://www.codebuddy.ai/docs/cli/cli-reference>

由于不同版本/发行渠道差异较大，这里给你两个稳定方案：

方案 A（推荐：用 system prompt file 指向 AGENTS.md）：
```bash
codebuddy -p --system-prompt-file ./AGENTS.md "Summarize the rules you loaded."
```
（交互模式下也可以用 `--append-system-prompt` 把 AGENTS.md 的关键信息追加进去）

方案 B（项目级 Sub-Agent：写一个“项目总控 agent”）：
1. 建 `.codebuddy/agents/project.md`
2. prompt 里写：先读 `AGENTS.md`，然后按其流程执行

### 3.10 Aider（Terminal）

Aider 不强制规定必须叫 `AGENTS.md`，它推荐用 “conventions file” 并通过 `--read` 或配置让它每次都加载。官方说明：<https://aider.chat/docs/usage/conventions.html>。

方案 A（推荐）：用 `--read` 每次启动都读规则：
```bash
aider --read AGENTS.md
```

方案 B（长期固定）：在 `.aider.conf.yml` 里配置 always read（Aider 文档里叫 “Always load conventions”）：<https://aider.chat/docs/usage/conventions.html>  

---

## 4. 规则加载之后，怎么“用起来”（不用记命令版）

你不需要背任何 `@xxx`。直接说人话就行，Agent 会自动判断应该走哪条轨道：

### A. 只想看懂（只读模式）

你可以这样说：
- “帮我把这个工程的目录结构讲一下，重点说入口在哪里。”
- “解释一下 `AGENTS.md` 里提到的 LIFECYCLE 是什么，给个例子。”

通常 Agent 会：
- 只读，不写代码
- 解释清楚后就停

### B. 小改动 / 修 Bug（快速修复模式）

你可以这样说：
- “修一下这个 NullPointerException，并加一个单元测试验证。”
- “把这个方法的参数校验补上，保证不会报错，然后跑一下编译。”

通常 Agent 会：
- 限定修改范围（尽量少改文件）
- 改完会做基本验证（编译/单测）

### C. 做一个完整小功能（闭环模式）

你可以这样说：
- “我们做一个最小的 Todo API：新增创建/查询两个接口，并带单元测试和使用说明。先出方案给我看，我确认后再写代码。”

通常 Agent 会：
1. 先问清楚需求边界
2. 写方案（spec/任务清单），等你点头
3. 再实现 + 测试
4. 最后归档（记录本次改动）

### 可选：快捷方式（不是必须）

如果你喜欢“明确告诉它走哪条路”，可以用快捷标记（本仓库路由支持）：

- `@learn`：强制“只读解释”
- `@patch`：强制“小改动/修 bug”
- `@standard`：强制“完整闭环”

但一定要写在文档里/团队里说明清楚：**不写 `@` 也能用**，它只是快捷方式，不是开关。

---

## 5. 一个真实小闭环示例：Todo API（需求 → 设计 → 实现 → 测试 → 归档）

这里用一个国际化、通用、不涉及任何行业术语的例子：**Todo（待办事项）API**。假设你的项目已经是一个简单的后端服务（语言/框架不限），你要加一个最小功能：

### 5.1 需求（你可以直接复制发给 Agent）

```
我们要做一个最小 Todo API 闭环：
1) 新增 POST /todos：创建待办（title 必填，max 100 字符）
2) 新增 GET /todos：列表查询（支持按 done=true/false 过滤）
3) 必须有单元测试覆盖：正常创建、title 为空报错、过滤查询
4) 先给我一份实现方案（包含会改哪些文件、会加哪些测试、怎么验证），我确认后你再开始写代码
```

### 5.2 设计阶段（你会看到的“正常输出”）

Agent 应该会输出类似这些内容：
- 需求拆解（有哪些接口、字段、错误）
- 文件范围（哪些文件要改，哪些文件不能碰）
- 测试计划（跑什么命令、用什么测试框架）
- 风险判断（这算小改动还是完整闭环）

你在这里做的动作只有一个：  
**确认/否决/补充**。比如你回复：
```
方案 OK，按这个做。注意：错误返回要保持项目现有风格。
```

### 5.3 实现阶段（写代码 + 最小验证）

实现阶段重点是：
- 只改“方案里列出来的文件”
- 写完先做基础验证（至少 compile / unit test）
- 遇到失败不要无限重试（超过限制就停下来问你）

### 5.4 测试阶段（验证闭环）

Agent 应该至少做到：
- 运行单元测试（或等价的测试命令）
- 把失败原因解释清楚（如果失败）
- 修一次、再跑一次（不无限循环）

### 5.5 归档阶段（把本次工作留下来）

你最终应该得到：
- “这次改了什么”的摘要（可用于 PR 描述）
- 测试/验证结果（命令与结论）
- 工作流产物被放进 `.agents/workflow/runs/`（不会把临时文件扔在根目录）

---

## 6. 排错：规则没生效怎么办？

### 6.1 最快自检方式

对 AI 说：
```
请列出你本次会话加载了哪些规则文件（文件名和路径），并用一句话复述最关键的 3 条约束。
```

如果它回答里完全没提到 `AGENTS.md`（或你工具对应的规则文件），说明没加载上。

### 6.2 常见原因

- 文件名不对：工具默认只认 `CLAUDE.md` / `GEMINI.md` / `.github/copilot-instructions.md`
- 文件在错的目录：比如你把规则放到子目录，但从项目根启动了工具
- 软链接在 Windows 上没权限：改用复制方案
- 规则太长太散：先缩成“最关键 30 行”，再逐步加

---

## 7. 你下一步可以做什么？

- 如果你主要用 Trae：先把规则加载搞定，然后用上面 Todo API 示例跑一次完整闭环
- 如果你团队多人：把“推荐加载方案”写进团队约定（比如统一用软链接或统一生成适配文件）
- 如果你想更精细：可以在子目录再放 `AGENTS.md`，让不同模块有不同约束（Windsurf/Codex 这类工具非常适合）
