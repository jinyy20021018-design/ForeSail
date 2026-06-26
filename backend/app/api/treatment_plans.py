from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services.treatment_plan_service import (
    ConfirmedFactsRequiredError,
    archive_treatment_plan,
    generate_approval_package,
    generate_treatment_plans,
    get_treatment_plan,
    list_approval_packages,
    list_treatment_plans,
    select_treatment_plan,
    update_approval_status,
)

router = APIRouter(prefix="/api/cases", tags=["treatment-plans"])


class ApprovalStatusPayload(BaseModel):
    status: str
    decision_note: str | None = None


@router.post("/{case_id}/treatment-plans/generate")
def generate_case_treatment_plans(case_id: str) -> dict:
    try:
        return generate_treatment_plans(case_id)
    except ConfirmedFactsRequiredError as error:
        return JSONResponse(status_code=409, content={"error": error.error, "message": error.message})
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Case or confirmed facts not found: {case_id}") from None


@router.get("/{case_id}/treatment-plans")
def read_treatment_plans(case_id: str) -> list[dict]:
    return _or_404(lambda: list_treatment_plans(case_id), case_id)


@router.get("/{case_id}/treatment-plans/{plan_id}")
def read_treatment_plan(case_id: str, plan_id: str) -> dict:
    return _or_404(lambda: get_treatment_plan(case_id, plan_id), case_id)


@router.post("/{case_id}/treatment-plans/{plan_id}/select")
def select_case_treatment_plan(case_id: str, plan_id: str) -> dict:
    return _or_404(lambda: select_treatment_plan(case_id, plan_id), case_id)


@router.post("/{case_id}/treatment-plans/{plan_id}/archive")
def archive_case_treatment_plan(case_id: str, plan_id: str) -> dict:
    return _or_404(lambda: archive_treatment_plan(case_id, plan_id), case_id)


@router.post("/{case_id}/treatment-plans/{plan_id}/approval-package")
def generate_case_approval_package(case_id: str, plan_id: str) -> dict:
    return _or_404(lambda: generate_approval_package(case_id, plan_id), case_id)


@router.get("/{case_id}/approval-packages")
def read_approval_packages(case_id: str) -> list[dict]:
    return _or_404(lambda: list_approval_packages(case_id), case_id)


@router.post("/{case_id}/approval-packages/{approval_package_id}/status")
def update_case_approval_status(case_id: str, approval_package_id: str, payload: ApprovalStatusPayload) -> dict:
    try:
        return update_approval_status(case_id, approval_package_id, payload.status, payload.decision_note)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Approval package not found: {approval_package_id}") from None


def _or_404(factory, case_id: str):
    try:
        return factory()
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Treatment plan resource not found for case: {case_id}") from None
