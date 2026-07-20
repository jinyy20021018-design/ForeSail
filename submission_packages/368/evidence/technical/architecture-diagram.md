# ForeSail 技术架构图

```mermaid
flowchart LR
    USER["评委 / 外贸运营人员"]
    DOCS["合同 / 订舱确认 / 信用证"]
    EXT["外部风险源<br/>Open-Meteo · GDELT · 航运 RSS<br/>台风 · 风险日历 · 政策与精选事件"]
    GEMINI["Google Gemini API<br/>结构化抽取 · 摘要 · 候选与草稿<br/>不直接评分或改变状态"]
    STORE[("SQLite kv_store + 本地 uploads<br/>Demo 临时存储")]

    subgraph VERCEL["Vercel"]
        FE["React + Vite 前端<br/>Case 创建 · 字段复核 · 风险看板 · 行动审批"]
    end

    subgraph RENDER["Render · FastAPI 后端"]
        API["REST API<br/>Cases · Documents · Events · Monitoring<br/>Actions · Treatment Plans"]
        DOCPIPE["单据抽取管线<br/>文本解析 · 字段抽取 · 字段白名单/格式校验"]
        REVIEW["人工确认<br/>字段证据 + 置信度<br/>Approve / Edit / Reject"]
        CASE["Trade Case + Watch Profile<br/>交易事实 · 航线 · 港口 · 硬期限"]
        INGEST["外部事件摄取<br/>查询 · 归一化 · 去重"]
        AGENT["MonitoringAgent<br/>流程编排 + 可审计 Trace"]
        CORE["确定性风险内核<br/>相关性评分 · 敞口映射 · Incoterms 归属<br/>义务/期限 · 风险日历 · 状态机"]
        GENERATE["受约束生成层<br/>摘要 · 相关性因子候选<br/>动作候选 · 三类处置方案草稿"]
        GUARD["安全边界<br/>JSON 格式 · 关键字段/枚举<br/>已知 ID 校验或清洗 · 用户确认"]
        OUTPUT["证据化输出<br/>相关性与风险摘要 · 截止期<br/>Action Board · Treatment Plans"]
    end

    USER --> FE
    DOCS --> FE
    FE <-->|"HTTPS · JSON · 文件上传"| API
    API --> DOCPIPE
    GEMINI -.->|"结构化字段抽取"| DOCPIPE
    DOCPIPE --> REVIEW --> CASE
    EXT --> INGEST
    API --> AGENT
    CASE --> AGENT
    INGEST --> AGENT
    AGENT --> CORE
    CORE --> OUTPUT
    CORE -->|"已确认事实与确定性结果"| GENERATE
    GEMINI -.->|"摘要与候选草稿"| GENERATE
    GENERATE --> GUARD --> OUTPUT
    OUTPUT --> API
    API <--> STORE

    classDef google fill:#e8f0fe,stroke:#4285f4,color:#174ea6,stroke-width:2px;
    classDef deterministic fill:#e6f4ea,stroke:#188038,color:#0d652d,stroke-width:2px;
    classDef boundary fill:#fef7e0,stroke:#f9ab00,color:#7a4f01,stroke-width:2px;
    class GEMINI google;
    class CORE deterministic;
    class GUARD boundary;
```

## 架构边界

- `MonitoringAgent` 只负责编排流程与记录 Trace；相关性评分、风险分类、敞口映射、Incoterms 责任归属、合同/信用证硬期限处理和状态流转均由确定性服务完成。
- Gemini 负责单据字段抽取、运行摘要、相关性因子候选、动作候选和处置方案草稿；结构化候选要求返回 JSON 对象，并经过关键字段、枚举、日期格式和已知 ID 的代码校验或清洗。动作候选可以包含建议执行日期，处置方案可以包含估算成本，但不会改写已确认交易金额、合同期限或核心风险决策；结果仍须用户确认。
- 当前免费 Demo 使用 SQLite 与本地上传目录。Render 文件系统可能在休眠或重部署后清空，因此该存储仅适用于演示环境。

## 代码证据映射

| 架构模块 | 可核验代码位置 |
|---|---|
| React/Vite 前端与 API 调用 | `frontend/src/App.tsx`、`frontend/src/pages/CaseWorkspace.tsx`、`frontend/src/api/client.ts` |
| FastAPI API 层 | `backend/app/main.py`、`backend/app/api/` |
| 单据抽取与字段确认 | `backend/app/services/document_service.py`、`document_extraction_pipeline.py`、`extraction_schema_validator.py` |
| 外部事件摄取 | `backend/app/services/event_ingestion_service.py`、`backend/app/services/event_connectors/` |
| Agent 编排 | `backend/app/agents/monitoring_agent.py` |
| 确定性风险内核 | `backend/app/services/relevance_engine.py`、`risk_mapper.py`、`incoterm_rule_service.py`、`obligation_service.py`、`status_machine.py` |
| Gemini 与受约束生成 | `backend/app/services/llm_provider.py`、`structured_llm_service.py`、`agent_summary_service.py`、`action_set_service.py`、`treatment_plan_service.py` |
| 持久化与上传文件 | `backend/app/services/persistence_service.py`、`backend/app/services/document_service.py` |
