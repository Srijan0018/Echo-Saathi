from decimal import Decimal
from enum import StrEnum
from hashlib import sha256
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, ConfigDict, Field


class Material(BaseModel):
    model_config = ConfigDict(frozen=True)

    material_code: str
    display_name: str
    aggregator_buy_rate: Decimal = Field(gt=0, decimal_places=2)
    collector_margin: Decimal = Field(gt=0, decimal_places=2)
    density_kg_per_m3: Decimal = Field(gt=0, decimal_places=2)
    co2e_factor: Decimal = Field(gt=0, decimal_places=3)


class UserRole(StrEnum):
    CITIZEN = "citizen"
    COLLECTOR = "collector"
    AGGREGATOR = "aggregator"
    RECYCLER = "recycler"
    ADMIN = "admin"


class RegisterRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=15, pattern=r"^\+?[0-9]{10,14}$")
    full_name: str = Field(min_length=2, max_length=100)
    role: UserRole
    upi_id: str | None = Field(default=None, max_length=50)


class User(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    phone: str
    full_name: str
    role: UserRole
    upi_id: str | None = None
    dpi_kyc_verified: bool = False
    dpi_kyc_ref_hash: str | None = None


class KycRequest(BaseModel):
    user_id: UUID
    reference_token: str = Field(min_length=8, max_length=100)


class KycResponse(BaseModel):
    status: str
    kyc_id: str
    name_match: bool
    user_id: UUID


class DetectedMaterial(BaseModel):
    material_code: str
    confidence: Decimal = Field(ge=0, le=1, decimal_places=2)
    estimated_kg: Decimal = Field(gt=0, decimal_places=2)


class ClassificationResponse(BaseModel):
    detected_materials: list[DetectedMaterial]
    contamination_detected: bool
    confidence_score: Decimal = Field(ge=0, le=1, decimal_places=2)
    fallback_used: bool


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

USERS: dict[UUID, User] = {}
KYC_SALT = "kabadiwala-connect-demo"

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


@app.post("/api/v1/auth/register", response_model=User, status_code=201, tags=["auth"])
def register_user(payload: RegisterRequest) -> User:
    if any(user.phone == payload.phone for user in USERS.values()):
        raise HTTPException(status_code=409, detail="phone already registered")
    user = User(
        id=uuid4(),
        phone=payload.phone,
        full_name=payload.full_name,
        role=payload.role,
        upi_id=payload.upi_id,
    )
    USERS[user.id] = user
    return user


@app.post("/api/v1/dpi/verify-kyc", response_model=KycResponse, tags=["dpi"])
def verify_kyc(payload: KycRequest) -> KycResponse:
    user = USERS.get(payload.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    token_hash = sha256(f"{KYC_SALT}:{payload.reference_token}".encode()).hexdigest()
    verified_user = user.model_copy(
        update={
            "dpi_kyc_verified": True,
            "dpi_kyc_ref_hash": token_hash,
        }
    )
    USERS[user.id] = verified_user
    return KycResponse(
        status="VERIFIED",
        kyc_id=f"DPI-KYC-{user.id.hex[:8].upper()}",
        name_match=True,
        user_id=user.id,
    )


@app.post(
    "/api/v1/ai/classify-waste",
    response_model=ClassificationResponse,
    tags=["ai"],
)
async def classify_waste(image: UploadFile = File(...)) -> ClassificationResponse:
    if not image.filename:
        raise HTTPException(status_code=400, detail="image filename is required")
    return ClassificationResponse(
        detected_materials=[
            DetectedMaterial(
                material_code="pet_plastic",
                confidence=Decimal("0.94"),
                estimated_kg=Decimal("4.50"),
            ),
            DetectedMaterial(
                material_code="cardboard",
                confidence=Decimal("0.88"),
                estimated_kg=Decimal("3.00"),
            ),
        ],
        contamination_detected=False,
        confidence_score=Decimal("0.91"),
        fallback_used=True,
    )


@app.get("/api/v1/materials", response_model=list[Material], tags=["materials"])
def list_materials(
    material_code: Annotated[str | None, Query(min_length=2, max_length=30)] = None,
) -> list[Material]:
    if material_code is None:
        return list(MATERIAL_CATALOG)
    return [material for material in MATERIAL_CATALOG if material.material_code == material_code]
