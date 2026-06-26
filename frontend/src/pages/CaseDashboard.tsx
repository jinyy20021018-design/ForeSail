import { useEffect, useState } from "react";
import {
  api,
  type ActionDraft,
  type AgentRunRecord,
  type AgentRunResponse,
  type DocumentRecord,
  type ExtractedField,
  type FieldConflict,
  type InformationGap,
  type ObligationDeadline,
  type StatusTimelineEntry,
  type TradeCase,
  type WatchProfile
} from "../api/client";
import { ActionBoard } from "../components/ActionBoard";
import { AgentRunSummary } from "../components/AgentRunSummary";
import { AgentRunTrace } from "../components/AgentRunTrace";
import { AgentRunHistory } from "../components/AgentRunHistory";
import { CaseSnapshot } from "../components/CaseSnapshot";
import { DocumentUploadPanel } from "../components/DocumentUploadPanel";
import { EventResultsTable } from "../components/EventResultsTable";
import { ExtractedFieldsReview } from "../components/ExtractedFieldsReview";
import { FieldConflictPanel } from "../components/FieldConflictPanel";
import { OperationalPanels } from "../components/OperationalPanels";
import { RiskSummaryPanel } from "../components/RiskSummaryPanel";
import { StatusTimeline } from "../components/StatusTimeline";
import { WatchProfilePanel } from "../components/WatchProfilePanel";
import { WorkflowStepper } from "../components/WorkflowStepper";
import { t, type Language } from "../i18n";

type Props = {
  activeCase: TradeCase;
  onCaseChange: (tradeCase: TradeCase) => void;
  language: Language;
};

