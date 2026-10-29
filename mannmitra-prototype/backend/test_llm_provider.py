# test_llm_provider.py
# Targeted unit tests for the LLM Provider Abstraction layer in MannMitra

import io
import importlib
import json
import os
import sys
import urllib.error
from unittest.mock import MagicMock, patch

from llm_provider import (
    LLMProvider,
    GroqProvider,
    OllamaProvider,
    LLMResponse,
    get_llm_provider,
)

def run_provider_tests():
    print("=" * 80)
    print("TESTING MINIMAL LLM PROVIDER ABSTRACTION")
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

    # 1. LLMResponse properties
    resp = LLMResponse(content="Test reply", finish_reason="stop")
    check(resp.content == "Test reply", "LLMResponse content field preserved")
    check(resp.text == "Test reply", "LLMResponse.text property aliases content")
    check(str(resp) == "Test reply", "str(LLMResponse) returns content string")
    check(resp.finish_reason == "stop", "LLMResponse finish_reason preserved")

    # 2. Default provider selection (without env var or with None)
    # Save current env if set
    orig_env = os.environ.get("LLM_PROVIDER")
    if "LLM_PROVIDER" in os.environ:
        del os.environ["LLM_PROVIDER"]

    default_provider = get_llm_provider()
    check(isinstance(default_provider, GroqProvider), "Default provider is GroqProvider when LLM_PROVIDER is unset")
    check(isinstance(default_provider, LLMProvider), "GroqProvider inherits from LLMProvider ABC")
    check(default_provider.model == "openai/gpt-oss-20b", "GroqProvider default model is 'openai/gpt-oss-20b'")

    # 3. Explicit LLM_PROVIDER=groq selection
    os.environ["LLM_PROVIDER"] = "groq"
    explicit_groq = get_llm_provider()
    check(isinstance(explicit_groq, GroqProvider), "Explicit LLM_PROVIDER='groq' selects GroqProvider")

    os.environ["LLM_PROVIDER"] = "GROQ"
    case_insensitive_groq = get_llm_provider()
    check(isinstance(case_insensitive_groq, GroqProvider), "Case-insensitive 'GROQ' selects GroqProvider")

    # 4. Explicit parameter selection
    param_groq = get_llm_provider("groq")
    check(isinstance(param_groq, GroqProvider), "Passing provider_name='groq' directly selects GroqProvider")

    # 5. Unsupported provider handling (must fail clearly with useful ValueError)
    unsupported_failed = False
    error_message = ""
    try:
        get_llm_provider("gemini")
    except ValueError as e:
        unsupported_failed = True
        error_message = str(e)
    check(unsupported_failed, "Unsupported provider 'gemini' raises ValueError (not yet implemented)")
    check("Unsupported LLM provider: 'gemini'" in error_message, f"Error message clearly identifies unsupported provider: {error_message}")

    bogus_failed = False
    try:
        get_llm_provider("unsupported_xyz")
    except ValueError as e:
        bogus_failed = True
    check(bogus_failed, "Arbitrary unsupported provider raises ValueError")

    # Restore original env
    if orig_env is not None:
        os.environ["LLM_PROVIDER"] = orig_env
    elif "LLM_PROVIDER" in os.environ:
        del os.environ["LLM_PROVIDER"]

    # 6. Existing application imports successfully
    main_imported = False
    try:
        import main
        main_imported = hasattr(main, "app") and hasattr(main, "chat")
    except Exception as e:
        print(f"Failed to import main: {e}")
    check(main_imported, "backend/main.py imports successfully with LLM provider abstraction")

    emotion_imported = False
    try:
        import emotion_engine
        emotion_imported = hasattr(emotion_engine, "analyze_emotional_state")
    except Exception as e:
        print(f"Failed to import emotion_engine: {e}")
    check(emotion_imported, "backend/emotion_engine.py imports successfully with LLM provider abstraction")

    # 7. OllamaProvider class properties and defaults
    default_ollama = OllamaProvider()
    check(isinstance(default_ollama, LLMProvider), "OllamaProvider inherits from LLMProvider ABC")
    check(default_ollama.base_url == "http://127.0.0.1:11434", "OllamaProvider default base_url is 'http://127.0.0.1:11434'")
    check(default_ollama.model == "llama3.2:3b", "OllamaProvider default model is 'llama3.2:3b'")

    # Trailing slash stripping in base_url
    trailing_slash_ollama = OllamaProvider(base_url="http://localhost:11434/")
    check(trailing_slash_ollama.base_url == "http://localhost:11434", "OllamaProvider strips trailing slash from base_url")

    # Custom attributes via constructor
    custom_ollama = OllamaProvider(base_url="http://custom-host:8080", model="qwen3:4b", timeout=30.0)
    check(custom_ollama.base_url == "http://custom-host:8080", "OllamaProvider constructor accepts custom base_url")
    check(custom_ollama.model == "qwen3:4b", "OllamaProvider constructor accepts custom model")
    check(custom_ollama.timeout == 30.0, "OllamaProvider constructor accepts custom timeout")

    # Custom attributes via environment variables
    with patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://env-host:11434", "OLLAMA_MODEL": "custom-model:3b"}):
        env_ollama = OllamaProvider()
        check(env_ollama.base_url == "http://env-host:11434", "OllamaProvider reads OLLAMA_BASE_URL from env")
        check(env_ollama.model == "custom-model:3b", "OllamaProvider reads OLLAMA_MODEL from env")

    # 8. Ollama provider selection via get_llm_provider
    param_ollama = get_llm_provider("ollama")
    check(isinstance(param_ollama, OllamaProvider), "Passing provider_name='ollama' directly selects OllamaProvider")

    param_ollama_caps = get_llm_provider("OLLAMA")
    check(isinstance(param_ollama_caps, OllamaProvider), "Case-insensitive 'OLLAMA' selects OllamaProvider")

    with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}):
        env_selected_ollama = get_llm_provider()
        check(isinstance(env_selected_ollama, OllamaProvider), "LLM_PROVIDER='ollama' selects OllamaProvider via env")

    # 9. Request formatting and options mapping with mocks
    mock_response_data = {
        "model": "llama3.2:3b",
        "message": {"role": "assistant", "content": "I am here to support you."},
        "done": True,
        "done_reason": "stop"
    }
    mock_bytes = json.dumps(mock_response_data).encode("utf-8")

    captured_request = None
    class MockHTTPResponse:
        def __init__(self, data):
            self._data = data
        def read(self):
            return self._data
        def decode(self, encoding="utf-8"):
            return self._data.decode(encoding)
        def getcode(self):
            return 200
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    def mock_urlopen(req, timeout=None):
        nonlocal captured_request
        captured_request = req
        return MockHTTPResponse(mock_bytes)

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        provider = OllamaProvider()
        test_messages = [{"role": "system", "content": "Be empathetic."}, {"role": "user", "content": "I am stressed."}]
        result = provider.generate(messages=test_messages, max_tokens=250, temperature=0.7)

        check(isinstance(result, LLMResponse), "generate() returns an LLMResponse instance")
        check(result.content == "I am here to support you.", "generate() extracts message.content correctly")
        check(result.finish_reason == "stop", "generate() extracts done_reason correctly")
        check(result.text == "I am here to support you.", "LLMResponse.text property functions for Ollama")

        # Inspect captured request
        check(captured_request is not None, "HTTP request was dispatched via urlopen")
        check(captured_request.full_url == "http://127.0.0.1:11434/api/chat", "Request targeted /api/chat endpoint")
        check(captured_request.get_method() == "POST", "Request used HTTP POST")
        check(captured_request.headers.get("Content-type") == "application/json", "Request specified Content-Type: application/json")

        req_payload = json.loads(captured_request.data.decode("utf-8"))
        check(req_payload.get("stream") is False, "Payload enforces stream: False")
        check(req_payload.get("model") == "llama3.2:3b", "Payload specifies correct model")
        check(req_payload.get("messages") == test_messages, "Payload includes exact conversation messages")
        check(req_payload.get("options", {}).get("num_predict") == 250, "max_tokens maps to options.num_predict")
        check(req_payload.get("options", {}).get("num_ctx") == 4096, "options.num_ctx defaults to 4096")
        check(req_payload.get("options", {}).get("temperature") == 0.7, "temperature maps to options.temperature")

    # 10. Robust error handling with mocks
    # 10a. HTTP error (e.g., HTTP 500)
    with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
        url="http://127.0.0.1:11434/api/chat", code=500, msg="Internal Server Error", hdrs={}, fp=io.BytesIO(b"error")
    )):
        http_err_caught = False
        err_msg = ""
        try:
            OllamaProvider().generate([{"role": "user", "content": "Hi"}])
        except RuntimeError as e:
            http_err_caught = True
            err_msg = str(e)
        check(http_err_caught, "OllamaProvider raises RuntimeError on HTTPError")
        check("HTTP 500" in err_msg, f"RuntimeError message mentions HTTP status code: {err_msg}")

    # 10b. Connection error (Ollama service down)
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError(reason="Connection refused")):
        conn_err_caught = False
        err_msg = ""
        try:
            OllamaProvider().generate([{"role": "user", "content": "Hi"}])
        except RuntimeError as e:
            conn_err_caught = True
            err_msg = str(e)
        check(conn_err_caught, "OllamaProvider raises RuntimeError on connection failure (URLError)")
        check("Connection refused" in err_msg, f"RuntimeError message mentions connection failure: {err_msg}")

    # 10c. Timeout error
    with patch("urllib.request.urlopen", side_effect=TimeoutError("Request timed out")):
        timeout_caught = False
        try:
            OllamaProvider().generate([{"role": "user", "content": "Hi"}])
        except RuntimeError as e:
            timeout_caught = True
        check(timeout_caught, "OllamaProvider raises RuntimeError on timeout")

    # 10d. Malformed JSON response
    with patch("urllib.request.urlopen", return_value=MockHTTPResponse(b"invalid-json-content")):
        malformed_caught = False
        try:
            OllamaProvider().generate([{"role": "user", "content": "Hi"}])
        except RuntimeError as e:
            malformed_caught = True
        check(malformed_caught, "OllamaProvider raises RuntimeError on malformed JSON response")

    # 10e. Missing message key in response
    missing_msg_bytes = json.dumps({"done": True, "error": "model not found"}).encode("utf-8")
    with patch("urllib.request.urlopen", return_value=MockHTTPResponse(missing_msg_bytes)):
        missing_msg_caught = False
        err_msg = ""
        try:
            OllamaProvider().generate([{"role": "user", "content": "Hi"}])
        except RuntimeError as e:
            missing_msg_caught = True
            err_msg = str(e)
        check(missing_msg_caught, "OllamaProvider raises RuntimeError when 'message' key is missing")
        check("model not found" in err_msg, f"RuntimeError message extracts Ollama top-level error: {err_msg}")

    # 11. Final verification: Groq remains default when LLM_PROVIDER is unset
    if "LLM_PROVIDER" in os.environ:
        del os.environ["LLM_PROVIDER"]
    final_default = get_llm_provider()
    check(isinstance(final_default, GroqProvider), "Final verification: default provider remains GroqProvider")

    # 12. Startup validation tests for main.py with isolated environment
    # 12a. LLM_PROVIDER=ollama starts up without GROQ_API_KEY
    with patch.dict(os.environ, {"LLM_PROVIDER": "ollama", "GROQ_API_KEY": ""}):
        ollama_startup_ok = False
        try:
            import main
            importlib.reload(main)
            ollama_startup_ok = isinstance(main.llm_provider, OllamaProvider)
        except Exception as e:
            print(f"Ollama startup failed: {e}")
        check(ollama_startup_ok, "main.py starts with LLM_PROVIDER=ollama and no GROQ_API_KEY")

    # 12b. LLM_PROVIDER=groq fails safely when GROQ_API_KEY is missing
    with patch.dict(os.environ, {"LLM_PROVIDER": "groq", "GROQ_API_KEY": ""}):
        groq_missing_key_caught = False
        err_msg = ""
        try:
            import main
            importlib.reload(main)
        except RuntimeError as e:
            groq_missing_key_caught = True
            err_msg = str(e)
        check(groq_missing_key_caught, "main.py raises RuntimeError when LLM_PROVIDER=groq and GROQ_API_KEY is missing")
        check("GROQ_API_KEY is missing" in err_msg, f"RuntimeError message specifies missing GROQ_API_KEY: {err_msg}")

    # 12c. LLM_PROVIDER unset/empty defaults to Groq and fails safely when GROQ_API_KEY is missing
    with patch.dict(os.environ, {"LLM_PROVIDER": "", "GROQ_API_KEY": ""}):
        empty_provider_missing_key = False
        try:
            import main
            importlib.reload(main)
        except RuntimeError as e:
            empty_provider_missing_key = True
        check(empty_provider_missing_key, "main.py defaults to Groq when LLM_PROVIDER='' and requires GROQ_API_KEY")

    # 12d. Unsupported provider in main.py raises ValueError
    with patch.dict(os.environ, {"LLM_PROVIDER": "unsupported_abc"}):
        unsupported_startup_caught = False
        err_msg = ""
        try:
            import main
            importlib.reload(main)
        except ValueError as e:
            unsupported_startup_caught = True
            err_msg = str(e)
        check(unsupported_startup_caught, "main.py raises ValueError on unsupported provider")
        check("Unsupported LLM provider: 'unsupported_abc'" in err_msg, f"ValueError message mentions unsupported provider: {err_msg}")

    # 12e. get_llm_provider empty/whitespace handling
    check(isinstance(get_llm_provider(""), GroqProvider), "get_llm_provider('') defaults to GroqProvider")
    check(isinstance(get_llm_provider("   "), GroqProvider), "get_llm_provider('   ') defaults to GroqProvider")
    with patch.dict(os.environ, {"LLM_PROVIDER": ""}):
        check(isinstance(get_llm_provider(), GroqProvider), "get_llm_provider() with LLM_PROVIDER='' defaults to GroqProvider")

    # Clean up: reload main with normal environment
    try:
        import main
        importlib.reload(main)
    except Exception:
        pass

    print(f"\nResult: {passed}/{total} passed")
    return passed == total


if __name__ == "__main__":
    success = run_provider_tests()
    sys.exit(0 if success else 1)
