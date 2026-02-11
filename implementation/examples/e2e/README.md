# E2E API Demo

This folder provides end-to-end examples for:
1. `/chat`
2. `/decision/{decision_id}/confirm`
3. `/decision/{decision_id}/outcome`

## Quick run

```bash
cd implementation
BASE_URL=http://127.0.0.1:8000 USER_ID=demo_user bash examples/e2e/run_curl_e2e.sh
```

## What to expect
- `POST /chat` returns `trace.decision_id`.
- If high-risk gate hits, `trace.high_risk_confirmation.required=true` and script auto-calls `/confirm`.
- Script always calls `/outcome` to close the feedback loop.

## Sample payloads
- `01_chat_request_high_risk.json`
- `01_chat_request_normal.json`
- `02_confirm_request_template.json`
- `03_outcome_request.json`
