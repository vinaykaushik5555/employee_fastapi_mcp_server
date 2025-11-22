from __future__ import annotations

from datetime import date
from typing import Generator

from fastmcp import FastMCP

from .converters import build_balance_dto, build_request_dto
from .db import SessionLocal
from .domain import DEFAULT_CL, DEFAULT_ML, DEFAULT_OTHER, DEFAULT_PL, LeaveTypeEnum
from .repository import LeaveRepository
from .responses import error, ok


mcp = FastMCP("leave-management")


def db_session_ctx() -> Generator:
    """Simple context manager to use DB inside MCP tools."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@mcp.tool
def initialize_employee_balance(
    employee_id: str,
    casual: float = DEFAULT_CL,
    privilege: float = DEFAULT_PL,
    medical: float = DEFAULT_ML,
    other: float = DEFAULT_OTHER,
) -> dict:
    """MCP tool: Create or reset an employee's leave balances."""
    if not employee_id:
        return error("VALIDATION_ERROR", "employee_id is required").model_dump()

    for db in db_session_ctx():
        repo = LeaveRepository(db)
        balance = repo.initialize_employee_balance(
            employee_id=employee_id,
            casual=casual,
            privilege=privilege,
            medical=medical,
            other=other,
        )
        dto = build_balance_dto(balance)
        return ok(
            {"employee_id": dto.employee_id, "balances": dto.balances}
        ).model_dump()


@mcp.tool
def get_leave_balance(employee_id: str) -> dict:
    """MCP tool: Get leave balances for an employee."""
    if not employee_id:
        return error("VALIDATION_ERROR", "employee_id is required").model_dump()

    for db in db_session_ctx():
        repo = LeaveRepository(db)
        balance = repo.get_or_create_balance(employee_id)
        dto = build_balance_dto(balance)
        return ok(
            {"employee_id": dto.employee_id, "balances": dto.balances}
        ).model_dump()


@mcp.tool
def apply_leave(
    employee_id: str,
    leave_type: LeaveTypeEnum,
    days: float,
    start_date: date,
    reason: str = "",
) -> dict:
    """MCP tool: Apply leave for an employee (auto-approves if enough balance)."""
    if not employee_id:
        return error("VALIDATION_ERROR", "employee_id is required").model_dump()
    if days <= 0:
        return error("VALIDATION_ERROR", "days must be greater than 0").model_dump()

    for db in db_session_ctx():
        repo = LeaveRepository(db)

        try:
            req = repo.apply_leave(
                employee_id=employee_id,
                leave_type=leave_type,
                days=days,
                start_date=start_date,
                reason=reason or "",
            )
        except ValueError as exc:
            return error("BUSINESS_RULE_VIOLATION", str(exc)).model_dump()

        balance = repo.get_or_create_balance(employee_id)
        return ok(
            {
                "request": build_request_dto(req).model_dump(),
                "balances": build_balance_dto(balance).balances,
            }
        ).model_dump()


@mcp.tool
def credit_leave(
    employee_id: str,
    leave_type: LeaveTypeEnum,
    days: float,
    note: str = "",
) -> dict:
    """MCP tool: Credit leave days to an employee."""
    if not employee_id:
        return error("VALIDATION_ERROR", "employee_id is required").model_dump()
    if days <= 0:
        return error("VALIDATION_ERROR", "days must be greater than 0").model_dump()

    for db in db_session_ctx():
        repo = LeaveRepository(db)

        balance = repo.credit_leave(
            employee_id=employee_id,
            leave_type=leave_type,
            days=days,
        )

        adjustment_record = {
            "employee_id": employee_id,
            "leave_type": leave_type.value,
            "days": days,
            "note": note or "manual credit",
            "type": "CREDIT",
        }

        return ok(
            {
                "adjustment": adjustment_record,
                "balances": build_balance_dto(balance).balances,
            }
        ).model_dump()


@mcp.tool
def list_employee_leave_requests(employee_id: str) -> dict:
    """MCP tool: List all leave requests for an employee."""
    if not employee_id:
        return error("VALIDATION_ERROR", "employee_id is required").model_dump()

    for db in db_session_ctx():
        repo = LeaveRepository(db)
        rows = repo.list_employee_requests(employee_id)
        dtos = [build_request_dto(r).model_dump() for r in rows]

        return ok(
            {
                "employee_id": employee_id,
                "count": len(dtos),
                "requests": dtos,
            }
        ).model_dump()
