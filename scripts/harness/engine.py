#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Harness Lifecycle Engine CLI
Agent 必须通过此工具来驱动状态机、执行任务队列并触发 Hooks。
禁止大模型自行在纯文本文件中修改队列状态（[ ] -> [x]），以防止幻觉导致状态错乱。
"""

import sys
import json
import os
from datetime import datetime

STATE_FILE = ".trae/harness/catalog/engine_state.json"
CATALOG_DIR = ".trae/intent/catalog"
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
        f.write("此文件由 Harness Engine 自动生成与维护。Agent 请使用 `python .trae/scripts/harness/engine.py status` 查看当前任务状态。\n\n")
        f.write("## 意图队列\n")
        for intent in intents:
            f.write(f"- [ ] {intent}\n")
    return filepath

def sync_launch_spec_checkbox(filepath, completed_intent):
    if not os.path.exists(filepath): return
    with open(filepath, "r") as f:
        lines = f.readlines()
    with open(filepath, "w") as f:
        for line in lines:
            if f"- [ ] {completed_intent}" in line:
                f.write(line.replace("- [ ]", "- [x]"))
            else:
                f.write(line)

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
        print("⚠️ 强拦截点：请等待人类确认后，再执行 `python .trae/scripts/harness/engine.py next` 进入 Implement 阶段！")

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
        sync_launch_spec_checkbox(state["launch_spec_file"], current_intent)
        state["current_intent_index"] += 1
        state["current_phase_index"] = 0
        state["retries"] = 0
        
        if state["current_intent_index"] >= len(state["queue"]):
            print("🏆 所有意图队列已执行完毕！系统安全退出。")
        else:
            next_intent = state["queue"][state["current_intent_index"]]
            print(f"🔄 [loop_hook] 自动拉起下一个意图: [{next_intent}] -> Phase: {PHASES[0]}")
    else:
        state["current_phase_index"] += 1
        state["retries"] = 0
        next_phase_name = PHASES[state["current_phase_index"]]
        print(f"⏩ 状态流转: 进入下一阶段 -> {next_phase_name}")
        if next_phase_name == "3.5_Approval":
            print("⚠️ 进入 HITL (人类防线) 阶段。Agent 请立即停止自动推进，询问用户意见。")
            
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
        print("⛔️ 【严重错误】已达到最大重试次数 (3)！触发防失控死循环保护。")
        print("Agent 请立即挂起并向人类报告，禁止继续盲目重试！")
    else:
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
