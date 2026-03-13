# Globant Data Engineering Challenge 🚀

REST API for a database migration challenge involving three tables: **departments**, **jobs**, and **hired_employees**.

Built with **FastAPI · SQLite · SQLAlchemy · Pytest · Docker**.

---

## 📁 Project Structure

```
globant_challenge/
├── app/
│   ├── main.py           # FastAPI app entry point
│   ├── database.py       # SQLite connection & session factory
│   ├── models.py         # SQLAlchemy ORM models
│   ├── schemas.py        # Pydantic request/response schemas
│   └── routers/
│       ├── upload.py     # Section 1 – CSV upload & batch insert
│       └── metrics.py    # Section 2 – SQL analytics endpoints
├── tests/
│   └── test_api.py       # Automated test suite (Pytest)
├── data/                 # Sample CSV files
│   ├── departments.csv
│   ├── jobs.csv
│   └── hired_employees.csv
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## ⚙️ Local Setup (without Docker)

### 1. Clone & create virtual environment

```bash
git clone https://github.com/<your-user>/globant-de-challenge.git
cd globant-de-challenge
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the API

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

---

## 🐳 Docker Setup

### Build & run with Docker Compose

```bash
docker compose up --build
```

### Or with plain Docker

```bash
docker build -t globant-de-api .
docker run -p 8000:8000 globant-de-api
```

---

## 📡 API Endpoints

### Health Check

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Returns API status |

---

### Section 1 – Upload (CSV & Batch)

#### Upload CSV files

| Method | Path | Description |
|--------|------|-------------|
| POST | `/upload/csv/departments` | Upload `departments.csv` |
| POST | `/upload/csv/jobs` | Upload `jobs.csv` |
| POST | `/upload/csv/employees` | Upload `hired_employees.csv` |

**Example (curl):**
```bash
curl -X POST http://localhost:8000/upload/csv/departments \
  -F "file=@data/departments.csv"
```

**Response:**
```json
{
  "message": "Departments uploaded successfully.",
  "rows_inserted": 5
}
```

---

#### Batch insert (JSON, 1–1000 rows)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/upload/batch/departments` | Batch insert departments |
| POST | `/upload/batch/jobs` | Batch insert jobs |
| POST | `/upload/batch/employees` | Batch insert employees |

**Example body:**
```json
{
  "rows": [
    { "id": 1, "department": "Supply Chain" },
    { "id": 2, "department": "Staff" }
  ]
}
```

> ⚠️ Sending more than 1000 rows returns HTTP 422. Duplicate IDs are handled via upsert.

---

### Section 2 – Metrics (SQL)

#### Hires by quarter (2021)

```
GET /metrics/hires-by-quarter
```

Returns employees hired per job & department in 2021, split by quarter. Ordered alphabetically by department and job.

**Response example:**
```json
[
  { "department": "Staff", "job": "Manager", "Q1": 2, "Q2": 1, "Q3": 0, "Q4": 2 },
  { "department": "Staff", "job": "Recruiter", "Q1": 3, "Q2": 0, "Q3": 7, "Q4": 11 },
  { "department": "Supply Chain", "job": "Manager", "Q1": 0, "Q2": 1, "Q3": 3, "Q4": 0 }
]
```

---

#### Departments above mean hires (2021)

```
GET /metrics/above-mean-hires
```

Returns departments that hired more employees than the mean across all departments in 2021. Ordered by number hired (descending).

**Response example:**
```json
[
  { "id": 7, "department": "Staff", "hired": 45 },
  { "id": 9, "department": "Supply Chain", "hired": 12 }
]
```

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

The test suite covers:
- ✅ Health check endpoint
- ✅ CSV upload for all three tables
- ✅ Invalid CSV returns 400
- ✅ Batch insert (valid, > 1000 rows, empty, upsert)
- ✅ Metrics endpoint structure and correctness
- ✅ Quarterly data excludes non-2021 records
- ✅ Above-mean list is sorted descending
- ✅ Empty DB returns empty list

Run with coverage:
```bash
pytest tests/ -v --tb=short
```

---

## 📦 CSV File Format

### departments.csv
```
id,department
1,Supply Chain
2,Maintenance
```

### jobs.csv
```
id,job
1,Recruiter
2,Manager
```

### hired_employees.csv
```
id,name,datetime,department_id,job_id
4535,Marcelo Gonzalez,2021-07-27T16:02:08Z,1,2
```

> All files are **comma-separated, no header row**.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| API Framework | FastAPI |
| Database | SQLite via SQLAlchemy |
| Data Processing | Pandas |
| Validation | Pydantic v2 |
| Testing | Pytest + HTTPX |
| Containerization | Docker + Docker Compose |

---

## ☁️ Cloud Deployment (Bonus)

This architecture can be deployed to any cloud provider with minimal changes:

| Component | AWS | GCP | Azure |
|-----------|-----|-----|-------|
| Container | ECS / App Runner | Cloud Run | Container Apps |
| Database | RDS (PostgreSQL) | Cloud SQL | Azure SQL |
| Storage (CSVs) | S3 | Cloud Storage | Blob Storage |

To switch from SQLite to PostgreSQL, change `DATABASE_URL` in `database.py`:
```python
DATABASE_URL = "postgresql://user:password@host:5432/dbname"
```

---

## 👤 Author

Built for Globant's Data Engineering Coding Challenge.
