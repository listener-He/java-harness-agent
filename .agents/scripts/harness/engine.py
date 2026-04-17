#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Harness Lifecycle Engine CLI
Helper tool to drive the state machine and maintain the task queue.
Prevents manual markdown editing errors.
"""

import sys
import json
import os
import argparse
from datetime import datetime

STATE_FILE = ".agents/workflow/runs/engine_state.json"
CATALOG_DIR = ".agents/router/runs"
ALL_PHASES = [
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
        f.write(f"# Launch Spec - {timestamp}\n\n")
        f.write("## State Machine\n")
        f.write("| Intent | Status | Phase | Artifact/Log | Failed_Reason |\n")
        f.write("|---|---|---|---|---|\n")
        for i, intent in enumerate(intents):
            status = "IN_PROGRESS" if i == 0 else "PENDING"
            phase = "1_Explorer" if i == 0 else "-"
            f.write(f"| {intent} | {status} | {phase} | - | - |\n")
        f.write("\n")
        f.write("## Resume\n")
        f.write("- When resuming, read this file and continue from `Status/Phase`.\n")
        f.write("- If `WAITING_APPROVAL`, wait for human confirmation before entering Implement.\n")
        f.write("- If `FAILED`, stop and request human intervention.\n")
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
            if status is not None: parts[1] = status
            if phase is not None: parts[2] = phase
            if artifact is not None: parts[3] = artifact
            if failed_reason is not None: parts[4] = failed_reason
            f.write("| " + " | ".join(parts) + " |\n")
            updated = True

def init_engine(args):
    intents = [i.strip() for i in args.intents.split(",") if i.strip()]
    if not intents:
        print("❌ Error: Must provide at least one intent (e.g., Propose.API,Implement.Code)")
        return
    
    filepath = write_launch_spec(intents)
    state = {
        "launch_spec_file": filepath,
        "queue": intents,
        "current_intent_index": 0,
        "current_phase": "1_Explorer",
        "retries": 0
    }
    save_state(state)
    print(f"✅ Engine initialized! Launch spec generated: {filepath}")
    print(f"🔄 Current Intent: [{intents[0]}] -> Phase: 1_Explorer")

def get_status(args):
    state = load_state()
    if not state:
        print("ℹ️ Engine idle.")
        return
    
    idx = state["current_intent_index"]
    if idx >= len(state["queue"]):
        print(f"✅ All intents completed! (File: {state['launch_spec_file']})")
        return
        
    current_intent = state["queue"][idx]
    current_phase = state["current_phase"]
    retries = state.get("retries", 0)
    print(f"📊 【Engine Status】")
    print(f"- File: {state['launch_spec_file']}")
    print(f"- Intent: [{current_intent}] ({idx+1}/{len(state['queue'])})")
    print(f"- Phase: {current_phase}")
    print(f"- Retries: {retries}/3")
    if current_phase == "3.5_Approval":
        print("⚠️ HITL Gate: Wait for human confirmation before transitioning to Implement!")

def transition_phase(args):
    state = load_state()
    if not state:
        print("❌ Error: Engine not initialized. Run `init` first.")
        return
    
    target_phase = args.to
    valid_phases = ALL_PHASES + ["DONE"]
    
    # Simple prefix matching for convenience (e.g., "Review" -> "3_Review")
    matched_phase = None
    for p in valid_phases:
        if target_phase.lower() in p.lower():
            matched_phase = p
            break
            
    if not matched_phase:
        print(f"❌ Error: Invalid phase '{target_phase}'. Valid phases: {valid_phases}")
        return
        
    intent_idx = state["current_intent_index"]
    if intent_idx >= len(state["queue"]):
        print("✅ Queue already completed.")
        return
        
    current_intent = state["queue"][intent_idx]
    
    if matched_phase == "DONE":
        print(f"🎉 Intent [{current_intent}] completed!")
        _update_launch_spec_row(state["launch_spec_file"], current_intent, status="DONE", phase="6_Archive")
        state["current_intent_index"] += 1
        state["current_phase"] = "1_Explorer"
        state["retries"] = 0
        
        if state["current_intent_index"] >= len(state["queue"]):
            print("🏆 All intents completed! Engine exiting cleanly.")
        else:
            next_intent = state["queue"][state["current_intent_index"]]
            print(f"🔄 Auto-pulling next intent: [{next_intent}] -> Phase: 1_Explorer")
            _update_launch_spec_row(state["launch_spec_file"], next_intent, status="IN_PROGRESS", phase="1_Explorer")
    else:
        state["current_phase"] = matched_phase
        state["retries"] = 0
        print(f"⏩ Transitioning to -> {matched_phase}")
        if matched_phase == "3.5_Approval":
            _update_launch_spec_row(state["launch_spec_file"], current_intent, status="WAITING_APPROVAL", phase=matched_phase)
            print("⚠️ HITL (Human-in-the-loop) Gate. Agent MUST stop and ask user for approval.")
        else:
            _update_launch_spec_row(state["launch_spec_file"], current_intent, status="IN_PROGRESS", phase=matched_phase)
            
    save_state(state)

def fail_phase(args):
    state = load_state()
    if not state:
        print("❌ Error: Engine not initialized.")
        return
        
    state["retries"] = state.get("retries", 0) + 1
    retries = state["retries"]
    current_phase = state["current_phase"]
    reason = args.reason
    
    print(f"🚨 [fail_hook] Error caught: {reason}")
    print(f"📉 Phase {current_phase} failures: {retries}/3")
    
    idx = state["current_intent_index"]
    if idx < len(state["queue"]):
        current_intent = state["queue"][idx]
        if retries >= 3:
            _update_launch_spec_row(state["launch_spec_file"], current_intent, status="FAILED", phase=current_phase, failed_reason=reason)
            print("⛔️ 【CRITICAL】Max retries (3) reached! Runaway protection triggered.")
            print("Agent MUST suspend and report to human. DO NOT BLINDLY RETRY!")
        else:
            _update_launch_spec_row(state["launch_spec_file"], current_intent, phase=current_phase, failed_reason=reason)
            
    save_state(state)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Harness Lifecycle Engine CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    init_p = subparsers.add_parser("init", help="Initialize the engine with intent queue")
    init_p.add_argument("intents", help="Comma-separated intents (e.g. Propose.API,Implement.Code)")
    
    status_p = subparsers.add_parser("status", help="Get current engine status")
    
    trans_p = subparsers.add_parser("transition", help="Transition to a new phase")
    trans_p.add_argument("--to", required=True, help="Target phase (e.g. Implement, QA, DONE)")
    
    fail_p = subparsers.add_parser("fail", help="Report a failure and trigger fail_hook")
    fail_p.add_argument("reason", help="Failure reason description")
    
    args = parser.parse_args()
    
    if args.command == "init":
        init_engine(args)
    elif args.command == "status":
        get_status(args)
    elif args.command == "transition":
        transition_phase(args)
    elif args.command == "fail":
        fail_phase(args)
