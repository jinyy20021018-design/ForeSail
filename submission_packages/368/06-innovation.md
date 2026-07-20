# 创新说明

## 技术创新

### 1. 确定性可审计风险内核（LLM 从不打分）

- 常见做法：部分 AI 风控或助手会让 LLM 直接输出风险分数、分类或状态决策。
- 本作品的不同：ForeSail 将核心风险评分与分类、暴露映射、Incoterms 责任归属、合同/信用证硬期限处理及 Case 状态流转交给确定性代码。Gemini 负责文档抽取、摘要、相关性因子候选、动作候选和处置方案草稿；结构化输出经过关键字段、枚举、日期格式和已知 ID 的校验或清洗，并由用户确认。LLM 可以提出建议行动日期和方案估算成本，但不能改写已确认事实或核心风险决策。
- 实际效果：核心风险结论可按相同事实输入复现并追溯到确定性规则；LLM 生成内容被限制在抽取、解释和候选草稿层，并通过代码约束与人工确认降低无效引用或越权决策风险。
- 证据位置：backend/app/services/relevance_engine.py、risk_mapper.py、incoterm_rule_service.py、obligation_service.py、status_machine.py（确定性核心）；backend/app/services/action_set_service.py 与 treatment_plan_service.py（候选草稿的字段、枚举、日期格式与已知 ID 约束）。

### 2. Incoterms 风险归属引擎 + per-Case 座位自动判定

- 常见做法：航运风险产品通常只做通用事件告警，不区分同一事件在不同贸易术语/买卖视角下的责任归属。
- 本作品的不同：从单据当事人字段自动判定我方座位（LC beneficiary/shipper→卖方，applicant/consignee→买方），再用确定性 Incoterms 2020 规则把同一事件映射为『谁的风险/谁能动手/要不要你管』。
- 实际效果：同一条台风或海峡新闻，对 CIF 卖方和 FOB 买方给出相反且正确的归属，并作为第二把降噪锁过滤掉与我方无关的事件。
- 证据位置：backend/app/services/incoterm_rule_service.py、perspective_detection_service.py；demo 中 SELLER/BUYER 两个对照端点。

### 3. 预测层：航程 × 气象预报 / 台风锥 / 地缘走廊状态机对齐

- 常见做法：常见做法是事件发生后再告警（反应式）。
- 本作品的不同：把航程时刻与 16 天预报、台风路径锥、地缘走廊状态机做时空对齐，在船驶入风险前就让暴露浮现。
- 实际效果：风险从『损失落地后通知』变成『装船/驶入前预警』，为处置留出时间窗。
- 证据位置：backend 预测层与 Open-Meteo/台风连接器；前端地图与风险日历。
## 产品与体验创新

### 1. 从『新闻推送』重构为『这笔单、这个截止期、谁暴露、发什么』

- 常见做法：现有工具给的是通用航运/天气新闻流或宽泛告警，需要用户自己判断相关性和责任。
- 本作品的不同：ForeSail 以单笔 trade Case 为状态单位，把外部事件直接落到本单的义务/期限/责任方上，并给出可发送的对外草稿。
- 实际效果：操作员不再『看到一堆新闻自己想办法』，而是直接得到一笔单可执行、带证据的处置建议。
- 证据位置：前端 Recommended Action Board / Action Drafts / hazard attribution note。

### 2. 逐层人审闸门：从抽取事实到确认动作再到处置方案

- 常见做法：常见的一次性生成式交互会连续输出抽取结果、风险建议和处置方案，用户往往只能在结果末端整体接受或放弃，前置事实错误可能继续传递到后续决策。
- 本作品的不同：ForeSail 将流程拆成 8 个有状态步骤，并设置多层人工确认：抽取字段可逐项接受、编辑或排除；高严重度字段冲突未解决时阻止事实确认；动作候选必须由用户选择并确认后，才可用于生成处置方案；已确认的动作集不能原位修改，后续方案只能引用其中已确认的动作。
- 实际效果：已实现的机制效果是：高严重度冲突会阻断事实确认，未确认动作无法进入处置方案，已确认动作集不可原位修改，从而把自动生成内容保持在明确的人工审批边界内。该流程约束已有代码和自动化测试支持，但尚未通过真实用户测试量化效率提升或风险降低幅度。
- 证据位置：backend/app/services/workflow_service.py（8 步状态与冲突阻断）；frontend/src/components/ExtractedFieldsReview.tsx（字段接受、编辑与排除）；backend/app/services/action_set_service.py（动作选择、确认及确认后不可变）；backend/app/services/treatment_plan_service.py（仅允许已确认动作进入处置方案）；backend/app/tests/test_mvp21_workflow.py、backend/app/tests/test_treatment_plans.py（流程约束测试）。
