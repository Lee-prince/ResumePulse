# ============================================
# AI Career Navigator — database.py
# Sets up the SQLite database connection
# and provides sessions for all DB operations
# ============================================

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from models import Base
import os

# Load our .env file so we can read DATABASE_URL
load_dotenv()

# ── DATABASE CONNECTION ────────────────────────────────────────────
# SQLite stores everything in a single file (database.db)
# This is the connection string that tells SQLAlchemy where it is

DATABASE_URL = f"sqlite:///{os.getenv('DATABASE_URL', 'database.db')}"

# ── ENGINE ────────────────────────────────────────────────────────
# The engine is the actual connection to the database
# check_same_thread=False is needed for FastAPI
# because multiple requests can come in at the same time

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # Set to True if you want to see SQL queries in terminal
)

# ── SESSION FACTORY ───────────────────────────────────────────────
# A session is like a "unit of work" with the database
# Every request gets its own session
# autocommit=False means we control when changes are saved
# autoflush=False means we control when data is sent to DB

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)


# ── CREATE ALL TABLES ─────────────────────────────────────────────
# This reads all our models (User, TailoredResume)
# and creates the actual tables in database.db
# If tables already exist, it skips them safely

def create_tables():
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")


# ── SESSION DEPENDENCY ────────────────────────────────────────────
# This is used by FastAPI to give each request its own DB session
# The "yield" makes it a generator — FastAPI handles cleanup
# This pattern ensures sessions are always properly closed

def get_db():
    db = SessionLocal()
    try:
        yield db        # give the session to the request
    finally:
        db.close()      # always close when request is done


# ── TEST THE CONNECTION ───────────────────────────────────────────
# This runs only when you execute this file directly
# python database.py → creates tables and confirms it worked

if __name__ == "__main__":
    print("🔄 Creating database tables...")
    create_tables()
    print("✅ Database ready at: database.db")
    print("\nTables created:")
    from sqlalchemy import inspect
    inspector = inspect(engine)
    for table_name in inspector.get_table_names():
        print(f"  📋 {table_name}")
        columns = inspector.get_columns(table_name)
        for col in columns:
            print(f"      - {col['name']} ({col['type']})")