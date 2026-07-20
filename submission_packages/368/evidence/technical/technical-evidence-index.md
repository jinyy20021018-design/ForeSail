# 技术证据索引

- **代码仓库**：https://github.com/jinyy20021018-design/ForeSail
- **在线 Demo**：前端 Vercel（https://fore-sail.vercel.app）+ 后端 Render（FastAPI）
- **后端测试**：188 项单元测试通过（`backend/` 下 `python -m unittest discover app/tests`）

## 可核验的关键实现

| 能力 | 代码位置 |
|---|---|
| 确定性可审计内核（LLM 从不打分/判定风险） | `backend/app/agents/monitoring_agent.py` |
| Incoterms 风险归属 + per-Case 座位自动判定 | `backend/app/services/incoterm_rule_service.py`、`perspective_detection_service.py` |
| Case 相关性引擎（按本单打分降噪） | `backend/app/services/relevance_engine.py` |
| 预测层（航程×气象预报 / 台风锥 / 地缘走廊状态机） | backend 预测层服务 + Open-Meteo / 台风连接器 |
| Google Gemini 接入（默认 LLM 提供方：gemini-3.1-flash-lite） | `backend/app/services/llm_provider.py` |
| Gemini 文档抽取（结构化字段 + 证据 + 置信度） | `backend/app/services/document_service.py` |
| Gemini Agent 摘要（只复述确定性监控结果） | `backend/app/services/agent_summary_service.py` |
| Gemini 相关性因子候选提取（最终由确定性校验筛选） | `backend/app/services/llm_relevance_factor_service.py` |
| Gemini 动作候选生成（schema / ID 校验后进入用户确认） | `backend/app/services/action_set_service.py`、`structured_llm_service.py` |
| Gemini 处置方案草稿生成（三方案 schema / ID 校验） | `backend/app/services/treatment_plan_service.py`、`structured_llm_service.py` |
| 实时真实新闻抓取（带真实来源 URL） | `backend/app/services/event_connectors/real_search_event_connector.py`、`rss_search_service.py`（gCaptain / Maritime Executive / Splash247） |
| 真实预置事件（带来源链接） | `backend/app/data/curated_events.json`（2026 霍尔木兹危机，附 seavantage / flexport / UNCTAD 来源） |
| 处置方案生成（需确认事实 + 确认动作方可生成） | `backend/app/services/treatment_plan_service.py`、`action_set_service.py` |

## 说明

- 所有风险打分 / 分类 / 暴露映射 / 状态流转 / 日期与金额计算均由确定性引擎产出；Gemini 只做文档抽取、摘要、相关性因子候选、动作候选与处置方案草稿，且后几类输出会经过 schema、白名单或 ID 校验。
- 外部事件来自：实时真实新闻（RSS，带 URL）+ 精选真实案例（带来源）+ 实时天气（Open-Meteo）。
