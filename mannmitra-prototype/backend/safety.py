# safety.py
# A simple, transparent first pass at detecting crisis-level language.
# This is intentionally rule-based (keyword matching) for the prototype stage.
# In the full version, this gets combined with the ML model's output for a
# more reliable signal - but a clear, auditable rule-based layer like this
# should always stay in place as a fast, explainable safety net.

HIGH_RISK_PHRASES = [
    "kill myself", "end my life", "suicide", "want to die", "ending it",
    "no reason to live", "better off dead", "hurt myself", "self harm",
    "self-harm", "can't go on", "cant go on",
]

MODERATE_RISK_PHRASES = [
    "hopeless", "worthless", "can't cope", "cant cope", "breaking down",
    "give up", "so tired of everything", "nobody would care", "panic attack",
    "can't sleep", "cant sleep", "overwhelmed",
]

HELPLINES = [
    {"name": "KIRAN Mental Health Helpline (India)", "number": "1800-599-0019"},
    {"name": "Vandrevala Foundation Helpline", "number": "1860-2662-345"},
    {"name": "iCall (TISS)", "number": "9152987821"},
]


def assess_risk(message: str) -> dict:
    """Returns a risk tier and, if relevant, helpline info to surface."""
    text = message.lower()

    for phrase in HIGH_RISK_PHRASES:
        if phrase in text:
            return {
                "risk_level": "high",
                "helplines": HELPLINES,
                "note": "Crisis language detected. Helpline info should be shown immediately.",
            }

    for phrase in MODERATE_RISK_PHRASES:
        if phrase in text:
            return {
                "risk_level": "moderate",
                "helplines": [],
                "note": "Elevated distress language detected. Consider gently suggesting the Wellbeing division.",
            }

    return {"risk_level": "low", "helplines": [], "note": None}
