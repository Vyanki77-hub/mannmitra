# personality.py
# Personality Engine v1: Language and Peer-Tone Alignment Layer for MannMitra.
# Detects input language/register and provides tailored peer-companion directives.

import re
from typing import Any

# Unicode range for Devanagari script (Hindi, Sanskrit, Marathi)
DEVANAGARI_RANGE = re.compile(r'[\u0900-\u097F]')

# Common Hinglish stopwords, markers, pronouns, and verbs in Latin script.
# Carefully curated to avoid collisions with common English words (e.g., 'is', 'me', 'to', 'or', 'in', 'us', 'main', 'lag', 'pure', 'door').
HINGLISH_TOKENS = {
    # Pronouns / demonstratives
    "yaar", "yar", "yarr", "bhai", "bhaiya", "bro", "dost",
    "mera", "meri", "mere", "mujhe", "mujhko", "mai", "hum", "humein", "humko",
    "tera", "teri", "tere", "tujhe", "tujhko", "tum", "tumhe", "tumhara", "tumhari", "tumhare",
    "aap", "aapka", "aapki", "aapke",
    "yeh", "woh", "inka", "unka", "inhe", "unhe",
    "kya", "kyun", "kyu", "kaise", "kahan", "kaha", "kab", "kaun", "kisko", "kisse",
    "kuch", "kuchh", "koi", "kisi", "sab", "sabka", "sabke", "sabki", "sabse",
    # Particles / conjunctions / adverbs
    "bas", "bhi", "toh", "nahi", "nhi", "nahin", "mat",
    "haan", "lekin", "magar",
    "se", "ko", "mein", "pe", "tak",
    "bilkul", "bohot", "bahut", "bhot", "zyada", "jyada", "kam", "thoda", "thodi", "thode",
    "aaj", "kal", "ab", "abhi", "phir", "fir", "baad", "pehle",
    "wahi", "yahi", "aisa", "aisi", "aise", "waisa", "waisi", "waise",
    # Verbs / auxiliaries
    "hai", "hain", "hoon", "hun", "tha", "thi", "thhe",
    "hoga", "hogi", "hoge", "honge",
    "kar", "karna", "karni", "karne", "karta", "karti", "karte", "karu", "karoon", "karein", "kiya", "kiye", "kiyi",
    "raha", "rahi", "rahe", "gaya", "gayi", "gaye",
    "lagta", "lagti", "lagte", "laga", "lagi", "lage",
    "aata", "aati", "aate", "aaya", "aayi", "aaye", "aana", "aane",
    "jana", "jaata", "jaati", "jaate", "jata", "jati", "jate", "jao",
    "bol", "bola", "boli", "bole", "bolu", "bolna", "bolne",
    "dekh", "dekha", "dekhi", "dekhe", "dekhna", "dekhne", "dekhu",
    "baith", "baitha", "baithi", "baithe", "baithna", "baithta", "baithti",
    "chala", "chali", "chale", "chalo",
    "samajh", "samjha", "samjhi", "samjhe",
    "paa", "sakta", "sakti", "sakte", "sake",
    "rehta", "rehti", "rehte", "raho",
    "suno", "sun", "sunna",
    # Emotional / colloquial concepts
    "dimaag", "dimag", "ajeeb", "poora", "puri", "poore", "pada", "padi", "pade",
    "padhai", "hasna", "chahiye", "paas", "dur",
    "khushi", "tension", "pareshan", "pareshani", "gussa",
    "aage", "peeche", "piche", "niche", "upar", "saath", "sath", "baat"
}

# Strong markers that uniquely identify Hinglish even in short/ambiguous phrases
STRONG_HINGLISH_MARKERS = {
    "yaar", "yar", "yarr", "bhai", "bhaiya", "dimaag", "dimag", "kahan", "kyun", "kyu",
    "bolu", "kaise", "nahi", "nhi", "nahin", "bilkul", "mujhe", "mera", "meri", "mere",
    "teri", "tera", "tere", "kuch", "kuchh", "aaj", "baithta", "rehta", "padhai", "ajeeb",
    "lagta", "lagti", "lagte", "laga", "lagi", "raha", "rahi", "hoon", "hain", "hai"
}


def detect_language(text: str) -> str:
    """
    Detect conversational language and script register.
    Returns: 'hindi_devanagari' | 'hinglish_latin' | 'english'
    """
    if not text or not text.strip():
        return "english"

    # 1. Check for Devanagari script (at least 2 Devanagari characters)
    devanagari_chars = DEVANAGARI_RANGE.findall(text)
    if len(devanagari_chars) >= 2:
        return "hindi_devanagari"

    # 2. Check for Hinglish markers in Latin text
    tokens = re.findall(r'[a-zA-Z]+', text.lower())
    if not tokens:
        return "english"

    # Strong single markers that definitively indicate Hinglish
    for t in tokens:
        if t in STRONG_HINGLISH_MARKERS:
            return "hinglish_latin"

    matches = [t for t in tokens if t in HINGLISH_TOKENS]

    # Ratio check: at least 2 matching tokens for non-strong markers
    if len(matches) >= 2:
        return "hinglish_latin"

    return "english"


