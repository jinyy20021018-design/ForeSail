import type { AgentRunResponse } from "../api/client";
import { t, translate, type Language } from "../i18n";

type Props = {
  result: AgentRunResponse | null;
  language: Language;
};

export function AgentRunSummary({ result, language }: Props) {
  if (!result) {
    return (
      <section className="panel full-width agent-summary-card">
        <div className="panel-heading">
          <h2>{t(language, "agentRunSummary")}</h2>
        </div>
        <p className="empty-state">{t(language, "agentSummaryEmpty")}</p>
      </section>
    );
  }

  return (
    <section className="panel full-width agent-summary-card">
      <div className="panel-heading">
        <div>
          <div className="page-kicker">{result.agent_run_id}</div>
          <h2>{t(language, "agentRunComplete")}</h2>
        </div>
        <span className="tag">
          {translate.status(language, result.status_before)} {"->"} {translate.status(language, result.status_after)}
        </span>
      </div>

      <div className="summary-metrics">
        <div className={result.llm_enabled ? "metric-active" : ""}>
          <strong>{result.llm_enabled ? "ON" : "OFF"}</strong>
          <span>{t(language, "llmAgent")}</span>
        </div>
        <div>
          <strong>{result.events_scanned}</strong>
          <span>{t(language, "eventsScanned")}</span>
        </div>
        <div>
          <strong>{result.relevant_count}</strong>
          <span>{translate.classification(language, "Relevant")}</span>
        </div>
        <div>
          <strong>{result.watch_count}</strong>
          <span>{translate.classification(language, "Watch")}</span>
        </div>
        <div>
          <strong>{result.irrelevant_count}</strong>
          <span>{translate.classification(language, "Irrelevant")}</span>
        </div>
        <div>
          <strong>{result.risk_summary.exposures.length}</strong>
          <span>{t(language, "exposureCategories")}</span>
        </div>
        <div>
          <strong>{result.actions.length}</strong>
          <span>{t(language, "actionsGenerated")}</span>
        </div>
      </div>

      <p className="subtle">
        {t(language, "summarySource")}: {t(language, result.summary_source)}
        {result.llm_required ? ` (${t(language, "llmRequired")})` : ""}
      </p>
      <p className="agent-summary-text">{result.summary}</p>
    </section>
  );
}
