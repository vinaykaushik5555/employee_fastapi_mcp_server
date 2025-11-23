"""
MCP Server Implementation for Leave Management System
-----------------------------------------------------

Supports:
- Token-based session authentication (single shared MCP server)
- Admin and Employee roles
- Secure permission enforcement inside tools
- Admin CRUD operations for employees
- Employee leave operations
- Logout support (token invalidation)

NOTE: In production move TOKENS to a persistent DB or redis.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Generator, Dict

from fastmcp import FastMCP

from .converters import (
    build_balance_dto,
    build_employee_dto,
    build_request_dto,
)
from .db import SessionLocal
from .domain import (
    DEFAULT_CL, DEFAULT_PL, DEFAULT_ML, DEFAULT_OTHER,
    LeaveTypeEnum,
)
from .models import EmployeeORM
from .repository import EmployeeRepository, LeaveRepository
from .responses import error, ok
from .schemas import EmployeeCreate


# ============================================================
# MCP instance
# ============================================================
mcp = FastMCP("leave-management")


# ============================================================
# In-memory token storage (temporary)
# token -> employee_id
# ============================================================
TOKENS: Dict[str, str] = {}


# ============================================================
# DB context helper
# ============================================================
def db_session_ctx() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# Authentication helpers
# ============================================================
def authenticate_token(token: str, db) -> EmployeeORM:
    """Validate token and return employee details."""
    employee_id = TOKENS.get(token)
    if not employee_id:
        raise ValueError("Invalid or expired token")

    emp = db.get(EmployeeORM, employee_id)
    if not emp:
        raise ValueError("Employee not found")

    return emp


# ============================================================
# LOGIN TOOL
# ============================================================
@mcp.tool
def login(username: str, password: str) -> dict:
    """
    Authenticate user using plain credentials
    and return a session token.
    """
    for db in db_session_ctx():
        emp = (
            db.query(EmployeeORM)
            .filter(EmployeeORM.username == username, EmployeeORM.password == password)
            .first()
        )
        if not emp:
            return error("AUTH_FAILED", "Invalid username or password").model_dump()

        token = uuid.uuid4().hex
        TOKENS[token] = emp.id

        return ok({
            "token": token,
            "employee_id": emp.id,
            "is_admin": emp.is_admin,
            "name": emp.name,
        }).model_dump()


# ============================================================
# LOGOUT TOOL
# ============================================================
@mcp.tool
def logout(token: str) -> dict:
    """
    Logout user by invalidating token.
    """
    if token in TOKENS:
        del TOKENS[token]
        return ok({"message": "Logout successful"}).model_dump()

    return error("AUTH_FAILED", "Invalid token").model_dump()


# ============================================================
# PROFILE TOOL
# ============================================================
@mcp.tool
def who_am_i(token: str) -> dict:
    """Return identity of currently authenticated user."""
    for db in db_session_ctx():
        try:
            emp = authenticate_token(token, db)
        except ValueError as exc:
            return error("AUTH_FAILED", str(exc)).model_dump()

        return ok({"employee": build_employee_dto(emp).model_dump()}).model_dump()


# ============================================================
# ADMIN TOOLS
# ============================================================
@mcp.tool
def admin_list_employees(token: str) -> dict:
    """Admin only: list all employees."""
    for db in db_session_ctx():
        try:
            emp = authenticate_token(token, db)
        except ValueError as exc:
            return error("AUTH_FAILED", str(exc)).model_dump()

        if not emp.is_admin:
            return error("FORBIDDEN", "Admin only feature").model_dump()

        repo = EmployeeRepository(db)
        rows = repo.list_employees()
        return ok({
            "employees": [build_employee_dto(r).model_dump() for r in rows]
        }).model_dump()


@mcp.tool
def admin_create_employee(
    token: str,
    id: str,
    username: str,
    password: str,
    name: str,
    email: str,
    department: str = "",
) -> dict:
    """Admin only: create new employee + assign default leave balance."""
    for db in db_session_ctx():
        try:
            requester = authenticate_token(token, db)
        except ValueError as exc:
            return error("AUTH_FAILED", str(exc)).model_dump()

        if not requester.is_admin:
            return error("FORBIDDEN", "Admin only feature").model_dump()

        repo = EmployeeRepository(db)
        try:
            new_emp = repo.create_employee(
                EmployeeCreate(
                    id=id,
                    username=username,
                    password=password,
                    name=name,
                    email=email,
                    department=department,
                ),
                is_admin=False,
            )
        except ValueError as exc:
            return error("VALIDATION_ERROR", str(exc)).model_dump()

        return ok({"employee": build_employee_dto(new_emp).model_dump()}).model_dump()


# ============================================================
# EMPLOYEE LEAVE TOOLS
# ============================================================
@mcp.tool
def get_leave_balance(token: str) -> dict:
    """Return leave balance for authenticated user."""
    for db in db_session_ctx():
        try:
            emp = authenticate_token(token, db)
        except ValueError as exc:
            return error("AUTH_FAILED", str(exc)).model_dump()

        repo = LeaveRepository(db)
        balance = repo.get_or_create_balance(emp.id)

        return ok({"balances": build_balance_dto(balance).balances}).model_dump()


@mcp.tool
def list_my_leave_requests(token: str) -> dict:
    """Return list of leave requests for authenticated user."""
    for db in db_session_ctx():
        try:
            emp = authenticate_token(token, db)
        except ValueError as exc:
            return error("AUTH_FAILED", str(exc)).model_dump()

        repo = LeaveRepository(db)
        rows = repo.list_employee_requests(emp.id)

        return ok({"requests": [build_request_dto(r).model_dump() for r in rows]}).model_dump()


@mcp.tool
def apply_leave(
    token: str,
    leave_type: LeaveTypeEnum,
    days: float,
    start_date: date,
    reason: str = "",
) -> dict:
    """Authenticated employees can apply leave for themselves only."""
    if days <= 0:
        return error("VALIDATION_ERROR", "days must be greater than 0").model_dump()

    for db in db_session_ctx():
        try:
            emp = authenticate_token(token, db)
        except ValueError as exc:
            return error("AUTH_FAILED", str(exc)).model_dump()

        repo = LeaveRepository(db)

        try:
            req = repo.apply_leave(emp.id, leave_type, days, start_date, reason)
        except ValueError as exc:
            return error("BUSINESS_RULE_VIOLATION", str(exc)).model_dump()

        balance = repo.get_or_create_balance(emp.id)
        return ok({
            "request": build_request_dto(req).model_dump(),
            "balances": build_balance_dto(balance).balances,
        }).model_dump()
