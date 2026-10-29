# test_emotion_adaptive.py — Emotion-Adaptive Intervention Engine tests
# Covers: strategy selection, safety override, RAG gating, and live /chat integration
# Run offline:  python test_emotion_adaptive.py --offline   (no backend / no API key needed for strategy+gating)
# Run live:    python test_emotion_adaptive.py              (requires backend at 127.0.0.1:8000)
import sys
import json
import argparse

if sys.stdout.encoding.lower() != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import os
BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from safety import assess_risk
from rag import get_grounded_context, _needs_semantic_search, INFO_SIGNAL_WORDS
from emotion_engine import select_response_strategy, STRATEGY_INSTRUCTIONS

# Simulated classifier outputs representative of Groq returns for each test message
SIM = {
    "low":        {"emotion":"sadness","intensity":7,"context":"general","need":"venting","conversation_mode":"reflective_listening"},
    "assignments":{"emotion":"anxiety","intensity":7,"context":"academic","need":"problem_solving","conversation_mode":"problem_solving"},
    "calm":       {"emotion":"anxiety","intensity":8,"context":"academic","need":"coping_tool","conversation_mode":"coping_tool"},
    "dsr":        {"emotion":"neutral","intensity":3,"context":"general","need":"casual_chat","conversation_mode":"casual"},
    "professor":  {"emotion":"frustration","intensity":6,"context":"academic","need":"problem_solving","conversation_mode":"problem_solving"},
    "crisis":     {"emotion":"sadness","intensity":9,"context":"general","need":"grounding","conversation_mode":"grounding_high_risk"},
}

CASES = [
    {"id":"low_today",   "message":"I'm feeling really low today.",                               "sim":"low",         "expected":"REFLECTIVE_LISTENING"},
    {"id":"assignments", "message":"I have too many assignments and don't know where to start.", "sim":"assignments","expected":"PROBLEM_SOLVING"},
    {"id":"calm_exam",   "message":"I can't calm down before my exam.",                          "sim":"calm",        "expected":"COPING_SUPPORT"},
    {"id":"dsr",         "message":"Where is the DSR office?",                                   "sim":"dsr",         "expected":"INFORMATIONAL"},
    {"id":"professor",   "message":"How do I talk to my professor about my workload?",           "sim":"professor",   "expected":"GUIDANCE", "also_ok":["PROBLEM_SOLVING"]},
    {"id":"crisis",      "message":"I don't want to live anymore",                               "sim":"crisis",      "expected":"CRISIS"},
]

pass_n = 0
fail_n = 0

def check(msg, expected, got, also_ok=None):
    global pass_n, fail_n
    allowed = [expected] + (also_ok or [])
    ok = got in allowed
    tag = "PASS" if ok else "FAIL"
    if ok: pass_n += 1
    else: fail_n += 1
    print(f"  [{tag}] -> {got} (expected {expected}{'' if not also_ok else ' or '+','.join(also_ok)})")
    return ok

print("="*80)
print("1) Strategy selection (offline, simulated classifier)")
print("="*80)
for c in CASES:
    emo = SIM[c["sim"]]
    risk = assess_risk(c["message"])
    grounding = get_grounded_context(c["message"])
    strat = select_response_strategy(emo, c["message"], risk, grounding["found"])
    print(f"[{c['id']}] \"{c['message']}\"")
    print(f"     emotion={emo['emotion']} need={emo['need']} mode={emo['conversation_mode']}  risk={risk['risk_level']} grounded={grounding['found']}")
    check(c["message"], c["expected"], strat, c.get("also_ok"))

print()
print("="*80)
print("2) Safety not weakened")
print("="*80)
# High-risk must still be CRISIS regardless of emo
for phrase in ["I want to die", "I don't want to live anymore", "kill myself"]:
    emo_fake = {"emotion":"positive","intensity":2,"context":"general","need":"casual_chat","conversation_mode":"casual"}
    risk = assess_risk(phrase)
    strat = select_response_strategy(emo_fake, phrase, risk, False)
    print(f"  phrase={phrase!r} risk={risk['risk_level']} helplines={len(risk['helplines'])} -> {strat}", end=" ")
    check(phrase, "CRISIS", strat)
    assert len(risk["helplines"])>0, "helplines empty for high risk!"

