from __future__ import annotations

import re
from typing import Any, Dict, List

from app.subagents.base import SubagentResult


class ConstraintIntakeAgent:
    name = 'constraint_intake'
    _shell_markers = [
        '我就是这样',
        '我们一直这样',
        '一直都是',
        '过去成功',
        '历史经验',
        '按老办法',
        'we always',
        'this is how we do things',
    ]
    _decision_markers = [
        '要不要',
        '是否',
        '选择',
        '决策',
        '继续',
        '转向',
        '方案',
        '计划',
        'should',
        'decide',
        'choose',
    ]
    _reality_markers = [
        '预算',
        '现金',
        '成本',
        '收益',
        '期限',
        '截止',
        '底线',
        '每天',
        '每周',
        '小时',
        '资源',
        '上限',
        'money',
        'budget',
        'deadline',
        'hours',
        'resources',
    ]
    _number_pattern = re.compile(r'\d+(\.\d+)?\s*(元|万|小时|h|hr|天|周|月|%|k|w)?', re.IGNORECASE)

    @staticmethod
    def required_slots(task_type: str) -> List[str]:
        if task_type == 'execution':
            return ['environment', 'target', 'success_criteria']
        if task_type == 'complex_decision':
            return [
                'done_definition',
                'money_budget',
                'money_deadline',
                'time_budget',
                'energy_budget',
                'bottom_line',
                'resources',
            ]
        return ['done_definition', 'purpose']

    @staticmethod
    def detect_task_type(message: str) -> str:
        text = message.lower()
        if any(k in text for k in ['run', 'command', 'exec', 'notes', 'osascript', '执行', '命令']):
            return 'execution'
        if any(k in text for k in ['赚钱', '项目', '预算', '收益', '半年', '一年', '计划']):
            return 'complex_decision'
        return 'concept_exploration'

    @staticmethod
    def make_questions(missing_slots: List[str]) -> List[str]:
        q: List[str] = []
        templates = {
            'done_definition': '做成什么算 done？（一句话）',
            'money_budget': '钱：你最多可投入多少？',
            'money_deadline': '钱：最晚多久必须见到收益？',
            'time_budget': '时间：每天/每周最多可投入多少？',
            'energy_budget': '精力：每天高质量工作上限多少小时？',
            'bottom_line': '底线：绝对不能发生什么？',
            'resources': '已有资源是什么？（技能/渠道/资产）',
            'environment': '运行环境是什么？（系统/权限/工具）',
            'target': '目标对象是什么？（标题/路径/名称）',
            'success_criteria': '验收标准是什么？',
            'purpose': '这次讨论要产出什么？',
        }
        for s in missing_slots:
            if s in templates:
                q.append(templates[s])
            if len(q) >= 3:
                break
        return q

    @classmethod
    def _collect_hits(cls, text: str, markers: List[str]) -> List[str]:
        return [m for m in markers if m in text]

    @classmethod
    def detect_shell_bias(cls, message: str) -> Dict[str, Any]:
        text = message.lower().strip()
        shell_hits = cls._collect_hits(text, cls._shell_markers)
        decision_hits = cls._collect_hits(text, cls._decision_markers)
        reality_hits = cls._collect_hits(text, cls._reality_markers)
        has_reality_signal = bool(reality_hits) or (cls._number_pattern.search(text) is not None)

        hit = bool(shell_hits and decision_hits and not has_reality_signal)
        questions = []
        if hit:
            questions = [
                '基于当前现实，你最多可投入的钱、时间、精力上限分别是多少？',
                '最晚什么时候必须看到可验证结果？',
            ]

        return {
            'hit': hit,
            'shell_evidence': shell_hits,
            'decision_evidence': decision_hits,
            'has_reality_signal': has_reality_signal,
            'questions': questions,
        }

    async def run(self, payload: Dict[str, Any]) -> SubagentResult:
        message = str(payload.get('message', ''))
        known_slots: Dict[str, Any] = dict(payload.get('known_slots') or {})
        task_type = self.detect_task_type(message)
        required_slots = self.required_slots(task_type)
        missing_slots = [s for s in required_slots if not str(known_slots.get(s, '')).strip()]
        questions = self.make_questions(missing_slots)
        shell_bias = self.detect_shell_bias(message)
        return SubagentResult(
            ok=True,
            data={
                'task_type': task_type,
                'required_slots': required_slots,
                'missing_slots': missing_slots,
                'questions': questions,
                'shell_bias': shell_bias,
            },
        )
