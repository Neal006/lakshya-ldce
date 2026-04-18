"""
Phase 2 integration test: Test the voice pipeline without telephony.
Tests the full pipeline from text input through all agents.

Usage:
    python tests/test_phase2.py
"""
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.session import SessionManager, CallSession, SessionState
from pipeline.coordinator import PipelineCoordinator


async def test_session_creation():
    print("\n=== Test 1: Session Creation ===")
    manager = SessionManager()
    session = manager.create_session("test-call-001")
    assert session.call_sid == "test-call-001"
    assert session.state == SessionState.greeting
    print(f"  PASS: Session created with state={session.state.value}")
    return manager, session


async def test_fsm_transitions():
    print("\n=== Test 2: FSM State Transitions ===")
    manager = SessionManager()
    session = manager.create_session("test-fsm")
    
    assert session.state == SessionState.greeting
    print(f"  Initial state: {session.state.value}")
    
    manager.update_state("test-fsm", SessionState.collecting)
    assert session.state == SessionState.collecting
    print(f"  After transition: {session.state.value}")
    
    manager.update_state("test-fsm", SessionState.confirming)
    assert session.state == SessionState.confirming
    print(f"  After transition: {session.state.value}")
    
    closed = manager.close_session("test-fsm")
    assert closed is not None
    assert manager.get_session("test-fsm") is None
    print("  PASS: All state transitions work")


async def test_coordinator_greeting():
    print("\n=== Test 3: Coordinator - Greeting State ===")
    coordinator = PipelineCoordinator()
    manager = SessionManager()
    session = manager.create_session("test-greeting")
    
    result = await coordinator.process_text(
        "My biscuit packet was torn and biscuits were broken",
        session
    )
    print(f"  State: {session.state.value}")
    print(f"  TTS text: {result.get('tts_text', 'N/A')[:100]}...")
    print(f"  Turn count: {session.turn_count}")
    assert "tts_text" in result
    print("  PASS: Greeting state processes text")


async def test_coordinator_collecting():
    print("\n=== Test 4: Coordinator - Collecting State ===")
    coordinator = PipelineCoordinator()
    manager = SessionManager()
    session = manager.create_session("test-collecting")
    session.state = SessionState.collecting
    session.transcript.append("The packaging of my Parle-G biscuits was damaged")
    
    result = await coordinator.process_text(
        "I bought it from a local store last week",
        session
    )
    print(f"  State: {session.state.value}")
    print(f"  TTS text: {result.get('tts_text', 'N/A')[:100]}...")
    print(f"  Transcript: {session.full_transcript[:80]}...")
    assert session.turn_count > 0
    print("  PASS: Collecting state processes text")


async def test_coordinator_confirmation_yes():
    print("\n=== Test 5: Coordinator - Confirmation (Yes) ===")
    coordinator = PipelineCoordinator()
    manager = SessionManager()
    session = manager.create_session("test-confirm-yes")
    session.state = SessionState.confirming
    session.extracted_data = {
        "complaint_type": "Packaging",
        "description": "Parle-G biscuit packet was torn",
        "confidence": 0.85,
    }
    session.transcript.append("My Parle-G biscuit packet was torn")
    
    result = await coordinator.process_text("yes that is correct", session)
    print(f"  State: {session.state.value}")
    print(f"  TTS text: {result.get('tts_text', 'N/A')[:100]}...")
    assert session.state in [SessionState.classifying, SessionState.ticket_created, SessionState.resolving]
    print("  PASS: Confirmation with 'yes' proceeds")


async def test_coordinator_confirmation_no():
    print("\n=== Test 6: Coordinator - Confirmation (No) ===")
    coordinator = PipelineCoordinator()
    manager = SessionManager()
    session = manager.create_session("test-confirm-no")
    session.state = SessionState.confirming
    session.transcript.append("My biscuit packet was torn")
    
    result = await coordinator.process_text("no that is wrong", session)
    print(f"  State: {session.state.value}")
    print(f"  TTS text: {result.get('tts_text', 'N/A')[:100]}...")
    assert session.state == SessionState.collecting
    print("  PASS: Confirmation with 'no' returns to collecting")


async def test_empty_input():
    print("\n=== Test 7: Empty Input Handling ===")
    coordinator = PipelineCoordinator()
    manager = SessionManager()
    session = manager.create_session("test-empty")
    
    result = await coordinator.process_text("", session)
    print(f"  TTS text: {result.get('tts_text', 'N/A')}")
    assert "didn't catch" in result.get("tts_text", "").lower() or "repeat" in result.get("tts_text", "").lower()
    print("  PASS: Empty input handled gracefully")


