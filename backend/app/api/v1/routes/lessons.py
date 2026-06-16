from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.integrations.cms import CMSClient, get_cms_client
from app.model.user import User
from app.schema.programme import LessonPatch, LessonRead, LessonWithContent
from app.service.programme import LessonService

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("/{lesson_id}", response_model=LessonWithContent)
def get_lesson(
    lesson_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    cms: CMSClient = Depends(get_cms_client),
):
    lesson, content = LessonService(db).get_with_content(user, lesson_id, cms)
    return LessonWithContent(
        id=lesson.id,
        module_id=lesson.module_id,
        title=lesson.title,
        content_ref=lesson.content_ref,
        meeting_url=lesson.meeting_url,
        order_index=lesson.order_index,
        content=content,
    )


@router.patch("/{lesson_id}", response_model=LessonRead)
def patch_lesson(
    lesson_id: str,
    payload: LessonPatch,
    user: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    return LessonService(db).patch(
        user, lesson_id, payload.model_dump(exclude_unset=True)
    )


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(
    lesson_id: str,
    user: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    LessonService(db).delete(user, lesson_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
