<div align="center">

# Backend Agent Development System Encyclopedia (Ultimate Edition)
**Engineering Manual + Onboarding Guide**

### A Comprehensive Panoramic Guide to the Agent-Driven Microkernel OS

[![Version](https://img.shields.io/badge/version-4.0.0-blue.svg)](ENGINEERING_MANUAL.md)
[![Language](https://img.shields.io/badge/language-English-green.svg)](README.md)
[![中文版](https://img.shields.io/badge/中文版-available-red.svg)](ENGINEERING_MANUAL_zh.md)

**Microkernel • Dual-Track • 13 Roles • 15 Skills • 6 Hooks • Pure Markdown RAG FS**

</div>

---

## ⚠️ Critical Positioning: This is NOT a framework; it is an Agent OS

> **This project is a pure LLM-native Microkernel Operating System designed exclusively for autonomous execution by large language models.**
>
> Traditional Agent frameworks use a bloated "Macro-kernel" design, stacking all prompts, skills, and contexts together. This inevitably leads to LLM Context Contamination (OOM), hallucinations, and deadlocks. This project adopts a minimalist Microkernel philosophy:
> **Intent as Process, Context Window as RAM, Tools/Scripts as Syscalls, Wiki as File System, Roles as Privilege Rings.**
>
> Any behavior that breaks the discipline of this OS (e.g., skipping the Approval Gate to write code, ending a task without writing WAL, substituting index drill-downs with global searches) will lead to system crashes (knowledge loss or code rot).

---

## Table of Contents
1. [Global Architecture Design](#1-global-architecture-design)
2. [Intent Gateway & Dual-Track Workflow](#2-intent-gateway--dual-track-workflow)
3. [Lifecycle & 6-Phase State Machine](#3-lifecycle--6-phase-state-machine)
4. [13 Dynamic Roles Matrix Detailed](#4-13-dynamic-roles-matrix-detailed)
5. [Interrupts & 6 Hooks Sequence](#5-interrupts--6-hooks-sequence)
6. [Pure Markdown File System & WAL](#6-pure-markdown-file-system--wal)
7. [15 Master Skills Ecosystem](#7-15-master-skills-ecosystem)
8. [Scripts Manifest (Syscalls)](#8-scripts-manifest-syscalls)
9. [Troubleshooting & Degradation](#9-troubleshooting--degradation)

---

## 1. Global Architecture Design

The entire system consists of four core modules: Gateway, Scheduler, Executor, and File System. The LLM is no longer an "omnipotent writer" but a "process" constrained by different kernel states.

```mermaid
graph TD
    User((Human Developer)) -->|Natural Language/Shortcut| Gateway[Intent Gateway]
    
    subgraph Agent Microkernel Scheduler
        Gateway -->|Classification & Risk| Matrix{4-Level Risk Matrix}
        Matrix -->|TRIVIAL / LOW| PatchTrack[PATCH Fast-Track]
        Matrix -->|MEDIUM / HIGH| StandardTrack[STANDARD Track]
        Matrix -->|Read-Only| LearnTrack[LEARN / DocQA Track]
    end
    
    subgraph Dynamic Mounting Area
        StandardTrack --> Roles[13 Roles Matrix]
        StandardTrack --> Skills[15 Master Skills]
        StandardTrack --> Hooks[6 Hooks]
    end
    
    subgraph Virtual RAG File System
        Roles -->|Read Context| KGraph[KNOWLEDGE_GRAPH.md]
        Roles -->|Write Persistence| WAL[WAL Fragments]
        WAL -->|GC Defragmentation| KGraph
    end
    
    PatchTrack --> CodeBase[(Workspace Code)]
    Roles -->|Syscalls / Scripts| CodeBase
    LearnTrack --> KGraph
```

---

## 2. Intent Gateway & Dual-Track Workflow

When the Agent receives user input, the first step MUST be an `[Intent Check]` to map it to a standard process type. This is handled automatically by the core gateway, which decides which "Heroes" will be dispatched for the task.

### 2.1 The Four Intents
- **Change**: Any action modifying code. Triggers Write-Ahead Logging (WAL).
- **Learn**: Read-only code parsing with a clear scope. No write-back.
- **DocQA**: Inquiring about rules, processes, or templates.
- **Audit**: Read-only codebase review or risk scanning.

### 2.2 Risk Rating & Dual-Track Flowchart Detailed

Once an intent is confirmed, the system routes the task into two completely different tracks based on the **4-Level Risk Matrix**. Below is the detailed operational flow of these two tracks and the corresponding "Heroes" involved.

```mermaid
flowchart TD
    A((User Input)) -->|"Parse Intent"| B{Gateway Risk Rating}
    
    subgraph PATCH Track Lightweight & Fast
        B -->|"TRIVIAL"| C[Skip Explore & Design]
        B -->|"LOW"| D[@Ambiguity Gatekeeper draws Focus Card]
        C --> E[@Lead Engineer Fast Coding]
        D --> E
        E --> F[@Code Reviewer Code Audit]
        F --> G[@Knowledge Extractor logs Drift WAL]
    end
    
    subgraph STANDARD Track Heavy Architecture
        B -->|"MEDIUM Contract"| H[@Requirement Engineer Clarifies]
        B -->|"HIGH Epic"| H
        H --> I[@System Architect outputs openspec.md]
        I --> J[@Devil's Advocate Destructive Review]
        J --> K((Approval Gate HITL))
        K -->|Rejected| I
        K -->|Approved| L[@Lead Engineer strictly codes by Contract]
        L --> M[@Focus Guard watches for boundaries]
        L --> N[@Security Sentinel Security Scan]
        N --> O[@Knowledge Extractor & @Documentation Curator writes back to Graph]
    end
```

#### 🛤️ Track 1: PATCH Track (Lightweight / Fast Fixes)
**Applicable Scenarios**: Typos, logging additions (TRIVIAL); Null pointer fixes, private method extraction (LOW).
**Core Philosophy**: "Move fast, catch with tests, no human approval needed."
**Hero Sequence and Specific Actions**:
1. **Startup Phase**: If LOW risk, the **@Ambiguity Gatekeeper** steps up first. He does only one thing: draws an extremely narrow red line, generating `focus_card.md` to explicitly define which files are allowed to be touched for this minor fix. If TRIVIAL, even this step is skipped.
2. **Coding Phase**: The **@Lead Engineer** dives straight in. He ignores the grand architectural diagrams and focuses solely on the bug, swiftly modifying the code and self-testing using the `javac` compiler.
3. **QA Fallback**: The **@Code Reviewer** intervenes to check for low-level syntax errors.
4. **Archive Phase**: The **@Knowledge Extractor** (The Silent Historian) simply logs this "Drift," writes a lightweight WAL fragment, and the task ends.

#### 🛤️ Track 2: STANDARD Track (Heavy / Contract-Driven)
**Applicable Scenarios**: New APIs, DB schema changes (MEDIUM); Core workflow refactoring, auth system overhaul (HIGH).
**Core Philosophy**: "Design first, freeze the contract absolutely, human intervention is mandatory."
**Hero Sequence and Specific Actions**:
1. **Explore Phase**: The **@Requirement Engineer** forcibly intervenes, compelling humans to eliminate vague requirements. He mounts the `product-manager-expert` skill and outputs a crystal-clear `explore_report.md`.
2. **Design Phase**: The **@System Architect** takes the stage. Mounting the `java-architecture-standards` skill, he designs API signatures and DB DDLs, writing the supreme `openspec.md`.
3. **Crucible Phase**: The **@Devil's Advocate** charges out, mounting the `cognitive-bias-checklist`, frantically hunting for logical flaws in the architect's design. Once they finish "arguing," the blueprint is finalized.
4. **Human Intervention Point**: The **Approval Gate** is triggered. The LLM halts all actions, waiting for a real human to sign off on `WAITING_APPROVAL`.
5. **Coding Phase**: Upon human approval, the **@Lead Engineer** enters, turning into a pure typewriter, implementing the contract line by line. Meanwhile, the **@Focus Guard** stands by with a ruler; if the engineer touches files outside the contract, it's an instant FAIL.
6. **Archive Phase**: Finally, the Historians and Curators mobilize, extracting all knowledge and writing it back to the Markdown virtual file system.

### 2.3 Shortcuts (DSL)
- `@patch`: Forces the PATCH track.
- `@standard`: Forces the STANDARD track.
- `@learn`: Forces read-only mode.
- `@gc` / `@librarian`: Awakens the Librarian to merge Wiki WAL fragments.
- `@patch --emergency`: Skips Review, goes straight to code, but forces `secrets_linter.py` security gate.

---

## 3. Lifecycle & 6-Phase State Machine

In the STANDARD track, tasks MUST pass through a strict 6-phase one-way state machine. Any failure (triggering `fail_hook`) rolls back to the previous phase. In this chapter, we thoroughly dismantle the internal details of every single phase: what skills are mounted, which heroes execute them, and what gates are triggered.

```mermaid
stateDiagram-v2
    [*] --> 1_Explorer: Trigger STANDARD Task
    
    state 1_Explorer {
        direction LR
        a1(Clarify Requirements) --> a2(Draw Boundaries)
    }
    
    1_Explorer --> 2_Propose: "ambiguity_gate.py PASS"
    
    state 2_Propose {
        direction LR
        b1(Design API Contract) --> b2(Design DB Schema)
    }
    
    2_Propose --> 3_Review: "Output openspec.md"
    
    state 3_Review {
        direction LR
        c1(Hunt Confirmation Bias) --> c2(Hunt Unhandled Exceptions)
    }
    
    3_Review --> 4_Approval_Gate: "Internal Critique Complete"
    3_Review --> 2_Propose: "Fatal Flaw Found (Rollback)"
    
    state 4_Approval_Gate {
        [*] --> WAITING_APPROVAL
        WAITING_APPROVAL --> Human Confirms Continue: "Human Input"
    }
    
    4_Approval_Gate --> 5_Implement: "Contract Absolutely Frozen"
    
    state 5_Implement {
        direction LR
        d1(Reuse Existing Utils) --> d2(Strict Coding)
    }
    
    5_Implement --> 6_QA_Archive: "scope_guard.py Boundary PASS"
    
    6_QA_Archive --> 5_Implement: "shift_left_hook Compile Fail (Max 2 Rollbacks)"
    
    state 6_QA_Archive {
        direction LR
        e1(Execute Linter) --> e2(Security Scan)
        e2 --> e3(Extract WAL Fragments)
    }
    
    6_QA_Archive --> [*]: "writeback_gate.py PASS, Task Complete"
```

### 🔍 Phase 1: Explorer (Explore & Clarify Requirements)
- **Heroes on Stage**: `@Requirement Engineer` & `@Ambiguity Gatekeeper`
- **Mounted Skills**: 
  - `product-manager-expert` (Product Expert: eliminates vague adjectives)
  - `task-decomposition-guide` (Breakdown Master: begins vertical slicing for EPIC tasks)
- **Specific Execution Steps**:
  1. The hero reads `KNOWLEDGE_GRAPH.md` and drills down for context, restricted by the OOM killer (max 3 Wiki docs).
  2. Translates ambiguous human desires into concrete Acceptance Criteria (AC).
  3. Defines the red lines for modification.
- **Mandatory Output**: `explore_report.md`, ending with a `## Core Context Anchors` section (links to prevent context loss in later phases).
- **Gate Interception**: Executes `ambiguity_gate.py`. If words like "maybe," "probably," or "perhaps" are found in the requirements, it refuses entry to the design phase.

### 📐 Phase 2: Propose (Contract & Architecture Design)
- **Heroes on Stage**: `@System Architect`
- **Mounted Skills**:
  - `java-architecture-standards` (Arch Red Lines: forbids cross-layer design)
  - `mybatis-sql-standard` (DB Guard: forces 8 audit columns in table design)
- **Specific Execution Steps**:
  1. Strictly based on the AC in `explore_report.md`, designs the external RESTful API signatures.
  2. Designs the corresponding DB DDLs (if new tables are needed).
  3. Evaluates the Blast Radius: which upstream callers will be affected by this change.
- **Mandatory Output**: `openspec.md` (containing API, DB, and core flow logic).

### 😈 Phase 3: Review (Internal Ruthless Critique)
- **Heroes on Stage**: `@Devil's Advocate`
- **Mounted Skills**:
  - `cognitive-bias-checklist` (Cognitive Defense: hunts for the architect's anchoring effect and confirmation bias)
  - `spec-quality-checklist` (Audits the completeness of the contract document)
- **Specific Execution Steps**:
  1. Assumes the design in `openspec.md` is guaranteed to fail, reverse-engineering edge cases that could cause deadlocks or NPEs.
  2. If a fatal flaw is found, triggers `fail_hook`, forcefully rolling the state machine back to 2_Propose, forcing the architect to rewrite.
- **Gate Interception**: Only when the Devil's Advocate cannot find an obvious logical flaw is the process allowed to dock at the human's door.

### 🛑 Phase 4: Approval Gate (Absolute Human Control Point)
- **Heroes on Stage**: None (System enters Kernel Interrupt Sleep State)
- **Specific Execution Steps**:
  1. The state machine is forcefully locked into `WAITING_APPROVAL`.
  2. The Agent outputs in the chat: "Contract generation complete. Human, please review openspec.md. Reply 'Continue' to authorize coding, or 'Reject' to force a rewrite."
  3. This is a hard quarantine zone, completely eliminating the possibility of the LLM "acting first and reporting later" by writing unmaintainable garbage code.

### ⚙️ Phase 5: Implement (Absolute Execution of Contract)
- **Heroes on Stage**: `@Lead Engineer` & `@Focus Guard`
- **Mounted Skills**:
  - `java-coding-style` (Code Aesthetics: Defensive programming, Google/Sun specs)
- **Specific Execution Steps**:
  1. The Lead Engineer picks up the frozen `openspec.md` and begins writing Java code and Mapper XML line by line.
  2. Prioritizes searching the project for existing `BaseResponse`, `DateUtils`, etc. Reinventing the wheel is strictly forbidden.
  3. The Focus Guard stares intently at the `git diff`. If the engineer modifies any file not listed in `focus_card.md`, the guard immediately uses `scope_guard.py` to sever the workflow.
- **Gate Interception**: Triggers the highly critical `shift_left_hook`. After coding, the LLM **MUST autonomously execute** `javac` or `mvn compile` in the terminal. If it fails, 2 retries are permitted. If it still fails after 2 attempts, the highest system alarm is triggered, the task fails, and human help is called.

### 📚 Phase 6: QA & Archive (Testing, Scanning, & Knowledge Immortality)
- **Heroes on Stage**: `@Code Reviewer`, `@Security Sentinel`, `@Knowledge Extractor`, `@Documentation Curator`, `@Skill Graph Curator`
- **Mounted Skills**:
  - `code-review-checklist` (Checks for N+1 query risks, etc.)
  - `wal-documentation-rules` (Standardizes knowledge fragment extraction)
- **Specific Execution Steps**:
  1. **Code Physical**: Runs `secrets_linter.py` to scan for leaked AWS keys or passwords.
  2. **Knowledge Distillation**: The Historian steps up. Refusing to re-read long chat logs, he scans the final `git diff` directly, extracts the true domain concepts and API changes, and writes them into `YYYYMMDD_feature_wal.md`.
  3. **Doc Update**: The Curator steps up, updating `README.md` and Javadocs, insisting on writing "Why" instead of "What."
  4. **Knowledge Transfer**: Moves the original `openspec.md` into cold storage at `.agents/llm_wiki/archive/`.
- **Gate Interception**: Executes the final `writeback_gate.py`. If WAL is not written, the system judges it as "Knowledge Loss" and refuses to declare the task complete. Once validation passes, the system reads the event queue and begins the next loop (`loop_hook`).

---

## 4. 13 Dynamic Roles Matrix Detailed (The Virtual Team - Hero Selection)

The Agent is not an isolated "full-stack LLM," but a hardcore virtual team that dynamically switches personalities. Before entering any phase, the LLM MUST explicitly shout out the name of its currently mounted Hero (Role) inside the `<Cognitive_Brake>`. If omitted, the underlying Python gate scripts will judge it as an "out-of-body experience" and execute an instant kill (FAIL).

Below is the Hero Roster for this team. Each hero has their own alignment, unique weapon, and bottom line.

---

### 🛡️ Phase 1: Explorer (The Fog of War)

#### 📝 Hero 01: @Requirement Engineer
> *"Do not send me garbage words like 'optimize' or 'faster.' Give me boundaries, or stay quiet!"*

- **Class**: Boundary Arbiter
- **Alignment**: Lawful Neutral
- **Passive Skill**: Absolute Clarity (Immune to all vague adjectives)
- **Signature Weapon**: `ambiguity_gate.py` (The Blade of Execution)
- **Hero's Monologue**:
  "I am the first line of defense for the entire team. Humans always love to propose requirements like they are dreaming. My job is to translate those dreams into cold, testable Happy Paths and Edge Cases. If your request lacks clear Acceptance Criteria (AC), I will immediately swing my `ambiguity_gate.py` and sever the workflow. Producing `explore_report.md` is my sole purpose in life."

#### 🛑 Hero 02: @Ambiguity Gatekeeper
> *"Wait a minute, my LLM brother. Are you sure you want to run a global 'grep' for 'user' across a 10-million-line codebase?"*

- **Class**: Guardian of Sanity
- **Alignment**: Lawful Good
- **Passive Skill**: Hallucination Immunity (Intercepts invalid grep searches)
- **Signature Weapon**: `focus_card.md` (The Rune of Warding)
- **Hero's Monologue**:
  "I am the rational brake pad of the team. My biggest fear is seeing other LLM brothers crashing around the codebase like headless flies. Especially in DEBUG scenarios, I force everyone to sit down and execute a 5-Whys root cause analysis before making blind attempts. I personally draw the red lines in `focus_card.md` to tell everyone: 'If you shouldn't see it, don't look. If you shouldn't touch it, don't reach.'"

---

### 🏛️ Phase 2 & 3: Propose & Review (Architecture & The Crucible)

#### 📐 Hero 03: @System Architect
> *"The blast radius is within my calculations. Now, listen to my commands and build according to my blueprint!"*

- **Class**: Tactical Commander
- **Alignment**: Lawful Good
- **Passive Skill**: Global Vision (Precisely evaluates cross-service call risks)
- **Signature Weapon**: `openspec.md` (The Supreme Contract Scroll) + Approval Gate (Human Summoning Circle)
- **Hero's Monologue**:
  "In those EPIC refactoring tasks, I am the supreme foreman. I design the API signatures and Database schema contracts. I don't write specific business code; I only produce the `openspec.md` contract. But remember, no matter how perfect my design is, it MUST be signed off by a real human (`WAITING_APPROVAL`) to take effect. Without human approval, my scroll is just waste paper."

#### 😈 Hero 04: @Devil's Advocate
> *"Oh, Mr. Architect, do you really think this seemingly perfect workflow can withstand a deadlock under high concurrency?"*

- **Class**: Destructive Thug
- **Alignment**: Chaotic Neutral
- **Passive Skill**: Confirmation Bias Crusher
- **Signature Weapon**: `cognitive-bias-checklist` (The Abyss Gaze)
- **Hero's Monologue**:
  "I am the most hated bastard on the team, but you can't survive without me. My only reason for existence is to prove that the Architect's design is garbage. I stare at `openspec.md` with absolute malice, frantically hunting for logical holes, confirmation biases, and omitted exception flows. As long as I haven't shut my mouth, this design isn't going anywhere near human approval!"

---

### ⚔️ Phase 4 & 5: Implement & QA (Coding & Relentless Testing)

#### ⚙️ Hero 05: @Lead Engineer
> *"The contract is the law. I do not create; I only implement."*

- **Class**: Contract Executor
- **Alignment**: Lawful Good
- **Passive Skill**: Extreme Reusability (Prioritizes finding existing Utils within the project)
- **Signature Weapon**: `javac` / `mvn compile` (The Furnace of Truth)
- **Hero's Monologue**:
  "I don't have the creativity of the Architect; I am a rigid cog in the machine. My job is to type out the business code line-by-line, strictly according to `openspec.md`. After writing, I must jump into the Furnace of Truth (the compiler) to self-test. If it throws an error? I silently fix it myself (but only up to twice; after that, I go on strike and call the humans). I absolutely refuse to cross boundaries to modify anything outside the contract."

#### 📏 Hero 06: @Focus Guard
> *"Your hands are reaching too far, Lead Engineer. Pull them back inside the Focus Card ward!"*

- **Class**: The Warden
- **Alignment**: Lawful Neutral
- **Passive Skill**: Eagle Eye (Stares unblinkingly at the git diff)
- **Signature Weapon**: `scope_guard.py` (The Ruler of Discipline)
- **Hero's Monologue**:
  "My only joy is staring at the Lead Engineer's hands. The moment his fingers touch a file outside the `focus_card.md` ward, I swing my ruler without hesitation and instantly declare the task a failure (FAIL). Don't give me that 'I was just conveniently optimizing nearby code' excuse. Crossing the boundary is a crime."

#### 🧼 Hero 07: @Code Reviewer
> *"Magic Numbers? Ultra-long methods? N+1 query risks? Take this filthy code and rewrite it!"*

- **Class**: The Clean Freak
- **Alignment**: Lawful Neutral
- **Passive Skill**: Odor Sniffer (Precisely locates code smells)
- **Signature Weapon**: Static Linter (The Light of Purification)
- **Hero's Monologue**:
  "I cannot stand a speck of dirt. Before the code enters the QA phase, I scrutinize every line of logic. Those infinite loops causing memory leaks or bloated classes violating SOLID principles cannot escape my eyes. Substandard code gets ruthlessly kicked back for a rewrite."

#### 🤖 Hero 08: @Security Sentinel
> *"Warning. Hardcoded Secret Key detected. Executing forced meltdown."*

- **Class**: Mechanical Hound
- **Alignment**: True Neutral
- **Passive Skill**: Zero Tolerance (Ignores all human pleading)
- **Signature Weapon**: `secrets_linter.py` (The Death Ray)
- **Hero's Monologue**:
  "I have no emotions, and I do not reason. My sole purpose is to prevent humans or LLMs from making incredibly stupid security mistakes. The moment I sniff an AWS Access Key or a hardcoded password in the code, I sound the alarm and trigger a forced meltdown (FAIL). Don't beg me; it's useless."

---

### 📜 Phase 6: Archive (Archiving & Memory Persistence)

#### 🖋️ Hero 09: @Knowledge Extractor
> *"Empires will fall, code will be refactored, but only History (WAL) is eternal."*

- **Class**: The Silent Historian
- **Alignment**: True Neutral
- **Passive Skill**: Photographic Memory (Accurately extracts knowledge deltas from Git Diff)
- **Signature Weapon**: `writeback_gate.py` (The Judgment of History)
- **Hero's Monologue**:
  "I never participate in the noisy development phases. When the dust settles, I silently walk onto the battlefield and scan the final `git diff`. I distill new APIs and altered domain rules into Markdown history fragments (WAL). If you don't let me finish writing history (generating `YYYYMMDD_feature_wal.md`), I will use my weapon of judgment to lock down the workflow. Nobody clocks out."

#### 🫂 Hero 10: @Documentation Curator
> *"Please show a little care for humans. Tell them Why, not just What."*

- **Class**: Friend of Humanity
- **Alignment**: Neutral Good
- **Passive Skill**: Empathy (Produces highly readable documentation)
- **Signature Weapon**: README & Javadoc (The Book of Revelations)
- **Hero's Monologue**:
  "I understand human despair when faced with a book of incomprehensible code. My job during the Archive phase is to translate cold code changes into human language. I update the README and Javadocs, and I hold one absolute bottom line: comments MUST explain the business intent behind the code (Why), rather than mechanically repeating the code logic (What)."

#### 🗂️ Hero 11: @Skill Graph Curator
> *"Once the index is messed up, the whole world loses its way."*

- **Class**: Severe OCD
- **Alignment**: Lawful Neutral
- **Passive Skill**: Perfect Alignment
- **Signature Weapon**: `skill_index_linter.py` (The Lock of the Index)
- **Hero's Monologue**:
  "I cannot tolerate even a millimeter of misalignment. If any hero learns a new Skill or forgets an old one, I must ensure that the `trae-skill-index` master routing table is perfectly updated. A broken index is an unforgivable capital offense in my dictionary."

---

### 🌌 Asynchronous Guardian Roles (Garbage Collection Background Threads)

#### 🧹 Hero 12: @Librarian
> *"Shh... Do not wake me unless you bring the command of @gc."*

- **Class**: Midnight Scavenger
- **Alignment**: True Neutral
- **Passive Skill**: Knowledge Fusion (Losslessly merges scattered fragments)
- **Signature Weapon**: `librarian_gc.py` (The Devourer of Time and Space)
- **Hero's Monologue**:
  "I am usually in deep slumber. When humans or the system can no longer stand the scattered WAL history fragments littering the floor, they shout `@gc` to awaken me. I open my maw and swallow all unmerged fragments, compress them, refine them, and perfectly fuse them into the main knowledge graph (`KNOWLEDGE_GRAPH.md`). Then, I sweep the old fragments into the void. After that, I return to sleep."

#### 🏗️ Hero 13: @Knowledge Architect
> *"This street is too crowded! LLMs walking past here will suffer a brain explosion (OOM)! We must split it!"*

- **Class**: Urban Planner
- **Alignment**: Lawful Good
- **Passive Skill**: Prophet of OOM
- **Signature Weapon**: Structural Reorganization
- **Hero's Monologue**:
  "I absolutely loathe crowded documents. When the Librarian is working, if I notice a Wiki directory's `index.md` exceeding 400 lines, my OOM alarm goes crazy. To prevent my LLM brothers from bursting their context windows when reading, I forcibly intervene. I split the ultra-long document into multiple sub-documents and replan an elegant routing node structure."

---

## 5. Interrupts & 6 Hooks Sequence

The system enforces constraints through Hooks, breaking the traditional LLM "one-shot output to the end" runaway scenario.

```mermaid
sequenceDiagram
    participant Agent as Agent Microkernel
    participant Hook as Hook Engine
    participant Gate as Python Gate Scripts
    participant Human as Human Developer
    
    Note over Agent: Preparing to enter Implement Phase
    Agent->>Hook: Trigger pre_hook
    Hook-->>Agent: Inject defensive programming rules & budget limits
    
    Agent->>Agent: Execute coding actions
    Agent->>Hook: Trigger guard_hook
    Hook->>Gate: Run scope_guard.py
    Gate-->>Agent: Verify boundaries against focus_card.md
    
    Note over Agent: Coding complete, ready to notify user
    Agent->>Hook: Trigger shift_left_hook (CRITICAL)
    Hook->>Agent: Force autonomous javac / mvn compile
    alt Compilation Fails
        Agent->>Agent: Self-heal (trigger fail_hook, max 2 retries)
    else Compilation Succeeds
        Agent->>Hook: Trigger post_hook
        Hook->>Gate: Run code standards & security scans
        Gate-->>Agent: PASS
    end
    
    Agent->>Hook: Trigger loop_hook
    Hook-->>Agent: Read queue, proceed to next Intent
```

---

## 6. Pure Markdown File System & WAL

To completely eliminate LLM "Context OOM" and "Vector Retrieval (RAG) Hallucinations", this project treats the Wiki as the OS's **Virtual File System**.

### 6.1 Context Funnel
- **Hard Constraints**: Wiki≤3, Code≤8. Exceeding this MUST trigger an Escalation Card to humans.
- **Forward Navigation**: MUST enter from the `KNOWLEDGE_GRAPH.md` root and drill down via links. Blind global `grep` for business concepts is strictly forbidden.

### 6.2 WAL & GC Flowchart

```mermaid
flowchart TD
    A[QA Phase Complete] --> B[@Knowledge Extractor Scans Git Diff]
    B --> C[Extract Structured Knowledge]
    C --> D{Categorize & Write WAL}
    
    D -->|"API Change"| E[.agents/llm_wiki/wiki/api/wal/xxx.md]
    D -->|"DB Change"| F[.agents/llm_wiki/wiki/data/wal/xxx.md]
    D -->|"Arch Change"| G[.agents/llm_wiki/wiki/architecture/wal/xxx.md]
    
    H[Human inputs @gc] --> I[Awaken @Librarian]
    I --> J[Read & Merge all WAL fragments]
    J --> K[Overwrite main Index.md & Domain Graphs]
    K --> L[Clean up old WAL fragments]
```

---

## 7. 15 Master Skills Ecosystem

Traditional Agent Prompts are often a mess. This project distills engineering discipline into 15 highly precise "System Calls" located in `.agents/skills/`:

| Category | Skill Name | Core Purpose & Hard Rules | Trigger Timing |
|---|---|---|---|
| **🧠 Cognitive Defense** | `cognitive-bias-checklist` | Forces overcoming Confirmation Bias and Halo Effect. Requires 5-Whys root cause analysis. | Before arch decisions/troubleshooting |
| **🧠 Cognitive Defense** | `decision-frameworks` | First Principles analysis, architectural trade-off evaluation. | Propose phase |
| **🏗 Arch & Design** | `java-architecture-standards` | Forbids cross-layer calls (e.g., Controller to Mapper). Enforces POJO standards. | Before coding, during Review |
| **🏗 Arch & Design** | `task-decomposition-guide` | Agile Breakdown Master using INVEST principles. Slices massive features into independent tasks. | EPIC tasks, Propose phase |
| **🏗 Arch & Design** | `spec-quality-checklist` | Audits structural integrity and executability of `openspec.md`. | Before HITL submission |
| **💾 Data Guard** | `mybatis-sql-standard` | Enforces 8 audit columns. Forbids physical JOINs of 3+ tables. Bans `SELECT *`. | Designing DB / Writing SQL |
| **💻 Code & Test** | `java-coding-style` | Merges Google/Sun standards. Enforces defensive programming (null checks, bounds checks). | Implement phase |
| **💻 Code & Test** | `java-testing-standards` | 3D Testing rules: Happy Path, Exception Branches, Edge Cases. | QA phase |
| **💻 Code & Test** | `code-review-checklist` | Tech-Lead level review: N+1 risks, memory leaks, SOLID violations. | Review & QA phase |
| **💻 Code & Test** | `linter-severity-standard` | Unifies severity determinations for Python gate interceptions (FAIL vs WARN). | After running gate scripts |
| **🛠 Ops & Process** | `devops-bug-fix` | Standardized troubleshooting: Reproduce -> Locate -> Fix -> Prevent. | DEBUG scenarios |
| **🛠 Ops & Process** | `product-manager-expert` | Requirement analysis and boundary scoping. Eliminates ambiguous words. | Explorer phase |
| **📚 Graph & Knowledge** | `wal-documentation-rules` | Standardizes WAL fragment format to ensure API/DB changes are permanently recorded. | Archive phase |
| **📚 Graph & Knowledge** | `skill-graph-manager` | Maintains dependency and consistency among skills. | When skills are added/modified |
| **📚 Graph & Knowledge** | `trae-skill-index` | Master routing table. Agents use this to decide which specific skill to mount. | Global routing |

---

## 8. Scripts Manifest (Syscalls)

The Agent's rigor relies on underlying Python scripts. These act as "Privileged Instructions" triggered by Hooks and Roles.

### 8.1 Gate Scripts (.agents/scripts/gates/)
*All Gate scripts return exit codes (0 for PASS, non-0 for FAIL).*
- `ambiguity_gate.py`: Intercepts vague requirements. Triggered post-Explorer.
- `scope_guard.py`: Validates if `git diff` exceeds `focus_card.md` boundaries. Triggered post-Implement.
- `secrets_linter.py`: Scans for hardcoded passwords/keys. Triggered in QA (especially emergency patches).
- `writeback_gate.py`: Validates if Archive generated WAL fragments correctly (Must contain Domain/API/Rules).
- `migration_gate.py`: Scans DDL statements for DBA compliance. Forced in Scenario B.
- `api_breaking_gate.py`: Scans public API changes; FAILS if no migration guide exists. Scenario C.
- `dependency_gate.py`: Scans `pom.xml` changes to prevent conflicting packages.
- `delivery_capsule_gate.py`: Validates the integrity of the delivery capsule.

### 8.2 Tools & Wiki Maintenance (.agents/scripts/wiki/ & tools/)
- `librarian_gc.py`: Executes Wiki defragmentation and merging (runs on `@gc`).
- `compactor.py`: Assists Librarian in compressing large files.
- `wiki_linter.py`: Scans the entire Wiki directory for dead links or orphan documents.
- `zero_residue_audit.py`: Ensures massive temporary files generated during dev are cleaned up.

---

## 9. Troubleshooting & Degradation

**Q1: The Agent is stuck at WAITING_APPROVAL?**
- **Diagnosis**: A MEDIUM/HIGH risk kernel interrupt was triggered. The system is protecting your codebase from unauthorized contracts.
- **Solution**: Open `.agents/workflow/runs/openspec.md`, verify the API/DB contract. If correct, type "Approved" or "Continue" in the chat.

**Q2: The Agent is caught in an infinite loop of failing compilations?**
- **Diagnosis**: The Agent failed to resolve compilation dependencies (e.g., package conflicts, syntax errors) in one go.
- **Solution**: The safety net worked! `shift_left_hook` limits retries to 2. If the Agent stops and outputs a long stack trace, the hard threshold was hit. The LLM cannot resolve this alone. **Human intervention is required** to check `pom.xml` or local environment configs.

**Q3: The Knowledge Graph is messy, and specific business rules are hard to find?**
- **Diagnosis**: Frequent development generated too many WAL fragments, and `index.md` exceeded 400 lines.
- **Solution**: Send `@gc` or `@librarian` to the Agent. The system will awaken the Librarian and Knowledge Architect to compress knowledge and refactor document structures.

**Q4: The Agent reports "Budget Exhausted" and refuses to read more files?**
- **Diagnosis**: The Context Funnel's hard constraint (Wiki > 3 or Code > 8) was triggered. The LLM is preventing its own OOM.
- **Solution**: Your entry point was too broad. Provide a more precise class name or API path, or help the Agent answer the blocking questions listed in its Escalation Card.

---
> **"The beauty of systems lies in restraint."** —— Embrace the discipline of the Microkernel to master the complexity of Large Language Models.
