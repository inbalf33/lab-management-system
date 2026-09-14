from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Database connection URL (Adjust user/password/host/db_name if needed)
# DATABASE_URL = "mysql+pymysql://root:password@localhost:3306/lab_management"

# 1. SQLite database stored as a local file inside the server directory
DATABASE_URL = "sqlite:///./labflow.db"

# 2. Create the SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
    # pool_pre_ping=True,  # Checks connection validity before executing queries
)

# 3. Create a SessionLocal class for DB sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Base class for ORM models
Base = declarative_base()

# 5. Dependency helper to get DB session per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()