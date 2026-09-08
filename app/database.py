import os


DEFAULT_DATABASE_URL = "postgresql://kabadiwala:kabadiwala_demo_password@localhost:5432/kabadiwala_connect"


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
