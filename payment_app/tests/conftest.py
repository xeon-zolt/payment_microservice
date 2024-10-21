import os
from typing import Final
from payment_app.main import app
from sqlalchemy import create_engine
from sqlmodel import Session
from fastapi.testclient import TestClient
from unittest.mock import Mock

x_api_key: Final = 'tabsvsspacess'
x_api_key_without_gateway: Final = 'without_gateway'
x_api_key_wrong: Final = 'wrong_token'

mockClient = Mock()
mockClient.host = '127.0.0.1'

client = TestClient(app)

host = os.environ["TEST_SQL_HOST"]
port = os.environ["TEST_SQL_PORT"]
user = os.environ["TEST_SQL_USER"]
password = os.environ["TEST_SQL_PASS"]
database = os.environ["TEST_SQL_DB"]
dbtype = "mysql"

DATABASE_URL = f"{dbtype}://{user}:{password}@{host}:{port}/{database}"

engine = create_engine(
    DATABASE_URL, echo=True
)
session = Session(autocommit=False, autoflush=False, bind=engine)
