from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date
from backend.app.models.employee import EmployeeRole, EmployeeStatus

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: Optional[EmployeeRole] = EmployeeRole.EMPLOYEE
    department_id: Optional[str] = None
    manager_id: Optional[str] = None
    grade: Optional[str] = "L3"
    country: Optional[str] = "US"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: EmployeeRole
    department_id: Optional[str]
    manager_id: Optional[str]
    grade: str
    country: str
    status: EmployeeStatus
    hire_date: date

    class Config:
        from_attributes = True

TokenResponse.model_rebuild()
