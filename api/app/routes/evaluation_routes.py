from fastapi import APIRouter, Depends, HTTPException, status
from app.db.database import User
from app.models.evaluation_models import EvaluationRequest, EvaluationResponse
from app.services.ai_service import get_ai_evaluation
from app.services.auth_dependencies import get_current_user

router = APIRouter()

@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_student_answer(
    request: EvaluationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    AI-powered evaluation endpoint.

    - Requires authentication.
    - Only accessible by users with the 'teacher' role.
    """
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action.",
        )

    evaluation_result = await get_ai_evaluation(
        model_answer=request.model_answer,
        student_answer=request.student_answer
    )

    if evaluation_result["score"] == -1:
            raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=evaluation_result["feedback"],
        )

    return evaluation_result
    