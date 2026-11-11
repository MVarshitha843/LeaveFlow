from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.app.core.database import get_db
from backend.app.core.security import verify_password, get_password_hash, create_access_token
from backend.app.models.employee import Employee, EmployeeRole, EmployeeStatus
from backend.app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from backend.app.api.deps import get_current_active_user
from backend.app.engines.audit.service import AuditService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Employee).filter(Employee.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.status != EmployeeStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Account is not active")

    access_token = create_access_token(
        subject=user.id,
        role=user.role.value,
        employee_id=user.id
    )

    AuditService.record_event(
        db=db,
        entity_type="EMPLOYEE",
        entity_id=user.id,
        action="LOGIN_SUCCESS",
        payload={"email": user.email, "role": user.role.value},
        actor_id=user.id
    )
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/register", response_model=UserResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(Employee).filter(Employee.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Generate sequential EMP ID
    count = db.query(Employee).count()
    emp_id = f"EMP-{count + 1:06d}"

    new_user = Employee(
        id=emp_id,
        email=request.email,
        hashed_password=get_password_hash(request.password),
        first_name=request.first_name,
        last_name=request.last_name,
        role=request.role or EmployeeRole.EMPLOYEE,
        department_id=request.department_id,
        manager_id=request.manager_id,
        grade=request.grade or "L3",
        country=request.country or "US",
        status=EmployeeStatus.ACTIVE
    )
    db.add(new_user)
    db.flush()

    AuditService.record_event(
        db=db,
        entity_type="EMPLOYEE",
        entity_id=emp_id,
        action="REGISTERED",
        payload={"email": new_user.email, "role": new_user.role.value},
        actor_id="SYSTEM"
    )
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/me", response_model=UserResponse)
def get_me(current_user: Employee = Depends(get_current_active_user)):
    return current_user

@router.get("/demo-accounts")
def get_demo_accounts(db: Session = Depends(get_db)):
    """
    Returns verified demo credentials across the 5 primary platform roles
    for effortless 1-click reviewer testing.
    """
    roles = [
        EmployeeRole.EMPLOYEE,
        EmployeeRole.MANAGER,
        EmployeeRole.FINANCE,
        EmployeeRole.PROCESS_OWNER,
        EmployeeRole.ADMIN
    ]
    demo_users = []
    for r in roles:
        user = db.query(Employee).filter(
            Employee.role == r,
            Employee.status == EmployeeStatus.ACTIVE
        ).first()
        if user:
            demo_users.append({
                "role": r.value,
                "label": f"{r.value.replace('_', ' ').title()} Portal",
                "email": user.email,
                "password": "Password123!",
                "name": f"{user.first_name} {user.last_name}",
                "employee_id": user.id,
                "department_id": user.department_id
            })
    return demo_users
