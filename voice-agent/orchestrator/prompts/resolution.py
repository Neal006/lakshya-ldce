RESOLUTION_PROMPT = """Generate specific resolution steps for this complaint.

Complaint: "{complaint}"
Category: {category}
Priority: {priority}
Customer sentiment score: {sentiment_score}

Return a JSON object with:
- steps: a list of 2-3 specific, actionable resolution steps (each step must be a plain string, NOT an object or dict)
- escalation: boolean, should this be escalated to a human agent?
- estimated_resolution: estimated time to resolve (e.g., "2-4 hours", "1 business day")

Rules:
- Steps must be specific to the category ({category}), not generic
- For "Product" issues: focus on verification, warranty, replacement
- For "Packaging" issues: focus on documentation, carrier claims, replacement shipment
- For "Trade" issues: focus on order verification, logistics coordination, timeline
- If priority is "High" or sentiment is very negative (below -0.6), set escalation to true
- Do not include steps like "listen to customer" or "document the issue" only action steps
- Steps should be things a support agent can actually do"""