# Kabadiwala Connect OS

Deterministic circular-economy operations platform for citizens, collectors, aggregators, recyclers, and municipalities.

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the API explorer.

## Test

```powershell
pytest
```
