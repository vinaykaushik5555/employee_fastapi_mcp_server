from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .converters import (
    build_balance_dto,
    build_employee_dto,
    build_request_dto,
)
from .deps import get_db
from .models import EmployeeORM
from .repository import EmployeeRepository, LeaveRepository
from .responses import error, ok
from .schemas import (
    ApiResponse,
    ApplyLeaveBody,
    CreditLeaveBody,
    EmployeeCreate,
    InitializeEmployeeBody,
    PasswordResetBody,
)
from .security import get_current_employee


router = APIRouter(prefix="/employees", tags=["employees"])


# -------- Employee endpoints (creation, list, self info, password reset) --------

@router.post("", response_model=ApiResponse)
def create_employee(
    body: EmployeeCreate,
    db: Session = Depends(get_db),
):
    """Create a new employee with username & password."""
    emp_repo = EmployeeRepository(db)
    try:
        emp = emp_repo.create_employee(body)
    except ValueError as exc:
        return error("VALIDATION_ERROR", str(exc))

    dto = build_employee_dto(emp)
    return ok({"employee": dto.model_dump()})


@router.get("/me", response_model=ApiResponse)
def get_me(
    current_employee: EmployeeORM = Depends(get_current_employee),
):
    dto = build_employee_dto(current_employee)
    return ok({"employee": dto.model_dump()})


@router.get("", response_model=ApiResponse)
def list_employees(
    db: Session = Depends(get_db),
):
    """List all active employees (no auth here; protect if needed)."""
    emp_repo = EmployeeRepository(db)
    rows = emp_repo.list_employees()
    data = [build_employee_dto(r).model_dump() for r in rows]
    return ok({"count": len(data), "employees": data})


@router.post("/{employee_id}/reset-password", response_model=ApiResponse)
def reset_password(
    employee_id: str,
    body: PasswordResetBody,
    db: Session = Depends(get_db),
    current_employee: EmployeeORM = Depends(get_current_employee),
):
    """Reset password for currently authenticated employee."""
    if current_employee.id != employee_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only reset your own password",
        )

    emp_repo = EmployeeRepository(db)
    emp_repo.reset_password(current_employee, body.new_password)
    return ok({"message": "Password updated successfully"})


# -------- Leave endpoints (all require Basic auth, must match employee_id) --------

@router.post("/{employee_id}/initialize", response_model=ApiResponse)
def initialize_employee_rest(
    employee_id: str,
    body,
    db: Session = Depends(get_db),  # type: ignore
    current_employee: EmployeeORM = Depends(get_current_employee),
):
    from .schemas import InitializeEmployeeBody  # imported here to avoid circular

    if current_employee.id != employee_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage your own leaves",
        )

    if not isinstance(body, InitializeEmployeeBody):
        body = InitializeEmployeeBody(**body.dict())

    repo = LeaveRepository(db)
    balance = repo.initialize_employee_balance(
        employee_id=employee_id,
        casual=body.casual,
        privilege=body.privilege,
        medical=body.medical,
        other=body.other,
    )
    dto = build_balance_dto(balance)
    return ok({"employee_id": dto.employee_id, "balances": dto.balances})


@router.get("/{employee_id}/leave-balance", response_model=ApiResponse)
def get_leave_balance_rest(
    employee_id: str,
    db: Session = Depends(get_db),
    current_employee: EmployeeORM = Depends(get_current_employee),
):
    if current_employee.id != employee_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own leave balance",
        )

    repo = LeaveRepository(db)
    balance = repo.get_or_create_balance(employee_id)
    dto = build_balance_dto(balance)
    return ok({"employee_id": dto.employee_id, "balances": dto.balances})


@router.post("/{employee_id}/apply-leave", response_model=ApiResponse)
def apply_leave_rest(
    employee_id: str,
    body: ApplyLeaveBody,
    db: Session = Depends(get_db),
    current_employee: EmployeeORM = Depends(get_current_employee),
):
    if current_employee.id != employee_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only apply leave for yourself",
        )

    repo = LeaveRepository(db)

    try:
        req = repo.apply_leave(
            employee_id=employee_id,
            leave_type=body.leave_type,
            days=body.days,
            start_date=body.start_date,
            reason=body.reason or "",
        )
    except ValueError as exc:
        return error("BUSINESS_RULE_VIOLATION", str(exc))

    balance = repo.get_or_create_balance(employee_id)
    return ok(
        {
            "request": build_request_dto(req).model_dump(),
            "balances": build_balance_dto(balance).balances,
        }
    )


@router.post("/{employee_id}/credit-leave", response_model=ApiResponse)
def credit_leave_rest(
    employee_id: str,
    body: CreditLeaveBody,
    db: Session = Depends(get_db),
    current_employee: EmployeeORM = Depends(get_current_employee),
):
    if current_employee.id != employee_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only credit leave to your own account",
        )

    repo = LeaveRepository(db)

    balance = repo.credit_leave(
        employee_id=employee_id,
        leave_type=body.leave_type,
        days=body.days,
    )

    adjustment_record = {
        "employee_id": employee_id,
        "leave_type": body.leave_type.value,
        "days": body.days,
        "note": body.note or "manual credit",
        "type": "CREDIT",
    }

    return ok(
        {
            "adjustment": adjustment_record,
            "balances": build_balance_dto(balance).balances,
        }
    )


@router.get("/{employee_id}/leave-requests", response_model=ApiResponse)
def list_employee_leave_requests_rest(
    employee_id: str,
    db: Session = Depends(get_db),
    current_employee: EmployeeORM = Depends(get_current_employee),
):
    if current_employee.id != employee_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own leave requests",
        )

    repo = LeaveRepository(db)
    rows = repo.list_employee_requests(employee_id)

    dtos = [build_request_dto(r).model_dump() for r in rows]

    return ok(
        {
            "employee_id": employee_id,
            "count": len(dtos),
            "requests": dtos,
        }
    )
