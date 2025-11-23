from __future__ import annotations

from datetime import date
from typing import List, Optional

from sqlalchemy.orm import Session

from .domain import (
    DEFAULT_CL,
    DEFAULT_ML,
    DEFAULT_OTHER,
    DEFAULT_PL,
    LeaveStatusEnum,
    LeaveTypeEnum,
)
from .models import EmployeeORM, LeaveBalanceORM, LeaveRequestORM
from .schemas import EmployeeCreate


class EmployeeRepository:
    """Repository for employee-related operations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_employee(self, data: EmployeeCreate, *, is_admin: bool = False) -> EmployeeORM:
        """
        Create a new employee.
        Also creates default leave balance for the new employee.
        """
        existing = self.db.get(EmployeeORM, data.id)
        if existing:
            raise ValueError("Employee with this id already exists")

        existing_username = (
            self.db.query(EmployeeORM)
            .filter(EmployeeORM.username == data.username)
            .first()
        )
        if existing_username:
            raise ValueError("Username already in use")

        employee = EmployeeORM(
            id=data.id,
            username=data.username,
            password=data.password,  # plain text
            name=data.name,
            email=data.email,
            department=data.department,
            is_admin=is_admin,
        )
        self.db.add(employee)

        # create default leave balance row
        balance = LeaveBalanceORM(
            employee_id=data.id,
            cl=DEFAULT_CL,
            pl=DEFAULT_PL,
            ml=DEFAULT_ML,
            other=DEFAULT_OTHER,
        )
        self.db.add(balance)

        self.db.commit()
        self.db.refresh(employee)
        return employee

    def get_employee(self, employee_id: str) -> Optional[EmployeeORM]:
        return self.db.get(EmployeeORM, employee_id)

    def list_employees(self) -> List[EmployeeORM]:
        return (
            self.db.query(EmployeeORM)
            .filter(EmployeeORM.is_active == True)  # noqa: E712
            .all()
        )

    def reset_password(self, employee: EmployeeORM, new_password: str) -> EmployeeORM:
        employee.password = new_password
        self.db.commit()
        self.db.refresh(employee)
        return employee


class LeaveRepository:
    """Repository for leave management operations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def initialize_employee_balance(
        self,
        employee_id: str,
        casual: float,
        privilege: float,
        medical: float,
        other: float,
    ) -> LeaveBalanceORM:
        balance = self.db.get(LeaveBalanceORM, employee_id)
        if balance is None:
            balance = LeaveBalanceORM(
                employee_id=employee_id,
                cl=casual,
                pl=privilege,
                ml=medical,
                other=other,
            )
            self.db.add(balance)
        else:
            balance.cl = casual
            balance.pl = privilege
            balance.ml = medical
            balance.other = other

        self.db.commit()
        self.db.refresh(balance)
        return balance

    def get_or_create_balance(self, employee_id: str) -> LeaveBalanceORM:
        balance = self.db.get(LeaveBalanceORM, employee_id)
        if balance is None:
            balance = LeaveBalanceORM(
                employee_id=employee_id,
                cl=DEFAULT_CL,
                pl=DEFAULT_PL,
                ml=DEFAULT_ML,
                other=DEFAULT_OTHER,
            )
            self.db.add(balance)
            self.db.commit()
            self.db.refresh(balance)
        return balance

    def _get_available_days(
        self,
        balance: LeaveBalanceORM,
        leave_type: LeaveTypeEnum,
    ) -> float:
        if leave_type == LeaveTypeEnum.CASUAL:
            return balance.cl
        if leave_type == LeaveTypeEnum.PRIVILEGE:
            return balance.pl
        if leave_type == LeaveTypeEnum.MEDICAL:
            return balance.ml
        if leave_type == LeaveTypeEnum.OTHER:
            return balance.other
        raise ValueError(f"Unsupported leave type: {leave_type}")

    def _deduct_days(
        self,
        balance: LeaveBalanceORM,
        leave_type: LeaveTypeEnum,
        days: float,
    ) -> None:
        if leave_type == LeaveTypeEnum.CASUAL:
            balance.cl -= days
        elif leave_type == LeaveTypeEnum.PRIVILEGE:
            balance.pl -= days
        elif leave_type == LeaveTypeEnum.MEDICAL:
            balance.ml -= days
        elif leave_type == LeaveTypeEnum.OTHER:
            balance.other -= days

    def credit_leave(
        self,
        employee_id: str,
        leave_type: LeaveTypeEnum,
        days: float,
    ) -> LeaveBalanceORM:
        balance = self.get_or_create_balance(employee_id)

        if leave_type == LeaveTypeEnum.CASUAL:
            balance.cl += days
        elif leave_type == LeaveTypeEnum.PRIVILEGE:
            balance.pl += days
        elif leave_type == LeaveTypeEnum.MEDICAL:
            balance.ml += days
        elif leave_type == LeaveTypeEnum.OTHER:
            balance.other += days

        self.db.commit()
        self.db.refresh(balance)
        return balance

    def apply_leave(
        self,
        employee_id: str,
        leave_type: LeaveTypeEnum,
        days: float,
        start_date: date,
        reason: str,
    ) -> LeaveRequestORM:
        balance = self.get_or_create_balance(employee_id)
        available = self._get_available_days(balance, leave_type)

        if days > available:
            raise ValueError(
                f"Insufficient balance for {leave_type.value}. "
                f"available={available}, requested={days}"
            )

        self._deduct_days(balance, leave_type, days)

        request = LeaveRequestORM(
            employee_id=employee_id,
            leave_type=leave_type.value,
            days=days,
            start_date=start_date,
            reason=reason,
            status=LeaveStatusEnum.APPROVED.value,
        )
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    def list_employee_requests(self, employee_id: str) -> List[LeaveRequestORM]:
        return (
            self.db.query(LeaveRequestORM)
            .filter(LeaveRequestORM.employee_id == employee_id)
            .order_by(LeaveRequestORM.created_at.desc())
            .all()
        )
