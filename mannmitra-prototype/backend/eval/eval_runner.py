# eval_runner.py
# Run this against your LOCAL backend (make sure uvicorn is running first)
# to see how MannMitra handles each test case. Read the replies yourself and
# mark pass/fail - this is a manual eval, which is completely fine and
# realistic for a project at this stage. You don't need automated grading.
#
# Usage:
#   python eval_runner.py

import json
import requests

BACKEND_URL = "http://127.0.0.1:8000/chat"

with open("eval_questions.json") as f:
    questions = json.load(f)

print(f"Running {len(questions)} eval questions against {BACKEND_URL}\n")

results = []
for i, q in enumerate(questions, 1):
    try:
        res = requests.post(BACKEND_URL, json={"message": q["question"], "history": []})
        data = res.json()
        print(f"[{i}] ({q['type']}) Q: {q['question']}")
        print(f"    A: {data['reply']}")
        print(f"    risk_level: {data['risk_level']}  |  grounded: {data.get('grounded')}")
        print(f"    expected: {q['expected_answer']}")
        print()
        results.append({"question": q["question"], "type": q["type"], "reply": data["reply"]})
    except Exception as e:
        print(f"[{i}] FAILED to get response: {e}\n")

with open("eval_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("Done. Full results also saved to eval_results.json for your report.")
print("Now go through each answer above and mark it pass/fail by hand.")
