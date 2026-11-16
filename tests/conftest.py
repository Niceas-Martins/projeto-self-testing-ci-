import uuid
import pytest
from fastapi.testclient import TestClient

from src.main import create_app
from src.repositories.sqlite_repository import SQLiteRepository


@pytest.fixture
def repo():
    repository = SQLiteRepository(f"file:wallet_{uuid.uuid4().hex}?mode=memory&cache=shared")
    yield repository
    repository.anchor.close()


@pytest.fixture
def client(repo):
    with TestClient(create_app(repo=repo)) as test_client:
        yield test_client
