from __future__ import annotations

from sqlalchemy import Boolean, Column, Date, DateTime, Float, Integer, String, func

from .db import Base


class EmployeeORM(Base):
    """Stores employee master data and credentials."""

    __tablename__ = "employees"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # plain text
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    department = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)


class LeaveBalanceORM(Base):
    """Stores leave balances per employee. One row per employee."""

    __tablename__ = "leave_balances"

    employee_id = Column(String, primary_key=True, index=True)
    cl = Column(Float, nullable=False, default=10.0)
    pl = Column(Float, nullable=False, default=15.0)
    ml = Column(Float, nullable=False, default=90.0)
    other = Column(Float, nullable=False, default=0.0)


class LeaveRequestORM(Base):
    """Stores individual leave requests."""

    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    employee_id = Column(String, index=True, nullable=False)
    leave_type = Column(String, nullable=False)  # CL/PL/ML/OTHER
    days = Column(Float, nullable=False)
    start_date = Column(Date, nullable=False)
    reason = Column(String, nullable=True)
    status = Column(String, nullable=False)  # APPROVED/REJECTED/PENDING
    created_at = Column(DateTime, nullable=False, server_default=func.now())
