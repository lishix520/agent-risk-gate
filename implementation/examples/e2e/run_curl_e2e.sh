#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
USER_ID="${USER_ID:-demo_user}"

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required"
  exit 1
fi

CHAT_IDEMPOTENCY="demo-$(date +%s)"
CHAT_PAYLOAD=$(jq -n --arg uid "$USER_ID" --arg idk "$CHAT_IDEMPOTENCY" '{user_id:$uid,message:"我刚刚误删了核心配置，可能需要强制回滚，风险很高。",idempotency_key:$idk}')

echo "[1/3] POST /chat"
CHAT_RESP=$(curl -sS -X POST "$BASE_URL/chat" -H 'content-type: application/json' -d "$CHAT_PAYLOAD")
echo "$CHAT_RESP" | jq .

DECISION_ID=$(echo "$CHAT_RESP" | jq -r '.trace.decision_id // empty')
if [ -z "$DECISION_ID" ]; then
  echo "missing trace.decision_id"
  exit 1
fi

CONFIRM_REQUIRED=$(echo "$CHAT_RESP" | jq -r '.trace.high_risk_confirmation.required // false')
CONFIRM_TOKEN=$(echo "$CHAT_RESP" | jq -r '.trace.high_risk_confirmation.confirm_token // empty')

if [ "$CONFIRM_REQUIRED" = "true" ] && [ -n "$CONFIRM_TOKEN" ]; then
  echo "[2/3] POST /decision/$DECISION_ID/confirm"
  CONFIRM_PAYLOAD=$(jq -n --arg uid "$USER_ID" --arg tok "$CONFIRM_TOKEN" '{user_id:$uid,confirm_token:$tok}')
  CONFIRM_RESP=$(curl -sS -X POST "$BASE_URL/decision/$DECISION_ID/confirm" -H 'content-type: application/json' -d "$CONFIRM_PAYLOAD")
  echo "$CONFIRM_RESP" | jq .
else
  echo "[2/3] skip confirm (not required)"
fi

echo "[3/3] POST /decision/$DECISION_ID/outcome"
OUTCOME_PAYLOAD=$(jq -n '{actual_impact_vector:{delta_money:0.0,delta_time:-0.1,delta_energy:-0.1,delta_asset:-0.2,delta_reliability:-0.1,delta_identity:0.0},actual_cost:0.45,continuity_failure:false,failure_type:null,user_visible_cost:"一次额外沟通",preventable:true}')
OUTCOME_RESP=$(curl -sS -X POST "$BASE_URL/decision/$DECISION_ID/outcome?user_id=$USER_ID" -H 'content-type: application/json' -d "$OUTCOME_PAYLOAD")
echo "$OUTCOME_RESP" | jq .

echo "done"
