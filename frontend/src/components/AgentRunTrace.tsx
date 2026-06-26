import type { AgentRunTraceStep } from "../api/client";
import { t, type Language } from "../i18n";

type Props = {
  trace: AgentRunTraceStep[];
  language: Language;
};

export function AgentRunTrace({ trace, language }: Props) {
  return (
    <section className="panel full-width">
      <div className="panel-heading">
        <h2>{t(language, "agentRunTrace")}</h2>
        <span className="tag">
          {trace.length} {t(language, "steps")}
        </span>
      </div>
      {trace.length === 0 ? (
        <p className="empty-state">{t(language, "agentTraceEmpty")}</p>
      ) : (
        <ol className="agent-trace">
          {trace.map((step) => (
            <li key={step.step}>
              <div className="trace-step-number">{step.step}</div>
              <div>
                <div className="trace-title">
                  <strong>{step.name}</strong>
                  <span>{step.tool_or_service}</span>
                </div>
                <p>{step.description}</p>
                <small>{step.output_summary}</small>
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