async def test_fmg_corrections():
    print("\n=== Test 8: FMCG Domain Corrections ===")
    from prompts.corrections import apply_fmcg_corrections
    
    test_cases = [
        ("parley g biscuit is damaged", "Parle-G"),
        ("the maggy noodles were spoiled", "Maggi"),
        ("surf excell packaging was torn", "Surf Excel"),
        ("the kurkure packet had issue", "Kurkure"),
    ]
    
    for input_text, expected_contains in test_cases:
        corrected = apply_fmcg_corrections(input_text)
        assert expected_contains in corrected, f"Expected '{expected_contains}' in '{corrected}'"
        print(f"  '{input_text}' -> '{corrected}' (contains '{expected_contains}')")
    
    print("  PASS: All FMCG corrections applied correctly")


async def test_audio_utils():
    print("\n=== Test 9: Audio Utils ===")
    from telephony.audio_utils import (
        pcm16_to_float32, float32_to_pcm16,
        resample_8k_to_16k, resample_16k_to_8k,
        mulaw_bytes_to_pcm16, pcm16_to_mulaw_bytes,
    )
    import numpy as np
    
    # Test PCM16 to float32 and back
    original = np.array([0, 1000, -1000, 32767, -32768], dtype=np.int16)
    original_bytes = original.tobytes()
    float_array = pcm16_to_float32(original_bytes)
    recovered = float32_to_pcm16(float_array)
    
    print(f"  PCM16 roundtrip: {len(original_bytes)} bytes -> float32 -> {len(recovered)} bytes")
    assert len(recovered) == len(original_bytes)
    
    # Test resampling
    audio_8k = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 8000)).astype(np.float32)
    pcm16_8k = (audio_8k * 32767).astype(np.int16).tobytes()
    pcm16_16k = resample_8k_to_16k(pcm16_8k)
    pcm16_back = resample_16k_to_8k(pcm16_16k)
    print(f"  8kHz->16kHz: {len(pcm16_8k)} -> {len(pcm16_16k)} bytes (ratio ~2x)")
    print(f"  16kHz->8kHz: {len(pcm16_16k)} -> {len(pcm16_back)} bytes (ratio ~0.5x)")
    
    print("  PASS: Audio utils work correctly")


async def test_barge_in():
    print("\n=== Test 10: Barge-In Detection ===")
    from telephony.barge_in import BargeInDetector, detect_speech_in_chunk
    import numpy as np
    
    # Silence should not trigger
    silence = np.zeros(16000, dtype=np.float32)
    assert detect_speech_in_chunk(silence) == False
    print("  Silence detection: no speech = False")
    
    # Speech-like energy should trigger
    speech = np.random.randn(16000).astype(np.float32) * 0.1
    assert detect_speech_in_chunk(speech) == True
    print("  Speech detection: random signal = True")
    
    # Barge-in detector
    detector = BargeInDetector()
    detector.set_tts_playing(True)
    assert detector.process_inbound(speech) == True
    print("  Barge-in during TTS: True")
    
    detector.set_tts_playing(False)
    assert detector.process_inbound(speech) == False
    print("  No barge-in when TTS not playing: False")
    
    print("  PASS: Barge-in detection works correctly")


async def test_config_values():
    print("\n=== Test 11: Config Values ===")
    from config import (
        STT_SERVICE_URL, CLASSIFIER_SERVICE_URL, BACKEND_SERVICE_URL,
        OLLAMA_BASE_URL, PRIMARY_LLM, PRIMARY_TTS, NETWORK_MODE,
        AUDIO_SAMPLE_RATE, INTERNAL_SAMPLE_RATE, STT_CONFIDENCE_THRESHOLD,
    )
    
    assert STT_SERVICE_URL == "http://localhost:8001"
    assert CLASSIFIER_SERVICE_URL == "http://localhost:8002"
    assert BACKEND_SERVICE_URL == "http://localhost:8000"
    assert AUDIO_SAMPLE_RATE == 8000
    assert INTERNAL_SAMPLE_RATE == 16000
    print(f"  STT URL: {STT_SERVICE_URL}")
    print(f"  Classifier URL: {CLASSIFIER_SERVICE_URL}")
    print(f"  Backend URL: {BACKEND_SERVICE_URL}")
    print(f"  Ollama URL: {OLLAMA_BASE_URL}")
    print(f"  Primary LLM: {PRIMARY_LLM}")
    print(f"  Primary TTS: {PRIMARY_TTS}")
    print(f"  Network Mode: {NETWORK_MODE}")
    print("  PASS: Config values correct")


async def main():
    print("=" * 60)
    print("  Lakshya Voice Agent - Phase 2 Integration Tests")
    print("=" * 60)
    
    tests = [
        test_session_creation,
        test_fsm_transitions,
        test_coordinator_greeting,
        test_coordinator_collecting,
        test_coordinator_confirmation_yes,
        test_coordinator_confirmation_no,
        test_empty_input,
        test_fmg_corrections,
        test_audio_utils,
        test_barge_in,
        test_config_values,
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