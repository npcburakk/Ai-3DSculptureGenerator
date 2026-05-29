# 🧊 Text-to-3D Generator — Backend

An AI-powered REST API that converts natural language text prompts into 3D model files (OBJ / PLY / GLB).

Supports multiple generation backends:
- **Shap-E** (OpenAI) — highest quality, requires GPU
- **Point-E** (OpenAI) — faster, requires GPU
- **Mock** — instant cube mesh, no ML needed (great for dev/testing)

---

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py               # FastAPI app & lifespan
│   ├── api/
│   │   └── routes.py         # All API endpoints
│   ├── core/
│   │   ├── config.py         # Settings (pydantic-settings + .env)
│   │   └── constants.py      # Job statuses, backends, pipeline stages
│   ├── schemas/
│   │   └── job_schema.py     # Pydantic request/response models
│   ├── services/
│   │   ├── job_service.py    # Job CRUD + background task runner
│   │   ├── pipeline_service.py  # Shap-E / Point-E / Mock pipelines
│   │   ├── file_service.py   # Output file management
│   │   └── status_service.py # Lightweight status polling
│   ├── models/
│   │   └── job_model.py      # Internal job dataclass
│   ├── utils/
│   │   ├── helpers.py        # Slugify, format_duration, etc.
│   │   └── validators.py     # Input validation helpers
│   └── storage/
│       └── memory_store.py   # Thread-safe in-memory job store
├── outputs/                  # Generated 3D files land here
├── requirements.txt
├── .env                      # Environment configuration
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone & create virtual environment

```bash
git clone <your-repo>
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure `.env`

```bash
cp .env .env.local   # edit as needed
```

Key settings:

| Variable | Default | Description |
|---|---|---|
| `DEFAULT_BACKEND` | `mock` | `mock` \| `shap_e` \| `point_e` |
| `OPENAI_API_KEY` | — | Required for `openai` backend |
| `OUTPUT_DIR` | `outputs` | Where 3D files are saved |
| `SHAP_E_NUM_STEPS` | `64` | Diffusion steps (quality ↔ speed) |

### 4. Run the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit **http://localhost:8000/docs** for the interactive Swagger UI.

---

## 🔌 API Reference

### Submit a Job

```http
POST /api/v1/jobs
Content-Type: application/json

{
  "prompt": "a wooden chair with four legs",
  "backend": "mock",
  "output_format": "obj",
  "num_steps": 64,
  "guidance_scale": 15.0
}
```

**Response `202 Accepted`:**
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "pending",
  "progress": 0,
  ...
}
```

### Poll Job Status

```http
GET /api/v1/jobs/{job_id}/status
```

```json
{
  "id": "...",
  "status": "running",
  "progress": 60,
  "current_stage": "generating_latents"
}
```

### Download Output

```http
GET /api/v1/jobs/{job_id}/download
```

Returns the 3D file as an `application/octet-stream` download.

### Other Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/jobs` | List all jobs (paginated) |
| `GET` | `/api/v1/jobs/{id}` | Get job details |
| `DELETE` | `/api/v1/jobs/{id}` | Cancel / delete job |
| `GET` | `/api/v1/models` | List available backends |
| `GET` | `/api/v1/stats` | Aggregate statistics |
| `GET` | `/health` | Health check |

---

## 🧠 Enabling Real AI Backends

### Shap-E (recommended)

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install git+https://github.com/openai/shap-e.git
```

Set in `.env`:
```
DEFAULT_BACKEND=shap_e
```

### Point-E

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install git+https://github.com/openai/point-e.git
```

Set in `.env`:
```
DEFAULT_BACKEND=point_e
```

---

## 🧪 Running Tests

```bash
pytest -v
```

---

## ⚙️ Pipeline Stages & Progress

| Stage | Progress |
|---|---|
| `initializing` | 5% |
| `encoding_text` | 20% |
| `generating_latents` | 60% |
| `decoding_mesh` | 85% |
| `exporting_file` | 95% |
| `done` | 100% |

---

## 📝 Notes

- The **mock** backend requires no GPU and is ideal for local development.
- The in-memory store resets on server restart. For persistence, swap `memory_store.py` with a Redis or SQLite adapter.
- Generated files are served statically at `/outputs/<job_id>.<format>`.
- Concurrent job limit is configurable via `MAX_CONCURRENT_JOBS` in `.env`.
