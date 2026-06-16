from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.model.user import User
from app.schema.programme import LessonCreate, LessonRead, ModulePatch, ModuleRead
from app.service.programme import LessonService, ModuleService

router = APIRouter(prefix="/modules", tags=["modules"])


@router.patch("/{module_id}", response_model=ModuleRead)
def patch_module(
    module_id: str,
    payload: ModulePatch,
    user: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    return ModuleService(db).patch(
        user, module_id, payload.model_dump(exclude_unset=True)
    )


@router.delete("/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_module(
    module_id: str,
    user: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    ModuleService(db).delete(user, module_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{module_id}/lessons",
    response_model=LessonRead,
    status_code=status.HTTP_201_CREATED,
)
def create_lesson(
    module_id: str,
    payload: LessonCreate,
    user: User = Depends(require_role("admin", "teacher")),
    db: Session = Depends(get_db),
):
    return LessonService(db).create(
        user,
        module_id,
        payload.title,
        payload.content_ref,
        payload.order_index,
        meeting_url=payload.meeting_url,
    )
