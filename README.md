# Echo Saathi OS

Deterministic circular-economy operations platform for citizens, collectors, aggregators, recyclers, and municipalities.

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
uvicorn app.main:app --reload
```
Or use the complete Windows setup command, which starts PostGIS, configures `DATABASE_URL`, and launches the API:

```powershell
.\scripts\start.ps1
```

Open `http://127.0.0.1:8000/dashboard/` for the municipal operations dashboard, `http://127.0.0.1:8000/citizen/citizen.html` to book a pickup, `http://127.0.0.1:8000/collector/collector.html` for the collector console, `http://127.0.0.1:8000/depot/depot.html` for depot and recycler processing, `http://127.0.0.1:8000/regulatory/regulatory.html` for the cited regulatory assistant, or `http://127.0.0.1:8000/docs` for the API explorer.

## Test

```powershell
pytest
```

## Persistence schema

The demo API currently uses deterministic in-memory state. The PostgreSQL 16/PostGIS target schema is available at `db/schema.sql` for the persistence integration phase. The local Compose database is published on port `5433` to avoid conflicts with an existing Windows PostgreSQL service on `5432`.

To start the local database service:

```powershell
docker compose up -d postgres
```

The schema and material catalog seed are applied automatically on the first volume initialization. Copy `.env.example` to `.env` and replace the demo password before using this service outside a local demo.
