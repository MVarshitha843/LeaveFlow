from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from backend.app.models.employee import EmployeeRole, EmployeeStatus

class DepartmentResponse(BaseModel):
    id: str
    code: str
    name: str
    head_id: Optional[str]
    annual_budget: float
    current_spend: float
    reserved_budget: float
    available_budget: float

    class Config:
        from_attributes = True

class CostCenterResponse(BaseModel):
    id: str
    code: str
    name: str
    department_id: str
    budget_limit: float
    current_spend: float
    reserved_spend: float
    available_spend: float

    class Config:
        from_attributes = True

class EmployeeDetailResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: EmployeeRole
    department_id: Optional[str]
    department_name: Optional[str] = None
    manager_id: Optional[str]
    manager_name: Optional[str] = None
    hire_date: date
    termination_date: Optional[date]
    grade: str
    country: str
    status: EmployeeStatus
    created_at: datetime

    class Config:
        from_attributes = True
