import io
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert

from app.database import get_db
from app.models import Department, Job, HiredEmployee
from app.schemas import (
    DepartmentCreate, JobCreate, HiredEmployeeCreate, UploadResponse
)

router = APIRouter(prefix="/upload", tags=["Upload"])

# ── Helper ───────────────────────────────────────────────────────────────────

def _upsert_rows(db: Session, model, rows: list[dict]) -> int:
    """Insert rows; on conflict (same PK) update the record."""
    if not rows:
        return 0
    stmt = insert(model).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={k: stmt.excluded[k] for k in rows[0] if k != "id"},
    )
    db.execute(stmt)
    db.commit()
    return len(rows)


# ── CSV endpoints ─────────────────────────────────────────────────────────────

@router.post("/csv/departments", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_departments_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload departments.csv and insert all rows into the DB."""
    content = await file.read()
    try:
        df = pd.read_csv(
            io.BytesIO(content),
            header=None,
            names=["id", "department"],
            skipinitialspace=True,
        )
        df = df.dropna(subset=["id"]).astype({"id": int})
        df["department"] = df["department"].str.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV format: {e}")

    rows = df.to_dict(orient="records")
    inserted = _upsert_rows(db, Department, rows)
    return UploadResponse(message="Departments uploaded successfully.", rows_inserted=inserted)


@router.post("/csv/jobs", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_jobs_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload jobs.csv and insert all rows into the DB."""
    content = await file.read()
    try:
        df = pd.read_csv(
            io.BytesIO(content),
            header=None,
            names=["id", "job"],
            skipinitialspace=True,
        )
        df = df.dropna(subset=["id"]).astype({"id": int})
        df["job"] = df["job"].str.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV format: {e}")

    rows = df.to_dict(orient="records")
    inserted = _upsert_rows(db, Job, rows)
    return UploadResponse(message="Jobs uploaded successfully.", rows_inserted=inserted)


@router.post("/csv/employees", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_employees_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload hired_employees.csv and insert all rows into the DB."""
    content = await file.read()
    try:
        df = pd.read_csv(
            io.BytesIO(content),
            header=None,
            names=["id", "name", "datetime", "department_id", "job_id"],
            skipinitialspace=True,
        )
        df = df.dropna(subset=["id"]).astype({"id": int})
        df["department_id"] = pd.to_numeric(df["department_id"], errors="coerce").astype("Int64")
        df["job_id"] = pd.to_numeric(df["job_id"], errors="coerce").astype("Int64")
        # Convert pandas NA to Python None for SQLite compatibility
        df = df.where(pd.notnull(df), None)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV format: {e}")

    rows = df.to_dict(orient="records")
    inserted = _upsert_rows(db, HiredEmployee, rows)
    return UploadResponse(message="Employees uploaded successfully.", rows_inserted=inserted)


# ── Batch JSON endpoints ──────────────────────────────────────────────────────

@router.post("/batch/departments", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
def batch_insert_departments(payload: DepartmentCreate, db: Session = Depends(get_db)):
    """Insert 1–1000 department rows via JSON body."""
    rows = [r.model_dump() for r in payload.rows]
    inserted = _upsert_rows(db, Department, rows)
    return UploadResponse(message="Batch inserted successfully.", rows_inserted=inserted)


@router.post("/batch/jobs", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
def batch_insert_jobs(payload: JobCreate, db: Session = Depends(get_db)):
    """Insert 1–1000 job rows via JSON body."""
    rows = [r.model_dump() for r in payload.rows]
    inserted = _upsert_rows(db, Job, rows)
    return UploadResponse(message="Batch inserted successfully.", rows_inserted=inserted)


@router.post("/batch/employees", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
def batch_insert_employees(payload: HiredEmployeeCreate, db: Session = Depends(get_db)):
    """Insert 1–1000 employee rows via JSON body."""
    rows = [r.model_dump() for r in payload.rows]
    inserted = _upsert_rows(db, HiredEmployee, rows)
    return UploadResponse(message="Batch inserted successfully.", rows_inserted=inserted)
