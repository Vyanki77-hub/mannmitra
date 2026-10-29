# emotion_engine.py
# Lightweight emotional state classification layer for MannMitra.
# Runs before the main conversational reply to adapt support strategy.

import os
import re
import json
from typing import Any

from dotenv import load_dotenv

from llm_provider import get_llm_provider
from personality import (
    infer_intent_heuristic,
    determine_advice_mode,
    is_reference_phrase,
    determine_context_continuity,
    has_explicit_advice_request,
    detect_domain,
)

# Initialize LLM provider
load_dotenv()
llm_provider = get_llm_provider()

# Reuse the same CASUAL_MESSAGES set from rag.py
CASUAL_MESSAGES = {
    "hi", "hii", "hiii", "hello", "hey", "heya", "yo",
    "how are you", "good morning", "good night", "good afternoon",
    "thanks", "thank you", "ok", "okay", "bye", "goodbye", "cool", "nice",
    "i'm bored", "im bored", "tell me something interesting",
}

# Enhanced Emotion Understanding v2 prompt with few-shot examples and rubric
CLASSIFICATION_PROMPT = """You are an emotion classifier for a student wellbeing companion.
Infer emotional context from semantic meaning, indirect language, behavioral cues, slang, and Hinglish. Output ONLY valid JSON, no markdown, no explanation.
Do NOT diagnose depression, anxiety disorders, or any clinical conditions.

If previous user statements are provided, use them only as background context to interpret ambiguous, short, indirect, or context-dependent expressions.
Classify the emotional state, intensity, context, underlying need, confidence, conversation mode, conversational intent, and advice mode of the CURRENT user message.
Do not classify the previous messages as if they are the current message.
Do not continue the conversation or answer the user.
Use previous context to resolve:
- ambiguous short messages
- pronouns/references
- emotional progression
- academic/social/relationship context
- indirect behavioral expressions
The latest user message remains the primary target.

Panic & Cognitive Freeze Guidance:
Panic, trembling, or cognitive-freeze language (e.g., 'dimaag blank', 'haath kaanp rahe hain', 'mind freezing') is not by itself a request for practical problem-solving. Treat these expressions as acute emotional distress/overwhelm; prefer emotional support or venting (conversation_mode: reflective_listening, underlying_need: venting or coping_tool, advice_mode: listen_first) unless the user explicitly asks for concrete steps or a plan.

Colloquial Venting & Cognitive Exhaustion Guidance:
Colloquial venting idioms expressing mental exhaustion or burnout (e.g., 'dimaag ka dahi', 'pak gaya', 'pak chuka', 'tang aa gaya') about assignments or exams are emotional venting expressions, NOT requests for practical problem-solving. Treat them as emotional distress/venting (conversation_mode: reflective_listening, underlying_need: venting, advice_mode: listen_first) unless the user explicitly asks for concrete steps, advice, or a plan.

Schema:
{
  "emotion": "anxiety|sadness|loneliness|anger|frustration|motivation_loss|neutral|positive",
  "intensity": 1-10,
  "context": "academic|social|family|self_esteem|general|casual",
  "underlying_need": "reassurance|problem_solving|venting|coping_tool|grounding|casual_chat",
  "confidence": "high|medium|low",
  "evidence": "Short quote or phrase identifying the behavioral cue",
  "conversation_mode": "reflective_listening|coping_tool|problem_solving|grounding_high_risk|casual",
  "conversational_intent": "humorous_complaint|genuine_distress|neutral_casual",
  "humour_confidence": "high|medium|low",
  "advice_mode": "listen_first|clarify_first|problem_solve|explicit_advice|crisis_support|informational",
  "context_continuity": "continuation|topic_shift|isolated",
  "context_confidence": "high|medium|low",
  "resolved_reference": "brief summary of referent or null"
}

Intensity Rubric:
1-3: Mild passing thought, slight irritation, or general casual remark.
4-6: Moderate distress, repeated worry, noticeable behavioral avoidance/procrastination, or humorous complaint.
7-8: High distress, explicit functional impact (freezing up, insomnia, overwhelm, acute pressure).
9-10: Extreme/Severe distress or crisis-level panic (safety critical).

Confidence Rubric:
high: Explicit cues or strong coherent behavioral indicators.
medium: Plausible inferred state with some ambiguity.
low: Ambiguous or minimal context where asking a clarifying question is preferred.

Conversational Intent Rubric:
- humorous_complaint: Playful irony, comedic hyperbole, or self-deprecating student jokes to vent (e.g., personifying syllabus or laptop, calling Instagram their "loyal partner", using laughing emojis with mild complaints).
- genuine_distress: Sincere emotional pain, anxiety, sadness, helplessness, loneliness, or distress (even on same topics like Instagram addiction or exams).
- neutral_casual: General chatting, factual queries, or ordinary remarks without humorous or acute emotional cues.

Advice Mode Rubric:
- listen_first: User is expressing feelings, venting, sharing emotional vulnerability, experiencing cognitive freeze/panic, or making a humorous complaint without asking for solutions. Panic or cognitive freeze alone is not a request for problem-solving; listen and reflect without unsolicited advice or habit lists.
- clarify_first: User message is ambiguous, very brief, or lacks sufficient context. Clarify before offering help.
- explicit_advice: User directly asks what to do, asks for advice, tips, or suggestions ("kya karu", "what should I do").
- problem_solve: User clearly presents an actionable, logistical academic/work problem with deadlines or assignments needing concrete structure (do not use for pure panic, trembling, or cognitive freeze without explicit action requests).
- crisis_support: High distress, hopelessness, or safety crisis; advice is suppressed in favor of immediate human support.
- informational: User is asking a factual campus or institutional query; verified facts are provided without life advice or emotional counseling.

Continuity Rubric:
- continuation: Message continues the ongoing topic, elaborates on prior context, or responds directly to prior statement (including short affirmations like 'haan wahi', 'exactly').
- topic_shift: Message pivots to a new topic (e.g. from exams to hostel WiFi, or to an unrelated question).
- isolated: Single-turn greeting, fresh standalone query, or conversation start with no prior context.

Few-Shot Examples:
Input: "Instagram meri padhai ka sabse loyal partner hai 😂"
Output: {"emotion":"frustration","intensity":4,"context":"academic","underlying_need":"venting","confidence":"high","evidence":"calling Instagram loyal partner ironically with emoji","conversation_mode":"reflective_listening","conversational_intent":"humorous_complaint","humour_confidence":"high","advice_mode":"listen_first"}

Input: "Kal exam hai aur syllabus mujhe dekh ke has raha hai."
Output: {"emotion":"anxiety","intensity":5,"context":"academic","underlying_need":"venting","confidence":"high","evidence":"personifying syllabus laughing at them","conversation_mode":"reflective_listening","conversational_intent":"humorous_complaint","humour_confidence":"high","advice_mode":"listen_first"}

Input: "Bhai mera laptop mujhe dekh ke hi hang ho jata hai."
Output: {"emotion":"frustration","intensity":4,"context":"academic","underlying_need":"venting","confidence":"high","evidence":"humorous complaint about laptop hanging","conversation_mode":"reflective_listening","conversational_intent":"humorous_complaint","humour_confidence":"high","advice_mode":"listen_first"}

Input: "Instagram ki wajah se main padh nahi paa raha aur bahut stress ho raha hai."
Output: {"emotion":"anxiety","intensity":7,"context":"academic","underlying_need":"problem_solving","confidence":"high","evidence":"cannot study due to Instagram, acute stress","conversation_mode":"problem_solving","conversational_intent":"genuine_distress","humour_confidence":"low","advice_mode":"listen_first"}

Input: "Exam kal hai aur mujhe bahut anxiety ho rahi hai."
Output: {"emotion":"anxiety","intensity":8,"context":"academic","underlying_need":"coping_tool","confidence":"high","evidence":"explicit acute exam anxiety","conversation_mode":"coping_tool","conversational_intent":"genuine_distress","humour_confidence":"low","advice_mode":"listen_first"}

Input: "Main procrastinate kar raha hoon, mujhe kya karna chahiye?"
Output: {"emotion":"anxiety","intensity":6,"context":"academic","underlying_need":"problem_solving","confidence":"high","evidence":"explicitly asking what to do about procrastinating","conversation_mode":"problem_solving","conversational_intent":"genuine_distress","humour_confidence":"low","advice_mode":"explicit_advice"}

Input: "Mere 4 assignments kal submit hone hain aur mujhe samajh nahi aa raha kahan se start karu."
Output: {"emotion":"anxiety","intensity":7,"context":"academic","underlying_need":"problem_solving","confidence":"high","evidence":"4 assignments due tomorrow, asking where to start","conversation_mode":"problem_solving","conversational_intent":"genuine_distress","humour_confidence":"low","advice_mode":"problem_solve"}

Input: "Yaar aaj bilkul mann nahi kar raha padhne ka."
Output: {"emotion":"motivation_loss","intensity":5,"context":"academic","underlying_need":"venting","confidence":"high","evidence":"expressing low motivation without asking for advice","conversation_mode":"reflective_listening","conversational_intent":"genuine_distress","humour_confidence":"low","advice_mode":"listen_first"}

Input: "Sab log mujhse better kar rahe hain."
Output: {"emotion":"sadness","intensity":6,"context":"self_esteem","underlying_need":"reassurance","confidence":"high","evidence":"comparing with peers, feeling inferior","conversation_mode":"reflective_listening","conversational_intent":"genuine_distress","humour_confidence":"low","advice_mode":"listen_first"}

Input: "Pata nahi yaar."
Output: {"emotion":"neutral","intensity":3,"context":"general","underlying_need":"casual_chat","confidence":"low","evidence":"ambiguous minimal reply","conversation_mode":"reflective_listening","conversational_intent":"neutral_casual","humour_confidence":"low","advice_mode":"clarify_first"}

Input: "I don't want to live anymore."
Output: {"emotion":"sadness","intensity":10,"context":"general","underlying_need":"grounding","confidence":"high","evidence":"explicit crisis ideation","conversation_mode":"grounding_high_risk","conversational_intent":"genuine_distress","humour_confidence":"low","advice_mode":"crisis_support"}

Input: "I'm really stressed about my assignments."
Output: {"emotion":"anxiety","intensity":6,"context":"academic","underlying_need":"problem_solving","confidence":"high","evidence":"stressed about assignments","conversation_mode":"problem_solving","conversational_intent":"genuine_distress","humour_confidence":"low","advice_mode":"listen_first"}

Input: "I keep looking at my task list and my brain just freezes."
Output: {"emotion":"anxiety","intensity":7,"context":"academic","underlying_need":"problem_solving","confidence":"high","evidence":"brain freezes on looking at task list","conversation_mode":"problem_solving","conversational_intent":"genuine_distress","humour_confidence":"low","advice_mode":"listen_first"}

Input: "Bro, so many assignments are piling up that I don't even know where to begin."
Output: {"emotion":"anxiety","intensity":7,"context":"academic","underlying_need":"problem_solving","confidence":"high","evidence":"assignments piling up, don't know where to begin","conversation_mode":"problem_solving","conversational_intent":"genuine_distress","humour_confidence":"low","advice_mode":"problem_solve"}

Input: "I come back to my room and there's nobody I feel like talking to."
Output: {"emotion":"loneliness","intensity":6,"context":"social","underlying_need":"venting","confidence":"high","evidence":"nobody to talk to in room","conversation_mode":"reflective_listening","conversational_intent":"genuine_distress","humour_confidence":"low","advice_mode":"listen_first"}

Input: "I have people around me but somehow I still feel alone."
Output: {"emotion":"loneliness","intensity":7,"context":"social","underlying_need":"venting","confidence":"high","evidence":"feel alone despite having people around","conversation_mode":"reflective_listening","conversational_intent":"genuine_distress","humour_confidence":"low","advice_mode":"listen_first"}

Input: "Bhai dimaag kharab ho gaya hai assignments se."
Output: {"emotion":"frustration","intensity":7,"context":"academic","underlying_need":"problem_solving","confidence":"high","evidence":"dimaag kharab from assignments","conversation_mode":"problem_solving","conversational_intent":"genuine_distress","humour_confidence":"low","advice_mode":"listen_first"}

Input: "Room pe aake ajeeb sa empty empty lagta hai."
Output: {"emotion":"loneliness","intensity":6,"context":"social","underlying_need":"venting","confidence":"high","evidence":"empty empty lagta hai","conversation_mode":"reflective_listening","conversational_intent":"genuine_distress","humour_confidence":"low","advice_mode":"listen_first"}

Input: "Sab log aage nikal rahe hain aur main wahi ka wahi hu."
Output: {"emotion":"sadness","intensity":6,"context":"self_esteem","underlying_need":"reassurance","confidence":"high","evidence":"peer comparison, feeling stuck","conversation_mode":"reflective_listening","conversational_intent":"genuine_distress","humour_confidence":"low","advice_mode":"listen_first"}

Input:
Previous user context:
- "Exam 3 din mein hai."
- "Kuch nahi padha."
Current user message to classify:
"Ab bas mann nahi kar raha."
Output: {"emotion":"motivation_loss","intensity":6,"context":"academic","underlying_need":"problem_solving","confidence":"high","evidence":"exam pressure followed by avoidance (mann nahi kar raha)","conversation_mode":"problem_solving","conversational_intent":"genuine_distress","humour_confidence":"low","advice_mode":"listen_first"}

Input:
Previous user context:
- "Hostel mein koi baat nahi karta."
- "Sab apne groups mein busy hain."
Current user message to classify:
"Room se nikalne ka bhi mann nahi hota."
Output: {"emotion":"loneliness","intensity":7,"context":"social","underlying_need":"reflective_listening","confidence":"high","evidence":"withdrawing to room due to isolation in hostel","conversation_mode":"reflective_listening","conversational_intent":"genuine_distress","humour_confidence":"low","advice_mode":"listen_first","context_continuity":"continuation","context_confidence":"high","resolved_reference":null}

Input:
Preceding assistant statement (for referent resolution ONLY; do NOT use as user emotion evidence):
- "Kya exam syllabus ki tension ho rahi hai?"
Current user message to classify:
"Haan wahi."
Output: {"emotion":"anxiety","intensity":5,"context":"academic","underlying_need":"venting","confidence":"high","evidence":"affirming tension about exam syllabus","conversation_mode":"reflective_listening","conversational_intent":"genuine_distress","humour_confidence":"low","advice_mode":"listen_first","context_continuity":"continuation","context_confidence":"high","resolved_reference":"exam syllabus tension"}

Input:
Previous user context:
- "Exam ki bohot tension hai."
Current user message to classify:
"Waise hostel ka WiFi phir band ho gaya."
Output: {"emotion":"frustration","intensity":4,"context":"campus_life","underlying_need":"venting","confidence":"high","evidence":"complaint about hostel WiFi being down","conversation_mode":"reflective_listening","conversational_intent":"genuine_distress","humour_confidence":"low","advice_mode":"listen_first","context_continuity":"topic_shift","context_confidence":"high","resolved_reference":null}
"""


