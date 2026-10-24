"""
VentureMind AI — Phase 3A
API routes for the Startup Validation Engine.

Endpoints:
  POST   /api/validation/analyze           — Run AI validation analysis
  GET    /api/validation/reports           — List persisted reports
  GET    /api/validation/reports/{id}      — Get specific report with full analysis
  DELETE /api/validation/reports/{id}      — Delete a report
"""
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.database.connection import get_db
from backend.schemas.validation import (
    ValidationRequest,
    ValidationReportResponse,
    ValidationReportListItem,
    ValidationAnalysis,
    SynthesisRequest,
    SynthesisResponse,
)
from backend.services.validation_service import (
    run_validation_analysis,
    get_validation_report,
    get_validation_reports,
    delete_validation_report,
    synthesize_startup_idea,
)
from backend.services.ai_service import AIError, AIConfigError

router = APIRouter(prefix="/api/validation", tags=["Startup Validation Engine"])


@router.post(
    "/synthesize",
    response_model=SynthesisResponse,
    status_code=status.HTTP_200_OK,
    summary="Stage 2 AI Co-Founder Idea Synthesis",
    description="Synthesize structured components and smart follow-up questions from a founder's natural language idea.",
)
async def synthesize_idea(payload: SynthesisRequest):
    """
    Stage 2 AI Idea Synthesis endpoint:
    Takes raw idea description and returns structured ICP, UVP, Problem, Solution,
    Business Model, and at most 2-3 high-impact clarifying follow-up questions.
    """
    try:
        return await synthesize_startup_idea(payload)
    except AIConfigError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except AIError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI synthesis response validation failed: {str(e)}",
        )



@router.post(
    "/analyze",
    response_model=ValidationReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run AI startup validation analysis",
    description=(
        "Submits startup information to the VentureMind AI Validation Engine. "
        "Returns a structured, scored analysis with transparent scoring breakdown. "
        "All assessments are AI-generated estimates — not verified market research."
    ),
)
async def analyze_startup(
    payload: ValidationRequest,
    db: Session = Depends(get_db),
):
    """
    Phase 3A: Startup Validation Engine endpoint.
    Validates inputs, calls AI, validates response, persists to MySQL.
    """
    # Optional: verify startup_id exists if provided
    if payload.startup_id is not None:
        from backend.models.startup import Startup
        startup = db.query(Startup).filter(Startup.id == payload.startup_id).first()
        if not startup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Startup with ID {payload.startup_id} not found."
            )

    try:
        analysis, db_report = await run_validation_analysis(payload, db)
    except AIConfigError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except AIError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=str(e),
        )
    except ValueError as e:
        # AI output validation failure
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI response validation failed: {str(e)}",
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while saving validation report.",
        )

    return ValidationReportResponse(
        id=db_report.id,
        startup_id=db_report.startup_id,
        report_type=db_report.report_type,
        status=db_report.status,
        score=db_report.score,
        input_summary=db_report.input_summary,
        model_used=db_report.model_used,
        created_at=db_report.created_at,
        analysis=analysis,
    )


@router.get(
    "/reports",
    response_model=List[ValidationReportListItem],
    status_code=status.HTTP_200_OK,
    summary="List validation reports",
    description="Retrieve a paginated list of persisted validation reports. Optionally filter by startup_id.",
)
def list_reports(
    startup_id: Optional[int] = Query(None, description="Filter by startup project ID"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results per page"),
    db: Session = Depends(get_db),
):
    try:
        reports = get_validation_reports(db, startup_id=startup_id, skip=skip, limit=limit)
        return [
            ValidationReportListItem(
                id=r.id,
                startup_id=r.startup_id,
                report_type=r.report_type,
                status=r.status,
                score=r.score,
                input_summary=r.input_summary,
                model_used=r.model_used,
                created_at=r.created_at,
            )
            for r in reports
        ]
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while retrieving validation reports.",
        )


@router.get(
    "/reports/{report_id}",
    response_model=ValidationReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a specific validation report",
    description="Retrieve a persisted validation report including the full structured analysis.",
)
def get_report(report_id: int, db: Session = Depends(get_db)):
    if report_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report ID. Must be a positive integer.",
        )
    report = get_validation_report(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation report {report_id} not found.",
        )

    # Deserialize stored JSON analysis
    try:
        analysis_dict = report.get_report_dict()
        analysis = ValidationAnalysis.model_validate(analysis_dict)
    except Exception:
        analysis = None

    return ValidationReportResponse(
        id=report.id,
        startup_id=report.startup_id,
        report_type=report.report_type,
        status=report.status,
        score=report.score,
        input_summary=report.input_summary,
        model_used=report.model_used,
        created_at=report.created_at,
        analysis=analysis,
    )


@router.delete(
    "/reports/{report_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a validation report",
    description="Permanently deletes a stored validation report by ID.",
)
def remove_report(report_id: int, db: Session = Depends(get_db)):
    if report_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report ID. Must be a positive integer.",
        )
    try:
        deleted = delete_validation_report(db, report_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Validation report {report_id} not found.",
            )
        return {"status": "ok", "message": f"Validation report {report_id} deleted.", "id": report_id}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while deleting validation report.",
        )
