# app/security.py
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from .deps import get_db
from .models import EmployeeORM

security = HTTPBasic()


def verify_password(plain_password: str, stored_password: str) -> bool:
    # plain-text comparison
    return plain_password == stored_password


def get_current_employee(
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> EmployeeORM:
    username = credentials.username
    password = credentials.password

    employee = (
        db.query(EmployeeORM)
        .filter(EmployeeORM.username == username, EmployeeORM.is_active == True)  # noqa: E712
        .first()
    )

    if employee is None or not verify_password(password, employee.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return employee