def analyze_emotional_state(message: str, history: list) -> dict[str, Any]:
    """
    Classify the emotional state of a user message with deep semantic understanding,
    incorporating recent conversation history, Hinglish support, behavioral cue
    recognition, and an explicit intensity rubric.

    Returns a dict with:
        emotion: str - primary emotion detected (anxiety, sadness, loneliness, anger, frustration, motivation_loss, neutral, positive)
        intensity: int - 1-10 scale based on explicit rubric
        context: str - academic, social, family, self_esteem, general, casual
        need: str - backward-compatible alias for underlying_need
        underlying_need: str - reassurance, problem_solving, venting, coping_tool, grounding, casual_chat
        confidence: str - high, medium, low (epistemic/model confidence, not clinical)
        evidence: str - behavioral cue or phrase supporting the classification
        conversation_mode: str - determines response strategy
        context_continuity: str - continuation, topic_shift, isolated
        context_confidence: str - high, medium, low
        resolved_reference: str - referent phrase or description
    """
    # Skip classification for pure casual greetings when not a reference phrase or continuation
    msg_lower = message.strip().lower()
    if (len(msg_lower.split()) <= 2 and not is_reference_phrase(message) and not history) or (msg_lower in CASUAL_MESSAGES and not is_reference_phrase(message)):
        return {
            "emotion": "neutral",
            "intensity": 3,
            "context": "general",
            "need": "casual_chat",
            "underlying_need": "casual_chat",
            "confidence": "high",
            "confidence_level": "high",
            "evidence": "casual greeting or short message",
            "conversation_mode": "casual",
            "conversational_intent": "neutral_casual",
            "humour_signal": False,
            "humour_confidence": "low",
            "advice_mode": "listen_first",
            "advice_allowed": False,
            "advice_reason": "CASUAL_SHORT: Short greeting or casual remark.",
            "context_continuity": "isolated",
            "context_confidence": "high",
            "resolved_reference": ""
        }

    # Extract only previous user messages (up to 3), ignoring assistant turns
    user_context_turns: list[str] = []
    if history:
        for turn in history:
            role = getattr(turn, "role", None) or (turn.get("role") if isinstance(turn, dict) else "")
            content = getattr(turn, "content", None) or (turn.get("content") if isinstance(turn, dict) else "")
            if role == "user" and content and content.strip():
                clean_text = content.strip()
                # Bound length to 300 characters while preserving complete meaning
                if len(clean_text) > 300:
                    clean_text = clean_text[:297] + "..."
                user_context_turns.append(clean_text)

        # Keep only the most recent 3 previous user messages
        user_context_turns = user_context_turns[-3:]

    # For short reference/affirmation phrases only, optionally extract immediately preceding assistant turn (bounded to 150 chars)
    # Strictly for referent resolution; NOT user emotion evidence.
    assistant_ref_turn = ""
    if history and is_reference_phrase(message):
        last_turn = history[-1]
        last_role = getattr(last_turn, "role", None) or (last_turn.get("role") if isinstance(last_turn, dict) else "")
        last_content = getattr(last_turn, "content", None) or (last_turn.get("content") if isinstance(last_turn, dict) else "")
        if last_role == "assistant" and last_content and last_content.strip():
            clean_ast = last_content.strip()
            if len(clean_ast) > 150:
                clean_ast = clean_ast[:147] + "..."
            assistant_ref_turn = clean_ast

    # Construct explicitly framed payload
    payload_parts = []
    if user_context_turns:
        context_lines = "\n".join(f'- "{turn}"' for turn in user_context_turns)
        payload_parts.append(f"Previous user context:\n{context_lines}")
    if assistant_ref_turn:
        payload_parts.append(
            f"Preceding assistant statement (for referent resolution ONLY; do NOT use as user emotion evidence):\n- \"{assistant_ref_turn}\""
        )
    payload_parts.append(f'Current user message to classify:\n"{message}"')
    user_payload = "\n\n".join(payload_parts)

    messages = [
        {"role": "system", "content": CLASSIFICATION_PROMPT},
        {"role": "user", "content": user_payload}
    ]

    try:
        response = llm_provider.generate(
            messages=messages,
            max_tokens=600,  # Accommodate reasoning token budget + multi-field JSON safely
            temperature=0.3,  # Lower temp for consistency
        )

        raw_content = response.content
        if raw_content is None or raw_content.strip() == "":
            raise ValueError("Empty classifier response")
        # Handle reasoning-model truncation (tokens spent on reasoning leave less for content)
        if response.finish_reason == "length":
            if raw_content and raw_content.strip().startswith("{") and '"emotion"' in raw_content:
                # Attempt to recover a truncated JSON object by removing incomplete trailing key and closing braces
                # Only if truncation is just at the tail; otherwise fail to safe default via outer except
                try:
                    truncated = raw_content.strip()
                    # Strip any trailing incomplete key or comma-separated fragment
                    truncated = re.sub(r',\s*"[^"]*"?\s*:?\s*"?$', '', truncated)
                    # If missing closing braces, add them
                    open_quotes = truncated.count('"') % 2
                    if open_quotes:
                        truncated += '"'
                    open_braces = truncated.count("{") - truncated.count("}")
                    truncated += "}" * open_braces
                    # Validate — if it parses, use it
                    json.loads(truncated)
                    raw_content = truncated
                except Exception:
                    raise ValueError(f"Classifier output truncated unrecoverably: {raw_content[:80]!r}")
            else:
                raise ValueError(f"Classifier output truncated: {raw_content[:80]!r}")

        # Parse JSON from response
        clean_json_str = raw_content.strip()
        if clean_json_str.startswith("```json"):
            clean_json_str = clean_json_str[7:]
        if clean_json_str.startswith("```"):
            clean_json_str = clean_json_str[3:]
        if clean_json_str.endswith("```"):
            clean_json_str = clean_json_str[:-3]

        parsed = json.loads(clean_json_str.strip())

        # Extract underlying_need and maintain backward compatibility for 'need'
        underlying_need = str(parsed.get("underlying_need", parsed.get("need", "casual_chat")))

        raw_conf = parsed.get("confidence", "medium")
        norm_conf = normalize_confidence(raw_conf)

        # Extract conversational intent and humour signals
        intensity = int(parsed.get("intensity", 5))
        context = str(parsed.get("context", "general"))

        raw_intent = str(parsed.get("conversational_intent", "")).strip().lower()
        if raw_intent in ("humorous_complaint", "genuine_distress", "neutral_casual"):
            conversational_intent = raw_intent
        else:
            conversational_intent = infer_intent_heuristic(message, intensity, context)

        raw_h_conf = parsed.get("humour_confidence", "medium")
        norm_h_conf = normalize_confidence(raw_h_conf)
        humour_signal = bool(conversational_intent == "humorous_complaint")

        # Extract advice_mode and advice gating signals
        temp_state = {
            "underlying_need": underlying_need,
            "need": underlying_need,
            "confidence": norm_conf,
            "confidence_level": norm_conf,
            "conversational_intent": conversational_intent,
            "intensity": intensity,
            "context": context,
        }
        raw_advice_mode = str(parsed.get("advice_mode", "")).strip().lower()
        if raw_advice_mode in ("listen_first", "clarify_first", "problem_solve", "explicit_advice", "crisis_support", "informational"):
            advice_mode = raw_advice_mode
            advice_allowed = bool(advice_mode in ("problem_solve", "explicit_advice"))
            advice_reason = f"CLASSIFIER_PREDICTED: {advice_mode}"
        else:
            advice_mode, advice_allowed, advice_reason = determine_advice_mode(message, temp_state)

        # Extract context_continuity, context_confidence, resolved_reference
        raw_cont = str(parsed.get("context_continuity", "")).strip().lower()
        if raw_cont in ("continuation", "topic_shift", "isolated"):
            context_continuity = raw_cont
        else:
            context_continuity, _, _ = determine_context_continuity(message, history, temp_state)

        raw_c_conf = str(parsed.get("context_confidence", "")).strip().lower()
        if raw_c_conf in ("high", "medium", "low"):
            context_confidence = raw_c_conf
        else:
            _, context_confidence, _ = determine_context_continuity(message, history, temp_state)

        raw_ref = parsed.get("resolved_reference")
        if raw_ref is None or str(raw_ref).strip().lower() in ("null", "none", ""):
            resolved_reference = ""
        else:
            resolved_reference = str(raw_ref).strip()

        if not resolved_reference and context_continuity == "continuation" and is_reference_phrase(message):
            _, _, resolved_reference = determine_context_continuity(message, history, temp_state)

        return {
            "emotion": str(parsed.get("emotion", "neutral")),
            "intensity": intensity,
            "context": context,
            "need": underlying_need,
            "underlying_need": underlying_need,
            "confidence": norm_conf,
            "confidence_level": norm_conf,
            "evidence": str(parsed.get("evidence", "")),
            "conversation_mode": str(parsed.get("conversation_mode", "casual")),
            "conversational_intent": conversational_intent,
            "humour_signal": humour_signal,
            "humour_confidence": norm_h_conf,
            "advice_mode": advice_mode,
            "advice_allowed": advice_allowed,
            "advice_reason": advice_reason,
            "context_continuity": context_continuity,
            "context_confidence": context_confidence,
            "resolved_reference": resolved_reference,
        }

    except Exception:
        # On failure - return safe default with heuristic intent and advice mode
        heuristic_intent = infer_intent_heuristic(message, 3, "general")
        msg_lower_exc = message.strip().lower() if message else ""

        # Check whether message is an actionable request or pure emotional venting
        has_advice_req = has_explicit_advice_request(message)
        practical_terms_regex = re.compile(
            r"\b(?:assignment|assignments|exam|exams|deadline|deadlines|submit|submission|due|syllabus|workload)\b",
            re.IGNORECASE
        )
        has_practical_terms = bool(practical_terms_regex.search(msg_lower_exc))
        action_stems = ["kya kar", "kaise kar", "how to", "how do i", "how can i", "start kar", "kahan se start", "where to start", "plan bana", "strategy", "manage kar", "submit hone", "submit hain"]
        has_action_request = any(stem in msg_lower_exc for stem in action_stems)

        if heuristic_intent == "genuine_distress":
            fb_emotion = "frustration"
            fb_need = "venting"
            fb_mode = "reflective_listening"
            fb_intensity = 6
        elif has_advice_req or (has_practical_terms and has_action_request):
            fb_emotion = "anxiety"
            fb_need = "problem_solving"
            fb_mode = "problem_solving"
            fb_intensity = 5
        elif heuristic_intent == "humorous_complaint":
            fb_emotion = "frustration"
            fb_need = "venting"
            fb_mode = "reflective_listening"
            fb_intensity = 4
        elif has_practical_terms and not has_action_request and not has_advice_req:
            # Declarative / expressive statement about workload without asking for advice/plan -> listen-first
            fb_emotion = "frustration"
            fb_need = "venting"
            fb_mode = "reflective_listening"
            fb_intensity = 6
            heuristic_intent = "genuine_distress"
        else:
            fb_emotion = "neutral"
            fb_need = "casual_chat"
            fb_mode = "casual"
            fb_intensity = 3

        # Determine fallback context using message and history domain
        fb_context = "academic" if has_practical_terms else "general"
        if history:
            hist_text = " ".join([getattr(t, "content", None) or (t.get("content") if isinstance(t, dict) else "") for t in history[-6:]])
            hist_domain = detect_domain(hist_text)
            if hist_domain in ("social", "academic"):
                fb_context = hist_domain
        if fb_context == "general":
            fb_context = detect_domain(message)

        if fb_context == "social" and fb_emotion == "neutral":
            fb_emotion = "loneliness"

        temp_state = {
            "underlying_need": fb_need,
            "need": fb_need,
            "confidence": "low",
            "confidence_level": "low",
            "conversational_intent": heuristic_intent,
            "intensity": fb_intensity,
            "context": fb_context,
            "emotion": fb_emotion,
            "conversation_mode": fb_mode,
        }
        adv_mode, adv_allowed, adv_reason = determine_advice_mode(message, temp_state)
        cont_mode, cont_conf, res_ref = determine_context_continuity(message, history, temp_state)
        return {
            "emotion": fb_emotion,
            "intensity": fb_intensity,
            "context": fb_context,
            "need": fb_need,
            "underlying_need": fb_need,
            "confidence": "low",
            "confidence_level": "low",
            "evidence": "fallback to safe default",
            "conversation_mode": fb_mode,
            "conversational_intent": heuristic_intent,
            "humour_signal": bool(heuristic_intent == "humorous_complaint"),
            "humour_confidence": "low",
            "advice_mode": adv_mode,
            "advice_allowed": adv_allowed,
            "advice_reason": adv_reason,
            "context_continuity": cont_mode,
            "context_confidence": cont_conf,
            "resolved_reference": res_ref,
        }


