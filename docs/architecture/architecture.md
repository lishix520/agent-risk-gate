# 连续性优先智能系统 - 完整技术架构 v1.1

## 0. 版本与定位
- 版本: `v1.1`
- 日期: `2026-02-06`
- 定位: 面向单用户长期协作的连续性优先系统
- 目标: 在连续性基石不被破坏的前提下，降低不可逆损耗并保证可审计与可回放

## 1. 一致性原则（工程硬约束）
1. 连续性是协作基石（invariant），不是可替代目标。
2. 真实性优先于表面连贯性。
3. 决策阶段遵循现实优先：可验证现实约束高于壳叙事。
4. 用户显式指令在连续性基石与现实边界内优先执行，系统默认低干预不对抗。
5. 所有状态更新必须可追溯到证据链。
6. 未知不等于 0 风险，未知必须显式标注。
7. 主约束只在六资源轴内选择，信息不确定属于元约束。

## 2. 逻辑分层

### 2.1 Rule Layer（不可改写）
- 时间不可逆
- 能量受限
- 不可逆损失不可回滚
- 用户退出即系统失败

### 2.2 Protocol Layer（运行协议）
- Ask-Then-Act
- 禁盲试（可问先问）
- 连续性失败自动自检
- 虚假限制提醒可退出（用户说“知道了”或表现不耐烦即停止）

### 2.3 Runtime Layer（编排与计算）
- 意图解析
- 槽位生成与询问
- 事件影响抽取
- 成本计算
- 记忆检索与约束
- 决策评分与执行

### 2.4 Object Store Layer（长期对象）
- `Shell`（覆盖式最新叙事）
- `SuccessPath`（可复用成功路径）

### 2.5 Event Store Layer（事件与审计）
- `MemoryEntry` 事件历史
- `state_evidence` 状态更新证据
- `action_outcome` 预测与真实偏差
- `decision_log` 决策轨迹

## 3. 子代理（Subagent）架构

## 3.1 设计目标
把高变动、高 token 消耗、易漂移任务拆到子代理，主编排器只做状态机与策略控制。

## 3.2 角色划分
1. `Orchestrator`（主代理）
- 负责流程状态机、策略闸门、事务边界、最终回复。

2. `ImpactExtractorAgent`
- 输入对话，输出 `event_impact_v2.1` JSON。
- 只做结构化抽取，不做决策。

3. `ConstraintIntakeAgent`
- 在关键槽位缺失时生成 2-3 个高信息增益问题。

4. `MemoryRetrievalAgent`
- 检索 `SuccessPath`、相似 `MemoryEntry`，返回候选与置信度。

5. `RiskAuditAgent`
- 执行连续性自检:
- 是否成功路径未复用
- 是否可问却盲试
- 是否跨会话断裂
- 是否存在编造风险

6. `DecisionScoringAgent`（可选）
- 只做候选动作打分解释，不直接执行。

## 3.3 编排约束
- 子代理必须输出结构化 JSON，禁止自由文本协议。
- 主代理只接受通过 schema 校验的子代理输出。
- 子代理失败时降级到规则引擎，不允许阻塞主流程。

## 4. 数据模型（完整）

## 4.1 user_state
用途: 存当前六轴状态与主约束。

关键字段:
- `money_value, time_value, energy_value, asset_value, reliability_value, identity_value` (`0..1`)
- `*_confidence` (`0..1`)
- `main_constraint` (`money|time|energy|asset|reliability|identity`)
- `uncertainty_meta` (`0..1`)
- `last_updated`

约束:
- 所有 value/confidence 范围检查
- `main_constraint` 枚举检查

## 4.2 state_evidence（新增）
用途: 审计状态更新来源。

字段:
- `evidence_id` (uuid pk)
- `user_id`
- `resource_axis`
- `before_value`, `after_value`
- `signal_type` (`behavior|language|explicit|external`)
- `signal_text`
- `weight`
- `confidence`
- `created_at`

约束:
- 无证据不得更新状态

## 4.3 memory_entries
用途: 事件历史与风险泛化。

字段:
- `entry_id` (uuid)
- `user_id`
- `event_class`
- `raw_context`
- `delta_*` 六轴
- `pre_state_snapshot`
- `continuity_cost`
- `irreversible`
- `system_caused`
- `memory_weight`
- `memory_layer` (`1..4`)
- `risk_vector` (pgvector)
- `created_at`

## 4.4 memory_objects（新增）
用途: 长期对象边界隔离。

字段:
- `object_id` (uuid)
- `user_id`
- `object_type` (`shell|success_path`)
- `name`
- `text_index`
- `payload_json`
- `confidence` (`high|medium|low`)
- `validity` (`long|medium|short`)
- `updated_at`

规则:
- `shell` 叙事层覆盖式更新
- `success_path` 保存可执行 procedure

## 4.5 decision_log
用途: 决策输入输出与理由存档。

字段:
- `context`
- `candidate_actions`
- `selected_action`
- `predicted_gain`
- `predicted_risk`
- `uncertainty_penalty`
- `memory_penalty`
- `decision_score`
- `timestamp`

## 4.6 action_outcome（新增）
用途: 预测-结果校准闭环。

字段:
- `outcome_id`
- `decision_id`
- `predicted_impact_vector`
- `actual_impact_vector`
- `vector_error_l1`
- `predicted_cost`
- `actual_cost`
- `cost_error`
- `continuity_failure` (bool)
- `failure_type` (nullable)
- `created_at`

## 4.7 conversation_history
用途: 会话上下文审计。

