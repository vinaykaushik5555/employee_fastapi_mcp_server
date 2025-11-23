import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:////tmp/leave_management.db",   # writable path on cloud
)
