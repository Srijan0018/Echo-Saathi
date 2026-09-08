import os
from uuid import UUID


DEFAULT_DATABASE_URL = "postgresql://kabadiwala:kabadiwala_demo_password@localhost:5433/kabadiwala_connect"


def persist_user(user_id: UUID, phone: str, full_name: str, role: str, upi_id: str | None) -> bool:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return False
    try:
        from psycopg import Error, connect

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
    except (ModuleNotFoundError, Error):
        return False


def persist_pickup(
    pickup_id: UUID,
    citizen_id: UUID,
    latitude: str,
    longitude: str,
    otp_code: str,
    items: list[tuple[str, str]],
) -> bool:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return False
    try:
        from psycopg import Error, connect

        with connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO pickup_requests (id, citizen_id, location, otp_code)
                    VALUES (%s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s)
                    """,
                    (pickup_id, citizen_id, longitude, latitude, otp_code),
                )
                cursor.executemany(
                    """
                    INSERT INTO pickup_items (pickup_id, material_code, ai_estimated_kg)
                    VALUES (%s, %s, %s)
                    """,
                    [(pickup_id, material_code, weight) for material_code, weight in items],
                )
        return True
    except (ModuleNotFoundError, Error):
        return False


def persist_kyc(user_id: UUID, reference_hash: str) -> bool:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return False
    try:
        from psycopg import Error, connect

        with connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE users
                    SET dpi_kyc_verified = TRUE, dpi_kyc_ref_hash = %s
                    WHERE id = %s
                    """,
                    (reference_hash, user_id),
                )
        return True
    except (ModuleNotFoundError, Error):
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
