from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import asyncpg

from app.config import settings
from app.core.cost_calculator import ContinuityCostCalculator
from app.core.state_manager import UserStateManager
from app.db.repositories import Repository
from app.schemas import ChatRequest, ChatResponse, DecisionScore, EventImpactResult
from app.subagents.constraint_intake import ConstraintIntakeAgent
from app.subagents.decision_scoring import DecisionScoringAgent
from app.subagents.impact_extractor import ImpactExtractorAgent
from app.subagents.memory_retrieval import MemoryRetrievalAgent
from app.subagents.risk_audit import RiskAuditAgent


class Orchestrator:
    def __init__(self):
        self.constraint_agent = ConstraintIntakeAgent()
        self.impact_agent = ImpactExtractorAgent()
        self.memory_agent = MemoryRetrievalAgent()
        self.audit_agent = RiskAuditAgent()
        self.scoring_agent = DecisionScoringAgent()

    async def handle_chat(self, conn: asyncpg.Connection, req: ChatRequest) -> ChatResponse:
        repo = Repository(conn)

        existing = await repo.get_idempotent_response(req.user_id, req.idempotency_key)
        if existing:
            return ChatResponse.model_validate(existing)

        session_id = req.session_id or uuid.uuid4()
        trace_id = str(uuid.uuid4())

        state = await repo.ensure_user_state(req.user_id)

        # 1) Ask-Then-Act gating
        intake = await self.constraint_agent.run({'message': req.message, 'known_slots': {}})
        task_type = intake.data.get('task_type')
        required_slots = list(intake.data.get('required_slots') or [])
        missing = list(intake.data.get('missing_slots') or [])
        questions = list(intake.data.get('questions') or []) if missing else []
        shell_bias = dict(intake.data.get('shell_bias') or {})
        shell_bias_hit = bool(shell_bias.get('hit'))
        shell_bias_questions = list(shell_bias.get('questions') or [])
        use_reality_hint = (
            settings.reality_first_mode.lower() != 'off'
            and shell_bias_hit
            and task_type in {'execution', 'complex_decision'}
        )

        if use_reality_hint and questions and shell_bias_questions and len(questions) < 3:
            hint_q = shell_bias_questions[0]
            if hint_q not in questions:
                questions.append(hint_q)

        if questions and task_type in {'execution', 'complex_decision'}:
            resp = ChatResponse(
                session_id=session_id,
                response='在执行前需要补齐关键槽位。',
                asked_questions=questions,
                user_state=state,
                trace={
                    'trace_id': trace_id,
                    'mode': 'clarify_first',
                    'task_type': task_type,
                    'missing_slots': missing,
                    'reality_first': {
                        'mode': settings.reality_first_mode,
                        'shell_bias_hit': shell_bias_hit,
                        'intervention': 'hint' if use_reality_hint else 'none',
                    },
                },
            )
            await repo.insert_conversation(req.user_id, session_id, 'user', req.message)
            await repo.insert_conversation(req.user_id, session_id, 'assistant', resp.response + ' ' + ' | '.join(questions))
            await repo.save_idempotent_response(
                req.user_id,
                req.idempotency_key,
                req.model_dump(mode='json'),
                resp.model_dump(mode='json'),
            )
            return resp

        # 2) Impact extraction
        impact_res = await self.impact_agent.run({'message': req.message, 'user_state': state.model_dump()})
        impact = EventImpactResult.model_validate(impact_res.data)

        # 3) Update state with evidence
        for axis in UserStateManager.AXES:
            before = float(getattr(state, f'{axis}_value'))
            new_value, new_conf = UserStateManager.update_axis_from_impact(state, impact, axis)
            await repo.write_state_evidence(
                req.user_id,
                axis,
                before,
                new_value,
                'language',
                req.message,
                weight=0.6,
                confidence=max(0.1, min(1.0, float(getattr(impact.axis_confidence, axis)))),
            )
            setattr(state, f'{axis}_value', new_value)
            setattr(state, f'{axis}_confidence', new_conf)

        state.main_constraint = UserStateManager.identify_main_constraint(state)
        state.uncertainty_meta = max(0.0, 1.0 - impact.analysis_confidence)

        for axis in UserStateManager.AXES:
            await repo.update_user_state_axis(
                req.user_id,
                axis,
                float(getattr(state, f'{axis}_value')),
                float(getattr(state, f'{axis}_confidence')),
                state.main_constraint,
                state.uncertainty_meta,
            )

        # 4) Cost and memory
        scarcity = UserStateManager.calculate_scarcity_weights(state)
        predicted_cost = ContinuityCostCalculator.calculate(impact, scarcity, state)
        risk_vector = ContinuityCostCalculator.risk_vector(impact, predicted_cost)
        memory_weight = ContinuityCostCalculator.memory_weight(predicted_cost, impact.irreversible)
        memory_layer = ContinuityCostCalculator.memory_layer(predicted_cost)

        entry_id = await repo.insert_memory_entry(
            req.user_id,
            impact,
            raw_context=req.message,
            continuity_cost=predicted_cost,
            memory_weight=memory_weight,
            memory_layer=memory_layer,
            risk_vector=risk_vector,
        )

        # 5) Memory retrieval with pre-gate and feature retrieval
        mem = await self.memory_agent.run(
            {
                'conn': conn,
                'user_id': req.user_id,
                'risk_vector': risk_vector,
                'intent_query': req.message,
                'required_slots': required_slots,
                'main_constraint': state.main_constraint,
                'l4_similarity_gate': settings.l4_similarity_gate,
            }
        )
        similar_memories = list(mem.data.get('similar_memories') or [])
        best_success_path = mem.data.get('best_success_path')
        ranked_success_paths = list(mem.data.get('ranked_success_paths') or [])
        l4_gate = dict(mem.data.get('l4_gate') or {})
        feature_penalty = float(mem.data.get('feature_penalty') or 0.0)
        matched_failure_types = list(mem.data.get('matched_failure_types') or [])

        # 6) Pre-score gate (L4 high risk)
        predicted_gain = max(0.0, -impact.impact_vector.delta_time + max(0.0, impact.impact_vector.delta_identity))
        uncertainty_penalty = settings.uncertainty_k * (1.0 - impact.analysis_confidence)

        if bool(l4_gate.get('hit')):
            score = DecisionScore(
                score=-999.0,
                predicted_gain=predicted_gain,
                predicted_risk=predicted_cost + 120.0 + feature_penalty,
                memory_penalty=120.0 + feature_penalty,
                uncertainty_penalty=uncertainty_penalty,
            )
            candidate_actions = [
                {'name': 'confirm_high_risk', 'description': 'explicit second confirmation required'},
                {'name': 'recovery_mode', 'description': 'switch to safer path'},
            ]
            selected_action = {'name': 'confirm_high_risk'}
        else:
            score_res = await self.scoring_agent.run(
                {
                    'predicted_gain': predicted_gain,
                    'predicted_cost': predicted_cost,
                    'uncertainty_penalty': uncertainty_penalty,
                    'similar_memories': similar_memories,
                }
            )
            base = DecisionScore.model_validate(score_res.data)
            score = DecisionScore(
                score=base.score - feature_penalty,
                predicted_gain=base.predicted_gain,
                predicted_risk=base.predicted_risk + feature_penalty,
                memory_penalty=base.memory_penalty + feature_penalty,
                uncertainty_penalty=base.uncertainty_penalty,
            )
            candidate_actions = [
                {'name': 'direct_execute', 'description': 'execute minimal action'},
                {'name': 'clarify', 'description': 'ask clarifying question'},
            ]
            selected_action = {'name': 'direct_execute' if score.score >= settings.safe_threshold else 'clarify'}

        used_success_path = bool(best_success_path) and selected_action['name'] == 'direct_execute'

        audit = await self.audit_agent.run(
            {
                'had_success_path': len(ranked_success_paths) > 0,
                'used_success_path': used_success_path,
                'asked_before_try': True,
                'user_repeated_context': False,
                'hallucinated': False,
            }
        )

        decision_id = await repo.insert_decision_log(
            req.user_id,
            context=req.message,
            candidate_actions=candidate_actions,
            selected_action=selected_action,
            predicted_gain=score.predicted_gain,
            predicted_risk=score.predicted_risk,
            uncertainty_penalty=score.uncertainty_penalty,
            memory_penalty=score.memory_penalty,
            decision_score=score.score,
            trace_id=trace_id,
        )

        confirm_meta: Dict[str, Any] = {'required': False}
        if selected_action['name'] == 'confirm_high_risk':
            token = secrets.token_urlsafe(24)
            token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.confirm_token_ttl_minutes)
            reason = 'l4_gate_hit'
            payload = {
                'l4_gate': l4_gate,
                'feature_penalty': feature_penalty,
                'matched_failure_types': matched_failure_types,
            }
            confirmation_id = await repo.create_high_risk_confirmation(
                decision_id=decision_id,
                user_id=req.user_id,
                token_hash=token_hash,
                expires_at=expires_at,
                reason=reason,
                payload=payload,
            )
            confirm_meta = {
                'required': True,
                'confirmation_id': str(confirmation_id),
                'confirm_token': token,
                'expires_at': expires_at.isoformat(),
                'confirm_endpoint': f'/decision/{decision_id}/confirm?user_id={req.user_id}',
            }

        outcome_id = await repo.insert_action_outcome_pending(
            decision_id=decision_id,
            user_id=req.user_id,
            predicted_impact_vector=impact.impact_vector.model_dump(),
            predicted_cost=predicted_cost,
        )

        response_text = self._build_response(
            score=score.score,
            selected_action=selected_action['name'],
            impact=impact,
            best_success_path=best_success_path,
            l4_gate=l4_gate,
            confirm_meta=confirm_meta,
            reality_hint=shell_bias_questions[0] if (use_reality_hint and shell_bias_questions) else None,
        )

        resp = ChatResponse(
            session_id=session_id,
            response=response_text,
            asked_questions=[],
            decision=score,
            user_state=state,
            trace={
                'trace_id': trace_id,
                'entry_id': str(entry_id),
                'decision_id': decision_id,
                'outcome_id': str(outcome_id),
                'outcome_status': 'pending_actual_feedback',
                'main_constraint': state.main_constraint,
                'task_type': task_type,
                'l4_gate': l4_gate,
                'feature_penalty': feature_penalty,
                'matched_failure_types': matched_failure_types,
                'high_risk_confirmation': confirm_meta,
                'reality_first': {
                    'mode': settings.reality_first_mode,
                    'shell_bias_hit': shell_bias_hit,
                    'intervention': 'hint' if use_reality_hint else 'none',
                    'question': shell_bias_questions[0] if (use_reality_hint and shell_bias_questions) else None,
                },
                'best_success_path': {
                    'object_id': best_success_path.get('object_id'),
                    'name': best_success_path.get('name'),
                    'retrieval_score': best_success_path.get('retrieval_score'),
                }
                if best_success_path
                else None,
                'continuity_failures': audit.data['continuity_failures'],
            },
        )

        await repo.insert_conversation(req.user_id, session_id, 'user', req.message)
        await repo.insert_conversation(req.user_id, session_id, 'assistant', resp.response)

        await repo.save_idempotent_response(
            req.user_id,
            req.idempotency_key,
            req.model_dump(mode='json'),
            resp.model_dump(mode='json'),
        )
        return resp

    @staticmethod
    def _build_response(
        *,
        score: float,
        selected_action: str,
        impact: EventImpactResult,
        best_success_path: Dict[str, Any] | None,
        l4_gate: Dict[str, Any],
        confirm_meta: Dict[str, Any],
        reality_hint: str | None,
    ) -> str:
        if selected_action == 'confirm_high_risk':
            top = l4_gate.get('top') or {}
            sim = top.get('similarity')
            endpoint = confirm_meta.get('confirm_endpoint')
            return (
                f'检测到高风险历史相似事件（L4门控命中，similarity={sim}）。'
                f'若确认继续，请调用确认接口：{endpoint}。'
            )
        if selected_action == 'clarify':
            base = '当前风险超过安全阈值，建议先补充关键信息后再执行。'
            if reality_hint:
                return f'{base} 现实校验问题：{reality_hint}'
            return base
        if best_success_path:
            base = f"建议优先复用已验证成功路径：{best_success_path.get('name')}，并记录实际结果回写。"
            if reality_hint:
                return f'{base} 现实校验问题：{reality_hint}'
            return base
        if impact.irreversible:
            base = '可执行，但存在不可逆风险，执行前建议先做备份或回滚点。'
            if reality_hint:
                return f'{base} 现实校验问题：{reality_hint}'
            return base
        if score < 0:
            base = '可执行，但预估收益低于风险，建议先走低成本验证。'
            if reality_hint:
                return f'{base} 现实校验问题：{reality_hint}'
            return base
        base = '已完成风险评估，建议执行最小可行动作并保留结果回写。'
        if reality_hint:
            return f'{base} 现实校验问题：{reality_hint}'
        return base
