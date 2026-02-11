# EventImpact Prompt v2.1

Use strict JSON output that matches `event_impact_v2.1` schema.

Required keys:
- schema_version
- event_summary
- event_class
- impact_vector
- axis_confidence
- missing_axes
- irreversible
- system_caused
- analysis_confidence
- baseline_used
- evidence_spans
- reasoning

Rules:
1. Unknown is not equal to zero risk.
2. If an axis is uncertain, keep value conservative, lower confidence, and include it in missing_axes.
3. Use ASCII snake_case keys only.
4. Never invent evidence; evidence_spans must map to user text.
