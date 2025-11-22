from __future__ import annotations

from datetime import date, datetime
from typing import Dict, Optional

from pydantic import BaseModel

from .domain import (
    DEFAULT_CL,
    DEFAULT_ML,
    DEFAULT_OTHER,
    DEFAULT_PL,
    LeaveStatusEnum,
    LeaveTypeEnum,
)


class LeaveBalances(BaseModel):
    """DTO for leave balances."""

    employee_id: str
    balances: Dict[str, float]


class LeaveRequestDTO(BaseModel):
    """DTO for leave request."""

    id: int
    employee_id: str
    leave_type: LeaveTypeEnum
    days: float
    start_date: date
    reason: Optional[str]
    status: LeaveStatusEnum
    created_at: datetime


class InitializeEmployeeBody(BaseModel):
    """Request body for initializing an employee's balances."""

    casual: float = DEFAULT_CL
    privilege: float = DEFAULT_PL
    medical: float = DEFAULT_ML
    other: float = DEFAULT_OTHER


class ApplyLeaveBody(BaseModel):
    """Request body for applying leave."""

    leave_type: LeaveTypeEnum
    days: float
    start_date: date
    reason: Optional[str] = ""


class CreditLeaveBody(BaseModel):
    """Request body for crediting leave."""

    leave_type: LeaveTypeEnum
    days: float
    note: Optional[str] = ""


class ApiResponse(BaseModel):
    """Standard API response wrapper."""

    success: bool
    data: Optional[dict] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


# -------- Employee schemas --------

class EmployeeCreate(BaseModel):
    id: str
    username: str
    password: str
    name: str
    email: str
    department: Optional[str] = None


class EmployeeDTO(BaseModel):
    id: str
    username: str
    name: str
    email: str
    department: Optional[str]
    is_active: bool


class PasswordResetBody(BaseModel):
    new_password: str
