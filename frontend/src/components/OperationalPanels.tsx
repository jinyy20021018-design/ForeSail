import { api, type ActionDraft, type InformationGap, type ObligationDeadline } from "../api/client";

type Props = {
  obligations: ObligationDeadline[];
  gaps: InformationGap[];
  drafts: ActionDraft[];
  caseId: string;
  onDraftsChange: (drafts: ActionDraft[]) => void;
  showObligations?: boolean;
  showGaps?: boolean;
  showDrafts?: boolean;
};

export function OperationalPanels({
  obligations,
  gaps,
  drafts,
  caseId,
  onDraftsChange,
  showObligations = true,
  showGaps = true,
  showDrafts = true
}: Props) {
  async function refreshDrafts() {
    onDraftsChange(await api.getActionDrafts(caseId));
  }

  async function updateDraft(draftId: string, action: "review" | "ready" | "reject" | "archive" | "regenerate") {
    if (action === "review") await api.markDraftInReview(caseId, draftId);
    if (action === "ready") await api.markDraftReady(caseId, draftId);
    if (action === "reject") await api.rejectDraft(caseId, draftId, "Rejected in MVP review");
    if (action === "archive") await api.archiveDraft(caseId, draftId);
    if (action === "regenerate") await api.regenerateDraft(caseId, draftId);
    await refreshDrafts();
  }
  return (
    <>
      {showObligations && <section className="panel full-width">
        <div className="panel-heading">
          <h2>Obligation & Deadline Map</h2>
          <span className="tag">{obligations.length} obligations</span>
        </div>
        {obligations.length === 0 ? <p className="empty-state">No obligations generated yet.</p> : <div className="action-grid">
          {obligations.map((obligation) => (
            <article className="action-item" key={obligation.obligation_id}>
              <span className="action-id">{obligation.obligation_id}</span>
              <h3>{obligation.name}</h3>
              <p>{obligation.current_assessment}</p>
              <small>{obligation.source} | {obligation.deadline_date} | {obligation.recommended_action}</small>
            </article>
          ))}
        </div>}
      </section>}
      {showGaps && <section className="panel full-width">
        <div className="panel-heading">
          <h2>Information Gaps</h2>
          <span className="tag">{gaps.length} gaps</span>
        </div>
        {gaps.length === 0 ? <p className="empty-state">No information gaps detected yet.</p> : <div className="action-grid">
          {gaps.map((gap) => (
            <article className="action-item" key={gap.gap_id}>
              <span className="action-id">{gap.gap_id}</span>
              <h3>{gap.title}</h3>
              <p>{gap.reason}</p>
              <small>{gap.owner_role} | {gap.priority} | blocks: {gap.blocks_decision}</small>
            </article>
          ))}
        </div>}
      </section>}
      {showDrafts && <section className="panel full-width">
        <div className="panel-heading">
          <h2>Action Drafts</h2>
          <span className="tag">{drafts.length} drafts</span>
        </div>
        {drafts.length === 0 ? <p className="empty-state">No action drafts generated yet.</p> : <div className="action-grid">
          {drafts.map((draft) => (
            <article className="action-item" key={draft.draft_id}>
              <span className="action-id">{draft.draft_id}</span>
              <h3>{draft.title}</h3>
              <p>{draft.body}</p>
              <small>{draft.recipient_role} | {draft.status}</small>
              <div className="inline-actions">
                <button type="button" onClick={() => updateDraft(draft.draft_id, "review")}>In Review</button>
                <button type="button" onClick={() => updateDraft(draft.draft_id, "ready")}>Ready</button>
                <button type="button" onClick={() => updateDraft(draft.draft_id, "reject")}>Reject</button>
                <button type="button" onClick={() => updateDraft(draft.draft_id, "archive")}>Archive</button>
                <button type="button" onClick={() => updateDraft(draft.draft_id, "regenerate")}>Regenerate</button>
              </div>
            </article>
          ))}
        </div>}
      </section>}
    </>
  );
}
