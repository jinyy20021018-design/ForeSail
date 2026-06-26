import { api, type FieldConflict } from "../api/client";

type Props = {
  caseId: string;
  conflicts: FieldConflict[];
  onConflictsChange: (conflicts: FieldConflict[]) => void;
};

export function FieldConflictPanel({ caseId, conflicts, onConflictsChange }: Props) {
  async function resolve(conflict: FieldConflict) {
    const defaultValue = String(conflict.values[0]?.value ?? "");
    const value = window.prompt("Resolved value", defaultValue);
    if (value === null) return;
    const note = window.prompt("Resolution note", "Resolved after document review.");
    if (note === null) return;
    await api.resolveFieldConflict(caseId, conflict.conflict_id, value, note);
    onConflictsChange(await api.getFieldConflicts(caseId));
  }

  return (
    <section className="panel full-width">
      <div className="panel-heading">
        <h2>Field Conflicts</h2>
        <span className="tag">{conflicts.length} conflicts</span>
      </div>
      {conflicts.length === 0 ? <p className="empty-state">No field conflicts detected.</p> : (
        <div className="action-grid">
          {conflicts.map((conflict) => (
            <article className="action-item" key={conflict.conflict_id}>
              <span className="action-id">{conflict.conflict_id} | {conflict.severity} | {conflict.status}</span>
              <h3>{conflict.field_name}</h3>
              <p>{conflict.explanation}</p>
              <ul>
                {conflict.values.map((value) => (
                  <li key={`${value.field_id}-${value.source_document_name}`}>{value.source_document_name}: {String(value.value)}</li>
                ))}
              </ul>
              {conflict.status === "OPEN" && <button type="button" onClick={() => resolve(conflict)}>Resolve</button>}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
