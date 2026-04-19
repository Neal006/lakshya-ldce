import asyncio
import logging
import time
from pipeline.session import CallSession, SessionState, SessionManager
from config import MAX_TURNS

logger = logging.getLogger(__name__)


class PipelineCoordinator:
    def __init__(self, session_manager: SessionManager = None):
        self.session_manager = session_manager or SessionManager()

    async def process_text(self, text: str, session: CallSession) -> dict:
        """
        Process text input through the agent pipeline.
        Returns dict with 'tts_text' and any agent results.
        """
        start = time.time()

        if not text or not text.strip():
            return {"tts_text": "I'm sorry, I didn't catch that. Could you please repeat?", "state": session.state.value}

        session.transcript.append(text)
        session.turn_count += 1
        logger.info(f"[{session.call_sid}] state={session.state.value} turn={session.turn_count} text='{text[:80]}'")

        if session.state == SessionState.greeting:
            session.state = SessionState.collecting
            return await self._handle_collecting(session)

        elif session.state == SessionState.collecting:
            return await self._handle_collecting(session)

        elif session.state == SessionState.confirming:
            return await self._handle_confirming(session)

        elif session.state == SessionState.satisfaction_check:
            return await self._handle_satisfaction(session)

        elif session.state in (SessionState.ticket_created, SessionState.done):
            return {
                "tts_text": "Your complaint has already been registered. Thank you for calling. Goodbye.",
                "state": session.state.value,
            }

        elapsed = round((time.time() - start) * 1000, 1)
        logger.warning(f"[{session.call_sid}] Unhandled state {session.state.value} ({elapsed}ms)")
        return {"tts_text": "I'm sorry, something went wrong. Let me transfer you to an agent.", "state": session.state.value}

    async def _handle_collecting(self, session: CallSession) -> dict:
        """Extract complaint data from transcript using Dialog Agent."""
        start = time.time()
        try:
            from agents.dialog import extract_complaint
            extraction = await extract_complaint(session.full_transcript)
            session.extracted_data = extraction
            logger.info(f"[{session.call_sid}] Extraction: type={extraction.get('complaint_type')} "
                        f"confidence={extraction.get('confidence', 0):.2f} "
                        f"missing={extraction.get('missing_fields', [])} ({round((time.time()-start)*1000)}ms)")
        except Exception as e:
            logger.error(f"[{session.call_sid}] Dialog Agent error: {e}", exc_info=True)
            extraction = {"complaint_type": "Product", "description": session.full_transcript, "confidence": 0.3, "missing_fields": []}

        # Use caller phone from Twilio if not extracted from speech
        if not extraction.get("customer_phone") and session.caller_phone:
            extraction["customer_phone"] = session.caller_phone
            session.extracted_data["customer_phone"] = session.caller_phone

        # Skip collection loop and confirmation — go straight to classify + resolve
        session.state = SessionState.classifying
        return await self._handle_classifying(session)

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
        """Classify the confirmed complaint, generate resolution via GenAI service."""
        pipeline_start = time.time()

        # --- Step 1: Classify (fast ONNX, 10-30ms) ---
        try:
            from agents.classify_client import classify_complaint
            classification = await classify_complaint(session.full_transcript)
            session.classification = classification
            logger.info(f"[{session.call_sid}] Classification: {classification}")
        except Exception as e:
            logger.error(f"[{session.call_sid}] Classification error: {e}", exc_info=True)
            session.classification = {
                "category": session.extracted_data.get("complaint_type", "Product"),
                "priority": "Medium",
                "sentiment_score": 0.0,
            }

        # --- Step 2: Resolve via GenAI microservice ---
        session.state = SessionState.resolving
        try:
            from agents.resolve import generate_resolution
            customer_name = session.extracted_data.get("customer_name") or session.caller_name or "Voice Caller"
            resolution = await generate_resolution(
                text=session.full_transcript,
                category=session.classification.get("category", "Product"),
                priority=session.classification.get("priority", "Medium"),
                sentiment=session.classification.get("sentiment_score", 0.0),
                customer_name=customer_name,
            )
            session.resolution = resolution
            logger.info(f"[{session.call_sid}] Resolution: escalation={resolution.get('escalation')} "
                        f"steps={len(resolution.get('steps', []))} ({round((time.time()-pipeline_start)*1000)}ms)")
        except Exception as e:
            logger.error(f"[{session.call_sid}] Resolve error: {e}", exc_info=True)
            session.resolution = {"steps": ["Investigate the complaint", "Contact customer for details"], "escalation": False}

        # --- Step 3: Build TTS response and ask for satisfaction ---
        session.state = SessionState.satisfaction_check

        # Use the customer_response from GenAI if available (better quality)
        customer_response = session.resolution.get("customer_response", "")
        if customer_response:
            tts_text = f"{customer_response} Are you satisfied with this resolution, or would you like us to escalate this further?"
        else:
            raw_steps = session.resolution.get("steps", [])[:2]
            steps_text = ". ".join(str(s) if isinstance(s, dict) else s for s in raw_steps)
            tts_text = f"Here is what we will do for you: {steps_text}. Are you satisfied with this resolution, or would you like us to escalate this further?"

        total_ms = round((time.time() - pipeline_start) * 1000, 1)
        logger.info(f"[{session.call_sid}] Pipeline complete in {total_ms}ms, waiting for satisfaction response")

        return {
            "tts_text": tts_text,
            "state": session.state.value,
            "classification": session.classification,
            "resolution": session.resolution,
        }

    async def _handle_satisfaction(self, session: CallSession) -> dict:
        """Handle customer satisfaction response."""
        last_text = session.transcript[-1].lower().strip() if session.transcript else ""
        logger.info(f"[{session.call_sid}] Satisfaction response: '{last_text}'")

        satisfied_words = ["yes", "satisfied", "good", "fine", "okay", "ok", "great",
                           "thank", "thanks", "haan", "ji", "theek", "accha"]
        unsatisfied_words = ["no", "not", "unsatisfied", "dissatisfied", "nahi", "nope",
                             "wrong", "bad", "worse", "escalate", "agent", "human", "manager"]

        is_satisfied = any(word in last_text for word in satisfied_words)
        is_unsatisfied = any(word in last_text for word in unsatisfied_words)

        if is_unsatisfied and not (is_satisfied and not is_unsatisfied):
            # Not satisfied -> create escalated ticket for admin portal
            session.state = SessionState.ticket_created
            session.resolution["escalation"] = True
            asyncio.create_task(self._create_ticket_background(session, escalated=True))
            logger.info(f"[{session.call_sid}] Customer NOT satisfied -> escalating to admin")

            return {
                "tts_text": "I understand your concern. I have escalated your complaint to our senior team. "
                            "A representative will contact you shortly on your registered number. "
                            "Thank you for your patience. Goodbye.",
                "state": session.state.value,
            }
        elif is_satisfied:
            # Satisfied -> create resolved ticket, end call
            session.state = SessionState.done
            asyncio.create_task(self._create_ticket_background(session, escalated=False))
            logger.info(f"[{session.call_sid}] Customer satisfied -> closing")

            return {
                "tts_text": "Thank you for your patience. Your complaint has been registered and our team will ensure it is resolved promptly. "
                            "Have a great day. Goodbye.",
                "state": session.state.value,
            }
        else:
            # Unclear response
            return {
                "tts_text": "I'm sorry, I didn't catch that. Are you satisfied with the resolution? Please say yes or no.",
                "state": session.state.value,
            }

    async def _create_ticket_background(self, session: CallSession, escalated: bool = False) -> None:
        """Create the ticket in the backend without blocking the TTS response."""
        try:
            from agents.ticket_client import create_ticket
            customer_name = session.extracted_data.get("customer_name") or session.caller_name or "Voice Caller"
            if not customer_name.strip():
                customer_name = "Voice Caller"

            customer_phone = session.extracted_data.get("customer_phone") or session.caller_phone or ""

            # Override priority to High if escalated by customer
            priority = session.classification.get("priority", "Medium")
            if escalated:
                priority = "High"

            ticket = await create_ticket(
                raw_text=session.full_transcript,
                category=session.classification.get("category", "Product"),
                priority=priority,
                sentiment_score=session.classification.get("sentiment_score", 0.0),
                resolution_steps=session.resolution.get("steps", []),
                customer_name=customer_name,
                customer_phone=customer_phone,
            )
            if ticket:
                session.ticket_id = str(ticket.get("id", ""))
                session.state = SessionState.done
                logger.info(f"[{session.call_sid}] Ticket created: id={session.ticket_id} escalated={escalated} "
                            f"phone={customer_phone} name={customer_name}")
            else:
                logger.warning(f"[{session.call_sid}] Ticket creation returned None")
        except Exception as e:
            logger.error(f"[{session.call_sid}] Background ticket creation error: {e}", exc_info=True)