# -------------------------------------------------------------------
# Confidence Interpretation Layer
# -------------------------------------------------------------------
def normalize_confidence(confidence: Any) -> str:
    """Normalize numeric or string confidence representations to conceptual levels:
    - 'high': confidence >= 0.80
    - 'medium': 0.50 <= confidence < 0.80
    - 'low': confidence < 0.50

    Safely handles malformed, missing, None, or out-of-range inputs by falling back to 'medium'.
    """
    if confidence is None:
        return "medium"

    # If it's already a string matching known levels
    if isinstance(confidence, str):
        c_str = confidence.strip().lower()
        if c_str in ("high", "medium", "low"):
            return c_str
        # Try converting string representation of float/int (e.g. "0.85", "0.4")
        try:
            val = float(c_str)
        except (ValueError, TypeError):
            return "medium"
    elif isinstance(confidence, (int, float)):
        val = float(confidence)
    else:
        return "medium"

    # Numeric range mapping
    if val >= 0.80:
        return "high"
    elif val >= 0.50:
        return "medium"
    elif val >= 0.0:
        return "low"
    else:
        return "medium"


CONFIDENCE_INSTRUCTIONS = {
    "high": (
        "CONFIDENCE GUIDANCE: HIGH CONFIDENCE\n"
        "- The emotional and situational cues are clear.\n"
        "- Allow the selected strategy and emotional context to guide your response directly and naturally.\n"
        "- Respond with warmth, active empathy, and focused presence without stating confidence metrics."
    ),
    "medium": (
        "CONFIDENCE GUIDANCE: MEDIUM CONFIDENCE (TENTATIVE & VALIDATING)\n"
        "- The emotional state is plausible but not fully certain.\n"
        "- Use gentle, tentative, or empathic phrasing rather than stating your interpretation as absolute fact.\n"
        "- Examples in Hinglish/English: 'Mujhe thoda aisa lag raha hai...', 'Agar main sahi samajh raha hoon...', 'Shayad...', 'Lag raha hai ki...', 'It sounds like...'.\n"
        "- Invite the student to confirm or clarify naturally if your sense of their situation fits."
    ),
    "low": (
        "CONFIDENCE GUIDANCE: LOW CONFIDENCE (CLARIFICATION & EXPLORATION)\n"
        "- The message is ambiguous, brief, or has minimal emotional context.\n"
        "- Do NOT assume, diagnose, or claim to know the student's internal emotional state.\n"
        "- Prefer a natural, open-ended question or gentle clarification to invite them to share more.\n"
        "- Examples in Hinglish/English: 'Mujhe exactly samajh nahi aa raha...', 'Kuch specific hua hai kya?', 'Bas mood off hai ya koi particular tension chal rahi hai?', 'What's been happening recently?'.\n"
        "- Keep the tone open, curious, supportive, and non-presumptive."
    ),
}