export function CaseDashboard({ activeCase, onCaseChange, language }: Props) {
  const [watchProfile, setWatchProfile] = useState<WatchProfile | null>(null);
  const [agentResult, setAgentResult] = useState<AgentRunResponse | null>(null);
  const [timeline, setTimeline] = useState<StatusTimelineEntry[]>([]);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [extractedFields, setExtractedFields] = useState<ExtractedField[]>([]);
  const [conflicts, setConflicts] = useState<FieldConflict[]>([]);
  const [workflow, setWorkflow] = useState<import("../api/client").WorkflowState | null>(null);
  const [agentRuns, setAgentRuns] = useState<AgentRunRecord[]>([]);
  const [obligations, setObligations] = useState<ObligationDeadline[]>([]);
  const [gaps, setGaps] = useState<InformationGap[]>([]);
  const [drafts, setDrafts] = useState<ActionDraft[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isMonitoring, setIsMonitoring] = useState(false);

  useEffect(() => {
    api
      .getWatchProfile(activeCase.case_id)
      .then(setWatchProfile)
      .catch(() => setError(t(language, "failedProfile")));
    api
      .getStatusTimeline(activeCase.case_id)
      .then(setTimeline)
      .catch(() => setError(t(language, "failedTimeline")));
    api.getDocuments(activeCase.case_id).then(setDocuments).catch(() => undefined);
    api.getExtractedFields(activeCase.case_id).then(setExtractedFields).catch(() => undefined);
    api.getFieldConflicts(activeCase.case_id).then(setConflicts).catch(() => undefined);
    api.getWorkflowState(activeCase.case_id).then(setWorkflow).catch(() => undefined);
    api.getAgentRuns(activeCase.case_id).then(setAgentRuns).catch(() => undefined);
  }, [activeCase.case_id, language]);

  async function runAgentMonitoringCycle() {
    setError(null);
    setIsMonitoring(true);
    try {
      const result = await api.runAgentMonitoringCycle(activeCase.case_id);
      setAgentResult(result);
      setWatchProfile(result.watch_profile);
      setTimeline(result.status_timeline);
      setObligations(result.obligations);
      setGaps(result.information_gaps);
      setDrafts(result.action_drafts);
      setAgentRuns(await api.getAgentRuns(activeCase.case_id));
      setWorkflow(await api.getWorkflowState(activeCase.case_id));
      onCaseChange(result.case);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : t(language, "failedMonitor"));
    } finally {
      setIsMonitoring(false);
    }
  }

  async function confirmFields() {
    setError(null);
    try {
      const facts = await api.confirmFields(activeCase.case_id);
      onCaseChange({ ...activeCase, ...facts, status: "ACTIVE" } as TradeCase);
      setWatchProfile(await api.getWatchProfile(activeCase.case_id));
      setWorkflow(await api.getWorkflowState(activeCase.case_id));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Confirm fields failed.");
    }
  }

  const canRunAgent = activeCase.status === "ACTIVE";
  const runButtonText =
    activeCase.status === "MONITORING"
      ? t(language, "monitoringActive")
      : isMonitoring
        ? t(language, "agentRunning")
        : t(language, "runAgentCycle");

  async function continueMonitoring() {
    setError(null);
    try {
      const result = await api.continueMonitoring(activeCase.case_id);
      onCaseChange(result.case);
      setTimeline(result.status_timeline);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : t(language, "failedContinue"));
    }
  }

  return (
    <section className="dashboard">
      <header className="dashboard-header">
        <div>
          <div className="page-kicker">
            {t(language, "caseLabel")} {activeCase.case_id}
          </div>
          <h1>{t(language, "dashboardTitle")}</h1>
        </div>
        <div className="header-actions">
          <button
            className="primary-action"
            type="button"
            onClick={runAgentMonitoringCycle}
            disabled={isMonitoring || !canRunAgent}
          >
            {runButtonText}
          </button>
          <button
            className="secondary-action"
            type="button"
            onClick={continueMonitoring}
            disabled={activeCase.status !== "ACTION_REQUIRED"}
          >
            {t(language, "continueMonitoring")}
          </button>
        </div>
      </header>

      {error && <div className="error">{error}</div>}
      <WorkflowStepper workflow={workflow} />

      <div className="dashboard-grid">
        <CaseSnapshot tradeCase={activeCase} language={language} />
        {watchProfile && <WatchProfilePanel profile={watchProfile} language={language} />}
        <StatusTimeline entries={timeline} language={language} />
      </div>

      <DocumentUploadPanel
        caseId={activeCase.case_id}
        documents={documents}
        onDocumentsChange={async (nextDocuments) => {
          setDocuments(nextDocuments);
          setWorkflow(await api.getWorkflowState(activeCase.case_id));
        }}
        onError={setError}
        language={language}
      />
      <ExtractedFieldsReview
        caseId={activeCase.case_id}
        fields={extractedFields}
        onFieldsChange={async (nextFields) => {
          setExtractedFields(nextFields);
          setConflicts(await api.getFieldConflicts(activeCase.case_id));
          setWorkflow(await api.getWorkflowState(activeCase.case_id));
        }}
        onError={setError}
        language={language}
      />
      <FieldConflictPanel caseId={activeCase.case_id} conflicts={conflicts} onConflictsChange={async (nextConflicts) => {
        setConflicts(nextConflicts);
        setWorkflow(await api.getWorkflowState(activeCase.case_id));
      }} />
      {extractedFields.length > 0 && (
        <button className="primary-action section-action" type="button" onClick={confirmFields} disabled={conflicts.some((conflict) => conflict.severity === "High" && conflict.status === "OPEN")}>
          Confirm Fields
        </button>
      )}

      <AgentRunSummary result={agentResult} language={language} />
      <AgentRunTrace trace={agentResult?.trace ?? []} language={language} />
      <EventResultsTable results={agentResult?.relevance_results ?? []} language={language} />
      <RiskSummaryPanel summary={agentResult?.risk_summary ?? null} language={language} />
      <OperationalPanels obligations={obligations} gaps={gaps} drafts={drafts} caseId={activeCase.case_id} onDraftsChange={setDrafts} />
      <AgentRunHistory caseId={activeCase.case_id} runs={agentRuns} />
      <ActionBoard actions={agentResult?.actions ?? []} language={language} />
    </section>
  );
}
