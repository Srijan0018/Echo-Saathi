# Kabadiwala Connect OS

Deterministic circular-economy operations platform for citizens, collectors, aggregators, recyclers, and municipalities.

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/dashboard/` for the municipal operations dashboard, `http://127.0.0.1:8000/citizen/citizen.html` to book a pickup, `http://127.0.0.1:8000/collector/collector.html` for the collector console, or `http://127.0.0.1:8000/docs` for the API explorer.

## Test

```powershell
pytest
```
