from decimal import Decimal
from typing import Annotated

from fastapi import FastAPI, Query
from pydantic import BaseModel, ConfigDict, Field


class Material(BaseModel):
    model_config = ConfigDict(frozen=True)

    material_code: str
    display_name: str
    aggregator_buy_rate: Decimal = Field(gt=0, decimal_places=2)
    collector_margin: Decimal = Field(gt=0, decimal_places=2)
    density_kg_per_m3: Decimal = Field(gt=0, decimal_places=2)
    co2e_factor: Decimal = Field(gt=0, decimal_places=3)


MATERIAL_CATALOG: tuple[Material, ...] = (
    Material(
        material_code="pet_plastic",
        display_name="PET Plastic",
        aggregator_buy_rate=Decimal("42.00"),
        collector_margin=Decimal("4.00"),
        density_kg_per_m3=Decimal("35.00"),
        co2e_factor=Decimal("1.450"),
    ),
    Material(
        material_code="cardboard",
        display_name="Cardboard",
        aggregator_buy_rate=Decimal("18.00"),
        collector_margin=Decimal("2.00"),
        density_kg_per_m3=Decimal("50.00"),
        co2e_factor=Decimal("0.950"),
    ),
    Material(
        material_code="iron",
        display_name="Ferrous Scrap Metal",
        aggregator_buy_rate=Decimal("32.00"),
        collector_margin=Decimal("3.00"),
        density_kg_per_m3=Decimal("600.00"),
        co2e_factor=Decimal("8.200"),
    ),
    Material(
        material_code="glass",
        display_name="Glass",
        aggregator_buy_rate=Decimal("12.00"),
        collector_margin=Decimal("1.50"),
        density_kg_per_m3=Decimal("350.00"),
        co2e_factor=Decimal("0.300"),
    ),
)

app = FastAPI(
    title="Kabadiwala Connect OS",
    version="0.1.0",
    description="Deterministic circular-economy operations API.",
)


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {"name": "Kabadiwala Connect OS", "status": "ready", "version": app.version}


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/materials", response_model=list[Material], tags=["materials"])
def list_materials(
    material_code: Annotated[str | None, Query(min_length=2, max_length=30)] = None,
) -> list[Material]:
    if material_code is None:
        return list(MATERIAL_CATALOG)
    return [material for material in MATERIAL_CATALOG if material.material_code == material_code]
