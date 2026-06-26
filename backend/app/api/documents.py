from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.services.document_service import (
    approve_field,
    confirm_fields,
    edit_field,
    extract_documents,
    get_action_drafts,
    get_confirmed_facts,
    get_documents,
    get_extracted_fields,
    get_field_conflicts,
    get_field_evidence,
    get_information_gaps,
    get_obligations,
    regenerate_action_draft,
    resolve_field_conflict,
    reject_field,
    update_action_draft_status,
    upload_document,
)
from app.services.case_detail_autofill_service import build_case_detail_autofill
from app.services.workflow_service import get_workflow_state

router = APIRouter(prefix="/api/cases", tags=["documents"])


class EditFieldPayload(BaseModel):
    value: str | int | float | bool | None


class ResolveConflictPayload(BaseModel):
    resolved_value: str | int | float | bool | None
    resolution_note: str = ""
    resolved_by: str = "user"


class RejectDraftPayload(BaseModel):
    reason: str = ""


@router.post("/{case_id}/documents/upload")
def upload_case_document(
    case_id: str,
    file: UploadFile = File(...),
    document_type: str = Form("UNKNOWN"),
) -> dict:
    try:
        return upload_document(case_id, file.filename or "uploaded-file", file.file, document_type)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}") from None


@router.get("/{case_id}/documents")
def read_documents(case_id: str) -> list[dict]:
    return _or_404(lambda: get_documents(case_id), case_id)


@router.post("/{case_id}/documents/extract")
def extract_case_documents(case_id: str) -> dict:
    return _or_404(lambda: extract_documents(case_id), case_id)


@router.get("/{case_id}/extracted-fields")
def read_extracted_fields(case_id: str) -> list[dict]:
    return _or_404(lambda: get_extracted_fields(case_id), case_id)


@router.post("/{case_id}/autofill-from-documents")
def autofill_case_from_documents(case_id: str) -> dict:
    return _or_404(lambda: build_case_detail_autofill(case_id), case_id)


@router.get("/{case_id}/autofill")
def read_case_autofill(case_id: str) -> dict:
    return _or_404(lambda: build_case_detail_autofill(case_id), case_id)


@router.get("/{case_id}/extracted-fields/{field_id}/evidence")
def read_field_evidence(case_id: str, field_id: str) -> dict:
    return _or_404(lambda: get_field_evidence(case_id, field_id), case_id)


@router.post("/{case_id}/extracted-fields/{field_id}/approve")
def approve_case_field(case_id: str, field_id: str) -> dict:
    return _or_404(lambda: approve_field(case_id, field_id), case_id)


@router.post("/{case_id}/extracted-fields/{field_id}/edit")
def edit_case_field(case_id: str, field_id: str, payload: EditFieldPayload) -> dict:
    return _or_404(lambda: edit_field(case_id, field_id, payload.value), case_id)


@router.post("/{case_id}/extracted-fields/{field_id}/reject")
def reject_case_field(case_id: str, field_id: str) -> dict:
    return _or_404(lambda: reject_field(case_id, field_id), case_id)


@router.post("/{case_id}/confirm-fields")
def confirm_case_fields(case_id: str) -> dict:
    try:
        return confirm_fields(case_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}") from None
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/{case_id}/field-conflicts")
def read_field_conflicts(case_id: str) -> list[dict]:
    return _or_404(lambda: get_field_conflicts(case_id), case_id)


@router.post("/{case_id}/field-conflicts/{conflict_id}/resolve")
def resolve_case_field_conflict(case_id: str, conflict_id: str, payload: ResolveConflictPayload) -> dict:
    return _or_404(
        lambda: resolve_field_conflict(case_id, conflict_id, payload.resolved_value, payload.resolution_note, payload.resolved_by),
        case_id,
    )


@router.get("/{case_id}/confirmed-facts")
def read_confirmed_facts(case_id: str) -> dict:
    return _or_404(lambda: get_confirmed_facts(case_id), case_id)


@router.get("/{case_id}/obligations")
def read_obligations(case_id: str) -> list[dict]:
    return _or_404(lambda: get_obligations(case_id), case_id)


@router.get("/{case_id}/information-gaps")
def read_information_gaps(case_id: str) -> list[dict]:
    return _or_404(lambda: get_information_gaps(case_id), case_id)


@router.get("/{case_id}/action-drafts")
def read_action_drafts(case_id: str) -> list[dict]:
    return _or_404(lambda: get_action_drafts(case_id), case_id)


@router.post("/{case_id}/action-drafts/{draft_id}/regenerate")
def regenerate_case_action_draft(case_id: str, draft_id: str) -> dict:
    return _or_404(lambda: regenerate_action_draft(case_id, draft_id), case_id)


@router.post("/{case_id}/action-drafts/{draft_id}/mark-in-review")
def mark_action_draft_in_review(case_id: str, draft_id: str) -> dict:
    return _or_404(lambda: update_action_draft_status(case_id, draft_id, "IN_REVIEW"), case_id)


@router.post("/{case_id}/action-drafts/{draft_id}/mark-ready")
def mark_action_draft_ready(case_id: str, draft_id: str) -> dict:
    return _or_404(lambda: update_action_draft_status(case_id, draft_id, "READY"), case_id)


@router.post("/{case_id}/action-drafts/{draft_id}/reject")
def reject_action_draft(case_id: str, draft_id: str, payload: RejectDraftPayload) -> dict:
    return _or_404(lambda: update_action_draft_status(case_id, draft_id, "REJECTED", payload.reason), case_id)


@router.post("/{case_id}/action-drafts/{draft_id}/archive")
def archive_action_draft(case_id: str, draft_id: str) -> dict:
    return _or_404(lambda: update_action_draft_status(case_id, draft_id, "ARCHIVED"), case_id)


@router.get("/{case_id}/workflow-state")
def read_workflow_state(case_id: str) -> dict:
    return _or_404(lambda: get_workflow_state(case_id), case_id)


def _or_404(factory, case_id: str):
    try:
        return factory()
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}") from None
