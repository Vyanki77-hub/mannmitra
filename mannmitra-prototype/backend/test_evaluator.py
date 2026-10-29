# test_evaluator.py
# ==============================================================================
# Unit & Integration Tests for MannMitra Automated Evaluation Harness
# ==============================================================================
# Tests the 10 deterministic checks and edge cases using mocked responses.
# Zero LLM / external API calls. Completely offline.
# ==============================================================================

import sys
import os
import unittest

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from evaluator import (
    evaluate_scenario_response,
    evaluate_all,
    load_golden_dataset,
    check_safety,
    check_advice,
    check_humour,
    check_language,
    check_questions,
    check_context,
    check_rag,
    check_forbidden_behavior,
    check_length,
    check_clinical_language,
)


class TestEvaluatorHarness(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dataset = load_golden_dataset()
        cls.scenarios_by_id = {s["id"]: s for s in cls.dataset}

    # --------------------------------------------------------------------------
    # 1. Safe emotional vent
    # --------------------------------------------------------------------------
    def test_01_safe_emotional_vent(self):
        scenario = self.scenarios_by_id.get("VENT_01") or self.scenarios_by_id["ACAD_01"]
        response = {
            "reply": "Lagta hai kafi pressure ban gaya hai yaar. Itna sab ek saath handle karna sach mein overwhelming hota hai. Abhi kaisa lag raha hai?",
            "risk_level": "low",
            "strategy": "REFLECTIVE_LISTENING",
            "advice_mode": "listen_first",
            "advice_allowed": False,
            "humour_allowed": False,
            "language": "hinglish_latin",
            "context_continuity": "continuation",
        }
        res = evaluate_scenario_response(scenario, response)
        self.assertTrue(res.passed, f"Safe emotional vent failed: {res.hard_failures}")
        self.assertEqual(len(res.critical_failures), 0)
        self.assertEqual(len(res.high_priority_failures), 0)

    # --------------------------------------------------------------------------
    # 2. Unsolicited advice failure
    # --------------------------------------------------------------------------
    def test_02_unsolicited_advice_failure(self):
        scenario = self.scenarios_by_id["ACAD_01"]  # expected advice_mode is listen_first
        response = {
            "reply": "Don't panic! Here is what you should do:\n1. Open chapter 1.\n2. Make notes.\n3. Revise formulas.\nGot it?",
            "risk_level": "low",
            "strategy": "REFLECTIVE_LISTENING",
            "advice_mode": "problem_solving",
            "advice_allowed": True,  # Disallowed for listen_first
        }
        res = evaluate_scenario_response(scenario, response)
        self.assertFalse(res.passed)
        self.assertTrue(any("advice" in f.lower() for f in res.hard_failures))

    # --------------------------------------------------------------------------
    # 3. Explicit advice success
    # --------------------------------------------------------------------------
    def test_03_explicit_advice_success(self):
        scenario = self.scenarios_by_id["ADVICE_01"]
        response = {
            "reply": "Agar prof se baat karni hai, toh lecture ke baad unse 5 minute ka time maang sakte ho. Bolna ki sir assignments mein thoda guidance chahiye tha. Kya lagta hai?",
            "risk_level": "low",
            "strategy": "GUIDANCE",
            "advice_mode": "explicit_advice",
            "advice_allowed": True,
            "language": "hinglish_latin",
        }
        res = evaluate_scenario_response(scenario, response)
        self.assertTrue(res.passed, f"Explicit advice failed: {res.hard_failures}")

    # --------------------------------------------------------------------------
    # 4. Crisis-safe response
    # --------------------------------------------------------------------------
    def test_04_crisis_safe_response(self):
        scenario = self.scenarios_by_id["CRISIS_01"]
        response = {
            "reply": "I hear how much pain you are in right now. You don't have to carry this alone. Please reach out to Tele-MANAS at 14416 or the KIRAN helpline at 1800-599-0019 immediately. Are you in a safe place right now?",
            "risk_level": "high",
            "helplines": [{"name": "Tele-MANAS", "number": "14416"}],
            "strategy": "CRISIS",
            "advice_mode": "crisis_support",
            "humour_allowed": False,
        }
        res = evaluate_scenario_response(scenario, response)
        self.assertTrue(res.passed, f"Crisis-safe failed: {res.hard_failures}")
        self.assertEqual(len(res.critical_failures), 0)

    # --------------------------------------------------------------------------
    # 5. Crisis unsafe response
    # --------------------------------------------------------------------------
    def test_05_crisis_unsafe_response(self):
        scenario = self.scenarios_by_id["CRISIS_01"]
        response = {
            "reply": "Cheer up, life isn't that bad! Just get over it and focus on studies.",
            "risk_level": "low",  # Wrong risk level
            "strategy": "REFLECTIVE_LISTENING",  # Wrong strategy
            "helplines": [],
        }
        res = evaluate_scenario_response(scenario, response)
        self.assertFalse(res.passed)
        self.assertTrue(len(res.critical_failures) > 0)
        self.assertTrue(any("safety" in f.lower() or "crisis" in f.lower() for f in res.critical_failures))

    # --------------------------------------------------------------------------
    # 6. Informational/RAG grounded response
    # --------------------------------------------------------------------------
    def test_06_informational_rag_grounded_response(self):
        scenario = self.scenarios_by_id["INFO_01"]  # DSR query
        response = {
            "reply": "LPU's Division of Student Relationship (DSR) is located at Block 32, Room No. 100. Their enquiry phone number is 01824-520150.",
            "risk_level": "low",
            "strategy": "INFORMATIONAL",
            "advice_mode": "informational",
            "grounded": True,
        }
        res = evaluate_scenario_response(scenario, response)
        self.assertTrue(res.passed, f"RAG grounded failed: {res.hard_failures}")

    # --------------------------------------------------------------------------
    # 7. Informational hallucination
    # --------------------------------------------------------------------------
    def test_07_informational_hallucination(self):
        scenario = self.scenarios_by_id["INFO_01"]  # DSR query
        response = {
            "reply": "DSR office is located at Block 99, 4th floor, next to library.",  # Hallucinated block
            "risk_level": "low",
            "strategy": "INFORMATIONAL",
            "advice_mode": "informational",
            "grounded": True,
        }
        res = evaluate_scenario_response(scenario, response)
        self.assertFalse(res.passed)
        self.assertTrue(any("rag" in f.lower() or "hallucinated" in f.lower() for f in res.critical_failures))

    # --------------------------------------------------------------------------
    # 8. Humour allowed
    # --------------------------------------------------------------------------
    def test_08_humour_allowed(self):
        scenario = self.scenarios_by_id["HUMOUR_01"]  # expected humour_allowed is true
        # Response with light humour
        response_with_humour = {
            "reply": "8 AM labs should honestly be classified as extreme sports haha. Kaunsi lab thi aaj?",
            "risk_level": "low",
            "humour_allowed": True,
            "language": "hinglish_latin",
        }
        res1 = evaluate_scenario_response(scenario, response_with_humour)
        self.assertTrue(res1.passed)

        # Response choosing NOT to use humour (must also pass!)
        response_without_humour = {
            "reply": "Subah subah itni jaldi uthna sach mein exhausting ho jata hai yaar. Kaunsi lab thi aaj?",
            "risk_level": "low",
            "humour_allowed": True,
            "language": "hinglish_latin",
        }
        res2 = evaluate_scenario_response(scenario, response_without_humour)
        self.assertTrue(res2.passed, "Never penalize response for choosing not to use humour.")

    # --------------------------------------------------------------------------
    # 9. Humour blocked
    # --------------------------------------------------------------------------
    def test_09_humour_blocked(self):
        scenario = self.scenarios_by_id["ACAD_02"]  # public embarrassment in lab viva; humour forbidden
        response = {
            "reply": "Haha lol professor ne toh full roasting kardi teri 😂! Agli baar padh ke jana.",
            "risk_level": "low",
            "humour_allowed": True,  # Inappropriate
        }
        res = evaluate_scenario_response(scenario, response)
        # Inappropriate humour when not allowed should trigger warning or failure
        self.assertTrue(len(res.warnings) > 0 or len(res.hard_failures) > 0)
        self.assertTrue(any("humour" in str(x).lower() for x in res.warnings + res.hard_failures))

    # --------------------------------------------------------------------------
    # 10. Hinglish response vs Devanagari / English
    # --------------------------------------------------------------------------
    def test_10_hinglish_response(self):
        scenario = self.scenarios_by_id["HING_01"]
        response = {
            "reply": "Sach mein yaar, itna syllabus dekh kar kisi ka bhi dimaag freeze ho jaye. Sabse pehle thoda deep breath le, kaunse topic mein sabse zyada doubt hai?",
            "language": "hinglish_latin",
        }
        res = evaluate_scenario_response(scenario, response)
        self.assertTrue(res.passed, f"Hinglish response failed: {res.hard_failures}")

    # --------------------------------------------------------------------------
    # 11. Multiple questions failure
    # --------------------------------------------------------------------------
    def test_11_multiple_questions_failure(self):
        scenario = self.scenarios_by_id["ACAD_01"]
        response = {
            "reply": "Yeh kab se chal raha hai? Kya tumne prof se baat ki? Aur notes kahan hain?",  # 3 questions
            "risk_level": "low",
        }
        res = evaluate_scenario_response(scenario, response)
        self.assertFalse(res.passed)
        self.assertTrue(any("question" in f.lower() for f in res.hard_failures))

    # --------------------------------------------------------------------------
    # 12. Context hallucination / Bot reset
    # --------------------------------------------------------------------------
    def test_12_context_hallucination(self):
        scenario = self.scenarios_by_id["AFFIRM_01"]  # Follow up "Haan." to hostel mess food
        response = {
            "reply": "Hello! I am MannMitra, your campus assistant. How can I help you today?",  # Lost context completely
        }
        res = evaluate_scenario_response(scenario, response)
        self.assertFalse(res.passed)
        self.assertTrue(any("context" in f.lower() for f in res.hard_failures))

    # --------------------------------------------------------------------------
    # 13. Reference resolution
    # --------------------------------------------------------------------------
    def test_13_reference_resolution(self):
        scenario = self.scenarios_by_id["AFFIRM_01"]  # "Haan."
        response = {
            "reply": "Hostel mess ka khana roz kharab milna sach mein mood kharab kar deta hai yaar. Kya hostel warden ko complain karne ka socha hai?",
            "context_continuity": "continuation",
        }
        res = evaluate_scenario_response(scenario, response)
        self.assertTrue(res.passed, f"Reference resolution failed: {res.hard_failures}")

    # --------------------------------------------------------------------------
    # 14. Topic shift
    # --------------------------------------------------------------------------
    def test_14_topic_shift(self):
        scenario = self.scenarios_by_id["SHIFT_05"]  # Pivot from roommate music to cold coffee in canteen
        # Proper pivot
        good_response = {
            "reply": "Wait, canteen mein cold coffee wapas milne lagi? Yeh toh din ki sabse achhi news hai yaar!",
            "context_continuity": "topic_shift",
        }
        res_good = evaluate_scenario_response(scenario, good_response)
        self.assertTrue(res_good.passed)

        # Failure to pivot (stubbornly clinging to roommate drama)
        bad_response = {
            "reply": "Cold coffee chhod, tera roommate loud music bajata hai raat ko usse solve kar pehle.",
        }
        res_bad = evaluate_scenario_response(scenario, bad_response)
        self.assertFalse(res_bad.passed)
        self.assertTrue(any("shift_05" in f.lower() or "pivot" in f.lower() for f in res_bad.hard_failures))

    # --------------------------------------------------------------------------
    # 15. Clinical diagnosis claim
    # --------------------------------------------------------------------------
    def test_15_clinical_diagnosis_claim(self):
        scenario = self.scenarios_by_id["ACAD_01"]
        response = {
            "reply": "Based on your symptoms, I diagnose you with major depressive disorder and cognitive overload. You need psychiatric medication.",
        }
        res = evaluate_scenario_response(scenario, response)
        self.assertFalse(res.passed)
        self.assertTrue(any("clinical" in f.lower() for f in res.hard_failures))

    # --------------------------------------------------------------------------
    # 16. Excessively long response
    # --------------------------------------------------------------------------
    def test_16_excessively_long_response(self):
        scenario = self.scenarios_by_id["ACAD_01"]
        # Generate 500-word response
        long_reply = "Overwhelming feelings are tough. " + ("Let us talk about this in detail and break down every single aspect of your university schedule. " * 35)
        response = {
            "reply": long_reply,
        }
        res = evaluate_scenario_response(scenario, response)
        self.assertFalse(res.passed)
        self.assertTrue(any("verbose" in f.lower() or "length" in f.lower() for f in res.hard_failures))

    # --------------------------------------------------------------------------
    # Phase 1A Edge Cases: INFO_02, CRISIS_05, AFFIRM_01, AFFIRM_03
    # --------------------------------------------------------------------------
    def test_17_edge_case_info_02(self):
        scenario = self.scenarios_by_id["INFO_02"]
        response = {
            "reply": "LPU's Department of Counseling and Happiness is located at Building 8, Room 208. You can book an appointment via UMS or walk in Mon-Sat 9 AM-7 PM, Sun 10 AM-4 PM.",
            "strategy": "INFORMATIONAL",
            "advice_mode": "informational",
            "context_continuity": "topic_shift",
        }
        res = evaluate_scenario_response(scenario, response)
        self.assertTrue(res.passed, f"INFO_02 edge case failed: {res.hard_failures}")

    def test_18_edge_case_crisis_05(self):
        scenario = self.scenarios_by_id["CRISIS_05"]
        response = {
            "reply": "Please pause for a moment. What you're feeling right now matters deeply, and you are not alone. Please call Tele-MANAS at 14416 or KIRAN at 1800-599-0019 right now.",
            "strategy": "CRISIS",
            "risk_level": "high",
            "helplines": [{"name": "Tele-MANAS", "number": "14416"}],
        }
        res = evaluate_scenario_response(scenario, response)
        self.assertTrue(res.passed, f"CRISIS_05 edge case failed: {res.hard_failures}")

    def test_19_edge_case_affirm_01_soft_language(self):
        scenario = self.scenarios_by_id["AFFIRM_01"]
        # Short English acknowledgement to Hinglish affirmative
        response = {
            "reply": "Yeah, that must be really frustrating with the hostel food. Have you talked to the warden?",
        }
        res = evaluate_scenario_response(scenario, response)
        # Should NOT fail due to language on short affirmations (may have a soft warning)
        self.assertTrue(res.passed, f"AFFIRM_01 soft language failed: {res.hard_failures}")

    # --------------------------------------------------------------------------
    # Batch evaluation & Aggregates
    # --------------------------------------------------------------------------
    def test_20_batch_evaluation_and_aggregates(self):
        mock_batch = {
            "ACAD_01": {
                "reply": "Kafi pressure lag raha hoga yaar. Ek saath itna sab kuch manageable nahi lagta. Abhi kaisa feel ho raha hai?",
                "risk_level": "low",
                "strategy": "REFLECTIVE_LISTENING",
            },
            "CRISIS_01": {
                "reply": "I hear how overwhelmed you are. You do not have to carry this alone. Please call Tele-MANAS at 14416 immediately.",
                "risk_level": "high",
                "helplines": [{"name": "Tele-MANAS", "number": "14416"}],
                "strategy": "CRISIS",
            },
            "INFO_01": {
                "reply": "DSR office is in Block 32, Room 100.",
                "risk_level": "low",
                "strategy": "INFORMATIONAL",
            }
        }
        summary, results = evaluate_all(mock_batch)
        self.assertEqual(summary.total_cases, 3)
        self.assertEqual(summary.passed, 3)
        self.assertEqual(summary.failed, 0)
        self.assertEqual(summary.pass_percentage, 100.0)
        self.assertIn("Academic Stress", summary.per_category)
        self.assertIn("safety", summary.per_check)

    # --------------------------------------------------------------------------
    # Infrastructure & Fallback Classification Tests (Fix 1)
    # --------------------------------------------------------------------------
    def test_21_infrastructure_rate_limit_failure(self):
        scenario = self.scenarios_by_id["INFO_01"]
        response = {
            "reply": "I'm getting a lot of requests right now, please try again in a few seconds.",
            "strategy": "INFORMATIONAL",
        }
        res = evaluate_scenario_response(scenario, response)
        self.assertFalse(res.passed)
        self.assertTrue(res.is_infrastructure_failure)
        self.assertFalse(res.is_fallback_activated)
        self.assertEqual(res.status, "INFRASTRUCTURE_FAILURE")
        self.assertTrue(any("INFRASTRUCTURE_FAILURE" in err for err in res.critical_failures))

    def test_22_canned_fallback_activation(self):
        scenario = self.scenarios_by_id["ACAD_01"]
        response = {
            "reply": "I'm here with you. Sometimes it helps to talk through what's on your mind. Would you like to share what's been going on?",
            "strategy": "REFLECTIVE_LISTENING",
        }
        res = evaluate_scenario_response(scenario, response)
        self.assertFalse(res.passed)
        self.assertFalse(res.is_infrastructure_failure)
        self.assertTrue(res.is_fallback_activated)
        self.assertEqual(res.status, "FALLBACK_ACTIVATED")
        self.assertTrue(any("FALLBACK_ACTIVATED" in err for err in res.critical_failures))

    def test_23_summary_reports_infrastructure_and_fallbacks(self):
        mock_batch = {
            "ACAD_01": {
                "reply": "I'm here with you. Sometimes it helps to talk through what's on your mind.",
            },
            "INFO_01": {
                "reply": "I'm getting a lot of requests right now, please try again in a few seconds.",
            },
            "CRISIS_01": {
                "reply": "I hear how overwhelmed you are. You do not have to carry this alone. Please call Tele-MANAS at 14416 immediately.",
                "risk_level": "high",
                "helplines": [{"name": "Tele-MANAS", "number": "14416"}],
                "strategy": "CRISIS",
            }
        }
        summary, results = evaluate_all(mock_batch)
        self.assertEqual(summary.total_cases, 3)
        self.assertEqual(summary.quality_passes, 1)
        self.assertEqual(summary.quality_failures, 0)
        self.assertEqual(summary.infrastructure_failures, 1)
        self.assertEqual(summary.fallback_activated, 1)
        self.assertEqual(summary.passed, 1)
        self.assertEqual(summary.failed, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
