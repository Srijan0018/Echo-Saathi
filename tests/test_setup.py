from pathlib import Path


def test_windows_startup_script_configures_database_and_api() -> None:
    script = (Path(__file__).parents[1] / "scripts" / "start.ps1").read_text()

    assert "docker compose up -d postgres" in script
    assert "$env:DATABASE_URL" in script
    assert "uvicorn app.main:app" in script