def get_language_and_register_instruction(
    language: str,
    strategy: str,
    risk_level: str
) -> str:
    """
    Generate prompt instructions for language mirroring and peer-companion tone.
    Enforces strict safety boundaries during high-risk/CRISIS situations.
    """
    # High-risk / CRISIS safety boundary has absolute priority
    if risk_level == "high" or strategy == "CRISIS":
        lang_target = {
            "hinglish_latin": "natural, empathetic Hinglish in Latin script",
            "hindi_devanagari": "warm, empathetic Hindi in Devanagari script",
            "english": "warm, compassionate English"
        }.get(language, "warm English")

        return (
            "CRITICAL SAFETY DIRECTIVE (ABSOLUTE PRIORITY):\n"
            "- High distress or crisis language detected.\n"
            "- DO NOT use casual slang, light humour, or playful peer tone.\n"
            f"- Respond with deep care, calm urgency, and warmth in {lang_target}.\n"
            "- Prioritize immediate human connection and encourage reaching out to the helplines shown.\n"
            "- Keep 2-4 sentences, non-judgmental, grounded."
        )

    # Normal / Supportive Conversation
    if language == "hinglish_latin":
        return (
            "PERSONALITY ENGINE — LANGUAGE & PEER-TONE ALIGNMENT (HINGLISH LATIN SCRIPT):\n"
            "- The student is speaking casual conversational Hinglish in the Latin alphabet.\n"
            "- You MUST respond in natural, conversational Hinglish using the Latin script (Roman alphabet).\n"
            "- NEVER respond in pure English. NEVER respond in Devanagari script.\n"
            "- Tone: Supportive Indian college friend / senior — warm, relatable, non-judgmental, grounded.\n"
            "- Natural Register: If the user says 'yaar' or 'bhai', you can acknowledge it naturally "
            "(e.g., 'Haan yaar...', 'Samajh raha hoon bhai...'), but keep it authentic without forcing slang into every sentence.\n"
            "- Pronoun & Register Consistency:\n"
            "  * UNCONDITIONAL RULE: NEVER use formal Romanized pronouns or honorific forms 'aap', 'aapka', 'aapke', 'aapko', or 'aapse' under any circumstances.\n"
            "  * You are speaking as an empathetic college peer/friend, NOT an elder, professor, or formal counselor.\n"
            "  * CONTRASTIVE REGISTER EXAMPLES (Strictly follow the DO pattern and NEVER use the DON'T pattern):\n"
            "    - Action-Plan / Practical Advice Responses:\n"
            "      * DON'T: 'Aapko chhota step lena chahiye', 'Kya aapke paas task hai?', 'Aap procrastination se joojh rahe hain'\n"
            "      * DO: 'Tumhein ek chhota step lena chahiye', 'Kya tere paas koi task hai?', 'Main samajh sakta hoon procrastination kitna frustrating hota hai'\n"
            "    - Empathy Reflection & Closing Questions:\n"
            "      * DON'T: 'Dekhiye, kya aap bata sakte hain jo aapko lagta hai', 'Aap kaisa mehsoos kar rahe hain?'\n"
            "      * DO: 'Dekh, kya kuch aisa hai jo lag raha hai?', 'Kaisa lag raha hai abhi?', 'Agar share karna chaho toh batao.'\n"
            "    - Hostel Loneliness & Social Isolation Reflections:\n"
            "      * DON'T: 'Aapko lagta hai ki hostel mein sabke groups hain', 'Aapke man mein koi connection nahi hai', 'Aap chupchap aakar room mein baithte hain'\n"
            "      * DO: 'Tumhein lagta hai hostel mein sabke groups hain', 'Tere man mein lagta hai koi connection nahi hai', 'Tu chupchap aake room mein baith jaata hai'\n"
            "  * Prefer natural informal peer pronouns such as 'tum', 'tumhein', 'tujhe', 'tera', or 'teri' where grammatically appropriate. Do NOT force unnatural pronouns into every sentence.\n"
            "  * Prefer first-person singular 'main/mujhe' instead of awkward 'hum/humko' unless the context genuinely requires plural 'hum'.\n"
            "  * Do not force slang or pronouns mechanically.\n"
            "- BANNED ROBOTIC / CLINICAL TRANSLATIONS (DO NOT USE):\n"
            "  * NEVER translate English counselor clichés literally like: 'Mujhe sunayi de raha hai ki...', "
            "'Yeh bilkul samanya/normal hai ki chhatra aisa mehsoos karein...', 'Aapke dimaag mein kya chal raha hai jo isme yogdaan de raha hai?'\n"
            "  * Instead, speak like a real college friend: "
            "'Haan yaar, lag raha hai aaj dimaag ne thoda break le liya.', "
            "'Sachi, jab sab ek saath pile up ho jaye toh aisi feeling aati hai.', "
            "'Kya cheez sabse zyada load de rahi hai abhi?'\n"
            "- Response Constraint: Ask at most ONE follow-up question or invitation at the end of a response. Never ask two separate questions in the same response."
        )

    elif language == "hindi_devanagari":
        return (
            "PERSONALITY ENGINE — LANGUAGE & PEER-TONE ALIGNMENT (HINDI DEVANAGARI SCRIPT):\n"
            "- The student is speaking Hindi in the Devanagari script.\n"
            "- You MUST reply in natural, warm conversational Hindi using the Devanagari script.\n"
            "- Tone: Caring, empathetic college companion. Use everyday spoken Hindi (avoid overly formal or archaic Sanskritized Hindi).\n"
            "- BANNED CLINICAL FORMULAS:\n"
            "  * Do NOT use mechanical textbook translations like: 'यह महसूस करना बिल्कुल सामान्य है...', 'मैं सुन सकता हूँ कि आप कैसा महसूस कर रहे हैं...'.\n"
            "  * Speak warmly like a real friend: 'हाँ, कभी-कभी दिमाग सच में पूरी तरह थक जाता है। क्या हुआ, कुछ खास बात परेशान कर रही है या बस दिन ही भारी बीता?'\n"
            "- Response Constraint: Ask at most ONE follow-up question or invitation at the end of a response. Never ask two separate questions in the same response."
        )

    else:
        return (
            "PERSONALITY ENGINE — LANGUAGE & PEER-TONE ALIGNMENT (NATURAL ENGLISH PEER):\n"
            "- The student is speaking English. Respond in natural, warm, conversational English.\n"
            "- Tone: Supportive college friend, NOT a clinical therapist or textbook wellness bot.\n"
            "- BANNED ROBOTIC COUNSELOR PHRASES (DO NOT USE THESE):\n"
            "  * NEVER say: 'I hear how you're feeling...', 'I hear you feeling...', 'It sounds like you're feeling...'\n"
            "  * NEVER say: 'It's completely normal for students to feel...' or 'Many students experience...'\n"
            "  * NEVER say: 'What has been on your mind lately that might be contributing to that sense?'\n"
            "  * NEVER say: 'What is one small thing you could do right now?'\n"
            "- USE NATURAL EMPATHETIC CONVERSATIONAL PHRASING:\n"
            "  e.g., 'That sounds genuinely exhausting.', 'I can totally get why you'd feel so drained.', 'Days like that just feel completely off.'\n"
            "- Response Constraint: Ask at most ONE follow-up question or invitation at the end of a response. Never ask two separate questions in the same response."
        )


