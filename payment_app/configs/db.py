"""Database configuration"""
import os

from sqlmodel import create_engine, Session

host = os.environ["SQL_HOST"]
port = os.environ["SQL_PORT"]
user = os.environ["SQL_USER"]
password = os.environ["SQL_PASS"]
db = os.environ["SQL_DB"]
DB_TYPE = "mysql"

DATABASE_URL = f"{DB_TYPE}://{user}:{password}@{host}:{port}/{db}"

engine = create_engine(DATABASE_URL, echo=True)

def get_session() -> Session:
    """Return database session"""
    with Session(engine) as session:
        yield session
