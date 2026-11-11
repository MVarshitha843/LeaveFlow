from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.core.database import get_db
from backend.app.models.employee import Employee, Department, CostCenter, EmployeeRole
from backend.app.schemas.employee import DepartmentResponse, CostCenterResponse, EmployeeDetailResponse
from backend.app.api.deps import get_current_active_user

router = APIRouter(tags=["Employees & Organization"])

@router.get("/employees", response_model=List[EmployeeDetailResponse])
def list_employees(
    department_id: Optional[str] = None,
    role: Optional[EmployeeRole] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    query = db.query(Employee)
    if department_id:
        query = query.filter(Employee.department_id == department_id)
    if role:
        query = query.filter(Employee.role == role)
    if search:
        s = f"%{search}%"
        query = query.filter(
            (Employee.first_name.ilike(s)) |
            (Employee.last_name.ilike(s)) |
            (Employee.email.ilike(s)) |
            (Employee.id.ilike(s))
        )
    employees = query.offset(skip).limit(limit).all()

    # Enrich with department and manager names
    results = []
    for emp in employees:
        dept_name = emp.department.name if emp.department else None
        mgr_name = f"{emp.manager.first_name} {emp.manager.last_name}" if emp.manager else None
        results.append(EmployeeDetailResponse(
            id=emp.id,
            email=emp.email,
            first_name=emp.first_name,
            last_name=emp.last_name,
            role=emp.role,
            department_id=emp.department_id,
            department_name=dept_name,
            manager_id=emp.manager_id,
            manager_name=mgr_name,
            hire_date=emp.hire_date,
            termination_date=emp.termination_date,
            grade=emp.grade,
            country=emp.country,
            status=emp.status,
            created_at=emp.created_at
        ))
    return results

@router.get("/employees/{id}", response_model=EmployeeDetailResponse)
def get_employee(
    id: str,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    emp = db.query(Employee).filter(Employee.id == id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    dept_name = emp.department.name if emp.department else None
    mgr_name = f"{emp.manager.first_name} {emp.manager.last_name}" if emp.manager else None
    return EmployeeDetailResponse(
        id=emp.id,
        email=emp.email,
        first_name=emp.first_name,
        last_name=emp.last_name,
        role=emp.role,
        department_id=emp.department_id,
        department_name=dept_name,
        manager_id=emp.manager_id,
        manager_name=mgr_name,
        hire_date=emp.hire_date,
        termination_date=emp.termination_date,
        grade=emp.grade,
        country=emp.country,
        status=emp.status,
        created_at=emp.created_at
    )

@router.get("/departments", response_model=List[DepartmentResponse])
def list_departments(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    departments = db.query(Department).all()
    results = []
    for d in departments:
        avail = float(d.annual_budget) - float(d.current_spend) - float(d.reserved_budget)
        results.append(DepartmentResponse(
            id=d.id,
            code=d.code,
            name=d.name,
            head_id=d.head_id,
            annual_budget=float(d.annual_budget),
            current_spend=float(d.current_spend),
            reserved_budget=float(d.reserved_budget),
            available_budget=avail
        ))
    return results

@router.get("/cost-centers", response_model=List[CostCenterResponse])
def list_cost_centers(
    department_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_active_user)
):
    query = db.query(CostCenter)
    if department_id:
        query = query.filter(CostCenter.department_id == department_id)
    cost_centers = query.all()
    results = []
    for c in cost_centers:
        avail = float(c.budget_limit) - float(c.current_spend) - float(c.reserved_spend)
        results.append(CostCenterResponse(
            id=c.id,
            code=c.code,
            name=c.name,
            department_id=c.department_id,
            budget_limit=float(c.budget_limit),
            current_spend=float(c.current_spend),
            reserved_spend=float(c.reserved_spend),
            available_spend=avail
        ))
    return results
