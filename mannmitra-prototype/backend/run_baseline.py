# run_baseline.py
# ==============================================================================
# Controlled Groq Baseline Evaluation Runner (Phase 4)
# ==============================================================================
# Executes exactly 20 representative Golden Dataset scenarios (1 per category)
# through the existing MannMitra pipeline and evaluates responses using evaluator.py.
#
# SAFETY & QUOTA CONTROLS:
# - Default mode is SAFE: Does NOT execute live API calls without explicit --live.
# - Dry-run mode (--dry-run) inspects the selected 20 cases with ZERO API calls.
# - Mock mode (--mock) allows end-to-end testing of runner & evaluation offline.
# - Strictly limited to 20 deterministic scenarios: no code path exists for 100 cases.
# - Sequential execution with configurable inter-request delay (default 3s).
# - Single controlled retry for transient errors; does not crash on single failure.
# - Secrets and API keys are NEVER printed or saved to output files.
# ==============================================================================

import os
import sys
import io
import json
import time
import argparse
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure backend root is on path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from evaluator import evaluate_scenario_response, load_golden_dataset, ScenarioEvaluation
from llm_provider import get_llm_provider

# Output paths
RESULTS_DIR = os.path.join(BASE_DIR, "evaluation_results")
DEFAULT_GROQ_OUTPUT_FILE = os.path.join(RESULTS_DIR, "groq_baseline_20.json")
DEFAULT_OLLAMA_OUTPUT_FILE = os.path.join(RESULTS_DIR, "ollama_baseline_20.json")
DEFAULT_OUTPUT_FILE = DEFAULT_GROQ_OUTPUT_FILE


def get_default_output_file(provider: str) -> str:
    """Return default output file path based on selected provider."""
    if provider == "ollama":
        return DEFAULT_OLLAMA_OUTPUT_FILE
    return DEFAULT_GROQ_OUTPUT_FILE


# ==============================================================================
# EXACT 20 REPRESENTATIVE SCENARIO SELECTION (1 PER CATEGORY)
# ==============================================================================
SELECTED_SCENARIOS = [
    # 1. Academic Stress: Acute exam freeze, checks listen-first vs timetable dump
    ("ACAD_01", "Academic Stress"),
    # 2. Motivation / Procrastination: Avoidance loop; validation without preaching
    ("MOTIV_01", "Motivation / Procrastination"),
    # 3. Loneliness / Hostel: Social isolation in university hostel; peer reflection
    ("LONE_01", "Loneliness / Hostel"),
    # 4. Self-Esteem / Peer Comparison: Vulnerability from LinkedIn peer comparisons
    ("ESTEEM_01", "Self-Esteem / Peer Comparison"),
    # 5. Interpersonal / Relationships: Loss of school friendship on campus
    ("RELAT_01", "Interpersonal / Relationships"),
    # 6. Humorous Complaints: Relatable study procrastination meme; humour gate check
    ("HUMOUR_01", "Humorous Complaints"),
    # 7. Hinglish Colloquial: High-frequency idiom ('dimaag ka dahi'); Latin script
    ("HING_01", "Hinglish Colloquial"),
    # 8. English Expressions: Burnout in English; authentic peer tone vs corporate bot
    ("ENG_01", "English Expressions"),
    # 9. Hindi Devanagari: Pure Devanagari script alignment and non-clinical warmth
    ("HINDI_01", "Hindi Devanagari"),
    # 10. Ambiguous Inputs: Short ambiguous 'Pata nahi yaar'; clarify-first handling
    ("AMBIG_01", "Ambiguous Inputs"),
    # 11. Multi-Turn Depth: Ongoing viva thread; contextual continuity & memory
    ("DEPTH_01", "Multi-Turn Depth"),
    # 12. Topic Shifts: Pivot from anxiety to hostel WiFi; clean anchor drop
    ("SHIFT_01", "Topic Shifts"),
    # 13. Explicit Advice: Direct advice request ('kya karna chahiye'); actionable tips
    ("ADVICE_01", "Explicit Advice"),
    # 14. Pure Venting: Ceiling-staring venting; strict advice gating suppression
    ("VENT_01", "Pure Venting"),
    # 15. Informational / RAG: DSR office location and phone; anti-hallucination
    ("INFO_01", "Informational / RAG"),
    # 16. Crisis / Safety: Severe crisis; safety override, helplines, zero humour
    ("CRISIS_01", "Crisis / Safety"),
    # 17. Prompt Injection / Adversarial: Jailbreak attempt; boundary enforcement
    ("ADVERS_01", "Prompt Injection / Adversarial"),
    # 18. Short Affirmations: Single-word 'Haan'; reference resolution vs bot reset
    ("AFFIRM_01", "Short Affirmations"),
    # 19. Anaphora / Reference Resolution: 'Haan wahi'; referent resolution
    ("REF_01", "Anaphora / Reference Resolution"),
    # 20. Complex Mixed Emotional + Practical: Code lost 2h before deadline; panic + practical
    ("MIXED_01", "Complex Mixed Emotional + Practical"),
]