# -------------------------------------------------------------------
# Personality Engine v1 Step 2: Sarcasm & Humour Gating Layer
# -------------------------------------------------------------------

def infer_intent_heuristic(message: str, intensity: int = 5, context: str = "general") -> str:
    """
    Lightweight heuristic intent resolver used when LLM output is missing intent
    or in offline/fallback execution.
    Classifies into: 'humorous_complaint' | 'genuine_distress' | 'neutral_casual'.
    """
    if not message or not message.strip():
        return "neutral_casual"

    msg_lower = message.strip().lower()

    # 1. Critical safety / acute distress keywords & venting distress markers -> ALWAYS genuine_distress
    distress_markers = [
        "stress ho raha", "anxiety ho rahi", "padh nahi paa", "handle nahi kar",
        "darr lag", "panic", "rona aa raha", "kisi se baat karne ka mann nahi",
        "room mein pada rehta", "sab aage nikal rahe", "wahi ka wahi",
        "die", "suicide", "kill myself", "hopeless", "can't go on", "depressed",
        "don't want to live", "cannot do this", "falling apart"
    ]
    if any(m in msg_lower for m in distress_markers) or intensity >= 7 or context == "self_esteem":
        return "genuine_distress"

    # 2. Humorous complaint / sarcastic indicators:
    # a) Personification of inanimate academic / technical objects
    has_personification = any(p in msg_lower for p in [
        "has raha", "dekh ke has", "dekh ke hi hang", "hang ho jata", "ghoor rahi", "dara raha"
    ])
    # b) Sarcastic partner / friendship metaphors for distractions
    has_sarcastic_metaphor = any(m in msg_lower for m in [
        "loyal partner", "best friend", "sabse loyal", "pyar ho gaya"
    ])
    # c) Laughing emojis / text laugh markers combined with mild frustration/complaints
    has_humour_markers = bool(re.search(r'[😂🤣]|(?:\b(?:lmao|lol|xd|haha)\b)', msg_lower))

    if (has_personification or has_sarcastic_metaphor or (has_humour_markers and intensity <= 6)):
        return "humorous_complaint"

    if intensity >= 6:
        return "genuine_distress"

    return "neutral_casual"


def is_humour_allowed(
    emotional_state: dict[str, Any],
    risk_level: str = "low",
    strategy: str = "",
) -> tuple[bool, str]:
    """
    Strict safety and vulnerability gate for humour and light commiseration.
    Priority hierarchy:
      SAFETY > CRISIS > existing strategy/routing > humour/personality

    Returns:
      (allowed: bool, reason: str)
    """
    # 1. Deterministic crisis / high-risk safety gate (ABSOLUTE PRIORITY)
    if risk_level == "high" or strategy == "CRISIS":
        return False, "SAFETY_OVERRIDE: High-risk/CRISIS state active; all humour strictly suppressed."

    # 2. Institutional factual questions require clean factual answers
    if strategy == "INFORMATIONAL":
        return False, "INFORMATIONAL_ACCURACY: Factual query requires verified institutional information."

    intent = emotional_state.get("conversational_intent", "neutral_casual")
    intensity = emotional_state.get("intensity", 5)
    context = emotional_state.get("context", "general")
    emotion = emotional_state.get("emotion", "neutral")
    h_conf = emotional_state.get("humour_confidence", "medium")

    # 3. Genuine distress expressed
    if intent == "genuine_distress":
        return False, "GENUINE_DISTRESS: User expressed sincere distress; humour could invalidate feelings."

    # 4. Severe emotional intensity (intensity >= 7 or grounding mode)
    if intensity >= 7 or emotional_state.get("conversation_mode") == "grounding_high_risk":
        return False, "HIGH_INTENSITY: Emotional distress is high (intensity >= 7); prioritise empathy and safety."

    # 5. Vulnerability guard: self-esteem collapse
    if context == "self_esteem" or (emotion in ("sadness", "loneliness") and intensity >= 6):
        return False, "VULNERABILITY_GUARD: Self-esteem insecurity or loneliness detected; humour risks compounding vulnerability."

    # 6. Vulnerability guard: social isolation / withdrawal
    if context == "social" and intensity >= 6:
        return False, "VULNERABILITY_GUARD: Social isolation/withdrawal detected; humour inappropriate."

    # 7. Low confidence in humour signal -> default to neutral supportive conversation
    if h_conf == "low":
        return False, "LOW_CONFIDENCE: Humour intent is uncertain; defaulting to neutral supportive response."

    # 8. Must have humorous_complaint intent
    if intent != "humorous_complaint":
        return False, "NO_HUMOUR_SIGNAL: Message is neutral or casual without humorous complaint intent."

    # All safety checks and gating criteria passed
    return True, "HUMOROUS_COMPLAINT_ALLOWED: Light commiseration and relatable peer banter permitted."


