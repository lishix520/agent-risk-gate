from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from app.subagents.base import SubagentResult


class MemoryRetrievalAgent:
    name = 'memory_retrieval'

    @staticmethod
    def _norm_tokens(text: str) -> Set[str]:
        cleaned = ''.join(ch.lower() if ch.isalnum() else ' ' for ch in text)
        return {t for t in cleaned.split() if len(t) >= 2}

    @staticmethod
    def _confidence_rank(level: str) -> float:
        m = {'high': 1.0, 'medium': 0.6, 'low': 0.3}
        return m.get((level or '').lower(), 0.3)

    @staticmethod
    def _recency_factor(updated_at: Any) -> float:
        if not updated_at:
            return 0.2
        try:
            if isinstance(updated_at, str):
                dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            else:
                dt = updated_at
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            days = max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0)
            if days <= 3:
                return 1.0
            if days <= 14:
                return 0.7
            if days <= 60:
                return 0.4
            return 0.2
        except Exception:  # noqa: BLE001
            return 0.2

    @classmethod
    def _score_success_path(
        cls,
        row: Dict[str, Any],
        *,
        intent_query: str,
        required_slots: List[str],
        main_constraint: Optional[str],
    ) -> Dict[str, Any]:
        payload = dict(row.get('payload_json') or {})
        name = str(row.get('name') or payload.get('name') or '')
        intent = str(payload.get('intent') or '')
        tags = [str(t).lower() for t in list(payload.get('tags') or [])]
        procedure = str(payload.get('procedure') or '')
        sp_slots = [str(s) for s in list(payload.get('required_slots') or [])]

        q_tokens = cls._norm_tokens(intent_query)
        s_tokens = cls._norm_tokens(' '.join([name, intent, ' '.join(tags)]))
        overlap = len(q_tokens & s_tokens)
        intent_rel = 0.0 if not q_tokens else overlap / max(1, len(q_tokens))

        required = [s for s in required_slots if s]
        slot_cov = 0.0
        if required:
            hit = len(set(required) & set(sp_slots))
            slot_cov = hit / max(1, len(required))

        constraint_rel = 0.0
        if main_constraint:
            mc = main_constraint.lower()
            text_blob = ' '.join([name.lower(), intent.lower(), procedure.lower(), ' '.join(tags)])
            constraint_rel = 1.0 if mc in text_blob else 0.0

        conf_rel = cls._confidence_rank(str(row.get('confidence') or 'low'))
        recency_rel = cls._recency_factor(row.get('updated_at'))

        score = (
            3.0 * intent_rel +
            2.5 * slot_cov +
            1.5 * constraint_rel +
            1.0 * conf_rel +
            0.5 * recency_rel
        )

        ranked = dict(row)
        ranked['retrieval_score'] = round(score, 6)
        ranked['score_breakdown'] = {
            'intent_rel': round(intent_rel, 6),
            'slot_cov': round(slot_cov, 6),
            'constraint_rel': round(constraint_rel, 6),
            'conf_rel': round(conf_rel, 6),
            'recency_rel': round(recency_rel, 6),
        }
        return ranked

    @classmethod
    def _extract_failure_features(cls, text: str) -> Set[str]:
        t = text.lower()
        features: Set[str] = set()

        if any(k in t for k in ['删库', '删除', '覆盖', '回滚', '丢失', 'loss', 'delete']):
            features.add('data_loss')
        if any(k in t for k in ['盲试', '重试', '重复', 'again', 'retry']):
            features.add('repeat_error')
        if any(k in t for k in ['上下文', '重复解释', 'lost context', 'context']):
            features.add('context_loss')
        if any(k in t for k in ['系统', 'assistant', '工具', '不靠谱', '忘']):
            features.add('system_error')
        if any(k in t for k in ['高风险', '危险', '不可逆', '风险', 'risk', 'irreversible']):
            features.add('high_risk')

        return features

    async def run(self, payload: Dict[str, Any]) -> SubagentResult:
        conn = payload['conn']
        user_id = str(payload['user_id'])
        risk_vector = payload.get('risk_vector')

        intent_query = str(payload.get('intent_query') or '')
        required_slots = list(payload.get('required_slots') or [])
        main_constraint = payload.get('main_constraint')
        l4_similarity_gate = float(payload.get('l4_similarity_gate', 0.85))

        features = self._extract_failure_features(intent_query)

        success_paths = await conn.fetch(
            """
            SELECT object_id, object_type, name, payload_json, confidence, validity, updated_at
            FROM memory_objects
            WHERE user_id=$1 AND object_type='success_path'
            ORDER BY updated_at DESC
            LIMIT 50
            """,
            user_id,
        )
        success_paths_dict = [dict(r) for r in success_paths]

        ranked_success_paths = [
            self._score_success_path(
                row,
                intent_query=intent_query,
                required_slots=required_slots,
                main_constraint=main_constraint,
            )
            for row in success_paths_dict
        ]
        ranked_success_paths.sort(key=lambda x: x.get('retrieval_score', 0.0), reverse=True)
        best_success_path = ranked_success_paths[0] if ranked_success_paths else None

        similar_memories: List[Dict[str, Any]] = []
        l4_top: Optional[Dict[str, Any]] = None

        if risk_vector:
            rows = await conn.fetch(
                """
                SELECT entry_id, memory_weight,
                       1 - (risk_vector <=> $1::vector) AS similarity,
                       memory_layer, continuity_cost, irreversible, system_caused
                FROM memory_entries
                WHERE user_id=$2 AND risk_vector IS NOT NULL
                ORDER BY risk_vector <=> $1::vector
                LIMIT 40
                """,
                risk_vector,
                user_id,
            )
            similar_memories = [dict(r) for r in rows if r['similarity'] is not None]

            l4_candidates = [m for m in similar_memories if int(m.get('memory_layer', 0)) == 4]
            l4_candidates.sort(key=lambda x: float(x.get('similarity', 0.0)), reverse=True)
            if l4_candidates:
                top = l4_candidates[0]
                if float(top.get('similarity', 0.0)) >= l4_similarity_gate:
                    l4_top = top

        # failure_type-based retrieval
        outcome_rows = await conn.fetch(
            """
            SELECT failure_type, created_at
            FROM action_outcome
            WHERE user_id=$1
              AND continuity_failure=TRUE
              AND failure_type IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 80
            """,
            user_id,
        )

        matched_failure_types: List[Dict[str, Any]] = []
        feature_penalty = 0.0
        for r in outcome_rows:
            ft = str(r['failure_type'] or '').lower()
            tokens = {x.strip() for x in ft.split(',') if x.strip()}
            overlap = sorted(list(features & tokens))
            if overlap:
                recency = self._recency_factor(r['created_at'])
                penalty = 3.0 * recency
                feature_penalty += penalty
                matched_failure_types.append(
                    {
                        'failure_type': ft,
                        'matched_features': overlap,
                        'recency_factor': round(recency, 6),
                        'penalty': round(penalty, 6),
                    }
                )

        # system_caused filter retrieval
        system_caused_rows = await conn.fetch(
            """
            SELECT entry_id, memory_weight, memory_layer, continuity_cost, created_at
            FROM memory_entries
            WHERE user_id=$1 AND system_caused=TRUE
            ORDER BY created_at DESC
            LIMIT 20
            """,
            user_id,
        )
        system_caused_memories = [dict(r) for r in system_caused_rows]

        if 'system_error' in features:
            feature_penalty += min(10.0, 0.8 * len(system_caused_memories))

        return SubagentResult(
            ok=True,
            data={
                'success_paths': success_paths_dict,
                'ranked_success_paths': ranked_success_paths,
                'best_success_path': best_success_path,
                'similar_memories': similar_memories,
                'l4_gate': {
                    'hit': l4_top is not None,
                    'threshold': l4_similarity_gate,
                    'top': l4_top,
                },
                'failure_features': sorted(list(features)),
                'matched_failure_types': matched_failure_types,
                'system_caused_memories': system_caused_memories,
                'feature_penalty': round(min(30.0, feature_penalty), 6),
            },
        )
