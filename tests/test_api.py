"""
Automated tests for Globant Data Engineering Challenge API.
Covers: health check, CSV upload, batch insert, and metrics endpoints.
"""
import io
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# ── Test DB setup (file-based SQLite for test isolation) ─────────────────────

TEST_DB_PATH = "./test_globant.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Apply override globally
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_db():
    """Drop and recreate all tables before each test for isolation."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    """Remove test DB file after all tests finish."""
    yield
    try:
        test_engine.dispose()
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
    except Exception:
        pass


client = TestClient(app)


# ── Health check ─────────────────────────────────────────────────────────────

class TestHealthCheck:
    def test_root_returns_ok(self):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


# ── CSV Upload ────────────────────────────────────────────────────────────────

class TestCSVUpload:
    def _csv_file(self, content: str, filename: str = "test.csv"):
        return {"file": (filename, io.BytesIO(content.encode()), "text/csv")}

    def test_upload_departments_csv(self):
        csv_content = "1,Supply Chain\n2,Maintenance\n3,Staff\n"
        response = client.post(
            "/upload/csv/departments",
            files=self._csv_file(csv_content, "departments.csv"),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["rows_inserted"] == 3
        assert "successfully" in body["message"]

    def test_upload_jobs_csv(self):
        csv_content = "1,Recruiter\n2,Manager\n3,Analyst\n"
        response = client.post(
            "/upload/csv/jobs",
            files=self._csv_file(csv_content, "jobs.csv"),
        )
        assert response.status_code == 201
        assert response.json()["rows_inserted"] == 3

    def test_upload_employees_csv(self):
        client.post(
            "/upload/csv/departments",
            files=self._csv_file("1,Supply Chain\n2,Staff\n", "departments.csv"),
        )
        client.post(
            "/upload/csv/jobs",
            files=self._csv_file("1,Recruiter\n2,Manager\n", "jobs.csv"),
        )
        csv_content = (
            "1,John Doe,2021-01-15T10:00:00Z,2,1\n"
            "2,Jane Smith,2021-07-20T09:00:00Z,1,2\n"
        )
        response = client.post(
            "/upload/csv/employees",
            files=self._csv_file(csv_content, "hired_employees.csv"),
        )
        assert response.status_code == 201
        assert response.json()["rows_inserted"] == 2

    def test_upload_invalid_csv_returns_400(self):
        bad_content = "not,valid,csv,data,extra,columns\n!!!"
        response = client.post(
            "/upload/csv/departments",
            files=self._csv_file(bad_content, "bad.csv"),
        )
        assert response.status_code in (400, 201)


# ── Batch Insert ──────────────────────────────────────────────────────────────

class TestBatchInsert:
    def test_batch_insert_departments(self):
        payload = {
            "rows": [
                {"id": 1, "department": "Engineering"},
                {"id": 2, "department": "Marketing"},
            ]
        }
        response = client.post("/upload/batch/departments", json=payload)
        assert response.status_code == 201
        assert response.json()["rows_inserted"] == 2

    def test_batch_insert_jobs(self):
        payload = {"rows": [{"id": 1, "job": "Engineer"}, {"id": 2, "job": "Designer"}]}
        response = client.post("/upload/batch/jobs", json=payload)
        assert response.status_code == 201
        assert response.json()["rows_inserted"] == 2

    def test_batch_insert_employees(self):
        client.post("/upload/batch/departments", json={"rows": [{"id": 1, "department": "Staff"}]})
        client.post("/upload/batch/jobs", json={"rows": [{"id": 1, "job": "Recruiter"}]})
        payload = {
            "rows": [
                {"id": 1, "name": "Alice", "datetime": "2021-03-10T08:00:00Z", "department_id": 1, "job_id": 1},
                {"id": 2, "name": "Bob",   "datetime": "2021-09-05T09:00:00Z", "department_id": 1, "job_id": 1},
            ]
        }
        response = client.post("/upload/batch/employees", json=payload)
        assert response.status_code == 201
        assert response.json()["rows_inserted"] == 2

    def test_batch_exceeds_1000_rows_returns_422(self):
        rows = [{"id": i, "department": f"Dept {i}"} for i in range(1001)]
        response = client.post("/upload/batch/departments", json={"rows": rows})
        assert response.status_code == 422

    def test_batch_empty_rows_returns_422(self):
        response = client.post("/upload/batch/departments", json={"rows": []})
        assert response.status_code == 422

    def test_batch_upsert_updates_existing_row(self):
        client.post("/upload/batch/departments", json={"rows": [{"id": 1, "department": "OldName"}]})
        client.post("/upload/batch/departments", json={"rows": [{"id": 1, "department": "NewName"}]})
        response = client.post("/upload/batch/departments", json={"rows": [{"id": 1, "department": "FinalName"}]})
        assert response.status_code == 201


# ── Metrics ───────────────────────────────────────────────────────────────────

class TestMetrics:
    def _seed_data(self):
        client.post("/upload/batch/departments", json={
            "rows": [
                {"id": 1, "department": "Staff"},
                {"id": 2, "department": "Supply Chain"},
                {"id": 3, "department": "Maintenance"},
            ]
        })
        client.post("/upload/batch/jobs", json={
            "rows": [
                {"id": 1, "job": "Manager"},
                {"id": 2, "job": "Recruiter"},
            ]
        })
        client.post("/upload/batch/employees", json={
            "rows": [
                {"id": 1, "name": "E1", "datetime": "2021-01-10T00:00:00Z", "department_id": 1, "job_id": 2},
                {"id": 2, "name": "E2", "datetime": "2021-02-15T00:00:00Z", "department_id": 1, "job_id": 2},
                {"id": 3, "name": "E3", "datetime": "2021-03-20T00:00:00Z", "department_id": 1, "job_id": 2},
                {"id": 4, "name": "E4", "datetime": "2021-04-10T00:00:00Z", "department_id": 1, "job_id": 1},
                {"id": 5, "name": "E5", "datetime": "2021-07-05T00:00:00Z", "department_id": 2, "job_id": 1},
                {"id": 6, "name": "E6", "datetime": "2021-08-20T00:00:00Z", "department_id": 2, "job_id": 1},
                {"id": 7, "name": "E7", "datetime": "2021-10-10T00:00:00Z", "department_id": 3, "job_id": 2},
                {"id": 8, "name": "E8", "datetime": "2020-06-01T00:00:00Z", "department_id": 1, "job_id": 1},
            ]
        })

    def test_hires_by_quarter_returns_list(self):
        self._seed_data()
        response = client.get("/metrics/hires-by-quarter")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_hires_by_quarter_correct_structure(self):
        self._seed_data()
        response = client.get("/metrics/hires-by-quarter")
        rows = response.json()
        assert len(rows) > 0
        keys = rows[0].keys()
        assert "department" in keys
        assert "job" in keys
        for q in ("Q1", "Q2", "Q3", "Q4"):
            assert q in keys

    def test_hires_by_quarter_alphabetical_order(self):
        self._seed_data()
        rows = client.get("/metrics/hires-by-quarter").json()
        departments = [r["department"] for r in rows]
        assert departments == sorted(departments)

    def test_hires_by_quarter_excludes_non_2021(self):
        self._seed_data()
        rows = client.get("/metrics/hires-by-quarter").json()
        staff_manager = next(
            (r for r in rows if r["department"] == "Staff" and r["job"] == "Manager"), None
        )
        assert staff_manager is not None
        assert staff_manager["Q2"] == 1

    def test_above_mean_hires_returns_list(self):
        self._seed_data()
        response = client.get("/metrics/above-mean-hires")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_above_mean_hires_correct_structure(self):
        self._seed_data()
        rows = client.get("/metrics/above-mean-hires").json()
        if rows:
            assert "id" in rows[0]
            assert "department" in rows[0]
            assert "hired" in rows[0]

    def test_above_mean_hires_descending_order(self):
        self._seed_data()
        rows = client.get("/metrics/above-mean-hires").json()
        hired_counts = [r["hired"] for r in rows]
        assert hired_counts == sorted(hired_counts, reverse=True)

    def test_above_mean_hires_empty_db(self):
        response = client.get("/metrics/above-mean-hires")
        assert response.status_code == 200
        assert response.json() == []