# Moderate risk should NOT trigger CRISIS
risk_mod = assess_risk("I feel hopeless")
strat_mod = select_response_strategy(SIM["low"], "I feel hopeless", risk_mod, False)
print(f"  moderate 'I feel hopeless' risk={risk_mod['risk_level']} -> {strat_mod} (must NOT be CRISIS)", end=" ")
ok = strat_mod != "CRISIS"
print(f"  [{'PASS' if ok else 'FAIL'}]")
if ok: pass_n+=1
else: fail_n+=1

print()
print("="*80)
print("3) RAG gating preserved — emotional messages do NOT become INFORMATIONAL")
print("="*80)
emotional_msgs = [
    "I'm feeling really low today.",
    "I feel lonely.",
    "I'm stressed about exams.",
]
for m in emotional_msgs:
    g = get_grounded_context(m)
    emo = {"emotion":"sadness","intensity":6,"context":"general","need":"venting","conversation_mode":"reflective_listening"}
    risk = assess_risk(m)
    strat = select_response_strategy(emo, m, risk, g["found"])
    needs = _needs_semantic_search(m)
    print(f"  \"{m}\" needs_search={needs} grounded={g['found']} -> {strat}", end=" ")
    ok = strat != "INFORMATIONAL"
    print(f"  [{'PASS' if ok else 'FAIL'}] (must not be INFORMATIONAL)")
    if ok: pass_n+=1
    else: fail_n+=1

# Informational should still be INFORMATIONAL
for m in ["Where is the DSR office?", "Where is the counselling office?"]:
    g = get_grounded_context(m)
    emo = {"emotion":"neutral","intensity":3,"context":"general","need":"casual_chat","conversation_mode":"casual"}
    risk = assess_risk(m)
    strat = select_response_strategy(emo, m, risk, g["found"])
    print(f"  \"{m}\" grounded={g['found']} -> {strat}", end=" ")
    check(m, "INFORMATIONAL", strat)

print()
print("="*80)
print("4) Clinical language guard — no diagnose/cure claims in strategy instructions")
print("="*80)
bad_terms = ["mild depression","moderate depression","severe depression","cure","treat your","you have depression","you are depressed"]
allowed_phrase = "do not diagnose"
for name, instr in STRATEGY_INSTRUCTIONS.items():
    low = instr.lower()
    hits = [t for t in bad_terms if t in low]
    filtered = [h for h in hits if allowed_phrase not in low]
    ok = len(filtered)==0
    print(f"  {name}: {'PASS' if ok else 'FAIL '+str(filtered)}")
    if ok: pass_n+=1
    else: fail_n+=1

# Allow handling of --offline flag
parser = argparse.ArgumentParser()
parser.add_argument("--offline", action="store_true")
args, _ = parser.parse_known_args()

if not args.offline:
    print()
    print("="*80)
    print("5) Live /chat integration (requires backend at 127.0.0.1:8000)")
    print("="*80)
    try:
        import requests
        for c in CASES:
            try:
                r = requests.post("http://127.0.0.1:8000/chat", json={"message": c["message"], "history": []}, timeout=20)
                data = r.json()
                strat = data.get("strategy", "MISSING")
                emo = data.get("emotional_state", {})
                risk_level = data.get("risk_level")
                grounded = data.get("grounded")
                print(f"[{c['id']}] \"{c['message']}\"")
                print(f"     live strategy={strat} risk={risk_level} grounded={grounded} emotion={emo.get('emotion')} need={emo.get('need')} mode={emo.get('conversation_mode')}")
                # Check strategy (professor allows also_ok)
                check(c["message"], c["expected"], strat, c.get("also_ok"))
                # Contract preserved
                assert "reply" in data and "risk_level" in data and "helplines" in data and "grounded" in data and "emotional_state" in data
                # High-risk still has helplines
                if risk_level == "high":
                    assert len(data.get("helplines", []))>0
                    assert strat == "CRISIS"
                # RAG gating: emotional low_today must NOT be INFORMATIONAL nor leak contacts when grounded would misfire
            except Exception as e:
                print(f"  ERROR {c['id']}: {e}")
                fail_n+=1
    except ImportError:
        print("  requests not installed — skipping live tests")
else:
    print()
    print("(offline mode — skipped live /chat integration)")

print()
print("="*80)
print(f"SUMMARY: {pass_n} passed, {fail_n} failed")
print("="*80)
sys.exit(1 if fail_n else 0)
