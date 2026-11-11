from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List
from backend.app.core.database import get_db
from backend.app.core.security import decode_access_token
from backend.app.models.employee import Employee, EmployeeRole, EmployeeStatus

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Employee:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    employee_id: str = payload.get("employee_id")
    if employee_id is None:
        raise credentials_exception
        
    user = db.query(Employee).filter(Employee.id == employee_id).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(
    current_user: Employee = Depends(get_current_user)
) -> Employee:
    if current_user.status != EmployeeStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Inactive user account")
    return current_user

def require_roles(allowed_roles: List[EmployeeRole]):
    def role_checker(current_user: Employee = Depends(get_current_active_user)) -> Employee:
        if current_user.role not in allowed_roles and current_user.role != EmployeeRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {[r.value for r in allowed_roles]}"
            )
        return current_user
    return role_checker
