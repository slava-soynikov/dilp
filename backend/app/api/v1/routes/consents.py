from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.model.user import User
from app.schema.consent import ConsentCreate, ConsentRead
from app.service.consent import ConsentService

router = APIRouter(prefix="/consents", tags=["consents"])


@router.get("", response_model=list[ConsentRead])
def list_my_consents(
    user: User = Depends(require_role("parent")),
    db: Session = Depends(get_db),
):
    return ConsentService(db).list_for_parent(user)


@router.post("", response_model=ConsentRead, status_code=status.HTTP_201_CREATED)
def grant_consent(
    payload: ConsentCreate,
    user: User = Depends(require_role("parent")),
    db: Session = Depends(get_db),
):
    return ConsentService(db).grant(
        user,
        payload.child_id,
        payload.consent_type,
        payload.consent_version,
        payload.consent_text_ref,
    )


@router.post("/{consent_id}/revoke", response_model=ConsentRead)
def revoke_consent(
    consent_id: str,
    user: User = Depends(require_role("parent")),
    db: Session = Depends(get_db),
):
    return ConsentService(db).revoke(user, consent_id)