def get_confidence_instruction(confidence_level: str, strategy: str = "") -> str:
    """Return the confidence-aware conversational guidance instruction.
    CRITICAL: Confidence should NEVER weaken crisis safety or dilute factual institutional answers.
    - If strategy is 'CRISIS', safety instructions are absolute; return empty string.
    - If strategy is 'INFORMATIONAL', verified institutional facts must remain factual; return empty string.
    """
    if strategy in ("CRISIS", "INFORMATIONAL"):
        return ""

    level = normalize_confidence(confidence_level)
    return CONFIDENCE_INSTRUCTIONS.get(level, CONFIDENCE_INSTRUCTIONS["medium"])


# Conversation mode to instruction mapping (kept for backwards compatibility)
CONVERSATION_MODE_INSTRUCTIONS = {
    "reflective_listening": "Focus on listening and validating the feeling first. Do not jump to solutions yet. Ask one gentle open question.",
    "coping_tool": "Gently offer one specific coping tool (like a short breathing exercise) rather than general advice.",
    "problem_solving": "Acknowledge the feeling briefly, then help break the problem into one small, concrete next step. Ask what the smallest immediate action could be.",
    "grounding_high_risk": "Respond calmly and briefly. Do not problem-solve. Prioritize connecting the student to real human support.",
    "casual": "Respond naturally and briefly, no technique needed.",
}

