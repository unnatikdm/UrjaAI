from fastapi import APIRouter, Depends
from app.schemas.predict import ExplainRequest, ExplainResponse
from app.services import ml as ml_service
from app.services.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/explain", tags=["Explainability"])


@router.post("", response_model=ExplainResponse)
def explain(req: ExplainRequest, _: User = Depends(get_current_user)):
    """
    Return a plain-English explanation and SHAP-style feature contribution
    breakdown for the most recent forecast of the requested building.
    """
    text, contributions = ml_service.get_explanation(req.building_id)

    return ExplainResponse(
        building_id=req.building_id,
        explanation_text=text,
        feature_contributions=contributions,
    )
