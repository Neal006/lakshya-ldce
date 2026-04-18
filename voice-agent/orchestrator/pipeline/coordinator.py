import asyncio
import logging
from pipeline.session import CallSession, SessionState, SessionManager
from config import MAX_TURNS

logger = logging.getLogger(__name__)


class PipelineCoordinator:
    def __init__(self, session_manager: SessionManager = None):
        self.session_manager = session_manager or SessionManager()

    async def process_text(self, text: str, session: CallSession) -> dict:
        """
        Process text input through the agent pipeline.
        Used for both telephony and API testing.
        Returns dict with 'tts_text' and any agent results.
        """
        if not text or not text.strip():
            return {"tts_text": "I'm sorry, I didn't catch that. Could you please repeat?", "state": session.state.value}

        session.transcript.append(text)
        session.turn_count += 1

        if session.state == SessionState.greeting:
            session.state = SessionState.collecting
            return await self._handle_collecting(session)

        elif session.state == SessionState.collecting:
            return await self._handle_collecting(session)

        elif session.state == SessionState.confirming:
            return await self._handle_confirming(session)

        elif session.state in (SessionState.ticket_created, SessionState.done):
            return {
                "tts_text": "Your complaint has already been registered. Thank you for calling. Goodbye.",
                "state": session.state.value,
            }

        return {"tts_text": "I'm sorry, something went wrong. Let me transfer you to an agent.", "state": session.state.value}

    async def _handle_collecting(self, session: CallSession) -> dict:
        """Extract complaint data from transcript using Dialog Agent."""
        try:
            from agents.dialog import extract_complaint
            extraction = await extract_complaint(session.full_transcript)
            session.extracted_data = extraction
        except Exception as e:
            logger.error(f"Dialog Agent error: {e}")
            extraction = {"complaint_type": "Product", "description": session.full_transcript, "confidence": 0.3, "missing_fields": []}

        confidence = extraction.get("confidence", 0.0)
        missing = extraction.get("missing_fields", [])

        if confidence < 0.6 or (missing and session.turn_count < session.max_turns - 1):
            field_names = ", ".join(missing) if missing else "more details"
            return {"tts_text": f"I understand. Could you tell me about the {field_names}?", "state": session.state.value}

        session.state = SessionState.confirming
        summary = extraction.get("description", session.full_transcript)
        category = extraction.get("complaint_type", "Product")
        return {"tts_text": f"I understand you have a {category} issue: {summary}. Is that correct?", "state": session.state.value}

    async def _handle_confirming(self, session: CallSession) -> dict:
        """Handle user confirmation of extracted data."""
        last_text = session.transcript[-1].lower().strip() if session.transcript else ""

        if any(word in last_text for word in ["yes", "correct", "right", "yeah", "haan", "ji", "ok", "okay"]):
            session.state = SessionState.classifying
            return await self._handle_classifying(session)
        elif any(word in last_text for word in ["no", "wrong", "incorrect", "nahi"]):
            session.state = SessionState.collecting
            session.turn_count = 0
            return {"tts_text": "I'm sorry about that. Could you please describe your issue again?", "state": session.state.value}
        else:
            return {"tts_text": f"I heard: {session.transcript[-1]}. Please say yes to confirm or no to correct.", "state": session.state.value}

    async def _handle_classifying(self, session: CallSession) -> dict:
        """Classify the confirmed complaint, generate resolution, and create ticket."""
        # --- Step 1: Classify (fast — ONNX, 10-30ms) ---
        try:
            from agents.classify_client import classify_complaint
            classification = await classify_complaint(session.full_transcript)
            session.classification = classification
        except Exception as e:
            logger.error(f"Classification error: {e}")
            session.classification = {"category": session.extracted_data.get("complaint_type", "Product"), "priority": "Medium", "sentiment_score": 0.0}

        # --- Step 2: Resolve (LLM call, 0.5-4s) ---
        session.state = SessionState.resolving
        try:
            from agents.resolve import generate_resolution
            resolution = await generate_resolution(
                text=session.full_transcript,
                category=session.classification.get("category", "Product"),
                priority=session.classification.get("priority", "Medium"),
                sentiment=session.classification.get("sentiment_score", 0.0),
            )
            session.resolution = resolution
        except Exception as e:
            logger.error(f"Resolve error: {e}")
            session.resolution = {"steps": ["Investigate the complaint", "Contact customer for details"], "escalation": False}

        # --- Step 3: Build TTS response immediately, create ticket in background ---
        session.state = SessionState.ticket_created

        raw_steps = session.resolution.get("steps", [])[:2]
        steps_text = ". ".join(str(s) if isinstance(s, dict) else s for s in raw_steps)

        # Fire ticket creation in background — don't make the caller wait
        asyncio.create_task(self._create_ticket_background(session))

        return {
            "tts_text": f"Your complaint has been registered and is being processed. {steps_text}. You will receive updates shortly. Thank you for calling.",
            "state": session.state.value,
            "classification": session.classification,
            "resolution": session.resolution,
        }

    async def _create_ticket_background(self, session: CallSession) -> None:
        """Create the ticket in the backend without blocking the TTS response."""
        try:
            from agents.ticket_client import create_ticket
            customer_name = session.extracted_data.get("customer_name") or "Voice Caller"
            if not customer_name.strip():
                customer_name = "Voice Caller"
            ticket = await create_ticket(
                raw_text=session.full_transcript,
                category=session.classification.get("category", "Product"),
                priority=session.classification.get("priority", "Medium"),
                sentiment_score=session.classification.get("sentiment_score", 0.0),
                resolution_steps=session.resolution.get("steps", []),
                customer_name=customer_name,
            )
            if ticket:
                session.ticket_id = str(ticket.get("id", ""))
                session.state = SessionState.done
                logger.info(f"Ticket created: {session.ticket_id}")
            else:
                logger.warning("Ticket creation returned None")
        except Exception as e:
            logger.error(f"Background ticket creation error: {e}")