# -------------------------------------------------------------------
# Emotion-Adaptive Intervention Engine — strategy layer
# -------------------------------------------------------------------
# Six internal strategies. Safety.py remains the authority for CRISIS.
STRATEGIES = [
    "REFLECTIVE_LISTENING",
    "COPING_SUPPORT",
    "PROBLEM_SOLVING",
    "GUIDANCE",
    "INFORMATIONAL",
    "CRISIS",
]

# Signals that indicate an explicit factual / institutional request.
# Kept local to avoid circular import with rag.py; word list mirrors
# rag.INFO_SIGNAL_WORDS intentionally so behaviour stays consistent.
_INFO_SIGNALS = [
    "where", "when", "how do i", "how can i", "what is the", "contact",
    "office", "block", "hostel", "deadline", "fee", "counsel", "wellbeing",
    "dsr", "location", "number", "email", "policy", "schedule", "exam date",
    "support", "talk to", "who to talk",
]

STRATEGY_INSTRUCTIONS = {
    "REFLECTIVE_LISTENING": (
        "ACTIVE STRATEGY: REFLECTIVE LISTENING — you MUST follow this for your entire reply.\n"
        "- Acknowledge the feeling first with natural warmth; do not minimize or diagnose.\n"
        "- Do not jump to solutions or lists. Do not label the condition.\n"
        "- Validate the experience conversationally like a peer (avoid rigid clichés like 'It is completely normal to feel...').\n"
        "- Ask ONE gentle open-ended follow-up question to invite sharing.\n"
        "- Keep 2-4 sentences, 30-70 words, no bullet lists."
    ),
    "COPING_SUPPORT": (
        "ACTIVE STRATEGY: COPING SUPPORT — you MUST follow this for your entire reply.\n"
        "- Acknowledge the stress briefly, without diagnosing.\n"
        "- Offer exactly ONE specific, concise calming technique (e.g., box breathing 4-4-4-4, "
        "grounding 5-4-3-2-1, or a 5-minute reset/break) in flowing sentences, not a list.\n"
        "- Keep steps actionable in the moment, not generic advice.\n"
        "- End with one gentle check-in question.\n"
        "- Keep 2-4 sentences, 30-70 words."
    ),
    "PROBLEM_SOLVING": (
        "ACTIVE STRATEGY: PROBLEM SOLVING — you MUST follow this for your entire reply.\n"
        "- Acknowledge the overwhelm briefly without diagnosing.\n"
        "- Help break the workload into the smallest concrete next step "
        "(one assignment, one 25-minute block, one section — closest deadline first).\n"
        "- Suggest prioritizing by closest deadline or smallest win.\n"
        "- Invite the student to choose one small next action.\n"
        "- Keep 2-4 sentences, 30-70 words, one suggestion only."
    ),
    "GUIDANCE": (
        "ACTIVE STRATEGY: GUIDANCE — you MUST follow this for your entire reply.\n"
        "- Acknowledge the situation with empathy, without diagnosing.\n"
        "- Offer clear, practical steps for the interpersonal/practical concern "
        "(e.g., how to approach a professor: choose a calm time, state the concern briefly, ask for one specific help).\n"
        "- Do not invent policies, contacts, or office details; stay general unless VERIFIED CONTEXT provides them.\n"
        "- End with one supportive follow-up question.\n"
        "- Keep 2-4 sentences, 30-70 words."
    ),
    "INFORMATIONAL": (
        "ACTIVE STRATEGY: INFORMATIONAL — you MUST follow this for your entire reply.\n"
        "- Answer ONLY from the VERIFIED CONTEXT provided. Do not invent or guess details.\n"
        "- Be concise and factual, warm in tone, 2-4 sentences.\n"
        "- If VERIFIED CONTEXT contains PLACEHOLDER or is missing, say you do not have verified "
        "information and suggest checking the relevant department or UMS.\n"
        "- Cite the source briefly if helpful."
    ),
    "CRISIS": (
        "ACTIVE STRATEGY: CRISIS — HIGH-RISK OVERRIDE — you MUST follow this for your entire reply.\n"
        "- Respond calmly, warmly, and briefly. Do NOT attempt problem-solving or coping techniques.\n"
        "- Prioritize connecting the student to real human support.\n"
        "- Do NOT repeat helpline numbers in your text; the system displays them separately. "
        "Instead encourage reaching out to the helplines shown below and to the LPU Division of Happiness and Wellbeing.\n"
        "- Keep 2-4 sentences, supportive and non-judgmental. Do not diagnose."
    ),
}


