# 原创性与合规声明

- 赛前已存在：是
- 比赛期间新增：比赛期间把 ForeSail 从『只有基础框架和很简单的 agent 架构』重写为一套完整、可运行、可审计的交易风险处置系统，主要新增工作包括：(1) 接入真实外部连接器 Open-Meteo（16 天气象预报）、GDELT（全球新闻）、RSS 航运源，替代早期桩数据；(2) 新建预测层——航程×气象预报时空对齐、台风路径锥、地缘走廊状态机与风险日历，把风险从『事后告警』提前到『驶入前预警』；(3) Incoterms 2020 风险归属引擎 + per-Case 座位自动判定（从单据当事人字段判定我方卖方/买方，输出『谁的风险/谁能动手/要不要你管』）；(4) 事件相关性引擎，对每条外部事件按本单监控画像打分降噪；(5) treatment/处置链路——义务与期限映射、信息缺口检测、带证据的对外动作草稿；(6) 确定性可审计内核（打分/分类/暴露/状态/日期全部确定性，LLM 从不打分），后端 188 项单元测试通过；(7) 前端全站重构并完成线上部署（Vercel 前端 + Render 后端）；(8) 接入 Google Gemini 作为默认 LLM 提供方，承担文档抽取与 agent 运行摘要。整条数据链（外部事件 → 相关性 → 敞口 → 义务/期限 → 处置草稿）在本次比赛期间打通并落地。
- 原创性确认：是
- 评委访问和测试授权：是

## 小型附件索引

- {"path": "evidence/demo-case-documents/contract.docx", "type": "technical", "note": "Hormuz 演示案例·合同（Shanghai Solaris，CIF，交易日期对齐至 2026-08/09）。评委可把本套 3 份单据在 Demo 的『Create New Case』上传，复现完整 抽取→确认→监控 流程。"}
- {"path": "evidence/demo-case-documents/booking_confirmation.docx", "type": "technical", "note": "Hormuz 演示案例·订舱确认（ETD 2026-08-28 / ETA 2026-09-15）。"}
- {"path": "evidence/demo-case-documents/letter_of_credit.docx", "type": "technical", "note": "Hormuz 演示案例·信用证（最迟装运 2026-09-05 / LC 到期 2026-09-30）。"}
- {"path": "evidence/demo-case-documents/README.txt", "type": "technical", "note": "Hormuz 演示案例单据说明。"}
- {"path": "evidence/user-research/user-interview-notes.md", "type": "user-research", "note": "一手用户访谈纪要（脱敏）——跨境电商进口团队从业者，印证核心痛点、买卖双视角与进口/中介新用户群。"}
- {"path": "evidence/technical/technical-evidence-index.md", "type": "technical", "note": "技术证据索引——仓库、188 测试、Gemini、实时真实新闻抓取等关键实现的代码位置，供评委核验。"}
