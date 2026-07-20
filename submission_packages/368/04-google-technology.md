# Google 技术与实现证据

## 1. Google Gemini API（默认 LLM 提供方）

- 具体能力或模型：gemini-3.1-flash-lite，用于长文本理解与受约束的结构化 JSON 输出；通过 Gemini 的 OpenAI 兼容端点（https://generativelanguage.googleapis.com/v1beta/openai）统一接入。当前 .env：LLM_PROVIDER=gemini，USE_LLM_EXTRACTION=true，LLM_FALLBACK_ENABLED=false。
- 对应功能：贸易单据智能抽取——把合同 / 订舱确认 / 信用证的自由文本解析为可核验的结构化贸易要素。
- 输入：单据解析后的全文文本（支持 TXT / DOCX / 文本 PDF）、允许抽取的 25 类字段白名单，以及约束返回格式的 JSON schema。
- 处理：Gemini 在 temperature=0、response_format=json_object 的强约束下，抽取买卖方、商品、金额、币种、Incoterm、装运与交单期限、当事人角色等字段，并为每个字段附上证据文本与置信度；系统提示明确限定其只做事实抽取，不得推断风险等级、责任归属、冲突或审批结论。
- 输出：带证据文本与置信度的结构化字段 JSON，进入前端逐字段 approve / edit / reject 的人工确认流程，成为整条风险链路的可信输入。
- 核心程度：支撑
- 选型原因：贸易单据是半结构化长文本、格式多样，Gemini 的长上下文理解与结构化输出适合在零微调下完成多字段抽取；OpenAI 兼容端点让既有请求结构保持不变。
- 移除后的影响：移除后系统回退到确定性规则抽取，demo 仍可跑通但字段覆盖度与鲁棒性下降；风险打分、归属、状态与期限决策不受影响。
- 证据位置：backend/app/services/llm_provider.py；backend/app/services/document_service.py::_llm_extract_fields；README「LLM Provider / Optional LLM Extraction」。
## 2. Google Gemini API（Agent Run Summary）

- 具体能力或模型：gemini-3.1-flash-lite，用于面向用户的自然语言摘要生成。当前 .env：USE_LLM_SUMMARY=true，REQUIRE_LLM_AGENT=true，GEMINI_SUMMARY_TIMEOUT_SECONDS=60。
- 对应功能：Agent 监控循环的运行摘要——把一次监控的确定性结果转写成操作员可读摘要。
- 输入：本次运行的确定性事实 JSON：相关性结果、敞口、风险摘要、处于风险的义务、信息缺口与动作草稿计数。
- 处理：Gemini 在“只允许复述既有事实、禁止产生新的打分 / 分类 / 状态 / 日期 / 动作决策”的约束下，把结构化结果转写为简洁摘要。
- 输出：一段展示在前端 Agent Run Summary 面板的可读摘要。
- 核心程度：支撑
- 选型原因：运行摘要是语言组织任务，适合用 Gemini 统一处理，同时保留确定性 fallback。
- 移除后的影响：移除后回退到确定性模板摘要；核心监控结果与风险判定不受影响。
- 证据位置：backend/app/services/agent_summary_service.py::_llm_summary；backend/app/services/llm_provider.py；README「Optional LLM Summary」。
## 3. Google Gemini API（相关性因子候选提取）

- 具体能力或模型：gemini-3.1-flash-lite，用于从 case watch profile 与外部事件文本中提出候选 relevance factors。当前 .env：USE_LLM_RELEVANCE_FACTORS=true，GEMINI_RELEVANCE_FACTOR_TIMEOUT_SECONDS=20。
- 对应功能：事件相关性解释增强——为外部事件提取候选匹配因子、缺失直接证据与简短解释。
- 输入：case watch profile（船舶、港口、航线区域、期限等）、外部事件标题/描述/影响范围，以及允许的 relevance factor 白名单。
- 处理：Gemini 只提出候选因子；系统随后用确定性规则校验候选是否在白名单内、是否有证据、是否被 deterministic case/event validation 支持。
- 输出：validated_factors、rejected_factors、missing_direct_evidence 与解释摘要，供评委/用户理解相关性来源。
- 核心程度：支撑
- 选型原因：LLM 适合从非结构化事件文本中提取可解释候选因子，但最终是否进入评分仍由确定性校验决定。
- 移除后的影响：移除后使用确定性 relevance factors；最终分数与分类仍由 relevance engine 决定。
- 证据位置：backend/app/services/llm_relevance_factor_service.py；backend/app/services/relevance_engine.py。
## 4. Google Gemini API（动作候选生成）

