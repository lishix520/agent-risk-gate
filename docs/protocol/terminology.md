# 连续性系统术语转换表 v1.0

## 1. 术语策略

- 内核层（协议、对象、推理）保留原术语：`Shell` / `Flow` / `Continuity` / `False Constraint`。
- 对外层（README、路演、开源简介）使用工程术语别名，降低理解门槛。
- 原则：`一对二`，一个内核术语可对应两个对外表述（技术向 + 产品向），但语义锚点不变。

## 2. 核心映射

| 内核术语 | 技术向表述 | 产品向表述 | 说明 |
|---|---|---|---|
| `Shell` | `Stable Interface State` | `Collaborative Contract Surface` | 用户在社会系统中承担责任的稳定接口，不等于人的全部。 |
| `Flow` | `Runtime Intent State` | `In-Session Drift` | 当下可变状态，允许波动与反转。 |
| `Shell/Flow Split` | `State-Intent Decoupling` | `Anti-Freezing Identity Protocol` | 避免把临时状态固化为长期身份。 |
| `Continuity` | `Systemic Stability` | `Collaboration Continuity` | 核心目标是减少断裂、重复试错、无谓损耗。 |
| `False Constraint` | `Cognitive Bias Signature` | `Pseudo-Constraint Pattern` | 由防御机制触发的次优启发式，不等于真实限制。 |
| `Constraint Intake` | `Constraint Refresh` | `Reality Check Intake` | 落地前刷新资源上限与底线，禁止凭旧记忆盲推。 |
| `SuccessPath` | `Reusable Procedure Memory` | `No-Retry Path` | 只记录可复用成功路径，避免重复踩坑。 |
| `Ask-Then-Act` | `Slot-Gated Execution` | `Clarify Before Action` | 执行前补足关键槽位，减少盲试。 |
| `L4 Gate` | `High-Risk Confirmation Gate` | `Risk Brake` | 高风险动作必须二次确认。 |

## 3. 防语义漂移规则

- 禁止把 `Shell` 解释为人格本体。
- 禁止把 `Flow` 解释为“情绪噪音”并忽略。
- 对外文档中出现 `Immutable` 时，必须注明是“接口稳定”，不是“人不可变”。
- 对外文档中出现 `Runtime Context` 时，必须注明“可覆盖历史、以当下为准”。

## 4. 对外推荐句式

- 推荐：`We separate stable interface state from runtime intent to prevent identity freezing.`
- 推荐：`The kernel optimizes collaboration continuity under real-world constraints.`
- 推荐：`Memory is a component; risk-aware execution policy is the core.`
- 不推荐：`This system models your true self.`
- 不推荐：`This is a memory product.`

## 5. 术语落地到对象模型

- `Shell Object`：稳定接口与最新叙事版本（覆盖式）。
- `SuccessPath Object`：可复用、可执行、可验收的成功程序记忆。
- `Flow`：默认不写入长期对象库，体现在当前会话和约束刷新结果。

## 6. 壳夺权机制与反夺权策略

### 6.1 壳夺权机制（个人与组织同构）

- `压缩收益`：把流动现实压缩为稳定身份，降低认知和协作成本。
- `激励锁定`：过去成功沉淀为流程、指标、声誉与资产结构，反向惩罚新路径。
- `风险回避`：系统默认把“未知”判为高风险，优先捍卫旧壳。

### 6.2 企业对应（创新者窘境）

- 个人：`我是这种人` 的自我叙事锁定选择空间。
- 企业：`我们一直靠这条线成功` 的组织叙事锁定资源配置。
- 共同结果：`壳` 从接口变成主权，`流` 被降权，探索能力下降。

### 6.3 反夺权策略（协议化）

- 规则1：`壳可审计，流可更新`。
- 规则2：当 `Shell` 与当下 `Flow` 冲突，先做澄清，不允许历史默认覆盖当下。
- 规则3：把旧壳约束显式化为成本项，再与新流候选动作比较，而不是隐式默认。
- 规则4：保留稳定交付壳，同时给探索流保留受控试验窗口。

### 6.4 触发信号

- 频繁出现 `我们一直都是这样` / `我就是这样`。
- 明显有新事实输入，但决策长期不更新。
- 反复诉诸历史成功作为唯一证据。