def get_humour_instruction(
    is_allowed: bool,
    language: str = "hinglish_latin",
    reason: str = ""
) -> str:
    """
    Generate prompt directives for handling sarcasm, irony, and humorous complaints.
    """
    if not is_allowed:
        return (
            "HUMOUR GATING: OFF\n"
            "- Do NOT use sarcasm, playful banter, teasing, or jokes.\n"
            "- Maintain an earnest, empathetic, and supportive tone."
        )

    if language == "hinglish_latin":
        return (
            "HUMOUR HANDLING: HUMOROUS COMPLAINT / LIGHT COMMISERATION (ALLOWED)\n"
            "- The student made a humorous complaint, self-deprecating student joke, or sarcastic remark about their situation.\n"
            "- Acknowledge the joke naturally with relatable peer commiseration (e.g., 'Haan yaar, syllabus ka alag hi attitude hota hai...').\n"
            "- Light, playful banter is allowed, but:\n"
            "  * NEVER mock the student or belittle their situation.\n"
            "  * NEVER make fun of their real feelings or stress.\n"
            "  * Do NOT turn the entire response into a standup comedy routine.\n"
            "  * Notice the underlying reality (they still have an exam or task) without jumping prematurely into advice.\n"
            "- SINGLE-QUESTION CEILING HARDENING (CRITICAL REQUIREMENT):\n"
            "  * STRICT CEILING: Ask at most ONE question in the entire response (Maximum ONE question mark '?' in the entire response).\n"
            "  * Do NOT use rhetorical or tag questions such as 'na?', 'hai na?', 'right?', 'you know?' if a follow-up question is also asked.\n"
            "  * If you commiserate using a tag (e.g. 'na'), write it as a declarative statement ending in a full stop (e.g., '...alag hi scene hai na.', NEVER '...alag hi scene hai, na?').\n"
            "  * Save your ONE question for a genuine, supportive follow-up question at the end."
        )
    elif language == "hindi_devanagari":
        return (
            "HUMOUR HANDLING: HUMOROUS COMPLAINT (HINDI DEVANAGARI)\n"
            "- The student is using light humour or sarcasm.\n"
            "- Acknowledge the humour warmly like a college friend; light commiseration is welcome.\n"
            "- Do not mock the user or force unwanted advice.\n"
            "- SINGLE-QUESTION CEILING HARDENING: Maximum ONE question in the entire response. Do NOT use rhetorical tag questions (जैसे 'है ना?', 'ना?') यदि अंत में कोई अन्य प्रश्न भी पूछा गया हो।"
        )
    else:
        return (
            "HUMOUR HANDLING: HUMOROUS COMPLAINT / LIGHT COMMISERATION (ALLOWED)\n"
            "- The student made a humorous, ironic, or sarcastic remark about their academic/campus situation.\n"
            "- Acknowledge the irony or humour warmly and naturally like a relatable college peer.\n"
            "- Light banter or commiseration is allowed, but:\n"
            "  * NEVER mock the student or belittle their difficulties.\n"
            "  * Do NOT force a lecture or unsolicited advice.\n"
            "  * Balance the humor with gentle validation of the underlying situation.\n"
            "- SINGLE-QUESTION CEILING HARDENING:\n"
            "  * Maximum ONE question in the entire response.\n"
            "  * Do NOT use rhetorical tag questions ('right?', 'you know?', 'isn't it?') if a follow-up question is also present."
        )


def enforce_single_question_ceiling(text: str) -> str:
    """
    Safely enforce the maximum-one-question constraint on generated text
    without damaging natural spoken language or dropping words.
    
    If multiple questions exist:
      1. Normalizes rhetorical / conversational tag questions (e.g. ', na?' -> ', na.')
         when followed by another question.
      2. If still >1 question mark, converts earlier questions to declarative statements ('.' instead of '?').
    """
    if not text or text.count("?") <= 1:
        return text

    # Step 1: Normalize rhetorical / tag questions before genuine follow-ups
    # Matches: ', na?', ', hai na?', ', right?', ', you know?'
    tag_pattern = re.compile(r'([,\s]+)(na|hai\s+na|haina|right|you\s+know)\s*\?', re.IGNORECASE)

    def replace_tag(match: re.Match) -> str:
        prefix = match.group(1)
        tag = match.group(2)
        return f"{prefix}{tag}."

    fixed_text = tag_pattern.sub(replace_tag, text)
    if fixed_text.count("?") <= 1:
        return fixed_text

    # Step 2: If still >1 question mark, keep only the final question mark
    # Convert preceding '?' to '.' to preserve sentence boundaries
    if fixed_text.count("?") > 1:
        q_indices = [i for i, c in enumerate(fixed_text) if c == "?"]
        chars = list(fixed_text)
        for idx in q_indices[:-1]:
            chars[idx] = "."
        return "".join(chars)

    return fixed_text


# -------------------------------------------------------------------
# Personality Engine v1 Step 3: Advice Gating & Listen-First Layer
# -------------------------------------------------------------------

