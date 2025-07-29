from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from beanie.odm.fields import PydanticObjectId
from app.db.database import User, QuestionSet, Submission
from app.models.student_models import QuestionSetForStudentOut, SubmissionCreate, SubmissionResultOut
from app.models.user_models import UserOut
from app.services.auth_dependencies import get_current_user
from app.services.ai_service import get_ai_evaluation

router = APIRouter()

@router.get("/question-sets", response_model=List[QuestionSetForStudentOut])
async def get_available_question_sets(current_user: User = Depends(get_current_user)):
    if current_user.role != "student":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied.")

    submitted_docs = [s async for s in Submission.find(Submission.student.id == current_user.id)]
    submitted_qset_ids = [s.question_set.ref.id for s in submitted_docs]

    unsubmitted_qsets_docs = [qs async for qs in QuestionSet.find({"_id": {"$nin": submitted_qset_ids}})]

    creator_ids = list(set([qs.creator.ref.id for qs in unsubmitted_qsets_docs]))
    creators_cursor = User.find({"_id": {"$in": creator_ids}})
    creators = [c async for c in creators_cursor]
    creators_map = {creator.id: creator for creator in creators}

    available_qsets = []
    for qs in unsubmitted_qsets_docs:
        is_public = not qs.assigned_students
        is_assigned = not is_public and current_user.id in [link.ref.id for link in qs.assigned_students]

        if is_public or is_assigned:
            creator_doc = creators_map.get(qs.creator.ref.id)
            if creator_doc:
                creator_out = UserOut.model_validate(creator_doc, from_attributes=True)
                qset_out = QuestionSetForStudentOut(**qs.model_dump(exclude={'creator'}), creator=creator_out)
                available_qsets.append(qset_out)

    return available_qsets

@router.post("/submissions", response_model=SubmissionResultOut, status_code=status.HTTP_201_CREATED)
async def create_submission(
    sub_data: SubmissionCreate,
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "student":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only students can submit answers.")

    question_set = await QuestionSet.get(PydanticObjectId(sub_data.question_set_id))
    if not question_set:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question set not found.")

    existing = await Submission.find_one(Submission.question_set.id == question_set.id, Submission.student.id == current_user.id)
    if existing:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You have already submitted an answer for this set.")

    evaluation = await get_ai_evaluation(question_set.model_answer, sub_data.answer)
    if evaluation["score"] == -1:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, evaluation["feedback"])

    submission = Submission(
        question_set=question_set,
        student=current_user,
        student_answer=sub_data.answer,
        ai_score=evaluation["score"],
        ai_feedback=evaluation["feedback"]
    )
    await submission.insert()
    
    creator_doc = await User.get(question_set.creator.ref.id)
    creator_out = UserOut.model_validate(creator_doc, from_attributes=True)
    qset_out = QuestionSetForStudentOut(**question_set.model_dump(exclude={'creator'}), creator=creator_out)

    return SubmissionResultOut(**submission.model_dump(exclude={'question_set', 'student'}), question_set=qset_out)

@router.get("/submissions", response_model=List[SubmissionResultOut])
async def get_my_submissions(current_user: User = Depends(get_current_user)):
    if current_user.role != "student":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied.")

    submissions_docs = [sub async for sub in Submission.find(Submission.student.id == current_user.id)]
    
    response = []
    if submissions_docs:
        qset_ids = list(set([sub.question_set.ref.id for sub in submissions_docs]))
        qsets_cursor = QuestionSet.find({"_id": {"$in": qset_ids}})
        qsets = [qs async for qs in qsets_cursor]
        
        creator_ids = list(set([qs.creator.ref.id for qs in qsets]))
        creators_cursor = User.find({"_id": {"$in": creator_ids}})
        creators = [c async for c in creators_cursor]
        creators_map = {creator.id: UserOut.model_validate(creator, from_attributes=True) for creator in creators}

        qsets_map = {}
        for qset in qsets:
            creator_out = creators_map.get(qset.creator.ref.id)
            if creator_out:
                qsets_map[qset.id] = QuestionSetForStudentOut(**qset.model_dump(exclude={'creator'}), creator=creator_out)
        
        for sub in submissions_docs:
            qset_out = qsets_map.get(sub.question_set.ref.id)
            if qset_out:
                response.append(SubmissionResultOut(**sub.model_dump(exclude={'question_set', 'student'}), question_set=qset_out))
                
    return response