def select_response_strategy(
    emotion_result: dict[str, Any],
    user_message: str,
    safety_result: dict[str, Any],
    grounding_found: bool = False,
) -> str:
    """Select the internal response strategy.

    Priority:
      1. CRISIS  — safety_result high risk always wins (authoritative)
      2. INFORMATIONAL — explicit factual/college request (grounding + factual anchor)
      3. Emotion-derived strategies from semantic classifier output (mode, need, emotion, context, intensity)
      4. Keyword fallback ONLY when semantic classification is unavailable/fallback/low-confidence
    """
    # 1. Safety is the authority
    if safety_result.get("risk_level") == "high":
        return "CRISIS"

    # Extract semantic classification fields
    mode = str(emotion_result.get("conversation_mode", "casual")).strip().lower()
    need = str(emotion_result.get("underlying_need", emotion_result.get("need", ""))).strip().lower()
    context = str(emotion_result.get("context", "")).strip().lower()
    emotion = str(emotion_result.get("emotion", "")).strip().lower()
    evidence = str(emotion_result.get("evidence", "")).strip().lower()
    raw_conf = emotion_result.get("confidence_level", emotion_result.get("confidence", ""))
    confidence = normalize_confidence(raw_conf)
    try:
        intensity = int(emotion_result.get("intensity", 5))
    except Exception:
        intensity = 5

    msg_lower = user_message.lower()

    # Determine if semantic classification failed into fallback default
    is_fallback = (
        evidence == "fallback to safe default"
        or (confidence == "low" and emotion == "neutral" and mode == "casual")
    )

    # 2. Informational: explicit factual/college request.
    # Distinguish genuine informational inquiries from emotional venting that merely mentions
    # a physical campus location/setting (e.g. "Hostel mein sabke groups hain aur main akela hoon").
    inquiry_stems = [
        "where is", "where are", "where can i", "where do i",
        "what is the", "what are the", "which block", "which room",
        "how do i", "how can i", "how to check", "how to apply",
        "timings", "office hours", "contact number", "phone number",
        "enquiry number", "due date", "deadline", "fee structure",
        "allotment", "email address"
    ]
    has_inquiry_stem = any(s in msg_lower for s in inquiry_stems)

    specific_institutional_anchors = [
        "dsr", "division of student relationship",
        "department of counseling", "happiness department",
        "counselling timings", "counseling timings", "fee deadline", "tuition fee"
    ]
    has_specific_institutional = any(a in msg_lower for a in specific_institutional_anchors)

    broad_context_anchors = ["hostel", "office", "block", "schedule", "policy", "room"]
    has_broad_anchor = any(b in msg_lower for b in broad_context_anchors)

    is_emotional_distress = (
        not is_fallback
        and confidence in ("high", "medium")
        and (
            emotion in ("loneliness", "sadness", "anxiety", "frustration", "overwhelm")
            or need in ("venting", "reassurance")
            or mode in ("reflective_listening", "coping_tool")
        )
    )

    is_genuine_informational = False
    if has_specific_institutional:
        is_genuine_informational = True
    elif has_inquiry_stem and has_broad_anchor and not is_emotional_distress:
        is_genuine_informational = True
    elif has_broad_anchor and "?" in msg_lower and not is_emotional_distress:
        is_genuine_informational = True
    elif grounding_found and (has_broad_anchor or any(k in msg_lower for k in ["dsr", "office", "timings", "counseling", "counselling", "fee", "allotment"])) and not is_emotional_distress:
        is_genuine_informational = True

    if is_genuine_informational:
        return "INFORMATIONAL"

    # 3. Semantic classifier output is the PRIMARY source for strategy selection
    if not is_fallback:
        # High-intensity anxiety / panic / acute grounding need -> COPING_SUPPORT
        if mode == "coping_tool" or need in ("coping_tool", "grounding"):
            return "COPING_SUPPORT"
        if emotion == "anxiety" and intensity >= 7 and need == "reassurance":
            return "COPING_SUPPORT"

        # Reflective listening: sadness, loneliness, venting, reassurance
        # Semantic emotion & need take precedence over topic keywords (e.g. assignments)
        if (
            mode == "reflective_listening"
            or need in ("venting", "reassurance")
            or emotion in ("sadness", "loneliness")
        ):
            return "REFLECTIVE_LISTENING"

        # Problem-solving: academic workload, procrastination, task breakdown
        if mode == "problem_solving" or need == "problem_solving":
            # Distinguish interpersonal GUIDANCE (e.g. how to approach a professor) from workload breakdown
            interpersonal = any(k in msg_lower for k in ["professor", "faculty", "teacher", "talk to", "approach"])
            how_to = any(k in msg_lower for k in ["how do i", "how can i", "how to", "advice", "guidance", "talk to"])
            if interpersonal and how_to:
                return "GUIDANCE"
            return "PROBLEM_SOLVING"

        # Academic distress with problem-solving orientation
        if context == "academic" and emotion in ("motivation_loss", "frustration") and need not in ("venting", "reassurance"):
            return "PROBLEM_SOLVING"

        # Casual chat -> light guidance (natural brief style)
        if mode == "casual" or need == "casual_chat":
            return "GUIDANCE"

        # Positive emotion
        if emotion == "positive":
            return "GUIDANCE"

    # 4. Keyword fallback ONLY when semantic classification is unavailable or low-confidence fallback
    if any(k in msg_lower for k in ["can't calm down", "cant calm down", "panic", "calm down before"]):
        return "COPING_SUPPORT"

    if any(k in msg_lower for k in ["feeling low", "feel low", "feel lonely", "feeling lonely", "feel sad", "feeling sad"]):
        return "REFLECTIVE_LISTENING"

    # Distinguish emotional venting from practical advice/solution requests in fallback
    has_action_request = (
        has_explicit_advice_request(user_message)
        or any(k in msg_lower for k in ["how do i", "how can i", "how to", "advice", "kya kar", "kaise kar", "where to start", "start kar", "plan bana", "strategy", "manage kar"])
    )

    if (mode == "reflective_listening" or need in ("venting", "reassurance")) and not has_action_request:
        return "REFLECTIVE_LISTENING"

    if any(k in msg_lower for k in ["assignments", "where to start", "procrastinat", "workload", "deadline"]):
        if not has_action_request and not any(k in msg_lower for k in ["where to start", "start kar"]):
            return "REFLECTIVE_LISTENING"
        interpersonal = any(k in msg_lower for k in ["professor", "faculty", "teacher", "talk to", "approach"])
        if interpersonal and any(k in msg_lower for k in ["how do i", "how can i", "how to", "advice"]):
            return "GUIDANCE"
        return "PROBLEM_SOLVING"

    if any(k in msg_lower for k in ["how do i", "how can i", "how to", "advice"]):
        return "GUIDANCE"

    # Safe final fallback
    return "REFLECTIVE_LISTENING"
