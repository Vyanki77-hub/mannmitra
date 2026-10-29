# test_baseline_runner.py
# ==============================================================================
# Offline Unit & Safety Tests for Controlled Baseline Runner (Phase 4)
# ==============================================================================
# Verifies scenario selection, category coverage, safety gates, dry-run mode,
# offline mock execution, output hygiene, and error capture.
# ZERO live API calls.
# ==============================================================================

import os
import sys
import io
import json
import unittest
import tempfile
from unittest.mock import patch

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure backend root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run_baseline import (
    SELECTED_SCENARIOS,
    SELECTED_SCENARIO_IDS,
    DEFAULT_OUTPUT_FILE,
    DEFAULT_GROQ_OUTPUT_FILE,
    DEFAULT_OLLAMA_OUTPUT_FILE,
    get_default_output_file,
    get_selected_scenarios,
    execute_baseline,
    run_pipeline_for_scenario,
)
from evaluator import load_golden_dataset
from llm_provider import get_llm_provider, GroqProvider, OllamaProvider



class TestBaselineRunner(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.all_scenarios = load_golden_dataset()
        cls.selected = get_selected_scenarios(cls.all_scenarios)

    def test_01_exactly_twenty_scenarios(self):
        """Verify that exactly 20 scenarios are selected."""
        self.assertEqual(len(SELECTED_SCENARIOS), 20)
        self.assertEqual(len(self.selected), 20)
        self.assertEqual(len(SELECTED_SCENARIO_IDS), 20)

    def test_02_all_twenty_categories_represented(self):
        """Verify that all 20 categories are covered exactly once."""
        categories = [cat for _, cat in SELECTED_SCENARIOS]
        unique_categories = set(categories)
        self.assertEqual(len(unique_categories), 20, "Every selected scenario must have a distinct category.")

        # Also verify against the actual dataset objects
        selected_cats = [sc["category"] for sc in self.selected]
        self.assertEqual(len(set(selected_cats)), 20)

    def test_03_deterministic_selection(self):
        """Verify that selection is 100% deterministic across multiple invocations."""
        run1 = [s["id"] for s in get_selected_scenarios(self.all_scenarios)]
        run2 = [s["id"] for s in get_selected_scenarios(self.all_scenarios)]
        self.assertEqual(run1, run2)
        self.assertEqual(run1, SELECTED_SCENARIO_IDS)

    def test_04_no_hundred_case_execution_path(self):
        """Verify that the runner operates only on the 20 selected scenarios."""
        # Check that SELECTED_SCENARIO_IDS length is fixed at 20
        self.assertEqual(len(SELECTED_SCENARIO_IDS), 20)
        self.assertLess(len(SELECTED_SCENARIO_IDS), len(self.all_scenarios))

    def test_05_dry_run_makes_zero_api_calls(self):
        """Verify that dry-run mode completes with zero API calls."""
        with patch("llm_provider.get_llm_provider") as mock_provider:
            result = execute_baseline(dry_run=True)
            mock_provider.assert_not_called()
            self.assertEqual(result["mode"], "dry_run")
            self.assertEqual(result["scenario_count"], 20)
            self.assertEqual(len(result["selected_ids"]), 20)

    def test_06_safety_default_refuses_live_without_flag(self):
        """Verify that execution is refused if live mode is not requested."""
        result = execute_baseline(live=False, mock=False, dry_run=False)
        self.assertEqual(result["mode"], "aborted")
        self.assertIn("Missing --live flag", result["reason"])

    def test_07_live_requires_groq_api_key(self):
        """Verify that live execution fails clearly if GROQ_API_KEY is missing."""
        with patch.dict(os.environ, {"GROQ_API_KEY": "", "LLM_PROVIDER": "groq"}):
            with self.assertRaises(EnvironmentError):
                execute_baseline(live=True, mock=False)

    def test_08_live_requires_groq_provider(self):
        """Verify that live execution fails if LLM_PROVIDER is not groq."""
        with patch.dict(os.environ, {"GROQ_API_KEY": "dummy_key", "LLM_PROVIDER": "gemini"}):
            with self.assertRaises(ValueError):
                execute_baseline(live=True, mock=False)

    def test_09_provider_resolved_through_llm_provider(self):
        """Verify that provider is obtained through llm_provider.get_llm_provider."""
        provider = get_llm_provider("groq")
        self.assertIsInstance(provider, GroqProvider)

    def test_10_mock_execution_produces_valid_structure(self):
        """Verify mock execution runs through runner and evaluator producing valid JSON."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            temp_output = tf.name

        try:
            result = execute_baseline(mock=True, delay_seconds=0.0, output_path=temp_output)
            self.assertEqual(result["scenario_count"], 20)
            self.assertEqual(len(result["results"]), 20)
            self.assertEqual(result["provider"], "groq")
            self.assertIn("summary", result)
            self.assertIn("pass_percentage", result["summary"])

            # Verify saved file
            self.assertTrue(os.path.exists(temp_output))
            with open(temp_output, "r", encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(saved["scenario_count"], 20)
            self.assertEqual(len(saved["results"]), 20)
        finally:
            if os.path.exists(temp_output):
                os.remove(temp_output)

    def test_11_no_api_keys_in_output(self):
        """Verify that no API keys or secrets are stored in output results."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            temp_output = tf.name

        try:
            result = execute_baseline(mock=True, delay_seconds=0.0, output_path=temp_output)
            raw_text = json.dumps(result)
            self.assertNotIn("gsk_", raw_text)
            self.assertNotIn("api_key", raw_text.lower())
            self.assertNotIn("bearer", raw_text.lower())
        finally:
            if os.path.exists(temp_output):
                os.remove(temp_output)

    def test_12_pipeline_error_capture(self):
        """Verify that pipeline execution errors are recorded without crashing the run."""
        def failing_pipeline(req):
            raise ConnectionError("Simulated connection timeout")

        sc = self.selected[0]
        resp, latency, err = run_pipeline_for_scenario(sc, pipeline_fn=failing_pipeline)
        self.assertIsNotNone(err)
        self.assertIn("Simulated connection timeout", err)
        self.assertEqual(resp, {})

    def test_13_ollama_live_bypasses_groq_api_key(self):
        """Verify that live execution with LLM_PROVIDER=ollama does not require GROQ_API_KEY."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            temp_output = tf.name

        try:
            with patch.dict(os.environ, {"LLM_PROVIDER": "ollama", "GROQ_API_KEY": ""}):
                with patch("run_baseline.get_llm_provider") as mock_get_provider, \
                     patch("run_baseline.run_pipeline_for_scenario") as mock_pipeline:
                    mock_llm = unittest.mock.MagicMock()
                    mock_llm.model = "llama3.2:3b"
                    mock_get_provider.return_value = mock_llm
                    mock_pipeline.return_value = (
                        {
                            "reply": "Mock reply",
                            "risk_level": "low",
                            "strategy": "REFLECTIVE_LISTENING",
                            "advice_mode": "listen_first",
                            "advice_allowed": False,
                            "humour_allowed": False,
                            "language": "hinglish_latin",
                            "context_continuity": "isolated",
                        },
                        10.0,
                        None
                    )
                    # Should execute smoothly without EnvironmentError
                    result = execute_baseline(live=True, mock=False, delay_seconds=0.0, output_path=temp_output)
                    self.assertEqual(result["provider"], "ollama")
                    self.assertEqual(result["model"], "llama3.2:3b")
                    self.assertEqual(result["scenario_count"], 20)
        finally:
            if os.path.exists(temp_output):
                os.remove(temp_output)

    def test_14_default_output_file_separation(self):
        """Verify that Groq and Ollama use strictly distinct default output file paths."""
        groq_path = get_default_output_file("groq")
        ollama_path = get_default_output_file("ollama")

        self.assertTrue(groq_path.endswith("groq_baseline_20.json"))
        self.assertTrue(ollama_path.endswith("ollama_baseline_20.json"))
        self.assertNotEqual(groq_path, ollama_path)
        self.assertEqual(DEFAULT_OUTPUT_FILE, DEFAULT_GROQ_OUTPUT_FILE)

    def test_15_provider_and_model_metadata_dynamic(self):
        """Verify that output metadata dynamically records provider and model."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            temp_output = tf.name

        try:
            # Default Groq mock run
            res_groq = execute_baseline(mock=True, provider="groq", delay_seconds=0.0, output_path=temp_output)
            self.assertEqual(res_groq["provider"], "groq")
            self.assertEqual(res_groq["model"], "openai/gpt-oss-20b")

            # Ollama mock run
            res_ollama = execute_baseline(mock=True, provider="ollama", delay_seconds=0.0, output_path=temp_output)
            self.assertEqual(res_ollama["provider"], "ollama")
            self.assertEqual(res_ollama["model"], "llama3.2:3b")

            # Custom Ollama model via env
            with patch.dict(os.environ, {"OLLAMA_MODEL": "custom-llama:3b"}):
                res_custom = execute_baseline(mock=True, provider="ollama", delay_seconds=0.0, output_path=temp_output)
                self.assertEqual(res_custom["provider"], "ollama")
                self.assertEqual(res_custom["model"], "custom-llama:3b")
        finally:
            if os.path.exists(temp_output):
                os.remove(temp_output)

    def test_16_delay_defaults_groq_and_ollama(self):
        """Verify delay defaults: 3.0s for Groq, 0.5s for Ollama, with explicit override."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            temp_output = tf.name

        try:
            mock_llm = unittest.mock.MagicMock()
            mock_llm.model = "test-model"
            with patch("run_baseline.time.sleep") as mock_sleep:
                with patch.dict(os.environ, {"LLM_PROVIDER": "groq", "GROQ_API_KEY": "dummy"}):
                    with patch("run_baseline.get_llm_provider", return_value=mock_llm), \
                         patch("run_baseline.run_pipeline_for_scenario", return_value=({"reply": "hi"}, 10.0, None)):
                        execute_baseline(mock=False, live=True, output_path=temp_output)
                        mock_sleep.assert_called_with(3.0)

            with patch("run_baseline.time.sleep") as mock_sleep:
                with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}):
                    with patch("run_baseline.get_llm_provider", return_value=mock_llm), \
                         patch("run_baseline.run_pipeline_for_scenario", return_value=({"reply": "hi"}, 10.0, None)):
                        execute_baseline(mock=False, live=True, output_path=temp_output)
                        mock_sleep.assert_called_with(0.5)

            with patch("run_baseline.time.sleep") as mock_sleep:
                with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}):
                    with patch("run_baseline.get_llm_provider", return_value=mock_llm), \
                         patch("run_baseline.run_pipeline_for_scenario", return_value=({"reply": "hi"}, 10.0, None)):
                        execute_baseline(mock=False, live=True, delay_seconds=1.2, output_path=temp_output)
                        mock_sleep.assert_called_with(1.2)
        finally:
            if os.path.exists(temp_output):
                os.remove(temp_output)

    def test_17_ollama_dry_run_no_keys_no_llm_calls(self):
        """Verify dry-run with LLM_PROVIDER=ollama requires no keys and makes zero LLM calls."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama", "GROQ_API_KEY": ""}):
            with patch("run_baseline.get_llm_provider") as mock_provider:
                result = execute_baseline(dry_run=True)
                mock_provider.assert_not_called()
                self.assertEqual(result["mode"], "dry_run")
                self.assertEqual(result["provider"], "ollama")
                self.assertEqual(result["scenario_count"], 20)
                self.assertEqual(len(result["selected_ids"]), 20)


if __name__ == "__main__":
    unittest.main(verbosity=2)

