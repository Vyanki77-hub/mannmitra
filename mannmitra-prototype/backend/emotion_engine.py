# emotion_engine.py
# Lightweight emotional state classification layer for MannMitra.
# Runs before the main conversational reply to adapt support strategy.

import os
import json
from typing import Any

from groq import Groq, RateLimitError
from dotenv import load_dotenv

# Initialize Groq client (avoiding circular import with main.py)
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is missing. Please add it to backend/.env")
client = Groq(api_key=GROQ_API_KEY)

# Reuse the same CASUAL_MESSAGES set from rag.py
CASUAL_MESSAGES = {
    "hi", "hii", "hiii", "hello", "hey", "heya", "yo",
    "how are you", "good morning", "good night", "good afternoon",
    "thanks", "thank you", "ok", "okay", "bye", "goodbye", "cool", "nice",
    "i'm bored", "im bored", "tell me something interesting",
}


def analyze_emotional_state(message: str, history: list) -> dict[str, Any]:
    """
    Classify the emotional state of a user message.

    Returns a dict with:
        emotion: str - the primary emotion detected
        intensity: int - 1-10 scale
        context: str - academic, social, family, self_esteem, general, casual
        need: str - reassurance, problem_solving, venting, coping_tool, grounding, casual_chat
        conversation_mode: str - determines response strategy
    """
    # FIX 1: Skip classification for casual/short messages
    msg_lower = message.strip().lower()
    if len(msg_lower.split()) <= 2 or msg_lower in CASUAL_MESSAGES:
        return {
            "emotion": "neutral",
            "intensity": 3,
            "context": "general",
            "need": "casual_chat",
            "conversation_mode": "casual"
        }

    # Classification system prompt - ONLY for classification, not conversation
    CLASSIFICATION_PROMPT = """You are an emotion classifier for a student wellbeing chatbot.

Output ONLY valid JSON with this exact schema:
{
  "emotion": "anxiety" | "sadness" | "loneliness" | "anger" |
             "frustration" | "motivation_loss" | "neutral" | "positive",
  "intensity": 1-10,
  "context": "academic" | "social" | "family" | "self_esteem" |
             "general" | "casual",
  "need": "reassurance" | "problem_solving" | "venting" |
          "coping_tool" | "grounding" | "casual_chat",
  "conversation_mode": "reflective_listening" | "coping_tool" |
                       "problem_solving" | "grounding_high_risk" | "casual"
}

Guidelines:
- anxiety: nervousness, worry, fear about upcoming events (exams, deadlines)
- sadness: feeling down, hopeless, tearful, discouraged
- loneliness: isolation, no friends, disconnected from others
- anger: frustration at unfairness, resentment, irritation
- frustration: blocked goals, obstacles, things not working
- motivation_loss: lack of energy,不愿做事情, apathy
- neutral: factual, no strong emotion, casual chat
- positive: happy, grateful, optimistic

- academic context: exams, studies, deadlines, professors, coursework
- social context: friends, relationships, belonging, loneliness
- family context: parents, home, family issues
- self_esteem context: confidence, self-worth, identity
- general context: mixed or unclear
- casual: trivial, no emotional depth

- coping_tool need: user asks for techniques, shows stress but not crisis
- problem_solving: user presents a problem to solve
- venting: user just wants to express feelings
- reassurance: user needs validation, "it's okay"
- grounding: user needs calming, present-moment focus
- casual_chat: short, no emotional depth

- conversation_mode mapping:
  * anxiety/sadness/motivation_loss -> reflective_listening or coping_tool
  * loneliness -> reflective_listening
  * anger/frustration -> problem_solving or coping_tool
  * high intensity (>7) with crisis keywords -> grounding_high_risk
  * neutral/positive/casual -> casual
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": CLASSIFICATION_PROMPT},
                {"role": "user", "content": f"Message: {message}"}
            ],
            max_completion_tokens=100,
            temperature=0.3,  # Lower temp for more consistent classification
        )

        raw_content = response.choices[0].message.content

        # Parse JSON from response
        parsed = json.loads(raw_content.strip())

        # Validate required fields
        required = ["emotion", "intensity", "context", "need", "conversation_mode"]
        for field in required:
            if field not in parsed:
                raise ValueError(f"Missing required field: {field}")

        return {
            "emotion": str(parsed["emotion"]),
            "intensity": int(parsed["intensity"]),
            "context": str(parsed["context"]),
            "need": str(parsed["need"]),
            "conversation_mode": str(parsed["conversation_mode"])
        }

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        # JSON parsing failed - return safe default
        return {
            "emotion": "neutral",
            "intensity": 3,
            "context": "general",
            "need": "casual_chat",
            "conversation_mode": "casual"
        }
    except RateLimitError:
        # Rate limit - return safe default
        return {
            "emotion": "neutral",
            "intensity": 3,
            "context": "general",
            "need": "casual_chat",
            "conversation_mode": "casual"
        }
    except Exception:
        # Any other exception - return safe default
        return {
            "emotion": "neutral",
            "intensity": 3,
            "context": "general",
            "need": "casual_chat",
            "conversation_mode": "casual"
        }


# Conversation mode to instruction mapping
CONVERSATION_MODE_INSTRUCTIONS = {
    "reflective_listening": "Focus on listening and validating the feeling first. Do not jump to solutions yet. Ask one gentle open question.",
    "coping_tool": "Gently offer one specific coping tool (like a short breathing exercise) rather than general advice.",
    "problem_solving": "Acknowledge the feeling briefly, then help break the problem into one small, concrete next step. Ask what the smallest immediate action could be.",
    "grounding_high_risk": "Respond calmly and briefly. Do not problem-solve. Prioritize connecting the student to real human support.",
    "casual": "Respond naturally and briefly, no technique needed.",
}
