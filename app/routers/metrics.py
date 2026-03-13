from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import QuarterlyHiresRow, AboveMeanHiresRow

router = APIRouter(prefix="/metrics", tags=["Metrics"])


# ── Endpoint 1: Quarterly hires per department & job in 2021 ─────────────────

QUARTERLY_SQL = """
SELECT
    d.department,
    j.job,
    SUM(CASE WHEN CAST(strftime('%m', e.datetime) AS INTEGER) BETWEEN 1  AND 3  THEN 1 ELSE 0 END) AS Q1,
    SUM(CASE WHEN CAST(strftime('%m', e.datetime) AS INTEGER) BETWEEN 4  AND 6  THEN 1 ELSE 0 END) AS Q2,
    SUM(CASE WHEN CAST(strftime('%m', e.datetime) AS INTEGER) BETWEEN 7  AND 9  THEN 1 ELSE 0 END) AS Q3,
    SUM(CASE WHEN CAST(strftime('%m', e.datetime) AS INTEGER) BETWEEN 10 AND 12 THEN 1 ELSE 0 END) AS Q4
FROM hired_employees e
JOIN departments d ON e.department_id = d.id
JOIN jobs         j ON e.job_id        = j.id
WHERE strftime('%Y', e.datetime) = '2021'
GROUP BY d.department, j.job
ORDER BY d.department ASC, j.job ASC;
"""


@router.get(
    "/hires-by-quarter",
    response_model=list[QuarterlyHiresRow],
    summary="Employees hired per job & department by quarter (2021)",
)
def hires_by_quarter(db: Session = Depends(get_db)):
    """
    Returns the number of employees hired for each job and department
    in 2021, split by quarter. Ordered alphabetically by department and job.
    """
    rows = db.execute(text(QUARTERLY_SQL)).mappings().all()
    return [QuarterlyHiresRow(**row) for row in rows]


# ── Endpoint 2: Departments above mean hires in 2021 ────────────────────────

ABOVE_MEAN_SQL = """
WITH dept_hires AS (
    SELECT
        d.id,
        d.department,
        COUNT(e.id) AS hired
    FROM departments d
    LEFT JOIN hired_employees e
           ON e.department_id = d.id
          AND strftime('%Y', e.datetime) = '2021'
    GROUP BY d.id, d.department
),
mean_hires AS (
    SELECT AVG(hired) AS mean_val FROM dept_hires
)
SELECT dh.id, dh.department, dh.hired
FROM dept_hires dh, mean_hires mh
WHERE dh.hired > mh.mean_val
ORDER BY dh.hired DESC;
"""


@router.get(
    "/above-mean-hires",
    response_model=list[AboveMeanHiresRow],
    summary="Departments that hired more than the mean in 2021",
)
def above_mean_hires(db: Session = Depends(get_db)):
    """
    Returns the id, name and number of employees hired of each department
    that hired more than the average across all departments in 2021.
    Ordered by hired count descending.
    """
    rows = db.execute(text(ABOVE_MEAN_SQL)).mappings().all()
    return [AboveMeanHiresRow(**row) for row in rows]
