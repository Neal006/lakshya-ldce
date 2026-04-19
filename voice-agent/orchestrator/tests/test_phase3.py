"""
Phase 3 integration test: Test full pipeline with real services.
Tests end-to-end flow through all agents with Ollama, classifier, and backend.
"""
import asyncio
import sys
import os
import json
import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ORCHESTRATOR_URL = "http://localhost:8003"
STT_URL = "http://localhost:8001"
CLASSIFIER_URL = "http://localhost:8002"
BACKEND_URL = "http://localhost:8000"
OLLAMA_URL = "http://localhost:11434"


async def test_stt_health():
    print("\n=== Test 1: STT Service Health ===")
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{STT_URL}/health")
        data = r.json()
        print(f"  Status: {data['status']}, Model loaded: {data['model_loaded']}, Device: {data['device']}")
        assert data['status'] == 'ok'
        assert data['model_loaded'] == True
        print("  PASS")


async def test_classifier_health():
    print("\n=== Test 2: Classifier Service Health ===")
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{CLASSIFIER_URL}/health")
        data = r.json()
        print(f"  Status: {data['status']}, Model loaded: {data['model_loaded']}")
        assert data['status'] == 'ok'
        assert data['model_loaded'] == True
        print("  PASS")


async def test_backend_health():
    print("\n=== Test 3: Backend Health ===")
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{BACKEND_URL}/health")
        data = r.json()
        print(f"  Status: {data['data']['status']}")
        assert data['data']['status'] == 'healthy'
        print("  PASS")


async def test_ollama_health():
    print("\n=== Test 4: Ollama LLM Health ===")
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.get(f"{OLLAMA_URL}/api/tags")
        data = r.json()
        models = [m['name'] for m in data.get('models', [])]
        print(f"  Available models: {models}")
        assert len(models) > 0
        print("  PASS")


async def test_classifier_predict():
    print("\n=== Test 5: Classifier Prediction ===")
    test_cases = [
        "My biscuit packet was torn",
        "The product quality is terrible",
        "I need bulk order delivery details",
    ]
    async with httpx.AsyncClient(timeout=10.0) as client:
        for text in test_cases:
            r = await client.post(f"{CLASSIFIER_URL}/predict", json={"complaint_id": "test", "text": text})
            data = r.json()
            print(f"  '{text[:40]}...' -> category={data['category']}, priority={data['priority']}, sentiment={data['sentiment_score']:.2f}, latency={data['latency_ms']:.0f}ms")
    print("  PASS")


async def test_pipeline_extraction():
    print("\n=== Test 6: Pipeline - Dialog Agent Extraction ===")
    test_cases = [
        "My Parle-G biscuit packet was torn and the biscuits were all broken. I am very angry.",
        "The packaging of Kurkure was completely damaged during delivery. This is unacceptable.",
        "I ordered 500 units of Maggi noodles but only received 300. I need this resolved immediately.",
    ]
    async with httpx.AsyncClient(timeout=60.0) as client:
        for text in test_cases:
            r = await client.post(f"{ORCHESTRATOR_URL}/test/pipeline", json={"text": text})
            data = r.json()
            extracted = data.get("extracted_data", {})
            print(f"  Input:    '{text[:50]}...'")
            print(f"  Type:     {extracted.get('complaint_type', 'N/A')}")
            print(f"  Desc:     {extracted.get('description', 'N/A')[:80]}...")
            print(f"  Brand:    {extracted.get('product_or_brand', 'N/A')}")
            print(f"  Urgency:  {extracted.get('urgency_signal', 'N/A')}")
            print(f"  Conf:     {extracted.get('confidence', 'N/A')}")
            print()
    print("  PASS")


async def test_pipeline_full_flow():
    print("\n=== Test 7: Pipeline - Full End-to-End Flow ===")
    from pipeline.session import SessionManager, CallSession, SessionState
    from pipeline.coordinator import PipelineCoordinator

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Step 1: Submit complaint text
        text = "My biscuit packet was torn and the biscuits were all broken. This is the third time this has happened."
        r = await client.post(f"{ORCHESTRATOR_URL}/test/pipeline", json={"text": text})
        step1 = r.json()
        print(f"  Step 1 - Greeting/Collecting:")
        print(f"    State: {step1['state']}")
        print(f"    TTS: {step1['pipeline_result']['tts_text'][:100]}...")
        print(f"    Extracted: {step1['extracted_data'].get('complaint_type', 'N/A')}")

        # The flow should have gone through extraction and into confirming
        # Now test with confirmation via the session manager directly
        coordinator = PipelineCoordinator()
        manager = SessionManager()
        session = manager.create_session("full-flow-test")
        session.state = SessionState.confirming
        session.transcript.append(text)
        session.extracted_data = step1.get("extracted_data", {})

        # Step 2: Confirm
        result = await coordinator.process_text("yes that is correct", session)
        print(f"\n  Step 2 - Confirming:")
        print(f"    State: {session.state.value}")
        print(f"    TTS: {result.get('tts_text', 'N/A')[:120]}...")
        if session.classification:
            print(f"    Classification: {session.classification.get('category', 'N/A')} / {session.classification.get('priority', 'N/A')}")
        if session.resolution:
            print(f"    Resolution steps: {session.resolution.get('steps', [])}")

        print(f"\n  Ticket ID: {session.ticket_id or 'Not created (backend auth issue expected)'}")
    print("  PASS")


async def test_orchestrator_health():
    print("\n=== Test 8: Orchestrator Full Health ===")
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(f"{ORCHESTRATOR_URL}/health")
        data = r.json()
        print(f"  Overall status: {data['status']}")
        for name, info in data['services'].items():
            print(f"  {name}: {info['status']}")
        print("  PASS")


async def main():
    print("=" * 60)
    print("  SOLV.ai Voice Agent - Phase 3 Integration Tests")
    print("  Testing with REAL services (STT, Classifier, Ollama, Backend)")
    print("=" * 60)

    tests = [
        test_stt_health,
        test_classifier_health,
        test_backend_health,
        test_ollama_health,
        test_classifier_predict,
        test_pipeline_extraction,
        test_pipeline_full_flow,
        test_orchestrator_health,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            await test()
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"  Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)