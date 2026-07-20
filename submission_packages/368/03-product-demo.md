# 产品与 Demo

## 解决方案

ForeSail 把每笔货当作一个持续存在的 trade Case：从合同/订舱确认/信用证中抽取并确认贸易要素，映射 Incoterm 责任划分与义务/期限日历，持续扫描外部事件并只挑出真正触及本单的，再由确定性可审计引擎算出暴露、判定风险归属、推进 case 状态，生成带证据、可直接发送的对外动作草稿。所有风险打分/分类/暴露映射/状态流转/日期与金额计算都由确定性引擎产出——agent 只负责编排流程与文书润色，从不自己编造风险分数。

## 用户价值

把原本靠人工盯新闻拍脑袋的外部风险判断，变成针对这一笔单的具体预警：哪个截止期现在有风险、在 Incoterm 下谁真正暴露、该发什么，而且还有时间处置——每条结论都可追溯、可放到一笔钱的决策面前。

## 用户流程

- 1. 上传单据（合同/PO、订舱确认、信用证）建立一个 trade Case。
- 2. 复核系统抽取的贸易要素字段（每字段带证据文本与置信度），逐字段 approve/edit/reject。
- 3. 解决跨单据的字段冲突。
- 4. 确认 case facts（同时自动判定我方座位：卖方/买方）。
- 5. 运行 Agent 监控 / 生成动作：拉取真实外部事件 → 相关性判定 → 暴露映射 → 义务/期限映射 → 生成动作与对外草稿。
- 6. 复核并确认推荐动作。
- 7. 生成并复核处置方案（treatment plan）。
- 8. 持续监控，case 状态随之在 DRAFT→ACTIVE→WATCHING→AT_RISK→ACTION_REQUIRED→MONITORING 间推进。（案例详情页顶部有这 8 步进度条；也可直接打开预置的已跑案例查看完整分析结果。）

## 核心功能

### 1. 单据抽取与要素确认

- 解决的问题：把非结构化的合同/订舱/信用证变成可信、可核验的结构化贸易要素。
- 输入：TXT / DOCX / 文本 PDF 格式的合同/PO、订舱确认、信用证。
- 系统处理：确定性规则抽取 +（可选）LLM 抽取，输出带证据文本与置信度的字段，支持逐字段人工核对。
- 输出：带证据、可 approve/edit/reject 的贸易要素字段，及确认后的 case facts。
- 当前状态：完整可用（真实解析 TXT/DOCX/文本 PDF，扫描件 OCR 在 roadmap）。
- 证据位置：README「Supported Demo Flow」；backend/app/services/document_service.py
### 2. Case 相关性引擎

- 解决的问题：从海量外部新闻/天气中过滤掉与本单无关的噪音。
- 输入：外部事件流 + 本 case 的监控画像（船舶、港口、航段区域、期限敏感度）。
- 系统处理：确定性打分与分类，只保留真正触及这笔单的事件。
- 输出：带分数的事件相关性结果，滤除新闻噪音。
- 当前状态：完整可用。
- 证据位置：前端 Event Relevance Results；backend/app/services/relevance_engine.py
### 3. Incoterms 风险归属引擎

- 解决的问题：同一事件在不同 Incoterm 下归属相反，人工易判错责任方。
- 输入：合同术语（CIF/FOB 等 11 种）+ 自动判定的我方座位 + 事件所处航段。
- 系统处理：确定性 Incoterms 2020 风险转移规则，判定谁的风险/谁能动手/要不要你管。
- 输出：每条事件的三判定与 attribution note（如『你是 CIF 卖方，货已装船风险转买方，但你仍控主运且收款风险未消』）。
- 当前状态：完整可用。
- 证据位置：backend/app/services/incoterm_rule_service.py、perspective_detection_service.py；hazard 卡 attribution note
### 4. 预测层：航程 × 预报对齐

- 解决的问题：让风险在船开进去之前就浮现，而不是损失落地后才知道。
- 输入：航程时刻表 + 16 天气象预报 + 台风路径 + 地缘走廊状态。
- 系统处理：航程与预报的时空对齐、台风路径锥、地缘走廊状态机。
- 输出：在船驶入风险前给出的暴露预警与风险日历。
- 当前状态：完整可用。
- 证据位置：前端地图/风险日历；backend 预测层服务与 Open-Meteo/台风连接器
### 5. 确定性可审计决策核 + 对外动作草稿