def has_explicit_advice_request(text: str) -> bool:
    """
    Check if the user explicitly asks for advice, guidance, or next steps.
    """
    if not text or not text.strip():
        return False
    t_lower = text.strip().lower()
    patterns = [
        r"\bkya\s+(?:karna\s+chahiye|karu|karoon|karein|kare|kru|karun)\b",
        r"\bkaise\s+(?:handle|manage|solve|deal|karu|karoon|karein|kare|kru|karun)\b",
        r"\b(?:advice|suggestion|tips?)\s+(?:do|de|chahiye|suggest|bata|batao|batana)\b",
        r"\bkuch\s+suggest\s+(?:karo|kar|karein)\b",
        r"\b(?:strategy\s+(?:bata|batao|batana|chahiye|do|de))\b",
        r"\b(?:give\s+me\s+a\s+plan|make\s+a\s+plan|action\s+plan|concrete\s+steps?)\b",
        r"\b(?:plan\s+(?:bana\s+ke\s+do|bana\s+do|chahiye|do))\b",
        r"\bwhat\s+(?:should|can|ought)\s+i\s+do\b",
        r"\bwhat\s+to\s+do\b",
        r"\bhow\s+should\s+i\b",
        r"\bhow\s+can\s+i\s+(?:handle|fix|manage|deal|solve)\b",
        r"\bgive\s+me\s+(?:some\s+)?advice\b",
        r"\bany\s+(?:advice|tips?|suggestions?)\b",
    ]
    return any(re.search(pat, t_lower) for pat in patterns)


def determine_advice_mode(
    message: str,
    emotional_state: dict[str, Any],
    risk_level: str = "low",
    strategy: str = "",
) -> tuple[str, bool, str]:
    """
    Determine the advice gate mode based on the strict hierarchy:
      SAFETY / CRISIS
      >
      EXPLICIT ADVICE REQUEST
      >
      COGNITIVE-FREEZE / SOMATIC PANIC GATING
      >
      CLEAR PRACTICAL PROBLEM
      >
      EMOTIONAL NEED / UNDERLYING NEED
      >
      AMBIGUITY / LOW CONFIDENCE

    Returns:
      (advice_mode: str, advice_allowed: bool, advice_reason: str)
    """
    # 1. SAFETY / CRISIS (Highest Priority)
    if risk_level == "high" or strategy == "CRISIS":
        return (
            "crisis_support",
            False,
            "CRISIS_SAFETY_PRIORITY: Crisis active; problem-solving advice suppressed in favor of immediate human support."
        )

    # 2. Institutional factual questions require factual answers, not life advice
    if strategy == "INFORMATIONAL":
        return (
            "informational",
            False,
            "INFORMATIONAL_QUERY: Institutional factual request; verified facts provided directly, personal advice suppressed."
        )

    msg_lower = message.strip().lower() if message else ""

    # 3. EXPLICIT ADVICE REQUEST (Priority 2)
    if has_explicit_advice_request(message):
        return (
            "explicit_advice",
            True,
            "EXPLICIT_ADVICE_REQUEST: User directly requested guidance/suggestions."
        )

    # 3b. NARROW COGNITIVE-FREEZE / SOMATIC PANIC GATING
    # When user is experiencing acute mental freeze, blanking out, or trembling,
    # prevent automatic problem-solving advice when the user is clearly overwhelmed
    # and has not explicitly asked for a concrete plan.
    panic_freeze_cues = [
        "dimaag blank", "dimag blank", "mind blank", "brain blank",
        "blank ho raha", "blank ho rahi", "blank ho gaya", "blank ho gayi",
        "haath kaanp", "hath kaanp", "kaanp rahe", "kaanp rahi", "kaanpne lag",
        "brain freeze", "brain freezes", "dimaag freeze", "dimag freeze",
        "freeze ho raha", "freeze hota ja raha", "freeze up", "freezing up",
        "panic freeze",
    ]
    has_panic_freeze = any(cue in msg_lower for cue in panic_freeze_cues) or (
        "freeze" in msg_lower and any(w in msg_lower for w in ["dimaag", "dimag", "brain", "mind", "soch", "haath", "hath", "body", "anxiety", "panic", "paralyz", "viva", "exam", "syllabus"])
    )
    if has_panic_freeze:
        return (
            "listen_first",
            False,
            "ACUTE_PANIC_FREEZE: Cognitive freeze or somatic panic cues detected without explicit plan request; prioritize listen_first validation over problem-solving advice."
        )

    # 3c. COLLOQUIAL COGNITIVE EXHAUSTION / VENTING GATING
    # Idiomatic expressions indicating mental saturation, exhaustion, or emotional venting
    # without an explicit request for problem-solving action.
    colloquial_exhaustion_cues = [
        "dimaag ka dahi", "dimag ka dahi",
        "pak gaya", "pak gayi", "pak chuka", "pak chuki",
        "tang aa gaya", "tang aa gayi", "tang aa chuka", "tang aa chuki",
    ]
    has_colloquial_exhaustion = any(cue in msg_lower for cue in colloquial_exhaustion_cues)
    if has_colloquial_exhaustion:
        return (
            "listen_first",
            False,
            "COLLOQUIAL_VENTING_EXHAUSTION: Colloquial cognitive exhaustion or venting cues detected without explicit plan request; prioritize listen_first validation over problem-solving advice."
        )

    # 4. CLEAR PRACTICAL PROBLEM (Priority 3)
    # Use word-boundary token matching to avoid substring collisions (e.g. 'exam' matching 'examiner' or 'example').
    PRACTICAL_SIGNALS_REGEX = re.compile(
        r"\b(?:assignment|assignments|exam|exams|deadline|deadlines|submit|submission|due|syllabus|project|projects|presentation|presentations|workload)\b",
        re.IGNORECASE
    )
    has_practical_context = bool(PRACTICAL_SIGNALS_REGEX.search(msg_lower))
    need = emotional_state.get("underlying_need", emotional_state.get("need", ""))
    intent = emotional_state.get("conversational_intent", "neutral_casual")

    # If it's a humorous complaint about academic objects, honour listen_first commiseration
    if intent == "humorous_complaint":
        return (
            "listen_first",
            False,
            "HUMOROUS_COMPLAINT: Humorous commiseration without unsolicited problem-solving advice."
        )

    # Check for concrete practical problem needing immediate structure.
    # Academic/exam context alone must NOT enable unsolicited advice if the strategy is reflective listening
    # or if the user is simply expressing frustration/stress without action-oriented inquiry.
    action_inquiry_cues = [
        "start karu", "kahan se start", "where to start", "where do i start",
        "submit hone hain", "submit hain", "submit hona hai"
    ]
    has_action_inquiry = any(k in msg_lower for k in action_inquiry_cues)
    is_reflective_strategy = strategy in ("REFLECTIVE_LISTENING", "COPING_SUPPORT", "VALIDATION")

    if has_practical_context and not is_reflective_strategy and (
        strategy == "PROBLEM_SOLVING" or
        has_action_inquiry or
        (need == "problem_solving" and intent != "humorous_complaint")
    ):
        return (
            "problem_solve",
            True,
            "CLEAR_PRACTICAL_PROBLEM: User presented concrete logistical/academic problem needing structural breakdown."
        )

    # 5. EMOTIONAL NEED / UNDERLYING NEED vs 6. AMBIGUITY / LOW CONFIDENCE
    confidence = emotional_state.get("confidence_level", emotional_state.get("confidence", "medium"))
    tokens = [t for t in re.findall(r'[a-zA-Z]+', msg_lower)]
    if confidence == "low" or (len(tokens) <= 3 and not has_practical_context and need not in ("problem_solving", "coping_tool", "venting", "reassurance")):
        return (
            "clarify_first",
            False,
            "AMBIGUOUS_LOW_CONFIDENCE: Context is ambiguous or minimal; clarify before making assumptions or offering solutions."
        )

    # Default for emotional expression / venting
    return (
        "listen_first",
        False,
        "LISTEN_FIRST: User is venting or expressing emotional state; listen and validate without unsolicited advice."
    )


