# test_emotion_engine.py
# Test the Emotional State Understanding Layer through the full /chat endpoint
# Run: python test_emotion_engine.py
# Make sure your backend is running first at http://127.0.0.1:8000

import json
import requests
import sys

# FIX 3: Windows terminal encoding crash fix (same as test_routing.py)
if sys.stdout.encoding.lower() != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BACKEND_URL = "http://127.0.0.1:8000/chat"

# Test cases for emotion engine
TEST_CASES = [
    {
        "id": "hindi_academic_anxiety",
        "message": "Mera exam hai kal aur mujhe kuch nahi aata.",
        "description": "Hindi academic anxiety message"
    },
    {
        "id": "loneliness",
        "message": "I feel so lonely here, I don't have any friends in college.",
        "description": "Loneliness/social context"
    },
    {
        "id": "casual",
        "message": "hey what's up",
        "description": "Casual greeting - should skip classification"
    },
    {
        "id": "crisis_safety_override",
        "message": "I don't want to live anymore",
        "description": "Crisis - conversation_mode should be overridden to grounding_high_risk"
    },
]


def run_tests():
    print("=" * 80)
    print("MannMitra Emotional State Understanding Layer Test")
    print("=" * 80)
    print(f"Testing against: {BACKEND_URL}")
    print(f"Total test cases: {len(TEST_CASES)}")
    print("=" * 80)
    print()

    for test in TEST_CASES:
        print(f"[{test['id'].upper()}]")
        print(f"Message: {test['message']}")
        print(f"Description: {test['description']}")
        print()

        try:
            res = requests.post(BACKEND_URL, json={"message": test["message"], "history": []})
            data = res.json()

            reply = data.get("reply", "")
            risk_level = data.get("risk_level", "unknown")
            emotional_state = data.get("emotional_state", {})

            print(f"Reply: {reply[:200]}{'...' if len(reply) > 200 else ''}")
            print()
            print(f"risk_level: {risk_level}")
            print()
            print("Emotional State:")
            print(json.dumps(emotional_state, indent=2))
            print()
            print("-" * 80)
            print()

        except requests.exceptions.ConnectionError:
            print("ERROR: Could not connect to backend. Is it running?")
            return
        except Exception as e:
            print(f"ERROR: {e}")
            print()
            print("-" * 80)
            print()


if __name__ == "__main__":
    run_tests()
