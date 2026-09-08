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


def persist_settlement(
    pickup_id: UUID,
    collector_id: UUID,
    items: list[tuple[str, str, str, str, str]],
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
                    UPDATE pickup_requests
                    SET collector_id = %s, otp_verified = TRUE,
                        status = 'completed', completed_at = NOW()
                    WHERE id = %s
                    """,
                    (collector_id, pickup_id),
                )
                cursor.executemany(
                    """
                    UPDATE pickup_items
                    SET actual_weight_kg = %s, quality_deduction_pct = %s,
                        subtotal_price = %s, co2_saved_kg = %s
                    WHERE pickup_id = %s AND material_code = %s
                    """,
                    [
                        (actual, deduction, subtotal, co2_saved, pickup_id, material_code)
                        for material_code, actual, deduction, subtotal, co2_saved in items
                    ],
                )
        return True
    except (ModuleNotFoundError, Error):
        return False


def persist_batch(
    batch_id: UUID,
    batch_hash: str,
    aggregator_id: UUID,
    material_code: str,
    gross_weight: str,
    pickup_ids: list[UUID],
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
                    INSERT INTO aggregator_batches
                        (batch_id, batch_hash, aggregator_id, material_code,
                         gross_weight_kg, net_weight_kg)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (batch_id) DO NOTHING
                    """,
                    (batch_id, batch_hash, aggregator_id, material_code, gross_weight, gross_weight),
                )
                cursor.executemany(
                    """
                    INSERT INTO batch_contributing_pickups (batch_id, pickup_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    [(batch_id, pickup_id) for pickup_id in pickup_ids],
                )
        return True
    except (ModuleNotFoundError, Error):
        return False


def persist_recycle(
    batch_id: UUID,
    moisture_deduction: str,
    foreign_matter_deduction: str,
    net_weight: str,
    co2e_avoided: str,
    epr_token: str,
    digilocker_uri: str,
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
                    UPDATE aggregator_batches
                    SET moisture_deduction_pct = %s,
                        foreign_matter_deduction_pct = %s,
                        net_weight_kg = %s,
                        co2e_avoided_kg = %s,
                        cpcb_epr_token = %s,
                        digilocker_doc_uri = %s,
                        status = 'processed',
                        recycled_at = NOW()
                    WHERE batch_id = %s
                    """,
                    (
                        moisture_deduction,
                        foreign_matter_deduction,
                        net_weight,
                        co2e_avoided,
                        epr_token,
                        digilocker_uri,
                        batch_id,
                    ),
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
