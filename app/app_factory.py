# app/app_factory.py

from fastapi import FastAPI
from sqlalchemy.orm import Session

from .db import Base, engine, SessionLocal
from .models import EmployeeORM, LeaveBalanceORM
from .repository import EmployeeRepository
from .domain import DEFAULT_CL, DEFAULT_PL, DEFAULT_ML, DEFAULT_OTHER
from .api import router as employees_router

def create_default_admin():
    db: Session = SessionLocal()
    try:
        admin = (
            db.query(EmployeeORM)
            .filter(EmployeeORM.username == "admin")
            .first()
        )
        if admin is None:
            admin = EmployeeORM(
                id="admin",
                username="admin",
                password="admin",  # plain text
                name="Administrator",
                email="admin@company.com",
                department="management",
                is_active=True,
                is_admin=True,
            )
            db.add(admin)

            # default leave allocation
            balance = LeaveBalanceORM(
                employee_id="admin",
                cl=DEFAULT_CL,
                pl=DEFAULT_PL,
                ml=DEFAULT_ML,
                other=DEFAULT_OTHER,
            )
            db.add(balance)

            db.commit()
            db.refresh(admin)
            print("💡 Default admin user created: username=admin, password=admin")
    finally:
        db.close()


def create_app() -> FastAPI:
    Base.metadata.create_all(bind=engine)
    create_default_admin()   # <-- add this line

    app = FastAPI(title="Employee + Leave Management System")
    app.include_router(employees_router)

    return app
