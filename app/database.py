"""
Database Layer: SQLModel engine, session factory, and initialization.
"""
from typing import Generator
from sqlmodel import Session, SQLModel, create_engine, select
from app.config import DATABASE_URL, INITIAL_PROFILE
from app.models.profile import UserProfile

# SQLite connection args for multi-threaded FastAPI access
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def init_db() -> None:
    """
    Creates database tables and ensures the initial profile record exists.
    Called on FastAPI startup lifespan.
    """
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        profile = session.get(UserProfile, 1)
        if not profile:
            # Seed the initial default profile
            seed_profile = UserProfile(
                id=1,
                display_name=INITIAL_PROFILE["displayName"],
                bio=INITIAL_PROFILE["bio"],
                link_label=INITIAL_PROFILE["link"]["label"],
                link_url=INITIAL_PROFILE["link"]["url"]
            )
            session.add(seed_profile)
            session.commit()


def get_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a database session per request.
    """
    with Session(engine) as session:
        yield session
