"""
Database initialization and demonstration data seeding.
Ensures tables exist and creates demo accounts if absent.
"""

from app.db.session import engine, SessionLocal
from app.models.orm import Base, User, UserRole, ConversationMessage  # ConversationMessage ensures table is registered
from app.services.auth_service import hash_password
from app.utils.logger import logger

DEMO_USERS = [
    {
        "username": "employee",
        "email": "employee@company.com",
        "password": "employee123",
        "role": UserRole.EMPLOYEE,
    },
    {
        "username": "support_agent",
        "email": "agent@company.com",
        "password": "agent123",
        "role": UserRole.SUPPORT_AGENT,
    },
    {
        "username": "admin",
        "email": "admin@company.com",
        "password": "admin123",
        "role": UserRole.ADMIN,
    },
]


def init_database():
    """Create all tables and seed default demo users."""
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        for u in DEMO_USERS:
            existing = db.query(User).filter(
                (User.username == u["username"]) | (User.email == u["email"])
            ).first()
            if not existing:
                user = User(
                    username=u["username"],
                    email=u["email"],
                    hashed_password=hash_password(u["password"]),
                    role=u["role"],
                )
                db.add(user)
                logger.info(f"Seeded demo user: {u['username']} ({u['role'].value})")
        db.commit()
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
