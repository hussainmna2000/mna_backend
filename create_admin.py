"""
Initial Administrator Provisioning Script for Trust Guard AI.
Reads credentials from environment variables or settings and securely seeds the superadmin account.
"""
import sys
import os

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.database import SessionLocal, Base, engine
from app.models.user import User
from app.utils.security import hash_password, generate_customer_id


def seed_admin():
    print(f"Connecting to database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        admin_email = settings.ADMIN_EMAIL.lower()
        existing = db.query(User).filter(User.email == admin_email).first()

        if existing:
            print(f"Administrator account already exists: {existing.email} (ID: {existing.id}, Role: {existing.role})")
            if existing.role != "superadmin":
                existing.role = "superadmin"
                existing.status = "active"
                db.commit()
                print("Promoted existing account to 'superadmin'.")
            return

        customer_id = generate_customer_id()
        hashed = hash_password(settings.ADMIN_PASSWORD)

        admin = User(
            email=admin_email,
            full_name=settings.ADMIN_NAME,
            customer_id=customer_id,
            hashed_password=hashed,
            role="superadmin",
            status="active",
            is_verified=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("=" * 60)
        print("  TRUST GUARD AI — SUPERADMIN CREATED SUCCESSFULLY")
        print("=" * 60)
        print(f"  Email:       {admin.email}")
        print(f"  Name:        {admin.full_name}")
        print(f"  Role:        {admin.role}")
        print(f"  Customer ID: {admin.customer_id}")
        print("=" * 60)
        print("  NOTE: Please change the password upon first administrative login.")
        print("=" * 60)
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