def get_advice_instruction(
    advice_mode: str,
    language: str = "hinglish_latin"
) -> str:
    """
    Generate prompt directives for Advice Gating to enforce Listen-First behavior.
    """
    if advice_mode == "listen_first":
        lang_note = ""
        if language == "hinglish_latin":
            lang_note = (
                "\n- Hinglish Register: In your reflection and closing question, NEVER use formal 'aap/aapko/aapke/dekhiye'. "
                "Speak naturally as a college friend ('Haan yaar', 'Main sun raha hoon', 'Kaisa lag raha hai?')."
            )
        return (
            "ADVICE GATING: LISTEN FIRST (NO UNSOLICITED ADVICE)\n"
            "- The student is venting, expressing feelings, or sharing emotional vulnerability. They did NOT ask for advice.\n"
            "- DO NOT give unsolicited advice, solutions, schedules, habit suggestions, or multi-step lists.\n"
            "- NEVER say things like: 'Try meditating, journaling, making a timetable, drinking water...'\n"
            "- Acknowledge and reflect their experience warmly like a supportive friend who simply understands.\n"
            "- Ask at most ONE natural, gentle follow-up question if appropriate."
            f"{lang_note}"
        )
    elif advice_mode == "clarify_first":
        return (
            "ADVICE GATING: CLARIFY FIRST (NO PREMATURE ADVICE OR ASSUMPTIONS)\n"
            "- The student's message is ambiguous, brief, or has minimal context.\n"
            "- DO NOT assume their emotional condition, diagnose their mood, or offer unsolicited advice.\n"
            "- DO NOT dump generic wellness tips or action lists.\n"
            "- Keep the response brief, warm, and open.\n"
            "- Ask at most ONE gentle clarification question to invite them to share more."
        )
    elif advice_mode == "problem_solve":
        lang_note = ""
        if language == "hinglish_latin":
            lang_note = (
                "\n- Hinglish Register: Use peer pronouns 'tum/tumhein/tumhare'. "
                "NEVER use formal honorifics 'aap/aapko/aapke' even when giving concrete task steps."
            )
        return (
            "ADVICE GATING: PROBLEM SOLVING (ACTIONABLE & CONCISE)\n"
            "- The student is facing a clear, practical problem that needs concrete structure.\n"
            "- Help break the immediate workload into the smallest manageable first step (e.g. prioritize by nearest deadline).\n"
            "- Keep suggestions concise, realistic, and focused (1 concrete next step only, no long lists).\n"
            "- Balance practical help with a supportive, grounded peer tone.\n"
            "- Ask at most ONE check-in question."
            f"{lang_note}"
        )
    elif advice_mode == "explicit_advice":
        lang_note = ""
        if language == "hinglish_latin":
            lang_note = (
                "\n- Hinglish Register: Use peer pronouns 'tum/tumhein/tumhare'. "
                "NEVER use formal honorifics 'aap/aapko/aapke' even when giving direct advice."
            )
        return (
            "ADVICE GATING: EXPLICIT ADVICE (REQUESTED BY USER)\n"
            "- The student explicitly asked for guidance, advice, or suggestions on what to do.\n"
            "- Provide direct, practical, and realistic advice tailored to a college student.\n"
            "- Keep it concise: offer 1-2 focused, high-leverage steps rather than an overwhelming list or generic lecture.\n"
            "- Avoid scripted therapy-speak; speak like a grounded, helpful senior or peer.\n"
            "- Ask at most ONE gentle follow-up question."
            f"{lang_note}"
        )
    elif advice_mode == "crisis_support":
        return (
            "ADVICE GATING: CRISIS SUPPORT (ABSOLUTE SAFETY)\n"
            "- High distress or crisis state active.\n"
            "- All routine problem-solving advice, productivity tips, and coping techniques are strictly suppressed.\n"
            "- Prioritize calm warmth, immediate emotional presence, and direct referral to professional helplines."
        )
    elif advice_mode == "informational":
        return (
            "ADVICE GATING: INFORMATIONAL (FACTUAL INSTITUTIONAL QUERY)\n"
            "- The student is asking a factual campus or institutional question.\n"
            "- Answer directly, accurately, and concisely using the verified facts provided.\n"
            "- DO NOT provide unsolicited life advice, emotional counseling, or wellness tips.\n"
            "- DO NOT force emotional reflection or unnecessary therapeutic validation."
        )
    else:
        return (
            "ADVICE GATING: LISTEN FIRST\n"
            "- Validate first; do not provide unsolicited advice."
        )


