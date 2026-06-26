import { useState } from "react";
import { api, type DocumentRecord, type ExtractedField, type FieldEvidence } from "../api/client";
import { type Language } from "../i18n";

type Props = {
  caseId: string;
  fields: ExtractedField[];
  onFieldsChange: (fields: ExtractedField[]) => void;
  onDocumentsChange?: (documents: DocumentRecord[]) => void;
  onError: (message: string) => void;
  language: Language;
  canExtract?: boolean;
};

export function ExtractedFieldsReview({ caseId, fields, onFieldsChange, onDocumentsChange, onError, canExtract = true }: Props) {
  const [evidence, setEvidence] = useState<FieldEvidence | null>(null);
  async function refresh() {
    onFieldsChange(await api.getExtractedFields(caseId));
  }

  async function extract() {
    if (!canExtract) {
      onError("Upload at least one document before extracting fields.");
      return;
    }
    try {
      const result = await api.extractDocuments(caseId);
      onFieldsChange(result.extracted_fields);
      onDocumentsChange?.(result.documents);
    } catch (error) {
      onError(error instanceof Error ? error.message : "Extraction failed.");
    }
  }

  async function approve(fieldId: string) {
    await api.approveField(caseId, fieldId);
    await refresh();
  }

  async function edit(field: ExtractedField) {
    const value = window.prompt(`Edit ${field.display_name}`, String(field.edited_value ?? field.value ?? ""));
    if (value === null) {
      return;
    }
    await api.editField(caseId, field.field_id, value);
    await refresh();
  }

  async function reject(fieldId: string) {
    await api.rejectField(caseId, fieldId);
    await refresh();
  }

  async function selectField(field: ExtractedField) {
    setEvidence(await api.getFieldEvidence(caseId, field.field_id));
  }

  return (
    <section className="panel full-width">
      <div className="panel-heading">
        <h2>Extracted Fields Review</h2>
        <button className="secondary-action" type="button" onClick={extract} disabled={!canExtract}>
          Extract Documents
        </button>
      </div>
      {fields.length === 0 ? (
        <p className="empty-state">Upload documents, then extract fields.</p>
      ) : (
        <div className="review-layout">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Field</th>
                <th>Value</th>
                <th>Evidence</th>
                <th>Confidence</th>
                <th>Status</th>
                <th>Review</th>
              </tr>
            </thead>
            <tbody>
              {fields.map((field) => (
                <tr key={field.field_id} onClick={() => selectField(field)} className="clickable-row">
                  <td>{field.display_name}</td>
                  <td>{String(field.edited_value ?? field.value ?? "")}</td>
                  <td>{field.evidence_text}</td>
                  <td>{Math.round(field.confidence * 100)}%</td>
                  <td>{field.review_status}</td>
                  <td>
                    <div className="inline-actions">
                      <button type="button" onClick={() => approve(field.field_id)}>Approve</button>
                      <button type="button" onClick={() => edit(field)}>Edit</button>
                      <button type="button" onClick={() => reject(field.field_id)}>Reject</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <aside className="evidence-viewer">
          <h3>Evidence Viewer</h3>
          {!evidence ? <p className="empty-state">Click a field row to inspect evidence.</p> : (
            <dl>
              <div><dt>Field</dt><dd>{evidence.display_name}</dd></div>
              <div><dt>Value</dt><dd>{String(evidence.value ?? "")}</dd></div>
              <div><dt>Source Document</dt><dd>{evidence.source_document_name}</dd></div>
              <div><dt>Page</dt><dd>{evidence.page_number ?? "Unknown"}</dd></div>
              <div><dt>Confidence</dt><dd>{Math.round(evidence.confidence * 100)}%</dd></div>
              <div><dt>Status</dt><dd>{evidence.review_status}</dd></div>
              <div><dt>Evidence Text</dt><dd><mark>{evidence.evidence_text}</mark></dd></div>
            </dl>
          )}
        </aside>
        </div>
      )}
    </section>
  );
}
