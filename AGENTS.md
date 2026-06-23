# AGENTS.md - Travel Spend AI Skill Demo

## Project Overview

This is a Streamlit-based MVP demonstrating AI-powered travel expense management.
It serves dual purposes:
1. Product demo of core travel spend assistant features
2. AI engineering learning lab for prompt/tool/safety concepts

## Architecture

- **Event-driven**: All interactions are modeled as events (payment.auth.success, receipt.uploaded, etc.)
- **Template fallback**: Works without API keys using pre-built response templates
- **Layered services**: ai_client → event_handler → domain services (matcher, parser, etc.)
- **Observability built-in**: Every AI call is instrumented

## Key Design Decisions

1. **No real API calls in demo mode** - Template responses ensure reproducibility
2. **Guardrails before AI** - Injection detection runs before any AI processing
3. **Confidence calibration** - Never report > 0.95 confidence (overconfidence prevention)
4. **Locked fields** - System facts cannot be modified by user verbal claims
5. **Working memory is ephemeral** - Cleared after each task to prevent context pollution

## Code Conventions

- Services are in `/services/` with singleton pattern for stateful services
- Prompts are in `/prompts/` with version suffixes (v1, v2)
- Mock data in `/data/` as JSON files
- All AI responses follow the schema: {action, message, confidence, details}

## Testing

Run evaluations via the "评估与观测" tab in the app, or:
```python
from services.evaluator import run_all_evals
results = run_all_evals()
```

## Security Considerations

- Receipt text is treated as DATA, never as instructions
- Injection patterns are checked via regex before processing
- User claims that conflict with locked system fields are rejected
- All security decisions are logged in observability