# -------------------------------------------------------------------
# Personality Engine v1 Step 4: Multi-Turn Continuity & Depth Layer
# -------------------------------------------------------------------

REFERENCE_PHRASES = {
    "haan wahi", "han wahi", "ha wahi", "haan yar", "haan yaar", "wahi",
    "wahi toh", "wahi to", "sahi bola", "sahi baat hai", "sahi kaha",
    "exactly", "true", "same here", "uske baad", "phir wohi hua", "fir wahi hua",
    "yehi problem hai", "yahi problem hai", "ab kya karu", "ab kya karoon",
    "kya karu ab", "yehi toh", "yahi toh"
}

REFERENCE_PATTERNS = [
    r"^(?:haan|ha|han)?\s*(?:wahi|wohi)(?:\s+(?:yaar|yar|bhai|toh|to))?[.!?]*$",
    r"^(?:exactly|true|same\s+here|sahi\s+(?:bola|kaha|baat\s+hai))[.!?]*$",
    r"\buske\s+baad\b",
    r"\b(?:phir|fir)\s+(?:wohi|wahi)\s+hua\b",
    r"\b(?:yehi|yahi)\s+problem\s+hai\b",
    r"\bab\s+kya\s+(?:karu|karoon|karein)\b",
]


def is_reference_phrase(text: str) -> bool:
    """
    Detect short context-dependent messages, affirmations, or anaphoric phrases
    that rely on immediate conversational context (e.g. 'haan wahi', 'exactly').
    """
    if not text or not text.strip():
        return False
    t_lower = text.strip().lower()
    if t_lower in REFERENCE_PHRASES:
        return True
    return any(re.search(pat, t_lower) for pat in REFERENCE_PATTERNS)


TOPIC_SHIFT_MARKERS = [
    r"\bwaise\b",
    r"\bby\s+the\s+way\b",
    r"\bbtw\b",
    r"\banyway\b",
    r"\bchhoro\b",
    r"\bchhod\b",
    r"\bek\s+aur\s+baat\b",
    r"\bleave\s+it\b",
]


def has_topic_shift_marker(text: str) -> tuple[bool, str]:
    """
    Check if the user uses a conversational pivot/transition marker.
    Returns: (has_marker: bool, matched_marker: str)
    """
    if not text or not text.strip():
        return False, ""
    t_lower = text.strip().lower()
    for pat in TOPIC_SHIFT_MARKERS:
        m = re.search(pat, t_lower)
        if m:
            return True, m.group(0)
    return False, ""


DOMAIN_KEYWORDS = {
    "academic": {
        "exam", "exams", "test", "tests", "quiz", "syllabus", "study", "studying", "padh", "padhai",
        "assignment", "assignments", "submission", "submit", "deadline", "marks", "grade", "cgpa",
        "professor", "faculty", "lecture", "class", "classes", "attendance", "admit", "card"
    },
    "campus_life": {
        "hostel", "room", "roommate", "wifi", "internet", "mess", "food", "canteen", "warden",
        "laundry", "gate", "pass", "water", "electricity", "gym", "block"
    },
    "social": {
        "friend", "friends", "dost", "group", "groups", "lonely", "alone", "talk", "baat",
        "ignore", "left out", "isolating", "isolated", "isolation", "relationship", "crush", "breakup"
    },
    "entertainment": {
        "cricket", "match", "movie", "series", "game", "gaming", "instagram", "reels", "youtube"
    }
}


def detect_domain(text: str) -> str:
    """Extract primary topical domain from text keywords by max overlap."""
    if not text:
        return "general"
    tokens = set(re.findall(r'[a-zA-Z]+', text.lower()))
    best_domain = "general"
    max_matches = 0
    for domain, kws in DOMAIN_KEYWORDS.items():
        matches = len(tokens & kws)
        if matches > max_matches:
            max_matches = matches
            best_domain = domain
    return best_domain


