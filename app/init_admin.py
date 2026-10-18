import getpass
import sys

from .core.database import SessionLocal
from .models import User
from .services.security import hash_password


def main():
    email = input("First admin email: ").strip().lower()
    password = getpass.getpass("Admin password (minimum 12 characters): ")
    confirm = getpass.getpass("Confirm password: ")
    if len(password) < 12 or password != confirm:
        raise SystemExit("Use a password of at least 12 characters and make both entries match.")
    db = SessionLocal()
    try:
        if db.query(User).filter_by(role="ADMIN").first():
            raise SystemExit("An admin already exists; refusing to create another initial admin.")
        if db.query(User).filter_by(email=email).first():
            raise SystemExit("That email is already registered.")
        db.add(User(email=email, password_hash=hash_password(password), role="ADMIN", is_active=True, display_name="Administrator"))
        db.commit()
        print("Initial admin created.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
