"""Admin / auditor bootstrap CLI.

Usage:
    python -m app.cli create-admin   --email boss@example.com   --password Bosspass1
    python -m app.cli create-auditor --email audit@example.com  --password Auditor1234
"""
import argparse
import sys

from sqlalchemy.orm import Session

from app.core.security import hash_password, validate_password_policy
from app.model.user import Role, User, UserRole


def _create_role_user(db: Session, email: str, password: str, role_name: str) -> User:
    email = email.strip().lower()
    err = validate_password_policy(password)
    if err:
        raise ValueError(err)
    if db.query(User).filter_by(email=email).first():
        raise ValueError("user with that email already exists")

    user = User(
        email=email,
        password_hash=hash_password(password),
        status="active",
    )
    db.add(user)
    db.flush()
    role = db.query(Role).filter_by(name=role_name).one()
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    return user


def create_admin(db: Session, email: str, password: str) -> User:
    return _create_role_user(db, email, password, "admin")


def create_auditor(db: Session, email: str, password: str) -> User:
    return _create_role_user(db, email, password, "auditor")


def _main() -> int:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("create-admin", "create-auditor"):
        sp = sub.add_parser(name)
        sp.add_argument("--email", required=True)
        sp.add_argument("--password", required=True)
    args = parser.parse_args()

    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        if args.cmd == "create-admin":
            u = create_admin(db, args.email, args.password)
            print(f"created admin id={u.id} email={u.email}")
        elif args.cmd == "create-auditor":
            u = create_auditor(db, args.email, args.password)
            print(f"created auditor id={u.id} email={u.email}")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(_main())