- 具体能力或模型：gemini-3.1-flash-lite，用于在严格 JSON schema 下生成可执行 trade-risk action candidates。当前 .env：GEMINI_ACTION_MODEL=gemini-3.1-flash-lite，GEMINI_ACTION_TIMEOUT_SECONDS=60。
- 对应功能：Recommended Action Board / Actions——基于已确认事实、风险摘要、义务、信息缺口和 hazard，生成可编辑、可确认的动作候选。
- 输入：已确认 case facts、relevance results、risk summary、obligations、information gaps、hazards 与 Incoterm responsibility。
- 处理：Gemini 生成结构化 actions；系统用 schema、优先级枚举、responsible party 枚举、hazard/obligation/exposure ID 校验与清洗，禁止重新分类事件、改变 case 状态或编造法律结论。
- 输出：候选 action set，用户可选择、编辑并确认，确认后才进入后续处置方案。
- 核心程度：支撑
- 选型原因：动作草稿需要把确定性风险结果转成操作语言，Gemini 能提升可读性与可执行性，同时由代码校验约束。
- 移除后的影响：移除后动作候选生成不可用或需人工编写，但底层风险识别、归属和状态机不受影响。
- 证据位置：backend/app/services/action_set_service.py；backend/app/services/structured_llm_service.py。
## 5. Google Gemini API（处置方案草稿生成）

- 具体能力或模型：gemini-3.1-flash-lite，用于在严格 JSON schema 下生成 LOW_COST / BALANCED / MAX_PROTECTION 三类 treatment plans。当前 .env：GEMINI_PLAN_MODEL=gemini-3.1-flash-lite，GEMINI_PLAN_TIMEOUT_SECONDS=60。
- 对应功能：Treatment Plans——基于用户已确认的动作集合，生成三种处置方案、残余风险、审批角色与推荐方案。
- 输入：已确认 case facts、已确认 actions、risk summary、obligations、information gaps、hazards 与 Incoterm responsibility。
- 处理：Gemini 生成 exactly three plans；系统校验方案类型、唯一 recommended plan、linked action/gap/obligation ID 是否存在，禁止引用未确认动作或未知标识。
- 输出：可供审批与选择的三套处置方案，以及对应 residual risks 和 approval package 输入。
- 核心程度：支撑
- 选型原因：方案草稿是跨多个已确认动作的语言与结构化组织任务，适合由 Gemini 生成后由 deterministic/schema 校验守住边界。
- 移除后的影响：移除后不能自动生成方案草稿，但不影响前置风险检测、责任归属、义务/期限计算和动作确认。
- 证据位置：backend/app/services/treatment_plan_service.py；backend/app/services/structured_llm_service.py。

## 技术材料

- 架构图：未提供
- 代码仓库：https://github.com/jinyy20021018-design/ForeSail
- 评审版本：5363a24aa5f1fe5e70bf1c0a5d1fb2079541a1de
- 部署说明：后端 FastAPI（Python 3.10）部署于 Render（Root: backend, Start: uvicorn app.main:app），前端 React/Vite 部署于 Vercel（Build: npm run build, Output: dist）。免费演示配置可无付费 API 运行：外部事件默认 REAL 模式接 Open-Meteo/GDELT/RSS，LLM 抽取/摘要可关闭并回退确定性实现。
- 保密限制：未提供

### 核心代码或证据位置

- backend/app/services/llm_provider.py — Gemini 提供方解析、OpenAI 兼容端点与模型选择
- backend/app/services/document_service.py — Gemini 文档抽取调用与 fallback
- backend/app/services/agent_summary_service.py — Gemini Agent Run Summary
- backend/app/services/llm_relevance_factor_service.py — Gemini 相关性因子候选提取 + 确定性校验
- backend/app/services/action_set_service.py — Gemini 动作候选生成 + schema/ID 校验
- backend/app/services/treatment_plan_service.py — Gemini 三方案生成 + schema/ID 校验
- backend/app/services/relevance_engine.py — Case 相关性确定性打分引擎
- backend/app/services/incoterm_rule_service.py — Incoterms 风险归属规则
- backend/app/agents/monitoring_agent.py — Agent 编排层（不参与打分/日期计算）

### 外部依赖

- FastAPI + Uvicorn（Python 3.10 后端）
- React + Vite + Leaflet（前端）
- Open-Meteo（天气/16 天预报，真实连接器）
- GDELT（全球新闻，真实连接器）
- RSS 搜索连接器（gCaptain / FreightWaves 等航运源）
- searoute（任意港口对海运航线计算）
- Google Gemini API（默认 LLM 提供方，gemini-3.1-flash-lite，经 OpenAI 兼容端点；用于文档抽取、Agent 摘要、相关性因子候选、动作候选和处置方案草稿）
