from pathlib import Path


def test_database_seed_contains_all_api_materials() -> None:
    seed = (Path(__file__).parents[1] / "db" / "seed.sql").read_text()

    for material_code in ("pet_plastic", "cardboard", "iron", "glass"):
        assert f"'{material_code}'" in seed