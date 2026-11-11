import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.core.security import create_access_token
from backend.app.models.employee import Employee, EmployeeRole

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="session")
def admin_token():
    return create_access_token("EMP-000001", EmployeeRole.ADMIN.value, "EMP-000001")

@pytest.fixture(scope="session")
def manager_token():
    return create_access_token("EMP-000004", EmployeeRole.MANAGER.value, "EMP-000004")

@pytest.fixture(scope="session")
def finance_token():
    return create_access_token("EMP-000003", EmployeeRole.FINANCE.value, "EMP-000003")

@pytest.fixture(scope="session")
def employee_token():
    return create_access_token("EMP-000005", EmployeeRole.EMPLOYEE.value, "EMP-000005")
