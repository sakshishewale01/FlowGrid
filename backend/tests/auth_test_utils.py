from sqlalchemy import text


def promote_test_user(session_factory, email: str, role: str) -> None:
    db = session_factory()
    try:
        db.execute(
            text("UPDATE users SET role = :role WHERE email = :email"),
            {"role": role, "email": email},
        )
        db.commit()
    finally:
        db.close()
