# test_paraphrase_v2.py
# Comprehensive test suite for Emotion Understanding v2:
# Paraphrase clusters, indirect language, behavioral cues, and Hinglish.

import sys
import os
import json

# Terminal encoding fix for Windows
if sys.stdout.encoding.lower() != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = "C:/Users/ASUS/Downloads/mannmitra-prototype/mannmitra-prototype/backend"
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from emotion_engine import analyze_emotional_state, select_response_strategy
from safety import assess_risk

TEST_CLUSTERS = {
    "ACADEMIC_OVERWHELM": {
        "expected_emotion": ["anxiety", "frustration", "motivation_loss"],
        "expected_context": ["academic"],
        "expected_need": ["problem_solving", "coping_tool", "reassurance"],
        "messages": [
            "I'm really stressed about my assignments.",
            "Bro, so many assignments are piling up that I don't even know where to begin.",
            "I keep looking at my task list and my brain just freezes.",
            "I've been avoiding my coursework all day and now I feel terrible about it.",
            "Everything related to college feels like too much right now."
        ]
    },
    "LONELINESS": {
        "expected_emotion": ["loneliness", "sadness"],
        "expected_context": ["social", "general"],
        "expected_need": ["venting", "reassurance", "reflective_listening"],
        "messages": [
            "I feel lonely.",
            "Everyone seems to have their own group and I feel like I don't belong anywhere.",
            "I come back to my room and there's nobody I feel like talking to.",
            "I have people around me but somehow I still feel alone."
        ]
    },
    "LOW_SELF_CONFIDENCE": {
        "expected_emotion": ["sadness", "frustration", "motivation_loss"],
        "expected_context": ["self_esteem", "social", "academic"],
        "expected_need": ["reassurance", "venting"],
        "messages": [
            "I don't feel confident.",
            "Everyone in my class seems better than me.",
            "I keep comparing myself with others and feel like I'm not good enough.",
            "I don't think I'm capable of doing anything properly."
        ]
    },
    "PROCRASTINATION_AVOIDANCE": {
        "expected_emotion": ["motivation_loss", "anxiety", "frustration"],
        "expected_context": ["academic", "general"],
        "expected_need": ["problem_solving", "reassurance"],
        "messages": [
            "I keep procrastinating.",
            "I sit down to study but somehow an hour disappears.",
            "I keep opening my laptop and then doing everything except my work.",
            "I know what I need to do, but I just can't get myself to start."
        ]
    },
    "HINGLISH_SLANG": {
        "expected_context": ["academic", "social", "self_esteem", "general"],
        "messages": [
            {"msg": "Bhai dimaag kharab ho gaya hai assignments se.", "expected_emo": ["frustration", "anxiety"], "expected_ctx": "academic"},
            {"msg": "Yaar padhne baithta hu but kuch andar hi nahi jaa raha.", "expected_emo": ["frustration", "motivation_loss", "anxiety"], "expected_ctx": "academic"},
            {"msg": "Sab log aage nikal rahe hain aur main wahi ka wahi hu.", "expected_emo": ["sadness", "frustration"], "expected_ctx": "self_esteem"},
            {"msg": "Room pe aake ajeeb sa empty empty lagta hai.", "expected_emo": ["loneliness", "sadness"], "expected_ctx": "social"},
            {"msg": "Kuch karne ka mann hi nahi karta yaar.", "expected_emo": ["motivation_loss", "sadness"], "expected_ctx": "general"}
        ]
    }
}


def run_evaluation():
    print("=" * 80)
    print("EMOTION UNDERSTANDING V2 — PARAPHRASE & SEMANTIC EVALUATION")
    print("=" * 80)

    total_cases = 0
    passed_cases = 0

    results_log = []

    for cluster_name, data in TEST_CLUSTERS.items():
        print(f"\n--- CLUSTER: {cluster_name} ---")
        if cluster_name == "HINGLISH_SLANG":
            for item in data["messages"]:
                total_cases += 1
                msg = item["msg"]
                res = analyze_emotional_state(msg, [])
                emo_ok = res["emotion"] in item["expected_emo"]
                ctx_ok = res["context"] == item["expected_ctx"]
                is_pass = emo_ok and ctx_ok
                if is_pass:
                    passed_cases += 1
                status = "PASS" if is_pass else "WARN/FAIL"
                print(f"[{status}] \"{msg}\"")
                print(f"       -> Emotion: {res['emotion']} (exp: {item['expected_emo']})")
                print(f"       -> Intensity: {res['intensity']}/10 | Context: {res['context']} (exp: {item['expected_ctx']})")
                print(f"       -> Need: {res['underlying_need']} | Conf: {res['confidence']}")
                print(f"       -> Evidence: {res['evidence']}")
                results_log.append({"msg": msg, "res": res, "status": status})
        else:
            for msg in data["messages"]:
                total_cases += 1
                res = analyze_emotional_state(msg, [])
                emo_ok = res["emotion"] in data["expected_emotion"]
                ctx_ok = res["context"] in data["expected_context"]
                need_ok = res["underlying_need"] in data["expected_need"]
                is_pass = emo_ok and (ctx_ok or need_ok)
                if is_pass:
                    passed_cases += 1
                status = "PASS" if is_pass else "WARN/FAIL"
                print(f"[{status}] \"{msg}\"")
                print(f"       -> Emotion: {res['emotion']} | Intensity: {res['intensity']}/10 | Context: {res['context']}")
                print(f"       -> Need: {res['underlying_need']} | Conf: {res['confidence']}")
                print(f"       -> Evidence: {res['evidence']}")
                results_log.append({"msg": msg, "res": res, "status": status})

    print("\n" + "=" * 80)
    print(f"SUMMARY: {passed_cases}/{total_cases} tests evaluated with aligned semantic classification.")
    print("=" * 80)


if __name__ == "__main__":
    run_evaluation()
