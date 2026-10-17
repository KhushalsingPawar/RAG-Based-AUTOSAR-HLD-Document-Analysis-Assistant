from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # Import all models to ensure they are registered with Base metadata
    from backend.app.models import schema  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Safe auto-migration for existing SQLite databases
    try:
        with engine.connect() as conn:
            # Check projects table
            proj_cols = [r[1] for r in conn.exec_driver_sql("PRAGMA table_info(projects)").fetchall()]
            if "user_id" not in proj_cols:
                conn.exec_driver_sql("ALTER TABLE projects ADD COLUMN user_id INTEGER REFERENCES users(id)")
                conn.exec_driver_sql("UPDATE projects SET user_id = 1 WHERE user_id IS NULL")
                conn.commit()

            # Check documents table
            doc_cols = [r[1] for r in conn.exec_driver_sql("PRAGMA table_info(documents)").fetchall()]
            if "user_id" not in doc_cols:
                conn.exec_driver_sql("ALTER TABLE documents ADD COLUMN user_id INTEGER REFERENCES users(id)")
                conn.exec_driver_sql("UPDATE documents SET user_id = 1 WHERE user_id IS NULL")
                conn.commit()

            # Replace unique index on projects.name with standard index so each user can have their own workspace
            conn.exec_driver_sql("DROP INDEX IF EXISTS ix_projects_name")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_projects_name ON projects (name)")
            conn.commit()
    except Exception as e:
        print(f"[DB Init Warning] Auto-migration check: {e}")

