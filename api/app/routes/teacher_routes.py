from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from beanie.odm.fields import PydanticObjectId
from app.db.database import User, QuestionSet, Submission
from app.models.teacher_models import QuestionSetCreate, QuestionSetOut, SubmissionReviewOut, ScoreUpdate
from app.models.user_models import UserOut
from app.services.auth_dependencies import get_current_user

router = APIRouter()

@router.post("/question-sets", response_model=QuestionSetOut, status_code=status.HTTP_201_CREATED)
async def create_question_set(qs_data: QuestionSetCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "teacher":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only teachers can create question sets.")
    
    assigned_student_list = []
    if qs_data.assigned_usernames:
        students = [s async for s in User.find({"username": {"$in": qs_data.assigned_usernames}, "role": "student"})]
        if len(students) != len(set(qs_data.assigned_usernames)):
             # Using set to handle duplicate usernames in input
            raise HTTPException(status.HTTP_404_NOT_FOUND, "One or more student usernames not found.")
        assigned_student_list = students

    question_set = QuestionSet(
        title=qs_data.title,
        question=qs_data.question,
        model_answer=qs_data.model_answer,
        creator=current_user,
        assigned_students=assigned_student_list
    )
    await question_set.insert()
    
    creator_out = UserOut.model_validate(current_user, from_attributes=True)
    assigned_students_out = [UserOut.model_validate(s, from_attributes=True) for s in assigned_student_list]
    
    return QuestionSetOut(
        **question_set.model_dump(exclude={'creator', 'assigned_students'}),
        creator=creator_out,
        assigned_students=assigned_students_out
    )

@router.get("/question-sets", response_model=List[QuestionSetOut])
async def get_teacher_question_sets(current_user: User = Depends(get_current_user)):
    if current_user.role != "teacher":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied.")
    
    q_sets_docs = [qs async for qs in QuestionSet.find(QuestionSet.creator.id == current_user.id)]
    
    response = []
    creator_out = UserOut.model_validate(current_user, from_attributes=True)
    for qs in q_sets_docs:
        assigned_students_out = []
        if qs.assigned_students:
            student_ids = [link.ref.id for link in qs.assigned_students]
            students = [s async for s in User.find({"_id": {"$in": student_ids}})]
            assigned_students_out = [UserOut.model_validate(s, from_attributes=True) for s in students]

        response.append(QuestionSetOut(
            **qs.model_dump(exclude={'creator', 'assigned_students'}), 
            creator=creator_out,
            assigned_students=assigned_students_out
        ))
    return response

@router.get("/question-sets/{qs_id}/submissions", response_model=List[SubmissionReviewOut])
async def get_submissions_for_set(qs_id: PydanticObjectId, current_user: User = Depends(get_current_user)):
    # ROBUST FIX: Fetch by ID first, then verify ownership.
    question_set = await QuestionSet.get(qs_id)
    if not question_set or question_set.creator.ref.id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question set not found or access denied.")
    
    submissions_docs = [sub async for sub in Submission.find(Submission.question_set.id == question_set.id)]
    
    response = []
    if submissions_docs:
        student_ids = list(set([sub.student.ref.id for sub in submissions_docs]))
        students_cursor = User.find({"_id": {"$in": student_ids}})
        students = [s async for s in students_cursor]
        students_map = {student.id: UserOut.model_validate(student, from_attributes=True) for student in students}
        
        for sub in submissions_docs:
            student_out = students_map.get(sub.student.ref.id)
            if student_out:
                response.append(SubmissionReviewOut(**sub.model_dump(exclude={'student'}), student=student_out))
    return response
        
@router.put("/submissions/{sub_id}/finalize", response_model=SubmissionReviewOut)
async def finalize_score(sub_id: PydanticObjectId, score_update: ScoreUpdate, current_user: User = Depends(get_current_user)):
    submission = await Submission.get(sub_id)
    if not submission:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Submission not found.")
    
    question_set = await QuestionSet.get(submission.question_set.ref.id)
    if not question_set or question_set.creator.ref.id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied.")

    submission.final_score = score_update.final_score
    await submission.save()
    
    student = await User.get(submission.student.ref.id)
    student_out = UserOut.model_validate(student, from_attributes=True)

    return SubmissionReviewOut(**submission.model_dump(exclude={'student'}), student=student_out)
