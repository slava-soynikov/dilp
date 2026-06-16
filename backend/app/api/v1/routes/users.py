import json

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.model.user import User
from app.schema.user import UserMePatch
from app.service.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return UserService(db).get_me(user)


@router.patch("/me")
def patch_me(
    payload: UserMePatch,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return UserService(db).patch_me(user, payload.model_dump(exclude_unset=True))


@router.get("/me/export")
def export_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = UserService(db).export_me(user)
    return Response(
        content=json.dumps(data, indent=2, default=str),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=dilp-export-{user.id}.json"},
    )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    UserService(db).delete_me(user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)