- 解决的问题：把风险判断变成可信、可追溯、可直接发送的处置动作。
- 输入：暴露、义务与期限。
- 系统处理：确定性 exposure/deadline/status 状态机产出决策；LLM 仅润色文书措辞，从不参与打分。
- 输出：带证据的处置建议与可发送对外草稿（LC amendment、承运人询问、保险澄清、RFQ 等）。
- 当前状态：部分可用（生成 ticket 与外发草稿，但不做真实成交，MVP 边界）。
- 证据位置：前端 Recommended Action Board / Action Drafts；backend agent 编排层

## Demo

- Demo链接：https://fore-sail.vercel.app
- 访问方式：浏览器 Web 应用（前端 Vercel + 后端 Render，无需登录）。首次访问有引导浮层，可随时点右上角『?』重放。
- 推荐环境：桌面端 Chrome / Edge 最新版，正常网络；首次访问若后端休眠需等待数十秒冷启动。
- 预计体验时长：5 分钟
- 备用下载链接：未提供
- 已发布渠道：未提供
- 已发布产品名称：未提供
- 技术支持联系人：未提供
- 受限访问：否
- 测试账号文件：private/08-test-access.md

### 体验步骤

1. 打开 Demo（https://fore-sail.vercel.app）。首次访问会弹出『Welcome to ForeSail』引导；老访客可随时点右上角『?』(Replay guided tour) 重放引导。点『Set up my first case →』开始——之后引导会逐页高亮、一步步带你走完整个流程。
   - 预期结果：进入新建 Case / 上传单据页，引导卡片开始逐步高亮讲解（Intake → Monitor → Treat 三段）。
2. 上传单据：把合同 / 信用证 / 订舱 / 提单拖进文档槽。三种取材皆可——① 用你自己的单据；② 点页面上的『load a ready-made sample document set』载入内置样例；③ 用随本材料包附带的样例单据 evidence/demo-case-documents/（contract、booking_confirmation、letter_of_credit）。然后点『Extract』抽取事实，完成后点『Continue to Review』进入 case 工作台。
   - 预期结果：系统从单据中抽取交易事实并标出跨单据冲突；抽取字段带证据来源。该文档抽取的 LLM 层由 Google Gemini 驱动（见 04-google-technology.md 与 backend/app/services/llm_provider.py）。
3. 在 Documents & Evidence：先确认『座位』（系统读单据当事人判定你是卖方/买方，如 LC beneficiary = 卖方）→『Accept all』批准抽取字段 →『Confirm Fields』锁定确认事实 → 点右上『Run Agent Monitoring Cycle』跑第一轮监控。
   - 预期结果：确认事实后监控按钮解锁；点击后 agent 拉取外部事件、按本 case 打分、浮现触及本单的风险。
4. 按引导巡览 Overview 与信号来源：Overview（Route alerts 点卡片联动地图、Route risk map 点风险看归属 note、Shipment facts、红/绿 Exposure flags）→ External Events（全球航运走廊状态板 +『Search Real External Events』实时拉真实新闻源（gCaptain、Maritime Executive 等，事件带可点的真实来源链接）与天气）→ Risks & Obligations（截止期倒计时矩阵 + 相关性打分 + CIF 下买/卖方归属）。
   - 预期结果：看到风险如何从真实外部信号 → 打分 → 落到本单的义务 / 期限 / 责任方；地图与走廊状态板随之高亮本航线。
5. 按引导完成处置闭环：Actions（Generate Actions → 勾选 / 编辑 → 确认）→ Treatment Plans（由确认动作生成方案 + 生成审批包）→ Audit（查看从 intake 到 treatment 的完整时间线）。
   - 预期结果：确认的动作汇入处置方案；Treatment Plans 生成可审批方案；Audit 显示全程可追溯时间线，引导在此收尾。

### 已知问题

- Render 免费后端闲置后会休眠，首次访问需数十秒冷启动。
- 演示环境使用本地 SQLite 与本地上传目录，属临时存储，重启/重部署后数据可能清空（适合 demo，非生产存储）。
- 文档抽取目前支持 TXT/DOCX/文本 PDF，扫描件图片 PDF 的 OCR 尚在 roadmap。

## 演示视频

- 视频链接：https://drive.google.com/file/d/1DJ9CeQ73f3fZdU9pqNWq_Lyz3mlROCGO/view?usp=sharing
- 时长：5 分钟
- 包含 Demo 演示：是
- 包含用户问题：是
- 包含 Google 技术说明：是
- 包含创新点说明：否
- 包含本地化说明：否
- 用户问题：未提供
- Demo：未提供
- Google技术：未提供
- 创新点：未提供
- 本地化：未提供
