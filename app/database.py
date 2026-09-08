import os
from uuid import UUID


DEFAULT_DATABASE_URL = "postgresql://kabadiwala:kabadiwala_demo_password@localhost:5432/kabadiwala_connect"


def persist_user(user_id: UUID, phone: str, full_name: str, role: str, upi_id: str | None) -> bool:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return False
    try:
        from psycopg import OperationalError, connect

        with connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (id, phone, full_name, role, upi_id)
                    VALUES (%s, %s, %s, %s::user_role, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (user_id, phone, full_name, role, upi_id),
                )
        return True
    except (ModuleNotFoundError, OperationalError):
        return False


def database_status() -> dict[str, str]:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return {"status": "not_configured", "mode": "in_memory"}
    try:
        from psycopg import OperationalError, connect

        with connect(database_url, connect_timeout=2) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_database(), PostGIS_Version()")
                database_name, postgis_version = cursor.fetchone()
        return {
            "status": "ok",
            "mode": "postgresql",
            "database": database_name,
            "postgis_version": postgis_version,
        }
    except ModuleNotFoundError:
        return {"status": "driver_unavailable", "mode": "postgresql"}
    except OperationalError:
        return {"status": "unavailable", "mode": "postgresql"}
