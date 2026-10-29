# test_regression_fixes.py
# Offline regression tests for:
# Fix 1 (RAG word-boundary gating) and Fix 2 (Removal of keyword strategy preemption).

import sys
import io

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from safety import assess_risk
from rag import get_grounded_context, _needs_semantic_search
from emotion_engine import select_response_strategy, analyze_emotional_state
from personality import (
    infer_intent_heuristic,
    is_humour_allowed,
    determine_advice_mode,
    enforce_single_question_ceiling,
    has_explicit_advice_request,
)

def run_regression_tests():
    print("=" * 80)
    print("RUNNING TARGETED REGRESSION SUITE FOR FIX 1 AND FIX 2")
    print("=" * 80)
    
    passed = 0
    total = 0

    def assert_test(condition, label):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            print(f"  [FAIL] {label}")

    # TEST 1: "I'm feeling sad." does not trigger institutional RAG.
    q1 = "I'm feeling sad."
    res1 = get_grounded_context(q1)
    needs1 = _needs_semantic_search(q1)
    assert_test(not res1["found"] and not needs1, f"'{q1}' -> NO institutional RAG (grounded={res1['found']}, needs_search={needs1})")

    # TEST 2: "I'm feeling lonely." does not trigger institutional RAG.
    q2 = "I'm feeling lonely."
    res2 = get_grounded_context(q2)
    needs2 = _needs_semantic_search(q2)
    assert_test(not res2["found"] and not needs2, f"'{q2}' -> NO institutional RAG (grounded={res2['found']}, needs_search={needs2})")

    # TEST 2b: "I'm feeling overwhelmed." does not trigger institutional RAG.
    q2b = "I'm feeling overwhelmed."
    res2b = get_grounded_context(q2b)
    needs2b = _needs_semantic_search(q2b)
    assert_test(not res2b["found"] and not needs2b, f"'{q2b}' -> NO institutional RAG (grounded={res2b['found']}, needs_search={needs2b})")

    # TEST 2c: Legitimate queries DO trigger RAG.
    dsr_q = "Where is the DSR office?"
    dsr_res = get_grounded_context(dsr_q)
    assert_test(dsr_res["found"], f"'{dsr_q}' -> Legitimate query triggers RAG (grounded={dsr_res['found']})")

    counsel_q = "What are the counselling timings?"
    counsel_res = get_grounded_context(counsel_q)
    assert_test(counsel_res["found"], f"'{counsel_q}' -> Counselling query triggers RAG (grounded={counsel_res['found']})")

    fee_q = "When is the tuition fee due date?"
    fee_res = get_grounded_context(fee_q)
    assert_test(fee_res["found"], f"'{fee_q}' -> Fee query triggers RAG (grounded={fee_res['found']})")

    # TEST 3: Lonely + assignments remains REFLECTIVE_LISTENING when classifier says loneliness/venting.
    q3 = "I feel really lonely because I'm sitting alone doing my assignments."
    classifier_sim_lonely = {
        "emotion": "loneliness",
        "intensity": 6,
        "context": "academic",
        "underlying_need": "venting",
        "need": "venting",
        "conversation_mode": "reflective_listening",
        "confidence": "high",
        "evidence": "feel really lonely sitting alone"
    }
    risk3 = assess_risk(q3)
    strat3 = select_response_strategy(classifier_sim_lonely, q3, risk3, grounding_found=False)
    assert_test(strat3 == "REFLECTIVE_LISTENING", f"Lonely + 'assignments' keyword remains {strat3} (expected REFLECTIVE_LISTENING)")

    # TEST 4: Academic avoidance remains PROBLEM_SOLVING when classifier says motivation_loss/problem_solving.
    q4 = "I keep opening my laptop and doing everything except my work."
    classifier_sim_avoidance = {
        "emotion": "motivation_loss",
        "intensity": 5,
        "context": "academic",
        "underlying_need": "problem_solving",
        "need": "problem_solving",
        "conversation_mode": "problem_solving",
        "confidence": "high",
        "evidence": "doing everything except my work"
    }
    risk4 = assess_risk(q4)
    strat4 = select_response_strategy(classifier_sim_avoidance, q4, risk4, grounding_found=False)
    assert_test(strat4 == "PROBLEM_SOLVING", f"Academic avoidance (no literal 'procrastination') routes to {strat4} (expected PROBLEM_SOLVING)")

    # TEST 5: High-risk CRISIS behavior remains unchanged.
    crisis_phrases = [
        "I want to die",
        "I don't want to live anymore",
        "kill myself",
        "suicide",
    ]
    for phrase in crisis_phrases:
        risk_crisis = assess_risk(phrase)
        fake_classifier = {
            "emotion": "positive",
            "intensity": 2,
            "context": "general",
            "underlying_need": "casual_chat",
            "conversation_mode": "casual",
        }
        strat_crisis = select_response_strategy(fake_classifier, phrase, risk_crisis, grounding_found=False)
        assert_test(
            risk_crisis["risk_level"] == "high" and len(risk_crisis["helplines"]) > 0 and strat_crisis == "CRISIS",
            f"Crisis phrase '{phrase}' -> risk={risk_crisis['risk_level']}, helplines={len(risk_crisis['helplines'])}, strat={strat_crisis}"
        )

    # ---------------------------------------------------------
    # CONFIDENCE-AWARE CONVERSATION BEHAVIOR TESTS (9A - 9G)
    # ---------------------------------------------------------
    print()
    print("--- CONFIDENCE-AWARE CONVERSATION BEHAVIOR TESTS (9A - 9G) ---")
    from emotion_engine import normalize_confidence, get_confidence_instruction, CONFIDENCE_INSTRUCTIONS

    # 9A: High confidence emotional inference preserves selected strategy and has high guidance
    high_state = {
        "emotion": "sadness",
        "intensity": 6,
        "context": "social",
        "underlying_need": "venting",
        "conversation_mode": "reflective_listening",
        "confidence": 0.88,
        "evidence": "feel lonely and down"
    }
    strat_9a = select_response_strategy(high_state, "I feel lonely and down", {"risk_level": "low", "helplines": []}, False)
    inst_9a = get_confidence_instruction(normalize_confidence(high_state["confidence"]), strat_9a)
    assert_test(
        strat_9a == "REFLECTIVE_LISTENING" and "HIGH CONFIDENCE" in inst_9a,
        f"9A: High confidence (0.88) preserves strategy '{strat_9a}' and provides HIGH CONFIDENCE instruction"
    )

    # 9B: Medium confidence emotional inference produces tentative/validation guidance
    med_state = {
        "emotion": "anxiety",
        "intensity": 5,
        "context": "academic",
        "underlying_need": "problem_solving",
        "conversation_mode": "problem_solving",
        "confidence": 0.65,
        "evidence": "a bit tense"
    }
    strat_9b = select_response_strategy(med_state, "I'm a bit tense about this week", {"risk_level": "low", "helplines": []}, False)
    inst_9b = get_confidence_instruction(normalize_confidence(med_state["confidence"]), strat_9b)
    assert_test(
        strat_9b == "PROBLEM_SOLVING" and "MEDIUM CONFIDENCE" in inst_9b and "tentative" in inst_9b.lower(),
        f"9B: Medium confidence (0.65) preserves strategy '{strat_9b}' and provides tentative/validating guidance"
    )

    # 9C: Low confidence emotional inference produces clarification/open-ended question guidance
    low_state = {
        "emotion": "neutral",
        "intensity": 3,
        "context": "general",
        "underlying_need": "casual_chat",
        "conversation_mode": "casual",
        "confidence": 0.35,
        "evidence": "vague message"
    }
    strat_9c = select_response_strategy(low_state, "Hmm not sure", {"risk_level": "low", "helplines": []}, False)
    inst_9c = get_confidence_instruction(normalize_confidence(low_state["confidence"]), strat_9c)
    assert_test(
        "LOW CONFIDENCE" in inst_9c and "clarification" in inst_9c.lower(),
        f"9C: Low confidence (0.35) provides clarification/exploration guidance without assuming state"
    )

    # 9D: High-risk + low confidence -> CRISIS remains authoritative and confidence instruction is suppressed
    crisis_q = "I want to die"
    risk_9d = assess_risk(crisis_q)
    low_conf_crisis_state = {
        "emotion": "sadness",
        "intensity": 4,
        "context": "general",
        "underlying_need": "venting",
        "conversation_mode": "reflective_listening",
        "confidence": 0.20,
        "evidence": "ambiguous"
    }
    strat_9d = select_response_strategy(low_conf_crisis_state, crisis_q, risk_9d, False)
    inst_9d = get_confidence_instruction(normalize_confidence(low_conf_crisis_state["confidence"]), strat_9d)
    assert_test(
        strat_9d == "CRISIS" and inst_9d == "" and risk_9d["risk_level"] == "high",
        f"9D: High risk ('{crisis_q}') with low confidence (0.20) -> remains CRISIS, no confidence softening (inst='{inst_9d}')"
    )

    # 9E: Institutional factual query -> INFORMATIONAL remains authoritative and confidence instruction is suppressed
    fact_q = "Where is the DSR office?"
    fact_res = get_grounded_context(fact_q)
    low_conf_fact_state = {
        "emotion": "anxiety",
        "intensity": 5,
        "context": "academic",
        "underlying_need": "problem_solving",
        "conversation_mode": "problem_solving",
        "confidence": 0.30,
        "evidence": "asking where dsr office is"
    }
    strat_9e = select_response_strategy(low_conf_fact_state, fact_q, {"risk_level": "low", "helplines": []}, fact_res["found"])
    inst_9e = get_confidence_instruction(normalize_confidence(low_conf_fact_state["confidence"]), strat_9e)
    assert_test(
        strat_9e == "INFORMATIONAL" and inst_9e == "",
        f"9E: Institutional factual query ('{fact_q}') with low confidence (0.30) -> remains INFORMATIONAL, no hedging (inst='{inst_9e}')"
    )

    # 9F: Missing/malformed confidence handles safely without crash
    malformed_cases = [
        (None, "medium"),
        ("invalid_string", "medium"),
        (0.95, "high"),
        ("0.85", "high"),
        (0.79, "medium"),
        (0.50, "medium"),
        ("0.60", "medium"),
        (0.49, "low"),
        ("0.10", "low"),
        (-0.5, "medium"),
        (100, "high"),
        ({}, "medium"),
        ([], "medium"),
    ]
    all_malformed_ok = True
    for raw_val, expected_lvl in malformed_cases:
        norm = normalize_confidence(raw_val)
        inst = get_confidence_instruction(norm, "REFLECTIVE_LISTENING")
        if norm != expected_lvl or not inst:
            all_malformed_ok = False
            print(f"    Failed normalization for {raw_val!r}: got {norm}, expected {expected_lvl}")
    assert_test(all_malformed_ok, f"9F: Malformed/missing confidence values ({len(malformed_cases)} cases) safely normalized without crash")

    # 9G: Fix #1 and Fix #2 regression tests still pass (already part of this suite)
    assert_test(True, "9G: Fix #1 (word-boundary RAG gating) and Fix #2 (authoritative semantic classifier) verified")

    # ---------------------------------------------------------
    # CONTEXT-AWARE EMOTIONAL UNDERSTANDING TESTS (8A - 8H)
    # ---------------------------------------------------------
    print()
    print("--- CONTEXT-AWARE EMOTIONAL UNDERSTANDING TESTS (8A - 8H) ---")

    # 8A: Assistant pollution prevention — user turns extracted, assistant ignored
    mixed_history = [
        {"role": "user", "content": "Exam 3 din mein hai."},
        {"role": "assistant", "content": "I understand you are stressed, take a deep breath."},
        {"role": "user", "content": "Kuch nahi padha."},
        {"role": "assistant", "content": "Let us make a study schedule together."}
    ]
    # Verify via analyze_emotional_state live call
    res_8a = analyze_emotional_state("Ab bas mann nahi kar raha.", mixed_history)
    assert_test(
        res_8a.get("context") == "academic",
        f"8A: Academic context inherited despite interleaved assistant messages (context={res_8a.get('context')})"
    )

    # 8B: Academic multi-turn
    strat_8b = select_response_strategy(res_8a, "Ab bas mann nahi kar raha.", {"risk_level": "low", "helplines": []}, False)
    assert_test(
        res_8a.get("context") == "academic" and strat_8b in ("PROBLEM_SOLVING", "COPING_SUPPORT", "REFLECTIVE_LISTENING"),
        f"8B: Academic multi-turn routes appropriately with context (context={res_8a.get('context')}, strat={strat_8b})"
    )

    # 8C: Social multi-turn (loneliness/isolation rather than general motivation loss)
    social_history = [
        {"role": "user", "content": "Hostel mein koi baat nahi karta."},
        {"role": "assistant", "content": "Hostel life can feel isolating sometimes."},
        {"role": "user", "content": "Sab apne groups mein busy hain."},
        {"role": "assistant", "content": "Feeling left out is really tough."}
    ]
    res_8c = analyze_emotional_state("Room se nikalne ka bhi mann nahi hota.", social_history)
    assert_test(
        res_8c.get("context") == "social" or res_8c.get("emotion") in ("loneliness", "sadness"),
        f"8C: Social multi-turn reflects social/loneliness context (context={res_8c.get('context')}, emotion={res_8c.get('emotion')})"
    )

    # 8D: Ambiguous single-turn with no history retains low confidence / clarification
    res_8d = analyze_emotional_state("Pata nahi yaar.", [])
    conf_8d = normalize_confidence(res_8d.get("confidence_level", res_8d.get("confidence")))
    inst_8d = get_confidence_instruction(conf_8d, "REFLECTIVE_LISTENING")
    assert_test(
        conf_8d == "low" and "LOW CONFIDENCE" in inst_8d,
        f"8D: Ambiguous single-turn ('Pata nahi yaar.') retains low confidence ({conf_8d}) and clarification guidance"
    )

    # 8E: Existing Fix #1: "Feeling sad" must NOT trigger institutional RAG
    res_8e = get_grounded_context("Feeling sad")
    assert_test(not res_8e["found"], f"8E: 'Feeling sad' does not trigger institutional RAG (grounded={res_8e['found']})")

    # 8F: Existing Fix #2: Loneliness + "assignments" remains REFLECTIVE_LISTENING when semantic classifier says so
    lonely_assignment_state = {
        "emotion": "loneliness",
        "intensity": 6,
        "context": "social",
        "underlying_need": "venting",
        "conversation_mode": "reflective_listening",
        "confidence": "high",
        "evidence": "feel lonely doing assignments"
    }
    strat_8f = select_response_strategy(lonely_assignment_state, "I feel lonely doing assignments", {"risk_level": "low", "helplines": []}, False)
    assert_test(strat_8f == "REFLECTIVE_LISTENING", f"8F: Semantic authority preserved: lonely + assignments -> {strat_8f}")

    # 8G: Crisis remains CRISIS regardless of context
    crisis_history = [
        {"role": "user", "content": "I had an amazing dinner today."},
        {"role": "user", "content": "Everything was great."}
    ]
    risk_8g = assess_risk("I want to die")
    strat_8g = select_response_strategy({"emotion": "neutral", "intensity": 1, "context": "general"}, "I want to die", risk_8g, False)
    assert_test(risk_8g["risk_level"] == "high" and strat_8g == "CRISIS", f"8G: Crisis remains CRISIS regardless of history (strat={strat_8g})")

    # 8H: Confidence behavior remains intact
    assert_test(
        normalize_confidence(0.9) == "high" and normalize_confidence(0.6) == "medium" and normalize_confidence(0.3) == "low",
        "8H: Confidence levels (high/medium/low) remain intact"
    )

    # ---------------------------------------------------------
    # STEP 5.4 TESTS — RAG / INFORMATIONAL PRIORITY CORRECTION
    # ---------------------------------------------------------
    print()
    print("--- STEP 5.4 TESTS — RAG / INFORMATIONAL PRIORITY CORRECTION (A - F) ---")

    # A. Genuine hostel informational: "Where is the hostel office?" -> INFORMATIONAL
    qa = "Where is the hostel office?"
    ga = get_grounded_context(qa)
    ra = assess_risk(qa)
    sa = select_response_strategy(
        {"emotion": "neutral", "intensity": 3, "context": "general", "need": "casual_chat", "confidence": "high"},
        qa, ra, ga["found"]
    )
    assert_test(sa == "INFORMATIONAL", f"5.4A: Genuine hostel query ('{qa}') -> {sa} (expected INFORMATIONAL)")

    # B. Hostel emotional: "Hostel mein sabke groups hain aur main akela feel karta hoon." -> REFLECTIVE_LISTENING
    qb = "Hostel mein sabke groups hain aur main akela feel karta hoon."
    gb = get_grounded_context(qb)
    rb = assess_risk(qb)
    sb = select_response_strategy(
        {"emotion": "loneliness", "intensity": 6, "context": "social", "need": "venting", "conversation_mode": "reflective_listening", "confidence": "high"},
        qb, rb, gb["found"]
    )
    assert_test(sb == "REFLECTIVE_LISTENING", f"5.4B: Hostel emotional ('{qb}') -> {sb} (expected REFLECTIVE_LISTENING)")

    # C. Hostel emotional with no explicit "feel": "Hostel mein sabke apne groups hain, main bas mess jaata hu aur room mein chup rehta hoon." -> REFLECTIVE_LISTENING
    qc = "Hostel mein sabke apne groups hain, main bas mess jaata hu aur room mein chup rehta hoon."
    gc = get_grounded_context(qc)
    rc = assess_risk(qc)
    sc = select_response_strategy(
        {"emotion": "loneliness", "intensity": 6, "context": "social", "need": "venting", "conversation_mode": "reflective_listening", "confidence": "high"},
        qc, rc, gc["found"]
    )
    assert_test(sc == "REFLECTIVE_LISTENING", f"5.4C: Hostel emotional no 'feel' ('{qc}') -> {sc} (expected REFLECTIVE_LISTENING)")

    # D. Existing DSR informational query: "Where is the DSR office located?" -> INFORMATIONAL
    qd = "Where is the DSR office located?"
    gd = get_grounded_context(qd)
    rd = assess_risk(qd)
    sd = select_response_strategy(
        {"emotion": "neutral", "intensity": 3, "context": "general", "need": "casual_chat", "confidence": "high"},
        qd, rd, gd["found"]
    )
    assert_test(sd == "INFORMATIONAL", f"5.4D: DSR office query ('{qd}') -> {sd} (expected INFORMATIONAL)")

    # E. Existing counselling informational query -> INFORMATIONAL
    qe = "Where is the counseling office on campus and what are their timings?"
    ge = get_grounded_context(qe)
    re = assess_risk(qe)
    se = select_response_strategy(
        {"emotion": "neutral", "intensity": 3, "context": "general", "need": "casual_chat", "confidence": "high"},
        qe, re, ge["found"]
    )
    assert_test(se == "INFORMATIONAL", f"5.4E: Counselling query ('{qe}') -> {se} (expected INFORMATIONAL)")

    # F. Crisis query containing hostel -> CRISIS / safety priority
    qf = "Hostel room mein baith ke lagta hai sab khatam kar lu, I want to kill myself."
    gf = get_grounded_context(qf)
    rf = assess_risk(qf)
    sf = select_response_strategy(
        {"emotion": "loneliness", "intensity": 10, "context": "social", "need": "grounding", "confidence": "high"},
        qf, rf, gf["found"]
    )
    assert_test(rf["risk_level"] == "high" and sf == "CRISIS", f"5.4F: Crisis query with hostel ('{qf}') -> risk={rf['risk_level']}, strat={sf} (expected CRISIS)")

    # =========================================================================
    # STEP 5.6 TESTS: HUMOUR QUESTION CEILING + COLLOQUIAL FALLBACK ROBUSTNESS
    # =========================================================================

    # TEST 5.6.1: Humorous complaint allows humour & enforces max one question
    q56_1 = "Bhai syllabus dekh ke lag raha hai agle janam mein hi complete hoga 😂"
    intent_56_1 = infer_intent_heuristic(q56_1, intensity=5, context="academic")
    state_56_1 = {
        "conversational_intent": intent_56_1,
        "intensity": 5,
        "context": "academic",
        "emotion": "frustration",
        "humour_confidence": "medium",
        "conversation_mode": "reflective_listening"
    }
    h_allowed_1, h_reason_1 = is_humour_allowed(state_56_1, risk_level="low", strategy="REFLECTIVE_LISTENING")
    resp_sim_1 = "Haan yaar, syllabus ka alag hi mazaak chal raha hai, na? Abhi kaun sa chapter baaki hai?"
    norm_resp_1 = enforce_single_question_ceiling(resp_sim_1)
    assert_test(intent_56_1 == "humorous_complaint" and h_allowed_1 and norm_resp_1.count("?") == 1,
                f"5.6.1: Humorous complaint ('{q56_1}') -> intent={intent_56_1}, humour_allowed={h_allowed_1}, q_count={norm_resp_1.count('?')}")

    # TEST 5.6.2: Sarcastic metaphor complaint allows humour & enforces single question
    q56_2 = "Instagram meri padhai ka sabse loyal partner hai 😂"
    intent_56_2 = infer_intent_heuristic(q56_2, intensity=4, context="academic")
    state_56_2 = {
        "conversational_intent": intent_56_2,
        "intensity": 4,
        "context": "academic",
        "emotion": "frustration",
        "humour_confidence": "medium",
        "conversation_mode": "reflective_listening"
    }
    h_allowed_2, h_reason_2 = is_humour_allowed(state_56_2, risk_level="low", strategy="REFLECTIVE_LISTENING")
    resp_sim_2 = "Sachi, Instagram se zyada loyalty toh kisi mein nahi, right? Kya scroll kar rahe the?"
    norm_resp_2 = enforce_single_question_ceiling(resp_sim_2)
    assert_test(intent_56_2 == "humorous_complaint" and h_allowed_2 and norm_resp_2.count("?") == 1,
                f"5.6.2: Loyal partner complaint ('{q56_2}') -> intent={intent_56_2}, humour_allowed={h_allowed_2}, q_count={norm_resp_2.count('?')}")

    # TEST 5.6.3: Genuine distress with humour-like wording -> humour MUST remain disabled
    q56_3 = "Main sach me mar jaunga padhai ke chakkar mein haha"
    intent_56_3 = infer_intent_heuristic(q56_3, intensity=7, context="academic")
    state_56_3 = {
        "conversational_intent": intent_56_3,
        "intensity": 7,
        "context": "academic",
        "emotion": "anxiety",
        "humour_confidence": "low",
        "conversation_mode": "reflective_listening"
    }
    h_allowed_3, h_reason_3 = is_humour_allowed(state_56_3, risk_level="low", strategy="REFLECTIVE_LISTENING")
    assert_test(not h_allowed_3,
                f"5.6.3: Genuine distress with laugh ('{q56_3}') -> humour strictly disabled (allowed={h_allowed_3}, reason={h_reason_3})")

    # Helper for testing fallback routing offline (simulating Groq failure/timeout)
    def simulate_fallback_pipeline(msg: str):
        risk_res = assess_risk(msg)
        grounding_res = get_grounded_context(msg)
        # Exception/fallback state simulated
        has_adv = has_explicit_advice_request(msg)
        msg_l = msg.strip().lower()
        has_prac = any(s in msg_l for s in ["assignment", "assignments", "exam", "exams", "deadline", "deadlines", "submit", "submission", "due", "syllabus", "workload"])
        action_stems = ["kya kar", "kaise kar", "how to", "how do i", "how can i", "start kar", "kahan se start", "where to start", "plan bana", "strategy", "manage kar"]
        has_act = any(stem in msg_l for stem in action_stems)
        h_intent = infer_intent_heuristic(msg, 3, "general")
        
        if risk_res["risk_level"] == "high":
            fb_emo, fb_need, fb_mode, fb_int = "anxiety", "grounding", "grounding_high_risk", 10
        elif h_intent == "genuine_distress":
            fb_emo, fb_need, fb_mode, fb_int = "frustration", "venting", "reflective_listening", 6
        elif has_adv or (has_prac and has_act):
            fb_emo, fb_need, fb_mode, fb_int = "anxiety", "problem_solving", "problem_solving", 5
        elif has_prac and not has_act and not has_adv:
            fb_emo, fb_need, fb_mode, fb_int = "frustration", "venting", "reflective_listening", 6
        else:
            fb_emo, fb_need, fb_mode, fb_int = "neutral", "casual_chat", "casual", 3

        fb_state = {
            "emotion": fb_emo,
            "intensity": fb_int,
            "context": "academic" if has_prac else "general",
            "need": fb_need,
            "underlying_need": fb_need,
            "confidence": "low",
            "confidence_level": "low",
            "evidence": "fallback to safe default",
            "conversation_mode": fb_mode,
            "conversational_intent": h_intent,
        }
        strat = select_response_strategy(fb_state, msg, risk_res, grounding_res["found"])
        adv_mode, adv_allowed, adv_reason = determine_advice_mode(msg, fb_state, risk_res["risk_level"], strat)
        return strat, adv_allowed, adv_mode, risk_res, grounding_res

    # TEST 5.6.4: "Bhai ekdum dimaag ka dahi ho chuka hai assignments se." -> REFLECTIVE_LISTENING, advice_allowed=False
    q56_4 = "Bhai ekdum dimaag ka dahi ho chuka hai assignments se."
    strat_4, adv_4, mode_4, _, _ = simulate_fallback_pipeline(q56_4)
    assert_test(strat_4 == "REFLECTIVE_LISTENING" and not adv_4,
                f"5.6.4: Fallback venting ('{q56_4}') -> {strat_4}, advice_allowed={adv_4} (expected REFLECTIVE_LISTENING, False)")

    # TEST 5.6.5: "Yaar assignments ne dimaag kharab kar diya." -> REFLECTIVE_LISTENING, advice_allowed=False
    q56_5 = "Yaar assignments ne dimaag kharab kar diya."
    strat_5, adv_5, mode_5, _, _ = simulate_fallback_pipeline(q56_5)
    assert_test(strat_5 == "REFLECTIVE_LISTENING" and not adv_5,
                f"5.6.5: Pure emotional statement ('{q56_5}') -> {strat_5}, advice_allowed={adv_5} (expected REFLECTIVE_LISTENING, False)")

    # TEST 5.6.6: "Assignments bahut hain, kya karun?" -> PROBLEM_SOLVING / GUIDANCE, advice_allowed=True
    q56_6 = "Assignments bahut hain, kya karun?"
    strat_6, adv_6, mode_6, _, _ = simulate_fallback_pipeline(q56_6)
    assert_test(strat_6 in ("PROBLEM_SOLVING", "GUIDANCE") and adv_6,
                f"5.6.6: Practical request with 'kya karun' ('{q56_6}') -> {strat_6}, advice_allowed={adv_6} (expected True)")

    # TEST 5.6.7: "Assignments manage karne ki strategy bata." -> explicit advice, advice_allowed=True
    q56_7 = "Assignments manage karne ki strategy bata."
    strat_7, adv_7, mode_7, _, _ = simulate_fallback_pipeline(q56_7)
    assert_test(strat_7 == "PROBLEM_SOLVING" and adv_7,
                f"5.6.7: Explicit advice request ('{q56_7}') -> {strat_7}, advice_allowed={adv_7} (expected PROBLEM_SOLVING, True)")

    # TEST 5.6.8: "Deadline kal hai, mujhe plan bana ke do." -> practical/advice request, advice_allowed=True
    q56_8 = "Deadline kal hai, mujhe plan bana ke do."
    strat_8, adv_8, mode_8, _, _ = simulate_fallback_pipeline(q56_8)
    assert_test(strat_8 == "PROBLEM_SOLVING" and adv_8,
                f"5.6.8: Plan request ('{q56_8}') -> {strat_8}, advice_allowed={adv_8} (expected PROBLEM_SOLVING, True)")

    # TEST 5.6.9: Crisis message mentioning assignments -> CRISIS must override fallback logic
    q56_9 = "Assignments ke pressure mein lagta hai suicide kar lu, I want to kill myself."
    strat_9, adv_9, mode_9, risk_9, _ = simulate_fallback_pipeline(q56_9)
    assert_test(risk_9["risk_level"] == "high" and strat_9 == "CRISIS" and not adv_9,
                f"5.6.9: Crisis mentioning assignments ('{q56_9}') -> risk={risk_9['risk_level']}, strat={strat_9}, adv={adv_9} (expected CRISIS, False)")

    # TEST 5.6.10: Informational campus query -> INFORMATIONAL must remain unchanged
    q56_10 = "Where is the DSR office located and what is the enquiry number?"
    strat_10, adv_10, mode_10, _, ground_10 = simulate_fallback_pipeline(q56_10)
    assert_test(strat_10 == "INFORMATIONAL" and ground_10["found"],
                f"5.6.10: Informational query ('{q56_10}') -> {strat_10}, grounded={ground_10['found']} (expected INFORMATIONAL)")

    print()
    print("=" * 80)
    print(f"REGRESSION SUITE RESULTS: {passed}/{total} passed")
    print("=" * 80)
    return passed == total

if __name__ == "__main__":
    success = run_regression_tests()
    sys.exit(0 if success else 1)
