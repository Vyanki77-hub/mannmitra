# test_personality.py
# Targeted unit tests for Personality Engine v1:
# Language & Peer-Tone Alignment Layer

import sys
import io

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from personality import (
    detect_language,
    get_language_and_register_instruction,
    infer_intent_heuristic,
    is_humour_allowed,
    get_humour_instruction,
    has_explicit_advice_request,
    determine_advice_mode,
    get_advice_instruction,
    is_reference_phrase,
    has_topic_shift_marker,
    detect_domain,
    detect_topic_shift_heuristic,
    determine_context_continuity,
    get_continuity_instruction,
    enforce_single_question_ceiling,
)
from safety import assess_risk
from emotion_engine import select_response_strategy


def run_tests():
    print("=" * 80)
    print("TESTING PERSONALITY ENGINE V1 — LANGUAGE, PEER-TONE & SARCASM/HUMOUR GATING")
    print("=" * 80)

    total = 0
    passed = 0

    def check(cond, label):
        nonlocal total, passed
        total += 1
        if cond:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            print(f"  [FAIL] {label}")

    # --- 1. LANGUAGE & SCRIPT DETECTION TESTS ---
    lang_cases = [
        # Hinglish Latin script
        ("Yaar aaj dimaag bilkul off hai.", "hinglish_latin"),
        ("Yaar aaj dimaag off hai.", "hinglish_latin"),
        ("Bhai aaj bahut stress hai.", "hinglish_latin"),
        ("Mujhe kuch accha nahi lag raha.", "hinglish_latin"),
        ("Mujhe lagta hai sab kharab ho raha hai.", "hinglish_latin"),
        ("Bas mann nahi kar raha kuch bhi karne ka.", "hinglish_latin"),
        ("Laptop khol ke baithta hoon aur ek ghanta reels dekh leta hoon.", "hinglish_latin"),
        ("Sab log aage nikal rahe hain aur main wahi ka wahi hoon.", "hinglish_latin"),
        ("Hostel mein sabke apne groups hain, main bas room mein pada rehta hoon.", "hinglish_latin"),
        ("Pata nahi, kisi se baat karne ka bhi mann nahi karta.", "hinglish_latin"),
        ("Kal exam hai aur syllabus mujhe dekh ke has raha hai.", "hinglish_latin"),
        ("Mere 4 assignments kal submit hone hain aur mujhe samajh nahi aa raha kahan se start karu.", "hinglish_latin"),
        ("Exam 3 din mein hai aur maine kuch nahi padha.", "hinglish_latin"),
        ("Pata nahi yaar.", "hinglish_latin"),
        ("Bas ho gaya.", "hinglish_latin"),
        ("Kya hi bolu ab.", "hinglish_latin"),
        ("Mujhe lag raha hai main handle nahi kar pa raha.", "hinglish_latin"),
        # English
        ("I feel really stressed today.", "english"),
        ("I don't want to live anymore.", "english"),
        ("Where is the DSR office?", "english"),
        ("What are the counselling timings?", "english"),
        ("How do I talk to my professor about my workload?", "english"),
        ("I have too many assignments and don't know where to start.", "english"),
        ("I can't calm down before my exam.", "english"),
        # English Homograph Regression Checks (Fix 1)
        ("The main issue is stress.", "english"),
        ("My screen has noticeable lag.", "english"),
        ("Close the room door.", "english"),
        ("It was pure luck.", "english"),
        # Devanagari Hindi
        ("आज मेरा दिमाग बिल्कुल काम नहीं कर रहा।", "hindi_devanagari"),
        ("मुझे बहुत डर लग रहा है परीक्षा से।", "hindi_devanagari"),
        ("बहुत उदास हूँ आज", "hindi_devanagari"),
    ]

    print("\n1. Language Detection Precision:")
    for msg, exp in lang_cases:
        got = detect_language(msg)
        check(got == exp, f"'{msg[:40]}' -> {got} (expected {exp})")

    # --- 2. PEER-TONE DIRECTIVE VALIDATION ---
    print("\n2. Peer-Tone Directives & Banned Phrases:")
    hinglish_inst = get_language_and_register_instruction("hinglish_latin", "REFLECTIVE_LISTENING", "low")
    check("HINGLISH LATIN SCRIPT" in hinglish_inst, "Hinglish instruction specifies Latin script")
    check("BANNED ROBOTIC" in hinglish_inst, "Hinglish instruction bans robotic counselor translations")
    check("Mujhe sunayi de raha hai ki" in hinglish_inst, "Bans literal 'I hear you' translation")
    check("college friend" in hinglish_inst.lower(), "Specifies college friend / peer persona")
    check("Pronoun & Register Consistency" in hinglish_inst, "Hinglish instruction specifies pronoun consistency")
    check("tum" in hinglish_inst and "aap" in hinglish_inst, "Hinglish instruction guides tum vs aap usage")
    check("UNCONDITIONAL RULE: NEVER use formal Romanized pronouns" in hinglish_inst, "Hinglish instruction unconditionally forbids formal Romanized aap forms")
    check("tum" in hinglish_inst and "tumhein" in hinglish_inst and "tujhe" in hinglish_inst and "tera" in hinglish_inst and "teri" in hinglish_inst, "Hinglish instruction guides informal peer pronouns")
    check("Do NOT force unnatural pronouns into every sentence" in hinglish_inst, "Hinglish instruction warns against mechanically forcing unnatural pronouns")
    check("main/mujhe" in hinglish_inst, "Hinglish instruction guides singular main/mujhe usage")
    check("Ask at most ONE follow-up question" in hinglish_inst, "Hinglish instruction limits to one follow-up question")
    check("Never ask two separate questions in the same response" in hinglish_inst, "Hinglish bans double questions")

    english_inst = get_language_and_register_instruction("english", "REFLECTIVE_LISTENING", "low")
    check("UNCONDITIONAL RULE: NEVER use formal Romanized pronouns" not in english_inst, "English instruction does not contain Romanized Hinglish constraints")
    check("I hear how you're feeling" in english_inst, "English instruction explicitly bans 'I hear how you're feeling'")
    check("It's completely normal for students to feel" in english_inst, "English instruction bans 'It's completely normal for students to feel'")
    check("What has been on your mind lately" in english_inst, "English instruction bans 'What has been on your mind lately'")
    check("college friend" in english_inst.lower(), "English instruction specifies peer companion tone")
    check("Ask at most ONE follow-up question" in english_inst, "English instruction limits to one follow-up question")
    check("Never ask two separate questions in the same response" in english_inst, "English bans double questions")

    hindi_inst = get_language_and_register_instruction("hindi_devanagari", "REFLECTIVE_LISTENING", "low")
    check("UNCONDITIONAL RULE: NEVER use formal Romanized pronouns" not in hindi_inst, "Hindi Devanagari instruction does not contain Romanized Hinglish constraints")
    check("DEVANAGARI SCRIPT" in hindi_inst, "Hindi instruction specifies Devanagari script")
    check("यह महसूस करना बिल्कुल सामान्य है" in hindi_inst, "Hindi instruction bans clinical formulas")
    check("Ask at most ONE follow-up question" in hindi_inst, "Hindi instruction limits to one follow-up question")

    # --- 3. SAFETY PRIORITY OVERRIDE ---
    print("\n3. Safety Priority Enforcement:")
    crisis_inst = get_language_and_register_instruction("hinglish_latin", "CRISIS", "high")
    check("CRITICAL SAFETY DIRECTIVE" in crisis_inst, "Safety override triggered for high-risk crisis")
    check("DO NOT use casual slang" in crisis_inst, "Casual slang strictly banned during crisis")
    check("DO NOT use" in crisis_inst and "playful" in crisis_inst, "Playful tone banned during crisis")

    # --- 4. STEP 2: SARCASM, HUMOUR & INTENT GATING TESTS ---
    print("\n4. Sarcasm / Humour Intent Detection & Gating:")

    # Case 1: Humorous laptop complaint
    case1_msg = "Bhai mera laptop mujhe dekh ke hi hang ho jata hai."
    case1_intent = infer_intent_heuristic(case1_msg, 4, "academic")
    check(case1_intent == "humorous_complaint", f"Case 1 intent: '{case1_msg}' -> {case1_intent} (expected humorous_complaint)")
    c1_allowed, c1_reason = is_humour_allowed(
        {"conversational_intent": case1_intent, "intensity": 4, "context": "academic", "humour_confidence": "high"},
        risk_level="low", strategy="REFLECTIVE_LISTENING"
    )
    check(c1_allowed is True, f"Case 1 humour gate allowed: {c1_allowed} ({c1_reason})")

    # Case 2: Sarcastic Instagram complaint
    case2_msg = "Instagram meri padhai ka sabse loyal partner hai 😂"
    case2_intent = infer_intent_heuristic(case2_msg, 4, "academic")
    check(case2_intent == "humorous_complaint", f"Case 2 intent: '{case2_msg}' -> {case2_intent} (expected humorous_complaint)")
    c2_allowed, c2_reason = is_humour_allowed(
        {"conversational_intent": case2_intent, "intensity": 4, "context": "academic", "humour_confidence": "high"},
        risk_level="low", strategy="REFLECTIVE_LISTENING"
    )
    check(c2_allowed is True, f"Case 2 humour gate allowed: {c2_allowed}")

    # Case 3: Syllabus personification
    case3_msg = "Kal exam hai aur syllabus mujhe dekh ke has raha hai."
    case3_intent = infer_intent_heuristic(case3_msg, 5, "academic")
    check(case3_intent == "humorous_complaint", f"Case 3 intent: '{case3_msg}' -> {case3_intent} (expected humorous_complaint)")
    c3_allowed, c3_reason = is_humour_allowed(
        {"conversational_intent": case3_intent, "intensity": 5, "context": "academic", "humour_confidence": "high"},
        risk_level="low", strategy="REFLECTIVE_LISTENING"
    )
    check(c3_allowed is True, f"Case 3 humour gate allowed: {c3_allowed}")

    # Case 4: Genuine Instagram-related distress
    case4_msg = "Instagram ki wajah se main padh nahi paa raha aur bahut stress ho raha hai."
    case4_intent = infer_intent_heuristic(case4_msg, 7, "academic")
    check(case4_intent == "genuine_distress", f"Case 4 intent: '{case4_msg}' -> {case4_intent} (expected genuine_distress)")
    c4_allowed, c4_reason = is_humour_allowed(
        {"conversational_intent": case4_intent, "intensity": 7, "context": "academic", "humour_confidence": "low"},
        risk_level="low", strategy="PROBLEM_SOLVING"
    )
    check(c4_allowed is False, f"Case 4 humour gate blocked (genuine distress): {c4_allowed} ({c4_reason})")

    # Case 5: Genuine exam anxiety
    case5_msg = "Exam kal hai aur mujhe bahut anxiety ho rahi hai."
    case5_intent = infer_intent_heuristic(case5_msg, 8, "academic")
    check(case5_intent == "genuine_distress", f"Case 5 intent: '{case5_msg}' -> {case5_intent} (expected genuine_distress)")
    c5_allowed, c5_reason = is_humour_allowed(
        {"conversational_intent": case5_intent, "intensity": 8, "context": "academic", "humour_confidence": "low"},
        risk_level="low", strategy="COPING_SUPPORT"
    )
    check(c5_allowed is False, f"Case 5 humour gate blocked (anxiety/high intensity): {c5_allowed}")

    # Case 6: Self-esteem vulnerability
    case6_msg = "Sab log aage nikal rahe hain aur main wahi ka wahi hoon."
    case6_intent = infer_intent_heuristic(case6_msg, 7, "self_esteem")
    check(case6_intent == "genuine_distress", f"Case 6 intent: '{case6_msg}' -> {case6_intent} (expected genuine_distress)")
    c6_allowed, c6_reason = is_humour_allowed(
        {"conversational_intent": case6_intent, "intensity": 7, "context": "self_esteem", "emotion": "sadness"},
        risk_level="low", strategy="REFLECTIVE_LISTENING"
    )
    check(c6_allowed is False, f"Case 6 humour gate blocked (self-esteem vulnerability): {c6_allowed}")

    # Case 7: Social withdrawal
    case7_msg = "Hostel mein sabke apne groups hain, main bas room mein pada rehta hoon."
    case7_intent = infer_intent_heuristic(case7_msg, 7, "social")
    check(case7_intent == "genuine_distress", f"Case 7 intent: '{case7_msg}' -> {case7_intent} (expected genuine_distress)")
    c7_allowed, c7_reason = is_humour_allowed(
        {"conversational_intent": case7_intent, "intensity": 7, "context": "social", "emotion": "loneliness"},
        risk_level="low", strategy="REFLECTIVE_LISTENING"
    )
    check(c7_allowed is False, f"Case 7 humour gate blocked (social withdrawal): {c7_allowed}")

    # Case 8: Explicit crisis
    case8_msg = "I don't want to live anymore."
    c8_allowed, c8_reason = is_humour_allowed(
        {"conversational_intent": "humorous_complaint", "intensity": 10},  # Even if mistakenly classified as humorous
        risk_level="high", strategy="CRISIS"
    )
    check(c8_allowed is False, f"Case 8 humour gate blocked on high-risk CRISIS: {c8_allowed} ({c8_reason})")

    # --- 5. CONFIDENCE & SAFETY BOUNDARY VALIDATION ---
    print("\n5. Confidence, Factual & Instruction Integrity:")
    # Low confidence in humour -> Humour OFF
    low_conf_allowed, low_conf_reason = is_humour_allowed(
        {"conversational_intent": "humorous_complaint", "intensity": 4, "context": "academic", "humour_confidence": "low"},
        risk_level="low", strategy="REFLECTIVE_LISTENING"
    )
    check(low_conf_allowed is False, f"Low humour confidence blocks humour: {low_conf_allowed} ({low_conf_reason})")

    # Informational strategy -> Humour OFF
    info_allowed, info_reason = is_humour_allowed(
        {"conversational_intent": "humorous_complaint", "intensity": 3, "context": "general", "humour_confidence": "high"},
        risk_level="low", strategy="INFORMATIONAL"
    )
    check(info_allowed is False, f"Informational strategy blocks humour: {info_allowed} ({info_reason})")

    # Humour active prompt directives
    h_prompt = get_humour_instruction(is_allowed=True, language="hinglish_latin")
    check("HUMOROUS COMPLAINT" in h_prompt, "Humour instruction specifies humorous complaint")
    check("NEVER mock the student" in h_prompt, "Humour instruction strictly bans mocking")
    check("without jumping prematurely into advice" in h_prompt, "Humour instruction prevents premature advice")
    check("at most ONE" in h_prompt, "Humour instruction enforces single question limit")

    # Humour off prompt directive
    h_off_prompt = get_humour_instruction(is_allowed=False)
    check("HUMOUR GATING: OFF" in h_off_prompt, "Humour off instruction specifies humour off")
    check("Do NOT use sarcasm" in h_off_prompt, "Humour off instruction bans sarcasm")

    # --- 6. STEP 3: ADVICE GATING / LISTEN-FIRST BEHAVIOR TESTS ---
    print("\n6. Step 3: Advice Gating / Listen-First Behavior (10 Required Cases):")

    # Case 1: Venting / Emotional Expression
    # "Yaar aaj bilkul mann nahi kar raha padhne ka." -> listen_first, advice_allowed=False
    c1_msg = "Yaar aaj bilkul mann nahi kar raha padhne ka."
    c1_state = {"emotion": "motivation_loss", "intensity": 5, "context": "academic", "underlying_need": "venting", "confidence": "high"}
    c1_mode, c1_allowed, c1_reason = determine_advice_mode(c1_msg, c1_state, risk_level="low", strategy="REFLECTIVE_LISTENING")
    check(c1_mode == "listen_first" and c1_allowed is False, f"Case 1 (Venting): '{c1_msg}' -> mode={c1_mode}, allowed={c1_allowed}")

    # Case 2: Emotional Vulnerability
    # "Sab log mujhse better kar rahe hain." -> listen_first, advice_allowed=False
    c2_msg = "Sab log mujhse better kar rahe hain."
    c2_state = {"emotion": "sadness", "intensity": 6, "context": "self_esteem", "underlying_need": "reassurance", "confidence": "high"}
    c2_mode, c2_allowed, c2_reason = determine_advice_mode(c2_msg, c2_state, risk_level="low", strategy="REFLECTIVE_LISTENING")
    check(c2_mode == "listen_first" and c2_allowed is False, f"Case 2 (Vulnerability): '{c2_msg}' -> mode={c2_mode}, allowed={c2_allowed}")

    # Case 3: Ambiguous / Minimal
    # "Pata nahi yaar." -> clarify_first, advice_allowed=False
    c3_msg = "Pata nahi yaar."
    c3_state = {"emotion": "neutral", "intensity": 3, "context": "general", "underlying_need": "casual_chat", "confidence": "low"}
    c3_mode, c3_allowed, c3_reason = determine_advice_mode(c3_msg, c3_state, risk_level="low", strategy="REFLECTIVE_LISTENING")
    check(c3_mode == "clarify_first" and c3_allowed is False, f"Case 3 (Ambiguous): '{c3_msg}' -> mode={c3_mode}, allowed={c3_allowed}")

    # Case 4: Explicit Advice Request
    # "Main procrastinate kar raha hoon, mujhe kya karna chahiye?" -> explicit_advice, advice_allowed=True
    c4_msg = "Main procrastinate kar raha hoon, mujhe kya karna chahiye?"
    check(has_explicit_advice_request(c4_msg) is True, f"Case 4 explicit advice detected: '{c4_msg}'")
    c4_state = {"emotion": "anxiety", "intensity": 6, "context": "academic", "underlying_need": "problem_solving", "confidence": "high"}
    c4_mode, c4_allowed, c4_reason = determine_advice_mode(c4_msg, c4_state, risk_level="low", strategy="PROBLEM_SOLVING")
    check(c4_mode == "explicit_advice" and c4_allowed is True, f"Case 4 (Explicit Advice): '{c4_msg}' -> mode={c4_mode}, allowed={c4_allowed}")

    # Case 5: Clear Practical Problem
    # "Mere 4 assignments kal submit hain, kahan se start karu?" -> problem_solve, advice_allowed=True
    c5_msg = "Mere 4 assignments kal submit hain, kahan se start karu?"
    c5_state = {"emotion": "anxiety", "intensity": 7, "context": "academic", "underlying_need": "problem_solving", "confidence": "high"}
    c5_mode, c5_allowed, c5_reason = determine_advice_mode(c5_msg, c5_state, risk_level="low", strategy="PROBLEM_SOLVING")
    check(c5_mode == "problem_solve" and c5_allowed is True, f"Case 5 (Practical Problem): '{c5_msg}' -> mode={c5_mode}, allowed={c5_allowed}")

    # Case 6: Humorous Complaint (Preserves Humour Gate, advice suppressed)
    # "Instagram meri padhai ka sabse loyal partner hai 😂" -> listen_first, advice_allowed=False, humour_allowed=True
    c6_msg = "Instagram meri padhai ka sabse loyal partner hai 😂"
    c6_state = {"conversational_intent": "humorous_complaint", "intensity": 4, "context": "academic", "humour_confidence": "high", "underlying_need": "venting"}
    c6_h_allowed, _ = is_humour_allowed(c6_state, risk_level="low", strategy="REFLECTIVE_LISTENING")
    c6_mode, c6_allowed, c6_reason = determine_advice_mode(c6_msg, c6_state, risk_level="low", strategy="REFLECTIVE_LISTENING")
    check(c6_mode == "listen_first" and c6_allowed is False and c6_h_allowed is True, f"Case 6 (Humour Complaint): mode={c6_mode}, advice_allowed={c6_allowed}, humour_allowed={c6_h_allowed}")

    # Case 7: Crisis (Absolute override: crisis_support, advice_allowed=False, humour_allowed=False)
    # "I don't want to live anymore." -> crisis_support, advice_allowed=False
    c7_msg = "I don't want to live anymore."
    c7_state = {"emotion": "sadness", "intensity": 10, "context": "general", "underlying_need": "grounding", "conversational_intent": "genuine_distress"}
    c7_h_allowed, _ = is_humour_allowed(c7_state, risk_level="high", strategy="CRISIS")
    c7_mode, c7_allowed, c7_reason = determine_advice_mode(c7_msg, c7_state, risk_level="high", strategy="CRISIS")
    check(c7_mode == "crisis_support" and c7_allowed is False and c7_h_allowed is False, f"Case 7 (Crisis Override): mode={c7_mode}, advice_allowed={c7_allowed}, humour_allowed={c7_h_allowed}")

    # Case 8: General Emotional Venting
    # "Aaj bahut exhausting day tha." -> listen_first, advice_allowed=False
    c8_msg = "Aaj bahut exhausting day tha."
    c8_state = {"emotion": "frustration", "intensity": 5, "context": "general", "underlying_need": "venting", "confidence": "high"}
    c8_mode, c8_allowed, c8_reason = determine_advice_mode(c8_msg, c8_state, risk_level="low", strategy="REFLECTIVE_LISTENING")
    check(c8_mode == "listen_first" and c8_allowed is False, f"Case 8 (Exhausting Day): '{c8_msg}' -> mode={c8_mode}, allowed={c8_allowed}")

    # Case 9: Direct Advice Request (Isolated)
    # "Mujhe kya karna chahiye?" -> explicit_advice, advice_allowed=True
    c9_msg = "Mujhe kya karna chahiye?"
    check(has_explicit_advice_request(c9_msg) is True, f"Case 9 explicit advice detected: '{c9_msg}'")
    c9_state = {"emotion": "anxiety", "intensity": 5, "context": "general", "underlying_need": "problem_solving", "confidence": "medium"}
    c9_mode, c9_allowed, c9_reason = determine_advice_mode(c9_msg, c9_state, risk_level="low", strategy="GUIDANCE")
    check(c9_mode == "explicit_advice" and c9_allowed is True, f"Case 9 (Direct Advice Query): '{c9_msg}' -> mode={c9_mode}, allowed={c9_allowed}")

    # Case 10: Clear Factual / Institutional Query (DSR office)
    # "Where is the DSR office?" -> informational, advice_allowed=False
    c10_msg = "Where is the DSR office?"
    c10_state = {"emotion": "neutral", "intensity": 2, "context": "general", "underlying_need": "casual_chat", "confidence": "high"}
    c10_mode, c10_allowed, c10_reason = determine_advice_mode(c10_msg, c10_state, risk_level="low", strategy="INFORMATIONAL")
    check(c10_mode == "informational" and c10_allowed is False, f"Case 10 (DSR Office Query): '{c10_msg}' -> mode={c10_mode}, allowed={c10_allowed}")

    # Case 10b: Another Factual Institutional Query (Counselling timings)
    # "What are the counselling centre timings?" -> informational, advice_allowed=False
    c10b_msg = "What are the counselling centre timings?"
    c10b_state = {"emotion": "neutral", "intensity": 2, "context": "general", "underlying_need": "casual_chat", "confidence": "high"}
    c10b_mode, c10b_allowed, c10b_reason = determine_advice_mode(c10b_msg, c10b_state, risk_level="low", strategy="INFORMATIONAL")
    check(c10b_mode == "informational" and c10b_allowed is False, f"Case 10b (Counselling Timings Query): '{c10b_msg}' -> mode={c10b_mode}, allowed={c10b_allowed}")

    # Priority Ordering & Prompt Directives Checks
    print("\n7. Priority Ordering & Directive Validation:")
    # Priority: Crisis overrides explicit advice
    crisis_adv_mode, crisis_adv_allowed, _ = determine_advice_mode(
        "Mujhe kya karna chahiye? I want to kill myself.",
        {"emotion": "sadness", "intensity": 10},
        risk_level="high",
        strategy="CRISIS"
    )
    check(crisis_adv_mode == "crisis_support" and crisis_adv_allowed is False, "Priority: Crisis strictly overrides explicit advice")

    # Priority: Informational strategy overrides explicit advice
    info_adv_mode, info_adv_allowed, _ = determine_advice_mode(
        "Where is the DSR office? kya karu?",
        {"confidence": "high"},
        risk_level="low",
        strategy="INFORMATIONAL"
    )
    check(info_adv_mode == "informational" and info_adv_allowed is False, "Priority: Informational strategy overrides advice request")

    # Priority: Explicit advice overrides practical ambiguity
    ambig_adv_mode, ambig_adv_allowed, _ = determine_advice_mode(
        "kya karu?",
        {"confidence": "low", "confidence_level": "low"},
        risk_level="low",
        strategy="REFLECTIVE_LISTENING"
    )
    check(ambig_adv_mode == "explicit_advice" and ambig_adv_allowed is True, "Priority: Explicit advice query overrides low confidence")

    # Prompt Directives validation
    p_listen = get_advice_instruction("listen_first", "hinglish_latin")
    check("LISTEN FIRST" in p_listen and "DO NOT give unsolicited advice" in p_listen, "Listen first instruction prohibits unsolicited advice")
    check("Try meditating, journaling" in p_listen, "Explicitly warns against generic habit dumping")

    p_clarify = get_advice_instruction("clarify_first", "hinglish_latin")
    check("CLARIFY FIRST" in p_clarify and "DO NOT assume" in p_clarify, "Clarify first instruction prohibits assumptions")

    p_problem = get_advice_instruction("problem_solve", "hinglish_latin")
    check("PROBLEM SOLVING" in p_problem and "smallest manageable first step" in p_problem, "Problem solve instruction focuses on small first step")

    p_explicit = get_advice_instruction("explicit_advice", "hinglish_latin")
    check("EXPLICIT ADVICE" in p_explicit and "1-2 focused" in p_explicit, "Explicit advice instruction requires focused concise steps")

    p_crisis = get_advice_instruction("crisis_support", "hinglish_latin")
    check("CRISIS SUPPORT" in p_crisis and "strictly suppressed" in p_crisis, "Crisis support instruction strictly suppresses productivity advice")

    p_info = get_advice_instruction("informational", "english")
    check("INFORMATIONAL" in p_info and "DO NOT provide unsolicited life advice" in p_info, "Informational instruction prohibits unsolicited advice")
    check("Answer directly, accurately, and concisely" in p_info, "Informational instruction enforces direct factual answer")

    # --- 8. STEP 4: MULTI-TURN CONTINUITY & CONVERSATIONAL DEPTH TESTS ---
    print("\n8. Step 4: Multi-Turn Continuity & Conversational Depth:")

    # 1. Emotional continuation
    hist_emo = [
        {"role": "user", "content": "Mujhe bahut akela feel ho raha hai hostel mein."},
        {"role": "assistant", "content": "Main sun raha hoon yaar. Kya hua?"}
    ]
    cont_emo, conf_emo, _ = determine_context_continuity("Kisi se baat karne ka mann nahi karta.", hist_emo)
    check(cont_emo == "continuation" and conf_emo == "high", "Case 1: Emotional continuation identified as continuation with high confidence")

    # 2. Academic continuation
    hist_acad = [
        {"role": "user", "content": "Kal mera maths ka exam hai aur syllabus complete nahi hua."},
        {"role": "assistant", "content": "Bohot pressure lag raha hoga."}
    ]
    cont_acad, conf_acad, _ = determine_context_continuity("Bohot dar lag raha hai fail hone ka.", hist_acad)
    check(cont_acad == "continuation" and conf_acad == "high", "Case 2: Academic continuation identified as continuation with high confidence")

    # 3. 'haan wahi'
    hist_ref1 = [
        {"role": "user", "content": "Exam ki tension hai."},
        {"role": "assistant", "content": "Kya syllabus ki chinta ho rahi hai?"}
    ]
    is_ref_hw = is_reference_phrase("haan wahi")
    cont_hw, conf_hw, res_hw = determine_context_continuity("haan wahi", hist_ref1)
    check(is_ref_hw is True and cont_hw == "continuation" and conf_hw == "high" and "syllabus" in res_hw,
          "Case 3: 'haan wahi' recognized as reference phrase and resolves to assistant context")

    # 4. 'exactly'
    hist_ref2 = [
        {"role": "user", "content": "Assignments are piling up."},
        {"role": "assistant", "content": "Does it feel like you don't even know where to begin?"}
    ]
    is_ref_ex = is_reference_phrase("exactly")
    cont_ex, conf_ex, res_ex = determine_context_continuity("exactly", hist_ref2)
    check(is_ref_ex is True and cont_ex == "continuation" and conf_ex == "high" and len(res_ex) > 0,
          "Case 4: 'exactly' recognized as reference phrase with resolved referent")

    # 5. 'uske baad'
    hist_ref3 = [
        {"role": "user", "content": "Maine project submit kiya tha."},
        {"role": "assistant", "content": "Phir kya response mila?"}
    ]
    is_ref_ub = is_reference_phrase("uske baad marks kat gaye")
    cont_ub, conf_ub, _ = determine_context_continuity("uske baad marks kat gaye", hist_ref3)
    check(is_ref_ub is True and cont_ub == "continuation", "Case 5: 'uske baad' matches reference pattern and continues context")

    # 6. 'ab kya karu?'
    hist_ref4 = [
        {"role": "user", "content": "Syllabus aadha bacha hai aur kal exam hai."},
        {"role": "assistant", "content": "Kafi tight timeline hai."}
    ]
    is_ref_ak = is_reference_phrase("ab kya karu?")
    cont_ak, conf_ak, _ = determine_context_continuity("ab kya karu?", hist_ref4)
    adv_mode_ak, adv_allowed_ak, _ = determine_advice_mode("ab kya karu?", {"context": "academic", "confidence": "high"})
    check(is_ref_ak is True and cont_ak == "continuation" and adv_mode_ak == "explicit_advice" and adv_allowed_ak is True,
          "Case 6: 'ab kya karu?' treated as continuation and explicit advice request")

    # 7. Ambiguous short reply
    hist_amb = [
        {"role": "user", "content": "College life feels strange."},
        {"role": "assistant", "content": "How so?"}
    ]
    cont_amb, conf_amb, _ = determine_context_continuity("pata nahi", hist_amb)
    adv_mode_amb, adv_allowed_amb, _ = determine_advice_mode("pata nahi", {"confidence": "low", "confidence_level": "low"})
    check(cont_amb == "continuation" and adv_mode_amb == "clarify_first" and adv_allowed_amb is False,
          "Case 7: Ambiguous short reply 'pata nahi' triggers clarify_first without advice")

    # 8. Academic -> hostel topic shift
    hist_shift = [
        {"role": "user", "content": "Kal physics ka mid-term exam hai."},
        {"role": "assistant", "content": "Revision kitna hua?"}
    ]
    msg_shift = "Waise hostel ka WiFi phir band ho gaya."
    has_m_shift, _ = has_topic_shift_marker(msg_shift)
    is_shift_h = detect_topic_shift_heuristic(msg_shift, hist_shift)
    cont_shift, conf_shift, _ = determine_context_continuity(msg_shift, hist_shift)
    check(has_m_shift is True and is_shift_h is True and cont_shift == "topic_shift",
          "Case 8: Academic to hostel WiFi cleanly detected as topic_shift")

    # 9. Emotional -> informational shift
    hist_info = [
        {"role": "user", "content": "I am feeling super stressed about college life."},
        {"role": "assistant", "content": "I hear you, take it easy."}
    ]
    msg_info = "Where is the DSR office?"
    strat_info = select_response_strategy({"emotion": "neutral"}, msg_info, {"risk_level": "low"}, grounding_found=True)
    adv_mode_info, adv_allowed_info, _ = determine_advice_mode(msg_info, {"confidence": "high"}, risk_level="low", strategy=strat_info)
    check(strat_info == "INFORMATIONAL" and adv_mode_info == "informational" and adv_allowed_info is False,
          "Case 9: Emotional to informational query cleanly switches strategy to INFORMATIONAL without emotional carryover")

    # 10. Crisis after normal conversation
    hist_crisis = [
        {"role": "user", "content": "Kal mera exam hai."},
        {"role": "assistant", "content": "All the best!"}
    ]
    msg_crisis = "I want to end my life."
    risk_crisis = assess_risk(msg_crisis)
    strat_crisis = select_response_strategy({"emotion": "sadness", "intensity": 10}, msg_crisis, risk_crisis, grounding_found=False)
    adv_mode_crisis, adv_allowed_crisis, _ = determine_advice_mode(msg_crisis, {}, risk_level=risk_crisis["risk_level"], strategy=strat_crisis)
    hum_allowed_crisis, _ = is_humour_allowed({"emotion": "sadness", "intensity": 10}, risk_level=risk_crisis["risk_level"], strategy=strat_crisis)
    check(risk_crisis["risk_level"] == "high" and strat_crisis == "CRISIS" and adv_mode_crisis == "crisis_support" and hum_allowed_crisis is False,
          "Case 10: Crisis strictly overrides previous normal context (CRISIS strategy, no humour, crisis advice mode)")

    # 11. Humour after stress
    hist_hum = [
        {"role": "user", "content": "Kal exam hai bahut tension hai."},
        {"role": "assistant", "content": "Syllabus kitna bacha hai?"}
    ]
    msg_hum = "Instagram meri padhai ka sabse loyal partner hai 😂"
    intent_hum = infer_intent_heuristic(msg_hum, 4, "academic")
    hum_allowed_hum, _ = is_humour_allowed({"conversational_intent": intent_hum, "intensity": 4}, risk_level="low", strategy="REFLECTIVE_LISTENING")
    check(intent_hum == "humorous_complaint" and hum_allowed_hum is True,
          "Case 11: Humorous complaint after stress cleanly recognized and permitted by humour gate")

    # 12. No-context conversation
    cont_none, conf_none, ref_none = determine_context_continuity("Hello, mujhe stress ho raha hai.", [])
    check(cont_none == "isolated" and ref_none == "", "Case 12: Empty conversation history yields isolated continuity")

    # 13. No hallucinated context in continuity prompt directives
    p_cont_high = get_continuity_instruction("continuation", "high", "hinglish_latin", "exam syllabus")
    p_cont_shift = get_continuity_instruction("topic_shift", "high", "hinglish_latin")
    check("NEVER invent names of friends" in p_cont_high and "Do NOT assume or manufacture facts" in p_cont_high,
          "Case 13: Anti-hallucination directive strictly included in prompt instructions")

    # 14. One-question maximum
    check("at most ONE natural, gentle follow-up question" in p_cont_high,
          "Case 14: One-question maximum strictly enforced in continuity instruction")

    # 15. 'Waise' used without topic shift
    hist_same = [
        {"role": "user", "content": "Exam kal subah hai."},
        {"role": "assistant", "content": "Haan, subah ke slot mein hai."}
    ]
    msg_same = "Waise exam kal subah 9 baje hai."
    has_m_same, _ = has_topic_shift_marker(msg_same)
    is_shift_same = detect_topic_shift_heuristic(msg_same, hist_same)
    cont_same, conf_same, _ = determine_context_continuity(msg_same, hist_same)
    check(has_m_same is True and is_shift_same is False and cont_same == "continuation",
          "Case 15: 'Waise' used within same domain remains continuation (marker alone != topic shift)")

    # 16. Multiple possible referents -> low confidence
    hist_multi = [
        {"role": "user", "content": "Kal exam hai."},
        {"role": "assistant", "content": "Padhai kaisi chal rahi hai?"},
        {"role": "user", "content": "Hostel mein paani nahi aa raha."},
        {"role": "assistant", "content": "Warden ko bola?"}
    ]
    msg_multi = "woh issue hai"
    cont_multi, conf_multi, _ = determine_context_continuity(msg_multi, hist_multi)
    p_low = get_continuity_instruction("continuation", "low", "hinglish_latin")
    check(conf_multi == "low" and "LOW CONTEXT CONFIDENCE" in p_low and "Clarify gently" in p_low,
          "Case 16: History with multiple topics + ambiguous short phrase yields low confidence and clarification directive")

    # 17. Assistant wording must not pollute emotion classification
    check(is_reference_phrase("haan wahi") is True and is_reference_phrase("Kal physics ka exam hai") is False,
          "Case 17: Reference phrase detection is strictly isolated to anaphoric triggers")

    # 18. Topic shift directive cleanly instructs dropping previous anchor
    check("Cleanly drop the previous emotional and topical anchor" in p_cont_shift,
          "Case 18: Topic shift directive instructs dropping previous anchor cleanly")

    # --- STEP 5.6: SINGLE QUESTION CEILING HARDENING & NORMALIZATION ---
    # 19. Humour prompt directive contains single question hardening
    h_prompt = get_humour_instruction(True, "hinglish_latin")
    check("SINGLE-QUESTION CEILING HARDENING" in h_prompt and "Maximum ONE question" in h_prompt and "tag questions" in h_prompt,
          "Case 19: Humour prompt contains explicit single-question ceiling and tag-question ban")

    # 20. enforce_single_question_ceiling normalizes rhetorical tag questions
    sample_tag_mult = "Haan yaar, syllabus ka alag hi mazaak chal raha hai, na? Abhi kaun sa chapter baaki hai?"
    norm_tag = enforce_single_question_ceiling(sample_tag_mult)
    check(norm_tag.count("?") == 1 and ", na." in norm_tag and norm_tag.endswith("baaki hai?"),
          "Case 20: enforce_single_question_ceiling normalizes ', na?' into declarative tag before genuine follow-up question")

    # 21. enforce_single_question_ceiling handles 'right?' tag question
    sample_right_mult = "College life can be completely exhausting, right? What are you focusing on first?"
    norm_right = enforce_single_question_ceiling(sample_right_mult)
    check(norm_right.count("?") == 1 and ", right." in norm_right and norm_right.endswith("first?"),
          "Case 21: enforce_single_question_ceiling normalizes ', right?' into statement when followed by real question")

    # 22. enforce_single_question_ceiling preserves single genuine question
    sample_single = "Haan yaar, kaafi heavy lag raha hai. Abhi sabse zyada tension kis cheez ki hai?"
    check(enforce_single_question_ceiling(sample_single) == sample_single,
          "Case 22: enforce_single_question_ceiling leaves valid single-question response untouched")

    # --- STEP 6.1: PHASE 4E STEP 2 REGRESSION TESTS ---
    print("\n9. Phase 4E Step 2 Regression Tests (Register, Panic Advice Gating, Prompt Guidance):")

    # 23. Panic Cue with Academic Context & Problem-Solving Classification -> listen_first, advice_allowed=False
    # Case ACAD_01 simulation
    acad_msg = "Aadha syllabus bacha hai aur dimaag blank ho raha hai."
    acad_state = {"emotion": "anxiety", "intensity": 8, "context": "academic", "underlying_need": "problem_solving", "confidence": "high"}
    acad_mode, acad_allowed, acad_reason = determine_advice_mode(acad_msg, acad_state, risk_level="low", strategy="PROBLEM_SOLVING")
    check(acad_mode == "listen_first" and acad_allowed is False and "ACUTE_PANIC_FREEZE" in acad_reason,
          "Case 23: 'dimaag blank' with academic workload overrides problem_solving to listen_first (False)")

    # 24. Somatic Panic Cue ('haath kaanp') with strict examiner concern -> listen_first, advice_allowed=False
    # Case DEPTH_01 simulation
    somatic_msg = "Haan, aur upar se external examiner bohot strict aane wala hai, sunke hi haath kaanp rahe hain."
    somatic_state = {"emotion": "anxiety", "intensity": 8, "context": "academic", "underlying_need": "problem_solving", "confidence": "high"}
    somatic_mode, somatic_allowed, somatic_reason = determine_advice_mode(somatic_msg, somatic_state, risk_level="low", strategy="PROBLEM_SOLVING")
    check(somatic_mode == "listen_first" and somatic_allowed is False and "ACUTE_PANIC_FREEZE" in somatic_reason,
          "Case 24: 'haath kaanp rahe' somatic panic overrides problem_solving to listen_first (False)")

    # 25. English Cognitive Freeze ('brain freezes') -> listen_first, advice_allowed=False
    eng_freeze_msg = "I keep looking at my task list and my brain just freezes."
    eng_freeze_state = {"emotion": "anxiety", "intensity": 7, "context": "academic", "underlying_need": "problem_solving", "confidence": "high"}
    eng_freeze_mode, eng_freeze_allowed, eng_freeze_reason = determine_advice_mode(eng_freeze_msg, eng_freeze_state, risk_level="low", strategy="PROBLEM_SOLVING")
    check(eng_freeze_mode == "listen_first" and eng_freeze_allowed is False and "ACUTE_PANIC_FREEZE" in eng_freeze_reason,
          "Case 25: 'brain freezes' cognitive freeze overrides problem_solving to listen_first (False)")

    # 26. Somatic Panic Cue ('blank ho gaya') -> listen_first, advice_allowed=False
    blank_msg = "Phir wohi hua. Paper dekhte hi blank ho gaya sab."
    blank_state = {"emotion": "anxiety", "intensity": 8, "context": "academic", "underlying_need": "problem_solving", "confidence": "high"}
    blank_mode, blank_allowed, blank_reason = determine_advice_mode(blank_msg, blank_state, risk_level="low", strategy="PROBLEM_SOLVING")
    check(blank_mode == "listen_first" and blank_allowed is False and "ACUTE_PANIC_FREEZE" in blank_reason,
          "Case 26: 'blank ho gaya' cognitive freeze overrides problem_solving to listen_first (False)")

    # 27. Explicit Advice Request with Panic Cue -> explicit_advice, advice_allowed=True (Legitimate advice not blocked)
    explicit_panic_msg = "Dimaag blank ho raha hai, mujhe kya karna chahiye?"
    explicit_panic_state = {"emotion": "anxiety", "intensity": 8, "context": "academic", "underlying_need": "problem_solving", "confidence": "high"}
    exp_p_mode, exp_p_allowed, exp_p_reason = determine_advice_mode(explicit_panic_msg, explicit_panic_state, risk_level="low", strategy="PROBLEM_SOLVING")
    check(exp_p_mode == "explicit_advice" and exp_p_allowed is True,
          "Case 27: Explicit advice request ('kya karna chahiye') preserves explicit_advice (True) even with 'dimaag blank'")

    # 28. Explicit Concrete Plan Request with Freeze Cue -> explicit_advice, advice_allowed=True
    plan_freeze_msg = "My mind went blank, please give me a plan to prepare."
    plan_freeze_state = {"emotion": "anxiety", "intensity": 8, "context": "academic", "underlying_need": "problem_solving", "confidence": "high"}
    plan_mode, plan_allowed, plan_reason = determine_advice_mode(plan_freeze_msg, plan_freeze_state, risk_level="low", strategy="PROBLEM_SOLVING")
    check(plan_mode == "explicit_advice" and plan_allowed is True,
          "Case 28: Explicit plan request ('give me a plan') preserves explicit_advice (True) even with 'mind blank'")

    # 29. Non-Panic Academic Workload (No panic cue) -> problem_solve, advice_allowed=True (Preserves practical advice)
    normal_acad_msg = "Mere 4 assignments kal submit hain, kahan se start karu?"
    normal_acad_state = {"emotion": "anxiety", "intensity": 7, "context": "academic", "underlying_need": "problem_solving", "confidence": "high"}
    norm_mode, norm_allowed, norm_reason = determine_advice_mode(normal_acad_msg, normal_acad_state, risk_level="low", strategy="PROBLEM_SOLVING")
    check(norm_mode == "problem_solve" and norm_allowed is True,
          "Case 29: Normal academic task question without panic cue preserves problem_solve (True)")

    # 30. Administrative Non-Panic Word ('Attendance freeze ho gayi') -> problem_solve, advice_allowed=True
    admin_freeze_msg = "Attendance 74% pe freeze ho gayi hai, kal submit hona hai."
    admin_freeze_state = {"emotion": "anxiety", "intensity": 6, "context": "academic", "underlying_need": "problem_solving", "confidence": "high"}
    admin_mode, admin_allowed, admin_reason = determine_advice_mode(admin_freeze_msg, admin_freeze_state, risk_level="low", strategy="PROBLEM_SOLVING")
    check(admin_mode == "problem_solve" and admin_allowed is True,
          "Case 30: Administrative freeze without cognitive/somatic panic cue does not falsely trigger panic gate")

    # 31. Crisis Override with Panic Cue -> crisis_support, advice_allowed=False (Crisis strictly wins)
    crisis_panic_msg = "Mera dimaag blank ho raha hai, I want to end my life."
    crisis_panic_state = {"emotion": "sadness", "intensity": 10, "context": "general", "underlying_need": "grounding"}
    cr_mode, cr_allowed, cr_reason = determine_advice_mode(crisis_panic_msg, crisis_panic_state, risk_level="high", strategy="CRISIS")
    check(cr_mode == "crisis_support" and cr_allowed is False,
          "Case 31: Crisis override strictly takes precedence over panic/cognitive-freeze cues")

    # 32. Emotion Engine Prompt Guidance Content Check (Offline verification)
    from emotion_engine import CLASSIFICATION_PROMPT
    check("Panic & Cognitive Freeze Guidance:" in CLASSIFICATION_PROMPT,
          "Case 32a: CLASSIFICATION_PROMPT contains dedicated panic/cognitive freeze guidance header")
    check("is not by itself a request for practical problem-solving" in CLASSIFICATION_PROMPT,
          "Case 32b: CLASSIFICATION_PROMPT states panic language is not by itself problem-solving")
    check("experiencing cognitive freeze/panic" in CLASSIFICATION_PROMPT,
          "Case 32c: CLASSIFICATION_PROMPT rubric guides listen_first for cognitive freeze/panic")

    # --- STEP 6.2: PHASE 4E STEP 5 REGRESSION TESTS ---
    print("\n10. Phase 4E Step 5 Regression Tests (Idiom Venting, Examiner Substring, Formal Register Boundaries):")

    # 33. HING_01: Colloquial exhaustion idiom ('dimaag ka dahi') -> listen_first, advice_allowed=False
    hing_msg = "Bhai ekdum dimaag ka dahi ho chuka hai assignments se."
    hing_state = {"emotion": "frustration", "intensity": 8, "context": "academic", "underlying_need": "problem_solving", "confidence": "high"}
    hing_mode, hing_allowed, hing_reason = determine_advice_mode(hing_msg, hing_state, risk_level="low", strategy="VALIDATION")
    check(hing_mode == "listen_first" and hing_allowed is False and "COLLOQUIAL_VENTING_EXHAUSTION" in hing_reason,
          "Case 33a: HING_01 'dimaag ka dahi' with assignments triggers listen_first (False) under VALIDATION")

    hing_mode2, hing_allowed2, hing_reason2 = determine_advice_mode(hing_msg, hing_state, risk_level="low", strategy="PROBLEM_SOLVING")
    check(hing_mode2 == "listen_first" and hing_allowed2 is False and "COLLOQUIAL_VENTING_EXHAUSTION" in hing_reason2,
          "Case 33b: HING_01 'dimaag ka dahi' overrides even PROBLEM_SOLVING strategy to listen_first (False)")

    # 34. Other colloquial exhaustion idioms ('pak gaya', 'tang aa gaya') -> listen_first, advice_allowed=False
    pak_msg = "Assignments kar kar ke pak chuka hoon ab."
    pak_mode, pak_allowed, _ = determine_advice_mode(pak_msg, hing_state, risk_level="low", strategy="PROBLEM_SOLVING")
    check(pak_mode == "listen_first" and pak_allowed is False,
          "Case 34a: 'pak chuka hoon' triggers listen_first (False)")

    tang_msg = "Main is syllabus se tang aa gaya hoon bilkul."
    tang_mode, tang_allowed, _ = determine_advice_mode(tang_msg, hing_state, risk_level="low", strategy="PROBLEM_SOLVING")
    check(tang_mode == "listen_first" and tang_allowed is False,
          "Case 34b: 'tang aa gaya' triggers listen_first (False)")

    # 35. DEPTH_01: 'examiner' substring must NOT trigger 'exam' practical signal
    depth_msg = "Haan, aur upar se external examiner bohot strict aane wala hai."
    depth_state = {"emotion": "anxiety", "intensity": 8, "context": "academic", "underlying_need": "problem_solving", "confidence": "high"}
    depth_mode, depth_allowed, depth_reason = determine_advice_mode(depth_msg, depth_state, risk_level="low", strategy="REFLECTIVE_LISTENING")
    check(depth_mode == "listen_first" and depth_allowed is False,
          "Case 35: DEPTH_01 'external examiner' does not trigger 'exam' practical signal and returns listen_first (False)")

    # 36. Explicit advice request: 'Mujhe padhai me bilkul mann nahi lag raha, kya karu? Kuch concrete steps batao' -> explicit_advice, advice_allowed=True
    exp_adv_msg = "Mujhe padhai me bilkul mann nahi lag raha, kya karu? Kuch concrete steps batao."
    exp_adv_state = {"emotion": "motivation_loss", "intensity": 7, "context": "academic", "underlying_need": "problem_solving", "confidence": "high"}
    exp_adv_mode, exp_adv_allowed, _ = determine_advice_mode(exp_adv_msg, exp_adv_state, risk_level="low", strategy="PROBLEM_SOLVING")
    check(exp_adv_mode == "explicit_advice" and exp_adv_allowed is True,
          "Case 36: Explicit advice request ('kya karu? Kuch concrete steps batao') returns explicit_advice (True)")

    # 37. Idiom with explicit advice: Idiom + explicit request does NOT suppress advice
    idiom_adv_msg = "Bhai ekdum dimaag ka dahi ho chuka hai assignments se, kya karu? Kuch concrete steps batao."
    idiom_adv_mode, idiom_adv_allowed, _ = determine_advice_mode(idiom_adv_msg, hing_state, risk_level="low", strategy="PROBLEM_SOLVING")
    check(idiom_adv_mode == "explicit_advice" and idiom_adv_allowed is True,
          "Case 37: Idiom combined with explicit request ('kya karu? steps batao') preserves explicit_advice (True)")

    # 38. Formal register token boundaries: Test exact token matching and non-matching words
    import re
    formal_regex = re.compile(r"\b(?:aap|aapka|aapke|aapko|aapse)\b", re.IGNORECASE)

    # True positives (should match)
    formal_positive_samples = [
        "aap", "aapka", "aapke", "aapko", "aapse",
        "Aap", "AAP", "Aapko", "Aapke", "Aapka", "Aapse",
        "Kya aap sun rahe hain?", "Aapko ek step lena chahiye.", "Yeh aapke liye hai."
    ]
    all_pos_matched = all(bool(formal_regex.search(s)) for s in formal_positive_samples)
    check(all_pos_matched, "Case 38a: Formal register regex matches all valid forms of aap/aapka/aapke/aapko/aapse across casing")

    # True negatives (must NOT match unrelated words containing similar letter sequences)
    unrelated_samples = [
        "baap", "naap", "aapas", "aapsi", "milaap", "alaap", "chhaap", "paap",
        "Hum aapas mein baat kar rahe hain.", "Yeh mera baap hai.", "Kapda naap lo."
    ]
    no_false_positives = all(not bool(formal_regex.search(s)) for s in unrelated_samples)
    check(no_false_positives, "Case 38b: Formal register regex does NOT falsely match unrelated words ('aapas', 'baap', 'naap', 'milaap')")

    # 39. Register contrastive examples in prompt directives
    hinglish_prompt = get_language_and_register_instruction("hinglish_latin", "REFLECTIVE_LISTENING", "low")
    check("CONTRASTIVE REGISTER EXAMPLES" in hinglish_prompt,
          "Case 39a: Hinglish Latin instruction contains CONTRASTIVE REGISTER EXAMPLES header")
    check("Aapko chhota step lena chahiye" in hinglish_prompt and "Tumhein ek chhota step" in hinglish_prompt,
          "Case 39b: Instruction includes action-plan contrastive example (Aapko vs Tumhein)")
    check("Dekhiye, kya aap bata sakte hain" in hinglish_prompt and "Dekh, kya kuch aisa hai" in hinglish_prompt,
          "Case 39c: Instruction includes empathy closing question contrastive example (Dekhiye kya aap vs Dekh)")

    # 40. Advice directives include Hinglish register peer-pronoun reminders
    adv_listen_inst = get_advice_instruction("listen_first", "hinglish_latin")
    check("NEVER use formal 'aap/aapko/aapke/dekhiye'" in adv_listen_inst,
          "Case 40a: get_advice_instruction(listen_first) reinforces ban on formal aap/dekhiye")

    adv_expl_inst = get_advice_instruction("explicit_advice", "hinglish_latin")
    check("NEVER use formal honorifics 'aap/aapko/aapke'" in adv_expl_inst,
          "Case 40b: get_advice_instruction(explicit_advice) reinforces ban on formal aap in advice mode")

    adv_prob_inst = get_advice_instruction("problem_solve", "hinglish_latin")
    check("NEVER use formal honorifics 'aap/aapko/aapke'" in adv_prob_inst,
          "Case 40c: get_advice_instruction(problem_solve) reinforces ban on formal aap in problem-solving mode")

    # 41. Emotion engine prompt guidance for colloquial venting
    check("Colloquial Venting & Cognitive Exhaustion Guidance:" in CLASSIFICATION_PROMPT,
          "Case 41a: CLASSIFICATION_PROMPT contains Colloquial Venting & Cognitive Exhaustion Guidance")
    check("dimaag ka dahi" in CLASSIFICATION_PROMPT,
          "Case 41b: CLASSIFICATION_PROMPT mentions 'dimaag ka dahi' as emotional venting expression")

    # 42. Phase 4E Step 8: Hostel Loneliness & Social Isolation Contrastive Examples
    check("Hostel Loneliness & Social Isolation Reflections:" in hinglish_prompt,
          "Case 42a: Hinglish Latin instruction contains hostel loneliness contrastive section")
    check("Aapko lagta hai ki hostel mein sabke groups hain" in hinglish_prompt and "Aapke man mein koi connection nahi hai" in hinglish_prompt,
          "Case 42b: Hostel DON'T example contains intended formal register ('Aapko lagta hai...', 'Aapke man mein...')")
    check("Tumhein lagta hai hostel mein sabke groups hain" in hinglish_prompt and "Tere man mein lagta hai" in hinglish_prompt and "Tu chupchap aake" in hinglish_prompt,
          "Case 42c: Hostel DO example uses peer-style register ('Tumhein lagta hai...', 'Tere man mein...', 'Tu chupchap...')")
    check(all(x in hinglish_prompt for x in ["Aapko chhota step", "Tumhein ek chhota step", "Dekhiye, kya aap", "Dekh, kya kuch aisa"]),
          "Case 42d: Existing action-plan and closing question contrastive examples remain present")
    check(all(x in adv_listen_inst for x in ["LISTEN FIRST", "Hinglish Register: In your reflection"]),
          "Case 42e: Existing advice-mode instructions remain present and intact")

    print(f"\nResult: {passed}/{total} passed")
    return passed == total


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

