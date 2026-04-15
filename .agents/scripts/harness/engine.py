#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Harness Lifecycle Engine CLI
可选辅助工具：驱动状态机、维护任务队列与阶段状态，降低手工编辑导致的状态错乱概率。
"""

import sys
import json
import os
from datetime import datetime

STATE_FILE = ".agents/workflow/runs/engine_state.json"
CATALOG_DIR = ".agents/router/runs"
PHASES = [
    "1_Explorer", "2_Propose", "3_Review", "3.5_Approval", 
    "4_Implement", "5_QA", "6_Archive"
]

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return None

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def write_launch_spec(intents):
    os.makedirs(CATALOG_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = f"{CATALOG_DIR}/launch_spec_{timestamp}.md"
    with open(filepath, "w") as f:
        f.write(f"# 启动计划 (Launch Spec) - {timestamp}\n\n")
        f.write("## 状态机 (State Machine)\n")
        f.write("| Intent | Status | Phase | Artifact/Log | Failed_Reason |\n")
        f.write("|---|---|---|---|---|\n")
        for i, intent in enumerate(intents):
            status = "IN_PROGRESS" if i == 0 else "PENDING"
            phase = PHASES[0] if i == 0 else "-"
            f.write(f"| {intent} | {status} | {phase} | - | - |\n")
        f.write("\n")
        f.write("## 断点续传 (Resume)\n")
        f.write("- 会话恢复时先读本文件，根据 `Status/Phase` 继续执行。\n")
        f.write("- 若为 `WAITING_APPROVAL`：等待人类确认后再进入 Implement。\n")
        f.write("- 若为 `FAILED`：停止自动推进，优先请求人类介入。\n")
    return filepath

def _update_launch_spec_row(filepath, intent, status=None, phase=None, artifact=None, failed_reason=None):
    if not os.path.exists(filepath):
        return
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    updated = False
    with open(filepath, "w", encoding="utf-8") as f:
        for line in lines:
            if not line.startswith("|"):
                f.write(line)
                continue
            parts = [p.strip() for p in line.strip().strip("|").split("|")]
            if len(parts) != 5:
                f.write(line)
                continue
            if parts[0] != intent:
                f.write(line)
                continue
            if status is not None:
                parts[1] = status
            if phase is not None:
                parts[2] = phase
            if artifact is not None:
                parts[3] = artifact
            if failed_reason is not None:
                parts[4] = failed_reason
            f.write("| " + " | ".join(parts) + " |\n")
            updated = True
    if not updated:
        return

def init_engine(intents_str):
    intents = [i.strip() for i in intents_str.split(",") if i.strip()]
    if not intents:
        print("❌ 错误：必须提供至少一个意图 (如 Propose.API,Implement.Code)")
        return
    
    filepath = write_launch_spec(intents)
    state = {
        "launch_spec_file": filepath,
        "queue": intents,
        "current_intent_index": 0,
        "current_phase_index": 0,
        "retries": 0
    }
    save_state(state)
    print(f"✅ 引擎初始化成功！已生成任务队列文件: {filepath}")
    print(f"🔄 当前处于意图: [{intents[0]}] -> Phase: {PHASES[0]}")

def get_status():
    state = load_state()
    if not state:
        print("ℹ️ 引擎空闲，没有运行中的任务队列。")
        return
    
    idx = state["current_intent_index"]
    if idx >= len(state["queue"]):
        print(f"✅ 任务队列已全部完成！(文件: {state['launch_spec_file']})")
        return
        
    current_intent = state["queue"][idx]
    current_phase = PHASES[state["current_phase_index"]]
    retries = state["retries"]
    print(f"📊 【引擎状态】")
    print(f"- 启动文件: {state['launch_spec_file']}")
    print(f"- 当前意图: [{current_intent}] ({idx+1}/{len(state['queue'])})")
    print(f"- 当前阶段: {current_phase}")
    print(f"- 当前阶段重试次数: {retries}/3")
    if current_phase == "3.5_Approval":
        print("⚠️ 强拦截点：请等待人类确认后，再执行 `python .agents/scripts/workflow/engine.py next` 进入 Implement 阶段！")

def next_phase():
    state = load_state()
    if not state:
        print("❌ 错误：引擎未初始化。请先使用 `init` 命令发车。")
        return
    
    intent_idx = state["current_intent_index"]
    if intent_idx >= len(state["queue"]):
        print("✅ 任务队列已全部完成，无需推进。")
        return
        
    phase_idx = state["current_phase_index"]
    current_intent = state["queue"][intent_idx]
    
    # Check if current phase is Archive (the last phase)
    if phase_idx == len(PHASES) - 1:
        print(f"🎉 意图 [{current_intent}] 生命周期结束，开始归档与闭环 (触发 loop_hook)！")
        _update_launch_spec_row(state["launch_spec_file"], current_intent, status="DONE", phase=PHASES[phase_idx])
        state["current_intent_index"] += 1
        state["current_phase_index"] = 0
        state["retries"] = 0
        
        if state["current_intent_index"] >= len(state["queue"]):
            print("🏆 所有意图队列已执行完毕！系统安全退出。")
        else:
            next_intent = state["queue"][state["current_intent_index"]]
            print(f"🔄 [loop_hook] 自动拉起下一个意图: [{next_intent}] -> Phase: {PHASES[0]}")
            _update_launch_spec_row(state["launch_spec_file"], next_intent, status="IN_PROGRESS", phase=PHASES[0])
    else:
        state["current_phase_index"] += 1
        state["retries"] = 0
        next_phase_name = PHASES[state["current_phase_index"]]
        print(f"⏩ 状态流转: 进入下一阶段 -> {next_phase_name}")
        if next_phase_name == "3.5_Approval":
            _update_launch_spec_row(state["launch_spec_file"], current_intent, status="WAITING_APPROVAL", phase=next_phase_name)
            print("⚠️ 进入 HITL (人类防线) 阶段。Agent 请立即停止自动推进，询问用户意见。")
        else:
            _update_launch_spec_row(state["launch_spec_file"], current_intent, status="IN_PROGRESS", phase=next_phase_name)
            
    save_state(state)

def fail_phase(reason):
    state = load_state()
    if not state:
        print("❌ 错误：引擎未初始化。")
        return
        
    state["retries"] += 1
    retries = state["retries"]
    current_phase = PHASES[state["current_phase_index"]]
    print(f"🚨 [fail_hook] 拦截到错误: {reason}")
    print(f"📉 阶段 {current_phase} 失败次数: {retries}/3")
    
    if retries >= 3:
        idx = state["current_intent_index"]
        if idx < len(state["queue"]):
            current_intent = state["queue"][idx]
            _update_launch_spec_row(state["launch_spec_file"], current_intent, status="FAILED", phase=current_phase, failed_reason=reason)
        print("⛔️ 【严重错误】已达到最大重试次数 (3)！触发防失控死循环保护。")
        print("Agent 请立即挂起并向人类报告，禁止继续盲目重试！")
    else:
        idx = state["current_intent_index"]
        if idx < len(state["queue"]):
            current_intent = state["queue"][idx]
            _update_launch_spec_row(state["launch_spec_file"], current_intent, phase=current_phase, failed_reason=reason)
        # Downgrade phase logic
        if state["current_phase_index"] > 0:
            state["current_phase_index"] -= 1
            prev_phase = PHASES[state["current_phase_index"]]
            print(f"🔙 状态机自动降级回溯 -> {prev_phase}")
        else:
            print("🔙 已在初始阶段，无法降级，请在当前阶段修复。")
            
    save_state(state)

def trigger_hook(hook_name):
    print(f"🪝 触发钩子 -> {hook_name} ...")
    print(f"✅ {hook_name} 执行完毕。")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python engine.py <init|status|next|fail|hook> [args]")
        sys.exit(1)
        
    cmd = sys.argv[1]
    if cmd == "init" and len(sys.argv) == 3:
        init_engine(sys.argv[2])
    elif cmd == "status":
        get_status()
    elif cmd == "next":
        next_phase()
    elif cmd == "fail" and len(sys.argv) >= 3:
        fail_phase(sys.argv[2])
    elif cmd == "hook" and len(sys.argv) == 3:
        trigger_hook(sys.argv[2])
    else:
        print("❌ 未知命令或参数错误。")