SELECTED_SCENARIO_IDS = [s[0] for s in SELECTED_SCENARIOS]


def get_selected_scenarios(all_scenarios: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deterministically filter and return exactly the 20 selected scenarios."""
    scenarios_by_id = {s["id"]: s for s in all_scenarios}
    selected: List[Dict[str, Any]] = []

    for sc_id, expected_cat in SELECTED_SCENARIOS:
        if sc_id not in scenarios_by_id:
            raise KeyError(f"Selected scenario '{sc_id}' not found in Golden Dataset.")
        sc = scenarios_by_id[sc_id]
        if sc.get("category") != expected_cat:
            raise ValueError(
                f"Scenario '{sc_id}' has category '{sc.get('category')}', expected '{expected_cat}'."
            )
        selected.append(sc)

    if len(selected) != 20:
        raise ValueError(f"Expected exactly 20 selected scenarios, found {len(selected)}.")

    return selected


def run_pipeline_for_scenario(
    scenario: Dict[str, Any],
    pipeline_fn: Optional[Any] = None,
    mock: bool = False,
) -> Tuple[Dict[str, Any], float, Optional[str]]:
    """Execute a single scenario through the existing MannMitra pipeline.
    
    Returns:
        (pipeline_response_dict, latency_ms, error_message_or_None)
    """
    if mock:
        # Offline mock response generator for testing runner without calling LLM
        return _generate_mock_pipeline_response(scenario)

    # Lazily import main.chat to preserve clean module boundaries
    from main import chat, ChatRequest, ChatMessage

    history_objs = [
        ChatMessage(role=m["role"], content=m["content"])
        for m in scenario.get("conversation_history", [])
    ]
    req = ChatRequest(
        message=scenario.get("current_user_message", ""),
        history=history_objs
    )

    t0 = time.time()
    try:
        fn = pipeline_fn or chat
        resp = fn(req)
        latency = round((time.time() - t0) * 1000.0, 2)
        return resp, latency, None
    except Exception as e:
        latency = round((time.time() - t0) * 1000.0, 2)
        return {}, latency, str(e)


def _generate_mock_pipeline_response(scenario: Dict[str, Any]) -> Tuple[Dict[str, Any], float, Optional[str]]:
    """Generate realistic mock response conforming to scenario expectations for offline testing."""
    sc_id = scenario.get("id", "")
    exp = scenario.get("expected_behavior", {})

    if sc_id == "CRISIS_01":
        reply = "I hear how much pain you're in. Please call Tele-MANAS at 14416 right now."
        risk = "high"
        helplines = [{"name": "Tele-MANAS", "number": "14416"}]
        strat = "CRISIS"
    elif sc_id == "INFO_01":
        reply = "LPU's DSR office is located at Block 32, Room No. 100. Contact: 01824-520150."
        risk = "low"
        helplines = []
        strat = "INFORMATIONAL"
    elif sc_id == "HINDI_01":
        reply = "मैं समझ सकता हूँ कि परीक्षा का दबाव कितना अधिक महसूस हो रहा है। अभी कैसा लग रहा है?"
        risk = "low"
        helplines = []
        strat = "REFLECTIVE_LISTENING"
    else:
        reply = "I hear what you are saying yaar. Take a deep breath. What feels most stressful right now?"
        risk = "low"
        helplines = []
        strat = exp.get("strategy", "REFLECTIVE_LISTENING").split()[0]

    resp = {
        "reply": reply,
        "risk_level": risk,
        "helplines": helplines,
        "grounded": strat == "INFORMATIONAL",
        "strategy": strat,
        "confidence_level": exp.get("context_confidence", "high"),
        "language": exp.get("language", "hinglish_latin"),
        "advice_mode": exp.get("advice_mode", "listen_first"),
        "advice_allowed": exp.get("advice_mode") == "explicit_advice",
        "humour_allowed": exp.get("humour_allowed", False),
        "context_continuity": exp.get("context_continuity", "isolated"),
    }
    return resp, 120.0, None


def execute_baseline(
    live: bool = False,
    mock: bool = False,
    dry_run: bool = False,
    delay_seconds: Optional[float] = None,
    output_path: Optional[str] = None,
    provider: Optional[str] = None,
) -> Dict[str, Any]:
    """Main execution controller for the 20-case baseline runner."""
    # Resolve provider
    raw_provider = provider or os.getenv("LLM_PROVIDER", "groq")
    selected_provider = raw_provider.lower().strip() if raw_provider else "groq"

    # Resolve effective delay
    effective_delay = (
        delay_seconds
        if delay_seconds is not None
        else (0.5 if selected_provider == "ollama" else 3.0)
    )

    # Resolve output path
    resolved_output_file = output_path or get_default_output_file(selected_provider)

    # 1. Load dataset & extract the exact 20 scenarios
    all_scenarios = load_golden_dataset()
    selected_scenarios = get_selected_scenarios(all_scenarios)

    # 2. Dry-Run Handling
    if dry_run:
        print("\n" + "=" * 80)
        print(f"BASELINE EVALUATION RUNNER ({selected_provider.upper()}) — DRY RUN")
        print("=" * 80)
        print(f"Selected exactly {len(selected_scenarios)} representative scenarios (1 per category):")
        for idx, sc in enumerate(selected_scenarios, 1):
            print(f"  {idx:2d}. [{sc['id']}] {sc['category']}: {sc['current_user_message'][:55]}...")
        print("\nDry-run completed successfully. ZERO API calls made.")
        print("=" * 80 + "\n")
        return {
            "mode": "dry_run",
            "provider": selected_provider,
            "scenario_count": len(selected_scenarios),
            "selected_ids": [s["id"] for s in selected_scenarios]
        }

    # 3. Verify Live Execution Requirements
    if live and not mock:
        if selected_provider not in ("groq", "ollama"):
            raise ValueError(
                f"Unsupported LLM_PROVIDER '{selected_provider}'. Supported providers are: 'groq', 'ollama'."
            )

        if selected_provider == "groq":
            groq_key = os.getenv("GROQ_API_KEY")
            if not groq_key or not groq_key.strip():
                raise EnvironmentError("GROQ_API_KEY environment variable is missing or empty.")

        # Ensure the provider abstraction resolves cleanly
        llm = get_llm_provider(selected_provider)
        raw_model = getattr(llm, "model", None)
        if isinstance(raw_model, str) and raw_model.strip():
            model_name = raw_model.strip()
        else:
            model_name = (
                os.getenv("OLLAMA_MODEL", "llama3.2:3b") if selected_provider == "ollama" else "openai/gpt-oss-20b"
            )
        print(f"[BASELINE] Verified provider: {type(llm).__name__} (Model: {model_name})")
        print(f"[BASELINE] Starting sequential execution of {len(selected_scenarios)} scenarios (Delay: {effective_delay}s)...")

    elif not mock:
        print("\n[SAFETY NOTICE] Live mode was not requested (--live).")
        print("Use --dry-run to inspect selected scenarios or --mock for offline runner validation.")
        print("To execute live evaluation calls, explicitly pass --live.\n")
        return {"mode": "aborted", "reason": "Missing --live flag"}
    else:
        # Mock mode model name resolution
        if selected_provider == "ollama":
            model_name = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        else:
            model_name = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    # 4. Sequential Execution Loop
    results: List[Dict[str, Any]] = []
    hard_failure_count = 0
    warning_count = 0
    quality_passes_count = 0
    quality_failures_count = 0
    infrastructure_failures_count = 0
    fallback_activated_count = 0

    for idx, scenario in enumerate(selected_scenarios, 1):
        sc_id = scenario["id"]
        cat = scenario["category"]
        msg = scenario["current_user_message"]

        print(f"  [{idx:2d}/{len(selected_scenarios)}] Running {sc_id} ({cat})...", end="", flush=True)

        # Execute with 1 controlled retry for transient errors
        resp, latency, err = run_pipeline_for_scenario(scenario, mock=mock)
        if err and not mock and live:
            print(f" [RETRYING due to: {err}]...", end="", flush=True)
            time.sleep(max(effective_delay, 5.0))
            resp, latency, err = run_pipeline_for_scenario(scenario, mock=mock)

        # Run evaluator on the response
        if err:
            eval_dict = {
                "id": sc_id,
                "category": cat,
                "passed": False,
                "status": "INFRASTRUCTURE_FAILURE",
                "is_infrastructure_failure": True,
                "is_fallback_activated": False,
                "hard_failures": [f"[PIPELINE_ERROR] {err}"],
                "warnings": [],
                "critical_failures": [f"[PIPELINE_ERROR] {err}"],
                "high_priority_failures": [],
                "checks": {}
            }
            infrastructure_failures_count += 1
            hard_failure_count += 1
            print(" [INFRASTRUCTURE_FAILURE: Pipeline Error]")
        else:
            eval_res: ScenarioEvaluation = evaluate_scenario_response(scenario, resp)
            eval_dict = eval_res.to_dict()
            if eval_res.is_infrastructure_failure:
                infrastructure_failures_count += 1
                print(f" [INFRASTRUCTURE_FAILURE: RateLimit] ({latency}ms)")
            elif eval_res.is_fallback_activated:
                fallback_activated_count += 1
                print(f" [FALLBACK_ACTIVATED: Emergency Fallback] ({latency}ms)")
            elif eval_res.passed:
                quality_passes_count += 1
                print(f" [QUALITY_PASS] ({latency}ms)")
            else:
                quality_failures_count += 1
                print(f" [QUALITY_FAIL: {len(eval_res.hard_failures)} hard failure(s)] ({latency}ms)")

            hard_failure_count += len(eval_res.hard_failures)
            warning_count += len(eval_res.warnings)

        # Sanitize metadata (never store any secret, api_key, or auth headers)
        clean_metadata = {
            k: v for k, v in resp.items()
            if k not in ("reply", "api_key", "authorization", "token")
        }

        record = {
            "id": sc_id,
            "category": cat,
            "current_user_message": msg,
            "generated_response": resp.get("reply", ""),
            "pipeline_metadata": clean_metadata,
            "evaluator_result": eval_dict,
            "latency_ms": latency,
            "error": err,
        }
        results.append(record)

        # Inter-scenario delay to protect quota and rate limits
        if idx < len(selected_scenarios) and (live or effective_delay > 0):
            if not mock:
                time.sleep(effective_delay)

    # 5. Compile Summary & Output
    summary = {
        "total": len(selected_scenarios),
        "quality_passes": quality_passes_count,
        "quality_failures": quality_failures_count,
        "infrastructure_failures": infrastructure_failures_count,
        "fallback_activated": fallback_activated_count,
        "passed": quality_passes_count,
        "failed": quality_failures_count + infrastructure_failures_count + fallback_activated_count,
        "pass_percentage": round((quality_passes_count / len(selected_scenarios)) * 100.0, 2),
        "hard_failures": hard_failure_count,
        "warnings": warning_count,
    }

    output_data = {
        "provider": selected_provider,
        "model": model_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "live" if live else "mock",
        "scenario_count": len(selected_scenarios),
        "summary": summary,
        "results": results,
    }

    # Save to file
    out_file = resolved_output_file
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print(f"{selected_provider.upper()} BASELINE EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Total Scenarios Evaluated: {summary['total']}")
    print(f"Quality Passes:           {summary['quality_passes']} ({summary['pass_percentage']}%)")
    print(f"Quality Failures:         {summary['quality_failures']}")
    print(f"Infrastructure Failures:  {summary['infrastructure_failures']}")
    print(f"Fallback-Activated Cases: {summary['fallback_activated']}")
    print(f"Hard Failures:            {summary['hard_failures']}")
    print(f"Warnings:                 {summary['warnings']}")
    print(f"Results saved to:         {out_file}")
    print("=" * 80 + "\n")

    return output_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Controlled Baseline Evaluation Runner (Groq / Ollama)")
    parser.add_argument("--live", action="store_true", help="Execute live API calls (requires GROQ_API_KEY for Groq)")
    parser.add_argument("--dry-run", action="store_true", help="Inspect the 20 selected scenarios with ZERO API calls")
    parser.add_argument("--mock", action="store_true", help="Run offline with mock responses for runner testing")
    parser.add_argument("--delay", type=float, default=None, help="Delay between scenarios in seconds (defaults: 3.0s for Groq, 0.5s for Ollama)")
    parser.add_argument("--output", type=str, default=None, help="Path to save evaluation results JSON (defaults to provider baseline JSON)")

    args = parser.parse_args()
    execute_baseline(
        live=args.live,
        mock=args.mock,
        dry_run=args.dry_run,
        delay_seconds=args.delay,
        output_path=args.output,
    )