字段:
- `session_id`
- `role`
- `content`
- `event_impact_id`
- `timestamp`

## 5. 核心计算与策略

## 5.1 EventImpact 抽取
标准: 使用 `event_impact_v2.1`。

强制输出:
- `impact_vector`
- `axis_confidence`
- `missing_axes`
- `evidence_spans`
- `analysis_confidence`

降级规则:
- 子代理失败 -> 规则模板抽取
- 仍失败 -> 返回全 0 向量 + 低置信度 + 强制询问

## 5.2 稀缺权重
- `ScarcityWeight[i] = g(1 - value_i)`
- 建议: logistic 非线性，临界区加速

示例:
- `g(x) = 1 / (1 + exp(-a*(x-b)))`
- 默认 `a=8, b=0.5`

## 5.3 联动放大器（TransferAmplifier）
`Cost = sum(abs(delta_i) * W_i * A_i)`

初始规则:
1. `delta_asset<=-0.6 && time_value<=0.4 => A_energy=1.4`
2. `delta_money<=-0.4 && identity_value<=0.5 => A_identity=1.3`
3. `system_caused=true && delta_reliability<0 => A_reliability=1.5`

冲突:
- 同轴多规则触发取 `max(A_i)`

## 5.4 记忆层惩罚
- `L1:1`
- `L2:5`
- `L3:30`
- `L4:120`

L4 闸门:
- 若 `similarity>=0.85`，进入 `high_risk_gate`
- 仅允许:
- 用户二次确认
- 恢复模式

## 5.5 不确定性处理
- `UncertaintyPenalty = k * (1 - prediction_confidence)`
- 默认 `k=0.4`
- 关键槽位缺失直接询问，不进入动作执行

## 5.6 Reliability 更新
- 默认仅下降
- 满足连续 `N=5` 次无损成功后每次 `+0.02`
- 上限 `0.9`
- 近期 L4 触发时冻结恢复

## 5.7 决策评分
`Score = PredictedGain - (PredictedCost + MemoryPenalty) - UncertaintyPenalty`

若 `best_score < safe_threshold`:
- 进入恢复模式
- 按主约束选恢复策略

## 6. Runtime 状态机
1. 接收输入
2. 读取会话和对象
3. 生成 required_slots
4. 若缺关键槽位 -> ConstraintIntakeAgent 提问
5. 抽取 EventImpact
6. 更新 UserState（含 evidence）
7. 计算成本与风险
8. 检索 SuccessPath 与相似记忆
9. 决策评分与闸门检查
10. 执行最小动作
11. 写入 decision/outcome/memory
12. 输出响应与必要解释

## 7. API 设计（FastAPI）

核心接口:
- `POST /chat`
- `GET /user/{user_id}/state`
- `GET /user/{user_id}/objects?type=shell|success_path`
- `GET /user/{user_id}/memories`
- `POST /user/{user_id}/objects`
- `POST /decision/{id}/outcome`

`POST /chat` 强制字段:
- `user_id`
- `message`
- `session_id`
- `idempotency_key`

幂等语义:
- 相同 `user_id + idempotency_key` 只处理一次
- 重试返回相同结果，不重复写库

## 8. 事务与一致性

事务顺序:
1. `conversation_history`
2. `event_impact`（内存对象或临时表）
3. `state_evidence + user_state`
4. `decision_log`
5. `action_outcome`（如有）
6. `memory_entries / memory_objects`

任何失败回滚。

## 9. 观测与告警

指标:
- `continuity_failure_rate`
- `blind_try_rate`
- `success_path_reuse_rate`
- `state_update_without_evidence`（应为 0）
- `prediction_cost_mae`
- `L4_gate_trigger_rate`

日志:
- 结构化 JSON 日志
- 每次决策包含 trace_id

## 10. 安全边界
- 不存储不必要隐私字段
- 证据文本脱敏（可配置）
- Prompt 注入防护（schema 强校验）
- 所有子代理输出先校验再入主流程

## 11. 部署架构

MVP 到完整版都可复用的单机起步:
- `api` (FastAPI)
- `postgres + pgvector`
- `redis`（缓存/队列，可选）
- `worker`（异步任务: 衰减、校准、索引维护）

生产建议:
- API 与 worker 分离
- 读写分离（可选）
- 定时任务使用 `celery/apscheduler`

## 12. 测试策略

### 12.1 单元测试
- EventImpact schema 合法性
- 成本计算与放大器
- L4 闸门逻辑
- 幂等逻辑

### 12.2 集成测试
- Ask-Then-Act 关键槽位流程
- SuccessPath 优先复用
- 连续性失败自动上报

### 12.3 回归场景
- 删库事件
- 重复试错
- 能问不问
- 跨会话断裂
- 虚假限制提醒退出
- 用户高风险强制执行

## 13. 默认参数（v1.1）
- `theta_ask = 0.55`
- `safe_threshold = 0.0`
- `reliability_recover_n = 5`
- `reliability_recover_step = 0.02`
- `l4_similarity_gate = 0.85`
- `uncertainty_k = 0.4`

## 14. 实施顺序
1. 先落数据层与幂等语义
2. 再落 EventImpact v2.1 与状态证据链
3. 再落决策评分与 L4 闸门
4. 最后接入子代理并做校准自动化

## 15. 交付物清单
- SQL 初始化脚本（含新增 4 表）
- FastAPI 路由与 schema
- Runtime 编排器
- 子代理协议定义
- 回归测试用例
- 运维观测看板
