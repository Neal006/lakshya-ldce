EXTRACTION_PROMPT = """Extract complaint information from this customer call transcript.

Transcript: "{transcript}"

Return a JSON object with these fields:
- complaint_type: one of "Product", "Packaging", "Trade"
- description: a clear, concise summary of the complaint in 1-2 sentences
- product_or_brand: the specific product or brand mentioned (or "unknown" if not mentioned)
- urgency_signal: one of "high", "medium", "low"
- customer_name: the caller's name if mentioned (or empty string)
- customer_phone: the caller's phone number if mentioned (or empty string)
- confidence: your confidence in the extraction from 0.0 to 1.0
- missing_fields: list of fields that are missing or unclear and need follow-up

Rules:
- If the complaint type is ambiguous, choose the most likely one
- "urgency_signal" should be "high" if the caller sounds angry, uses words like "urgent", "immediately", or mentions safety/legal
- If the description is unclear, set confidence below 0.5 and add "description" to missing_fields
- Always extract the core issue, not peripheral details
- For Indian names, accept common Hindi/English name patterns"""