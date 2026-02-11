from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

import asyncpg

from app.schemas import EventImpactResult, OutcomeUpdateRequest, UserState


class Repository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def ensure_user_state(self, user_id: str) -> UserState:
        row = await self.conn.fetchrow("SELECT * FROM user_state WHERE user_id=$1", user_id)
        if row is None:
            await self.conn.execute(
                """
                INSERT INTO user_state (user_id) VALUES ($1)
                ON CONFLICT (user_id) DO NOTHING
                """,
                user_id,
            )
            row = await self.conn.fetchrow("SELECT * FROM user_state WHERE user_id=$1", user_id)
        assert row is not None
        return UserState(**dict(row))

    async def get_idempotent_response(self, user_id: str, idempotency_key: str) -> Optional[Dict[str, Any]]:
        row = await self.conn.fetchrow(
            "SELECT response_json FROM chat_idempotency WHERE user_id=$1 AND idempotency_key=$2",
            user_id,
            idempotency_key,
        )
        return dict(row['response_json']) if row else None

    async def save_idempotent_response(
        self,
        user_id: str,
        idempotency_key: str,
        request_payload: Dict[str, Any],
        response_payload: Dict[str, Any],
    ) -> None:
        request_hash = hashlib.sha256(json.dumps(request_payload, sort_keys=True).encode('utf-8')).hexdigest()
        await self.conn.execute(
            """
            INSERT INTO chat_idempotency (user_id, idempotency_key, request_hash, response_json)
            VALUES ($1, $2, $3, $4::jsonb)
            ON CONFLICT (user_id, idempotency_key) DO NOTHING
            """,
            user_id,
            idempotency_key,
            request_hash,
            json.dumps(response_payload),
        )

    async def insert_conversation(self, user_id: str, session_id: UUID, role: str, content: str) -> None:
        await self.conn.execute(
            """
            INSERT INTO conversation_history (user_id, session_id, role, content)
            VALUES ($1, $2, $3, $4)
            """,
            user_id,
            session_id,
            role,
            content,
        )

    async def insert_memory_entry(
        self,
        user_id: str,
        impact: EventImpactResult,
        raw_context: str,
        continuity_cost: float,
        memory_weight: float,
        memory_layer: int,
        risk_vector: List[float],
    ) -> UUID:
        row = await self.conn.fetchrow(
            """
            INSERT INTO memory_entries (
                user_id, event_class, raw_context,
                delta_money, delta_time, delta_energy, delta_asset, delta_reliability, delta_identity,
                axis_confidence, missing_axes,
                pre_state_snapshot,
                continuity_cost, irreversible, system_caused,
                memory_weight, memory_layer, risk_vector
            ) VALUES (
                $1, $2, $3,
                $4, $5, $6, $7, $8, $9,
                $10::jsonb, $11::jsonb,
                $12::jsonb,
                $13, $14, $15,
                $16, $17, $18
            ) RETURNING entry_id
            """,
            user_id,
            impact.event_class,
            raw_context,
            impact.impact_vector.delta_money,
            impact.impact_vector.delta_time,
            impact.impact_vector.delta_energy,
            impact.impact_vector.delta_asset,
            impact.impact_vector.delta_reliability,
            impact.impact_vector.delta_identity,
            json.dumps(impact.axis_confidence.model_dump()),
            json.dumps(impact.missing_axes),
            json.dumps({}),
            continuity_cost,
            impact.irreversible,
            impact.system_caused,
            memory_weight,
            memory_layer,
            risk_vector,
        )
        return row['entry_id']

    async def write_state_evidence(
        self,
        user_id: str,
        axis: str,
        before_value: float,
        after_value: float,
        signal_type: str,
        signal_text: str,
        weight: float,
        confidence: float,
    ) -> None:
        await self.conn.execute(
            """
            INSERT INTO state_evidence (
                user_id, resource_axis, before_value, after_value,
                signal_type, signal_text, weight, confidence
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
            """,
            user_id,
            axis,
            before_value,
            after_value,
            signal_type,
            signal_text,
            weight,
            confidence,
        )

    async def update_user_state_axis(
        self,
        user_id: str,
        axis: str,
        value: float,
        confidence: float,
        main_constraint: Optional[str],
        uncertainty_meta: float,
    ) -> None:
        value_col = f"{axis}_value"
        conf_col = f"{axis}_confidence"
        now = datetime.now(timezone.utc)
        await self.conn.execute(
            f"""
            UPDATE user_state
            SET {value_col}=$2,
                {conf_col}=$3,
                main_constraint=$4,
                uncertainty_meta=$5,
                update_count=update_count+1,
                last_updated=$6
            WHERE user_id=$1
            """,
            user_id,
            value,
            confidence,
            main_constraint,
            uncertainty_meta,
            now,
        )

    async def insert_decision_log(
        self,
        user_id: str,
        context: str,
        candidate_actions: List[Dict[str, Any]],
        selected_action: Dict[str, Any],
        predicted_gain: float,
        predicted_risk: float,
        uncertainty_penalty: float,
        memory_penalty: float,
        decision_score: float,
        trace_id: Optional[str] = None,
    ) -> int:
        row = await self.conn.fetchrow(
            """
            INSERT INTO decision_log (
                user_id, context, candidate_actions, selected_action,
                predicted_gain, predicted_risk, uncertainty_penalty, memory_penalty, decision_score, trace_id
            ) VALUES ($1, $2, $3::jsonb, $4::jsonb, $5, $6, $7, $8, $9, $10)
            RETURNING id
            """,
            user_id,
            context,
            json.dumps(candidate_actions),
            json.dumps(selected_action),
            predicted_gain,
            predicted_risk,
            uncertainty_penalty,
            memory_penalty,
            decision_score,
            trace_id,
        )
        return int(row['id'])

    async def insert_action_outcome_pending(
        self,
        decision_id: int,
        user_id: str,
        predicted_impact_vector: Dict[str, Any],
        predicted_cost: float,
    ) -> UUID:
        row = await self.conn.fetchrow(
            """
            INSERT INTO action_outcome (
                decision_id, user_id,
                predicted_impact_vector,
                predicted_cost,
                continuity_failure
            ) VALUES ($1, $2, $3::jsonb, $4, FALSE)
            ON CONFLICT (decision_id) DO UPDATE
            SET user_id=EXCLUDED.user_id,
                predicted_impact_vector=EXCLUDED.predicted_impact_vector,
                predicted_cost=EXCLUDED.predicted_cost
            RETURNING outcome_id
            """,
            decision_id,
            user_id,
            json.dumps(predicted_impact_vector),
            predicted_cost,
        )
        return row['outcome_id']

    async def update_action_outcome(
        self,
        decision_id: int,
        user_id: str,
        req: OutcomeUpdateRequest,
    ) -> Optional[Dict[str, Any]]:
        row = await self.conn.fetchrow(
            """
            SELECT outcome_id, predicted_impact_vector, predicted_cost
            FROM action_outcome
            WHERE decision_id=$1 AND user_id=$2
            LIMIT 1
            """,
            decision_id,
            user_id,
        )
        if row is None:
            return None

        predicted_impact = dict(row['predicted_impact_vector'] or {})
        predicted_cost = row['predicted_cost']
        actual_impact = req.actual_impact_vector

        vector_error_l1 = 0.0
        keys = set(predicted_impact.keys()) | set(actual_impact.keys())
        for k in keys:
            vector_error_l1 += abs(float(predicted_impact.get(k, 0.0)) - float(actual_impact.get(k, 0.0)))

        cost_error = None if predicted_cost is None else float(req.actual_cost) - float(predicted_cost)

        updated = await self.conn.fetchrow(
            """
            UPDATE action_outcome
            SET actual_impact_vector=$1::jsonb,
                vector_error_l1=$2,
                actual_cost=$3,
                cost_error=$4,
                continuity_failure=$5,
                failure_type=$6,
                user_visible_cost=$7,
                preventable=$8
            WHERE outcome_id=$9
            RETURNING *
            """,
            json.dumps(actual_impact),
            vector_error_l1,
            req.actual_cost,
            cost_error,
            req.continuity_failure,
            req.failure_type,
            req.user_visible_cost,
            req.preventable,
            row['outcome_id'],
        )
        return dict(updated) if updated else None

    async def put_shell_object(
        self,
        user_id: str,
        social_interface: Dict[str, Any],
        narratives: Dict[str, Any],
        confidence: str,
        validity: str,
        source: str,
    ) -> Dict[str, Any]:
        payload = {
            'type': 'shell',
            'social_interface': social_interface,
            'narratives': narratives,
            'source': source,
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }
        text_index = self._build_object_index('shell', name='', intent='', slots=[], tags=[], updated_at=payload['updated_at'])
        row = await self.conn.fetchrow(
            """
            INSERT INTO memory_objects (user_id, object_type, name, text_index, payload_json, confidence, validity, updated_at)
            VALUES ($1, 'shell', NULL, $2, $3::jsonb, $4, $5, $6)
            RETURNING object_id, object_type, name, payload_json, confidence, validity, updated_at
            """,
            user_id,
            text_index,
            json.dumps(payload),
            confidence,
            validity,
            payload['updated_at'],
        )
        return dict(row)

    async def put_success_path_object(
        self,
        user_id: str,
        name: str,
        intent: str,
        required_slots: List[str],
        slot_definitions: Dict[str, str],
        procedure: str,
        success_criteria: str,
        confidence: str,
        validity: str,
        tags: List[str],
    ) -> Dict[str, Any]:
        payload = {
            'type': 'success_path',
            'name': name,
            'intent': intent,
            'required_slots': required_slots,
            'slot_definitions': slot_definitions,
            'procedure': procedure,
            'success_criteria': success_criteria,
            'tags': tags,
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }
        text_index = self._build_object_index(
            'success_path',
            name=name,
            intent=intent,
            slots=required_slots,
            tags=tags,
            updated_at=payload['updated_at'],
        )
        row = await self.conn.fetchrow(
            """
            INSERT INTO memory_objects (user_id, object_type, name, text_index, payload_json, confidence, validity, updated_at)
            VALUES ($1, 'success_path', $2, $3, $4::jsonb, $5, $6, $7)
            RETURNING object_id, object_type, name, payload_json, confidence, validity, updated_at
            """,
            user_id,
            name,
            text_index,
            json.dumps(payload),
            confidence,
            validity,
            payload['updated_at'],
        )
        return dict(row)

    async def get_latest_shell(self, user_id: str) -> Optional[Dict[str, Any]]:
        row = await self.conn.fetchrow(
            """
            SELECT object_id, object_type, name, payload_json, confidence, validity, updated_at
            FROM memory_objects
            WHERE user_id=$1 AND object_type='shell'
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            user_id,
        )
        return dict(row) if row else None

    async def list_memory_objects(self, user_id: str, object_type: Optional[str], limit: int = 50) -> List[Dict[str, Any]]:
        if object_type:
            rows = await self.conn.fetch(
                """
                SELECT object_id, object_type, name, payload_json, confidence, validity, updated_at
                FROM memory_objects
                WHERE user_id=$1 AND object_type=$2
                ORDER BY updated_at DESC
                LIMIT $3
                """,
                user_id,
                object_type,
                limit,
            )
        else:
            rows = await self.conn.fetch(
                """
                SELECT object_id, object_type, name, payload_json, confidence, validity, updated_at
                FROM memory_objects
                WHERE user_id=$1
                ORDER BY updated_at DESC
                LIMIT $2
                """,
                user_id,
                limit,
            )
        return [dict(r) for r in rows]

    async def create_high_risk_confirmation(
        self,
        decision_id: int,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
        reason: str,
        payload: Dict[str, Any],
    ) -> UUID:
        row = await self.conn.fetchrow(
            """
            INSERT INTO high_risk_confirmations (
                decision_id, user_id, token_hash, expires_at, reason, payload
            ) VALUES ($1, $2, $3, $4, $5, $6::jsonb)
            RETURNING confirmation_id
            """,
            decision_id,
            user_id,
            token_hash,
            expires_at,
            reason,
            json.dumps(payload),
        )
        return row['confirmation_id']

    async def consume_high_risk_confirmation(self, decision_id: int, user_id: str, token: str) -> Optional[Dict[str, Any]]:
        token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
        row = await self.conn.fetchrow(
            """
            UPDATE high_risk_confirmations
            SET consumed_at=NOW()
            WHERE decision_id=$1
              AND user_id=$2
              AND token_hash=$3
              AND consumed_at IS NULL
              AND expires_at > NOW()
            RETURNING *
            """,
            decision_id,
            user_id,
            token_hash,
        )
        return dict(row) if row else None

    async def mark_decision_confirmed(self, decision_id: int, user_id: str, confirmation_id: UUID) -> Optional[Dict[str, Any]]:
        row = await self.conn.fetchrow(
            "SELECT selected_action FROM decision_log WHERE id=$1 AND user_id=$2",
            decision_id,
            user_id,
        )
        if row is None:
            return None

        action = dict(row['selected_action'] or {})
        action['confirmed'] = True
        action['confirmed_at'] = datetime.now(timezone.utc).isoformat()
        action['confirmation_id'] = str(confirmation_id)

        updated = await self.conn.fetchrow(
            """
            UPDATE decision_log
            SET selected_action=$1::jsonb
            WHERE id=$2 AND user_id=$3
            RETURNING *
            """,
            json.dumps(action),
            decision_id,
            user_id,
        )
        return dict(updated) if updated else None

    @staticmethod
    def _build_object_index(
        object_type: str,
        name: str,
        intent: str,
        slots: List[str],
        tags: List[str],
        updated_at: str,
    ) -> str:
        lines = [
            '[OM-OBJECT v1]',
            f'type:{object_type}',
            f'name:{name}',
            f'intent:{intent}',
            f"slots:{','.join(slots)}",
            f"tags:{','.join(tags)}",
            f'updated_at:{updated_at}',
        ]
        return '\n'.join(lines)
