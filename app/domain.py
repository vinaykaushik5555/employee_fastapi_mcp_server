from __future__ import annotations

from enum import Enum


class LeaveTypeEnum(str, Enum):
    CASUAL = "CL"
    PRIVILEGE = "PL"
    MEDICAL = "ML"
    OTHER = "OTHER"


class LeaveStatusEnum(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"


DEFAULT_CL = 10.0
DEFAULT_PL = 15.0
DEFAULT_ML = 90.0
DEFAULT_OTHER = 0.0
