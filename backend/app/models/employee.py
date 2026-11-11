import enum
from datetime import datetime, date, timezone
from sqlalchemy import Column, String, Integer, Float, Date, DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class EmployeeRole(str, enum.Enum):
    EMPLOYEE = "EMPLOYEE"
    MANAGER = "MANAGER"
    FINANCE = "FINANCE"
    PROCESS_OWNER = "PROCESS_OWNER"
    ADMIN = "ADMIN"

class EmployeeStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ON_LEAVE = "ON_LEAVE"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"

class Department(Base):
    __tablename__ = "departments"

    id = Column(String(50), primary_key=True)  # e.g., "DEP-ENG"
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    head_id = Column(String(50), nullable=True)  # Employee ID of Department Head
    annual_budget = Column(Numeric(12, 2), nullable=False, default=100000.00)
    current_spend = Column(Numeric(12, 2), nullable=False, default=0.00)
    reserved_budget = Column(Numeric(12, 2), nullable=False, default=0.00)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    employees = relationship("Employee", back_populates="department", foreign_keys="Employee.department_id")
    cost_centers = relationship("CostCenter", back_populates="department")

class CostCenter(Base):
    __tablename__ = "cost_centers"

    id = Column(String(50), primary_key=True)  # e.g., "CC-ENG-001"
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    department_id = Column(String(50), ForeignKey("departments.id"), nullable=False)
    budget_limit = Column(Numeric(12, 2), nullable=False, default=50000.00)
    current_spend = Column(Numeric(12, 2), nullable=False, default=0.00)
    reserved_spend = Column(Numeric(12, 2), nullable=False, default=0.00)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    department = relationship("Department", back_populates="cost_centers")
    employee_mappings = relationship("EmployeeCostCenter", back_populates="cost_center")

class Employee(Base):
    __tablename__ = "employees"

    id = Column(String(50), primary_key=True)  # e.g., "EMP-000001"
    email = Column(String(150), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    role = Column(Enum(EmployeeRole), default=EmployeeRole.EMPLOYEE, nullable=False)
    department_id = Column(String(50), ForeignKey("departments.id"), nullable=True)
    manager_id = Column(String(50), ForeignKey("employees.id"), nullable=True)
    hire_date = Column(Date, nullable=False, default=date(2023, 1, 1))
    termination_date = Column(Date, nullable=True)
    grade = Column(String(20), default="L3", nullable=False)  # L1, L2, L3, L4, L5, EXEC
    country = Column(String(50), default="US", nullable=False)
    status = Column(Enum(EmployeeStatus), default=EmployeeStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    department = relationship("Department", back_populates="employees", foreign_keys=[department_id])
    manager = relationship("Employee", remote_side=[id], backref="direct_reports")
    cost_center_mappings = relationship("EmployeeCostCenter", back_populates="employee")

class EmployeeCostCenter(Base):
    __tablename__ = "employee_cost_centers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String(50), ForeignKey("employees.id"), nullable=False)
    cost_center_id = Column(String(50), ForeignKey("cost_centers.id"), nullable=False)
    is_default = Column(Integer, default=1)  # 1: true, 0: false

    employee = relationship("Employee", back_populates="cost_center_mappings")
    cost_center = relationship("CostCenter", back_populates="employee_mappings")
