from pydantic import BaseModel, field_validator
from typing import Optional, List


# ── Department ──────────────────────────────────────────────────────────────

class DepartmentBase(BaseModel):
    id: int
    department: str


class DepartmentCreate(BaseModel):
    rows: List[DepartmentBase]

    @field_validator("rows")
    @classmethod
    def validate_batch_size(cls, v):
        if not (1 <= len(v) <= 1000):
            raise ValueError("Batch size must be between 1 and 1000 rows.")
        return v


# ── Job ─────────────────────────────────────────────────────────────────────

class JobBase(BaseModel):
    id: int
    job: str


class JobCreate(BaseModel):
    rows: List[JobBase]

    @field_validator("rows")
    @classmethod
    def validate_batch_size(cls, v):
        if not (1 <= len(v) <= 1000):
            raise ValueError("Batch size must be between 1 and 1000 rows.")
        return v


# ── HiredEmployee ────────────────────────────────────────────────────────────

class HiredEmployeeBase(BaseModel):
    id: int
    name: Optional[str] = None
    datetime: Optional[str] = None
    department_id: Optional[int] = None
    job_id: Optional[int] = None


class HiredEmployeeCreate(BaseModel):
    rows: List[HiredEmployeeBase]

    @field_validator("rows")
    @classmethod
    def validate_batch_size(cls, v):
        if not (1 <= len(v) <= 1000):
            raise ValueError("Batch size must be between 1 and 1000 rows.")
        return v


# ── Response schemas ─────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    message: str
    rows_inserted: int


class QuarterlyHiresRow(BaseModel):
    department: str
    job: str
    Q1: int
    Q2: int
    Q3: int
    Q4: int


class AboveMeanHiresRow(BaseModel):
    id: int
    department: str
    hired: int
