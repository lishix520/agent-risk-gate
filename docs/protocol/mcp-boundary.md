# MCP 接口边界说明 v1.0

## 1. 目标

把现有 Continuity API 封装为 MCP 工具，供 Claude Code / Codex / 其他 Agent Host 调用。

关键原则：

- `MCP = Transport + Tooling`，不是决策内核。
- 约束刷新、风险门控、对象写入规则必须在后端执行。

## 2. 边界划分

### 后端必须负责（不可上移到 MCP）

1. `Ask-Then-Act` 槽位门控
2. `L4` 高风险识别与确认令牌生成
3. `Shell/SuccessPath` 写入条件校验
4. 决策日志与 outcome 回写一致性
5. 幂等与审计（`idempotency_key`、trace、decision_id）

### MCP 负责（适配层职责）

1. 工具参数校验（基础类型、必填）
2. 调用后端 API
3. 标准化返回结构（错误码、trace 展开）
4. Host 侧工具发现与权限声明

## 3. 推荐 MCP 工具集

1. `continuity_chat`
- 映射：`POST /chat`
- 用途：主入口，触发完整运行协议。

2. `continuity_confirm_decision`
- 映射：`POST /decision/{decision_id}/confirm`
- 用途：高风险动作二次确认。

3. `continuity_report_outcome`
- 映射：`POST /decision/{decision_id}/outcome?user_id=...`
- 用途：结果回写，闭环学习。

4. `continuity_get_state`
- 映射：`GET /user/{user_id}/state`
- 用途：读取当前资源状态摘要。

5. `continuity_list_objects`
- 映射：`GET /user/{user_id}/objects`
- 用途：查询 Shell/SuccessPath 对象。

6. `continuity_put_shell`
- 映射：`POST /user/{user_id}/objects/shell`
- 用途：覆盖式更新 Shell。

7. `continuity_put_success_path`
- 映射：`POST /user/{user_id}/objects/success-path`
- 用途：写入可复用成功路径。

## 4. 工具输入输出约定

### continuity_chat

输入最小字段：
- `user_id: string`
- `message: string`
- `idempotency_key: string`
- `session_id?: string`

输出关键字段（建议透传）：
- `response`
- `decision_id`
- `trace.l4_gate`
- `trace.high_risk_confirmation.confirm_token`（若存在）
- `trace.best_success_path`
- `trace.reality_first.mode`
- `trace.reality_first.shell_bias_hit`
- `trace.reality_first.intervention`
- `trace.reality_first.question`（若存在）

### continuity_confirm_decision

输入：
- `decision_id: number`
- `user_id: string`
- `confirm_token: string`

输出：
- `confirmed: boolean`
- `message`

### continuity_report_outcome

输入：
- `decision_id: number`
- `user_id: string`
- `outcome_status`（建议枚举：`success|failed|partial`）
- `outcome_note`
- `system_caused?`
- `failure_type?`

输出：
- 更新后的 outcome 记录

## 5. 运行时流程（Host 侧）

1. 调 `continuity_chat`。
2. 若返回高风险门控：
- 向用户明确展示风险摘要。
- 用户确认后调 `continuity_confirm_decision`。
3. 若返回 `trace.reality_first.intervention=hint`：
- 仅展示现实校验问句，不做人格解释。
- 用户若不接受，继续走执行路径，不做对抗。
4. 执行动作。
5. 调 `continuity_report_outcome` 回写结果。

## 6. 安全与合规

- MCP 层不得自行生成“确认通过”结果。
- 未拿到 `confirm_token` 不得绕过高风险门。
- 所有写操作必须带 `user_id` 与幂等键（适用时）。
- 错误需透传后端语义：`invalid_or_expired_confirm_token`、`pending outcome not found` 等。
- 不得把 `reality_first` 提示解释为人格诊断或心理结论。

## 7. 版本与兼容

- 建议 MCP server 暴露版本：`continuity_mcp_version`。
- 与后端 API 版本绑定：`v1.1.x`。
- 当后端新增字段时，MCP 默认透传未知字段，避免强耦合。

## 8. 最小上线条件

1. MCP 七个基础工具可用。
2. 高风险确认链路可完整走通。
3. outcome 回写可落库并可查询。
4. 错误码语义保持一致。
5. `trace.reality_first` 字段在客户端可见并保持透传。

## 9. 明确不做

- 不在 MCP 内实现策略评分。
- 不在 MCP 内维护独立记忆副本。
- 不在 MCP 内做“猜测式约束推断”替代后端 intake。