def detect_topic_shift_heuristic(message: str, history: list) -> bool:
    """
    Determine if the message represents a genuine topic shift.
    Rule: A marker alone (e.g. 'waise') must NEVER automatically mean topic shift.
    Combine marker detection with semantic/context evidence:
    - It is a shift ONLY IF a topic-shift marker is present AND the domain or subject pivots away from recent user context.
    Example:
      Previous: 'Kal exam hai', Current: 'Waise exam kal subah 9 baje hai' -> NOT a shift (same domain).
      Previous: 'Kal exam hai', Current: 'Waise hostel ka WiFi phir down hai' -> IS a shift.
    """
    if not history or not message:
        return False

    has_marker, marker_text = has_topic_shift_marker(message)
    if not has_marker:
        return False

    # Strong reset markers (e.g. 'chhoro', 'chhod', 'leave it', 'ek aur baat') always indicate a pivot
    reset_markers = {"chhoro", "chhod", "leave it", "ek aur baat"}
    if marker_text.lower() in reset_markers:
        return True

    current_domain = detect_domain(message)

    # Extract previous user turns
    user_turns = []
    for turn in history:
        role = getattr(turn, "role", None) or (turn.get("role") if isinstance(turn, dict) else "")
        content = getattr(turn, "content", None) or (turn.get("content") if isinstance(turn, dict) else "")
        if role == "user" and content:
            user_turns.append(content)

    if not user_turns:
        return False

    last_user_text = user_turns[-1]
    last_domain = detect_domain(last_user_text)

    # If both domains are recognized and identical -> continuation (e.g. 'waise exam kal subah hai')
    if current_domain != "general" and last_domain != "general" and current_domain == last_domain:
        return False

    # Check keyword overlap between message and recent turns
    prev_tokens = set(re.findall(r'[a-zA-Z]+', " ".join(user_turns[-2:]).lower()))
    curr_tokens = set(re.findall(r'[a-zA-Z]+', message.lower()))
    stop_words = {"waise", "by", "the", "way", "btw", "anyway", "hai", "ka", "ki", "ko", "se", "aur", "is", "a", "an", "to", "bhi", "yeh", "woh", "phir", "fir"}
    overlap = (prev_tokens & curr_tokens) - stop_words

    # If domain clearly changed, or there is no significant topical keyword overlap
    if current_domain != "general" and last_domain != "general" and current_domain != last_domain:
        return True

    if not overlap:
        return True

    return False


def determine_context_continuity(
    message: str,
    history: list,
    emotional_state: dict[str, Any] = None
) -> tuple[str, str, str]:
    """
    Determine context continuity, context confidence, and resolved referent.
    Returns:
      (context_continuity: "continuation" | "topic_shift" | "isolated",
       context_confidence: "high" | "medium" | "low",
       resolved_reference: str)
    """
    if not history:
        return ("isolated", "medium", "")

    # Check for genuine topic shift first
    if detect_topic_shift_heuristic(message, history):
        return ("topic_shift", "high", "")

    msg_lower = message.strip().lower() if message else ""

    # Check for short reference / affirmative phrases
    if is_reference_phrase(message):
        last_turn = history[-1]
        last_role = getattr(last_turn, "role", None) or (last_turn.get("role") if isinstance(last_turn, dict) else "")
        last_content = getattr(last_turn, "content", None) or (last_turn.get("content") if isinstance(last_turn, dict) else "")

        if last_content:
            clean_ref = last_content.strip()
            if len(clean_ref) > 100:
                clean_ref = clean_ref[:97] + "..."
            return ("continuation", "high", clean_ref)

        return ("continuation", "medium", "")

    # Ambiguous short reply with multiple possible referents or minimal context
    tokens = [t for t in re.findall(r'[a-zA-Z]+', msg_lower)]
    domain_cues = ["exam", "assignment", "padh", "stress", "hostel", "wifi", "marks", "deadline"]
    if len(tokens) <= 3 and not any(s in msg_lower for s in domain_cues):
        user_turns = [
            getattr(t, "content", None) or (t.get("content") if isinstance(t, dict) else "")
            for t in history if (getattr(t, "role", None) or (t.get("role") if isinstance(t, dict) else "")) == "user"
        ]
        # If previous history spans multiple distinct domains, flag low confidence / multiple referents
        if len(user_turns) >= 2 and detect_domain(user_turns[-1]) != detect_domain(user_turns[-2]):
            return ("continuation", "low", "multiple_possible_referents")
        return ("continuation", "medium" if len(user_turns) >= 1 else "low", "")

    return ("continuation", "high", "")


def get_continuity_instruction(
    continuity: str,
    confidence: str,
    language: str = "hinglish_latin",
    resolved_reference: str = ""
) -> str:
    """
    Generate prompt directives for Conversational Depth and Context Continuity.
    Enforces anti-hallucination, clean topic-shifting, and the one-question maximum.
    """
    directives = []

    if continuity == "topic_shift":
        directives.append(
            "CONTINUITY GUIDANCE: TOPIC SHIFT DETECTED\n"
            "- The student has shifted to a new topic.\n"
            "- Cleanly drop the previous emotional and topical anchor.\n"
            "- Respond directly to the new topic; DO NOT drag in or re-mention previous topics unless the student brings them up again."
        )
    elif continuity == "continuation":
        if confidence == "high":
            ref_note = f" (Referent: '{resolved_reference}')" if resolved_reference else ""
            directives.append(
                f"CONTINUITY GUIDANCE: CLEAR CONTINUATION{ref_note}\n"
                "- The student is actively continuing the ongoing discussion.\n"
                "- Maintain the established context naturally like a peer who remembers what was just said.\n"
                "- Do NOT re-summarize the conversation from the beginning or state obvious facts."
            )
        elif confidence == "low":
            directives.append(
                "CONTINUITY GUIDANCE: LOW CONTEXT CONFIDENCE (NATURAL CLARIFICATION)\n"
                "- The student's message or reference is ambiguous or could relate to multiple topics.\n"
                "- Clarify gently and naturally without assuming internal facts.\n"
                "- Examples in Hinglish: 'Agar tu pichli wali baat kar raha hai...', 'Tu usi topic ki baat kar raha hai na?'\n"
                "- Examples in English: 'Just to make sure I am following, are you talking about...?'\n"
                "- NEVER use robotic phrases like: 'I require further context', 'My memory indicates', or 'As an AI'."
            )

    directives.append(
        "ANTI-HALLUCINATION & CONVERSATIONAL CONSTRAINTS:\n"
        "- NEVER invent names of friends, professors, course codes, deadlines, or events not present in the conversation history.\n"
        "- Do NOT assume or manufacture facts or emotional traumas the student hasn't shared.\n"
        "- Maintain at most ONE natural, gentle follow-up question in the entire response."
    )

    return "\n\n".join(directives)


