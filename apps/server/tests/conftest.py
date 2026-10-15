import pytest
from app.storage.database import Database
from app.service import Service

@pytest.fixture
def service(tmp_path):
    result = Service(Database(tmp_path / 'test.sqlite'))
    result.principal('alice')
    result.principal('bob')
    return result

@pytest.fixture
def project(service):
    return service.create_project('alice', 'Avatar')['project_id']
