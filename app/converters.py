from __future__ import annotations

from .domain import LeaveStatusEnum, LeaveTypeEnum
from .models import EmployeeORM, LeaveBalanceORM, LeaveRequestORM
from .schemas import EmployeeDTO, LeaveBalances, LeaveRequestDTO


def build_balance_dto(balance: LeaveBalanceORM) -> LeaveBalances:
    """Convert ORM to DTO with normalized keys."""
    return LeaveBalances(
        employee_id=balance.employee_id,
        balances={
            "CL": balance.cl,
            "PL": balance.pl,
            "ML": balance.ml,
            "OTHER": balance.other,
        },
    )


def build_request_dto(req: LeaveRequestORM) -> LeaveRequestDTO:
    """Convert ORM to DTO."""
    return LeaveRequestDTO(
        id=req.id,
        employee_id=req.employee_id,
        leave_type=LeaveTypeEnum(req.leave_type),
        days=req.days,
        start_date=req.start_date,
        reason=req.reason,
        status=LeaveStatusEnum(req.status),
        created_at=req.created_at,
    )


def build_employee_dto(emp: EmployeeORM) -> EmployeeDTO:
    return EmployeeDTO(
        id=emp.id,
        username=emp.username,
        name=emp.name,
        email=emp.email,
        department=emp.department,
        is_active=emp.is_active,
    )
