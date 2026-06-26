from dataclasses import dataclass


@dataclass
class Document:
    document_id: str
    case_id: str
    document_type: str
    filename: str
    file_path: str
    uploaded_at: str
    parse_status: str
    raw_text: str


@dataclass
class ExtractedField:
    field_id: str
    case_id: str
    field_name: str
    display_name: str
    value: str | int | float | bool | None
    source_document_id: str
    source_document_name: str
    evidence_text: str
    page_number: int | None
    confidence: float
    requires_confirmation: bool
    review_status: str
    edited_value: str | int | float | bool | None


@dataclass
class ObligationDeadline:
    obligation_id: str
    case_id: str
    name: str
    source: str
    source_document_id: str | None
    deadline_date: str
    current_assessment: str
    severity: str
    recommended_action: str
    evidence_field_ids: list[str]
    status: str


@dataclass
class InformationGap:
    gap_id: str
    case_id: str
    title: str
    reason: str
    blocks_decision: str
    owner_role: str
    priority: str
    status: str


@dataclass
class ActionDraft:
    draft_id: str
    case_id: str
    draft_type: str
    title: str
    recipient_role: str
    body: str
    related_actions: list[str]
    status: str
    requires_user_review: bool
