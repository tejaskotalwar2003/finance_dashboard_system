
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# DB config
DB_NAME = "finance_db"
DB_USER = "Enter your username"
DB_PASSWORD = "Enter your password"
DB_HOST = "localhost"

# Step 1: connect to default postgres database
DEFAULT_DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/postgres"
default_engine = create_engine(DEFAULT_DB_URL)

# Step 2: create database if not exists
with default_engine.connect() as conn:
    conn.execution_options(isolation_level="AUTOCOMMIT")

    result = conn.execute(
        text(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
    )

    if not result.scalar():
        conn.execute(text(f'CREATE DATABASE {DB_NAME}'))
        print(" Database created successfully")

# Step 3: connect to your actual database
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()
