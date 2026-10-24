from fastapi import APIRouter, HTTPException, status
from backend.schemas.simulation import SimulationRequest, SimulationResponse
from backend.services.simulation_service import run_simulation

router = APIRouter(prefix="/api/simulation", tags=["Simulation Engine"])


@router.post(
    "/run",
    response_model=SimulationResponse,
    status_code=status.HTTP_200_OK,
    summary="Run deterministic financial simulation",
    description="Computes deterministic SaaS metrics (MRR, ARR, monthly burn, runway) without AI."
)
def execute_simulation(payload: SimulationRequest):
    try:
        results = run_simulation(payload)
        return results
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error calculating financial simulation parameters."
        )
