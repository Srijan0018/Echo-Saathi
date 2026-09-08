from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from hashlib import sha256
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.database import (
    database_status,
    load_user,
    persist_batch,
    persist_kyc,
    persist_assignment,
    persist_pickup,
    persist_recycle,
    persist_settlement,
    persist_user,
)
from app.fraud import assess_discrepancy
from app.rag import query_regulations
from app.routing import RouteStop, optimize_routes


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


class LoginRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=15, pattern=r"^\+?[0-9]{10,14}$")
    role: UserRole


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "User"


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


class PickupStatus(StrEnum):
    REQUESTED = "requested"
    ASSIGNED = "assigned"
    EN_ROUTE = "en_route"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PickupItemRequest(BaseModel):
    material_code: str = Field(min_length=2, max_length=30)
    ai_estimated_kg: Decimal = Field(gt=0, decimal_places=2)


class PickupRequest(BaseModel):
    citizen_id: UUID
    latitude: Decimal = Field(ge=Decimal("-90"), le=Decimal("90"), decimal_places=6)
    longitude: Decimal = Field(ge=Decimal("-180"), le=Decimal("180"), decimal_places=6)
    items: list[PickupItemRequest] = Field(min_length=1, max_length=20)
    is_rwa_drive: bool = False
    rwa_name: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def validate_rwa_name(self) -> "PickupRequest":
        if self.is_rwa_drive and not self.rwa_name:
            raise ValueError("rwa_name is required for an RWA drive")
        return self


class PickupResponse(BaseModel):
    id: UUID
    citizen_id: UUID
    collector_id: UUID | None = None
    status: PickupStatus
    otp_code: str
    items: list[PickupItemRequest]
    is_rwa_drive: bool = False
    rwa_name: str | None = None
    offline_sync_token: str


class MapPoint(BaseModel):
    pickup_id: UUID
    latitude: Decimal
    longitude: Decimal
    status: PickupStatus
    is_rwa_drive: bool
    rwa_name: str | None = None


class MapResponse(BaseModel):
    center_latitude: Decimal
    center_longitude: Decimal
    points: list[MapPoint]


class SettlementItem(BaseModel):
    material_code: str = Field(min_length=2, max_length=30)
    actual_weight_kg: Decimal = Field(gt=0, decimal_places=2)
    quality_deduction_pct: Decimal = Field(ge=0, le=100, decimal_places=2)


class SettlementRequest(BaseModel):
    pickup_id: UUID
    collector_id: UUID
    otp_code: str = Field(min_length=4, max_length=4, pattern=r"^[0-9]{4}$")
    items: list[SettlementItem] = Field(min_length=1, max_length=20)


class SettlementResponse(BaseModel):
    pickup_id: UUID
    status: PickupStatus
    payout_amount: Decimal
    upi_reference: str
    audit_flagged: bool
    z_score: Decimal


class AssignPickupRequest(BaseModel):
    pickup_id: UUID
    collector_id: UUID


class CollectorPickupInbox(BaseModel):
    collector_id: UUID
    pickups: list[PickupResponse]


class BatchStatus(StrEnum):
    CREATED = "created"
    PROCESSED = "processed"


class BatchAggregateRequest(BaseModel):
    aggregator_id: UUID
    material_code: str = Field(min_length=2, max_length=30)
    pickup_ids: list[UUID] = Field(min_length=1, max_length=100)


class BatchResponse(BaseModel):
    batch_id: UUID
    batch_hash: str
    material_code: str
    gross_weight_kg: Decimal
    net_weight_kg: Decimal
    status: BatchStatus
    co2e_avoided_kg: Decimal = Decimal("0.00")
    cpcb_epr_token: str | None = None
    digilocker_doc_uri: str | None = None


class RecycleRequest(BaseModel):
    moisture_deduction_pct: Decimal = Field(ge=0, le=100, decimal_places=2)
    foreign_matter_deduction_pct: Decimal = Field(ge=0, le=100, decimal_places=2)


class MunicipalSummary(BaseModel):
    pickups_completed: int
    recovered_weight_kg: Decimal
    processed_batches: int
    active_collectors: int
    fraud_audit_flags: int


class AuditLogResponse(BaseModel):
    collector_id: UUID
    pickup_id: UUID
    calculated_z_score: Decimal
    flagged_reason: str


class RagQuery(BaseModel):
    query: str = Field(min_length=3, max_length=500)


class RagCitation(BaseModel):
    title: str
    citation: str
    text: str


class RagResponse(BaseModel):
    answer: str
    citations: list[RagCitation]


class RouteStopRequest(BaseModel):
    stop_id: str = Field(min_length=1, max_length=50)
    weight_kg: Decimal = Field(gt=0, decimal_places=2)
    volume_m3: Decimal = Field(gt=0, decimal_places=3)


class RouteOptimizeRequest(BaseModel):
    collector_id: UUID
    max_payload_kg: Decimal = Field(gt=0, decimal_places=2)
    max_volume_m3: Decimal = Field(gt=0, decimal_places=3)
    stops: list[RouteStopRequest] = Field(min_length=1, max_length=9)


class RouteTripResponse(BaseModel):
    stop_ids: tuple[str, ...]
    weight_kg: Decimal
    volume_m3: Decimal
    returned_to_depot: bool


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
SESSIONS: dict[str, UUID] = {}
PICKUPS: dict[UUID, PickupResponse] = {}
PICKUP_LOCATIONS: dict[UUID, tuple[Decimal, Decimal]] = {}
DISCREPANCIES: dict[UUID, list[Decimal]] = {}
FRAUD_AUDIT_LOGS: list[dict[str, str | Decimal | UUID]] = []
SETTLED_WEIGHTS: dict[UUID, dict[str, Decimal]] = {}
BATCHES: dict[UUID, BatchResponse] = {}
KYC_SALT = "kabadiwala-connect-demo"

app = FastAPI(
    title="Kabadiwala Connect OS",
    version="0.1.0",
    description="Deterministic circular-economy operations API.",
)
app.mount("/dashboard", StaticFiles(directory="frontend", html=True), name="dashboard")
app.mount("/citizen", StaticFiles(directory="frontend", html=True), name="citizen")
app.mount("/collector", StaticFiles(directory="frontend", html=True), name="collector")
app.mount("/depot", StaticFiles(directory="frontend", html=True), name="depot")
app.mount("/regulatory", StaticFiles(directory="frontend", html=True), name="regulatory")
app.mount("/login", StaticFiles(directory="frontend", html=True), name="login")


@app.get("/", tags=["system"])
def root() -> RedirectResponse:
    return RedirectResponse(url="/dashboard/", status_code=307)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/database", tags=["system"])
def database_health() -> dict[str, str]:
    return database_status()


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
    persist_user(user.id, user.phone, user.full_name, user.role.value, user.upi_id)
    return user


@app.post("/api/v1/auth/login", response_model=LoginResponse, tags=["auth"])
def login_user(payload: LoginRequest) -> LoginResponse:
    user = next(
        (candidate for candidate in USERS.values() if candidate.phone == payload.phone and candidate.role == payload.role),
        None,
    )
    if user is None:
        stored_user = load_user(payload.phone, payload.role.value)
        if stored_user is not None:
            user = User(**stored_user)
            USERS[user.id] = user
    if user is None:
        raise HTTPException(status_code=401, detail="invalid phone or role")
    access_token = sha256(f"session:{user.id}:{payload.role.value}".encode()).hexdigest()
    SESSIONS[access_token] = user.id
    return LoginResponse(access_token=access_token, user=user)


@app.post("/api/v1/dpi/verify-kyc", response_model=KycResponse, tags=["dpi"])
def verify_kyc(payload: KycRequest) -> KycResponse:
    user = USERS.get(payload.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    if user.role != UserRole.COLLECTOR:
        raise HTTPException(status_code=403, detail="only collectors can complete DPI KYC")
    token_hash = sha256(f"{KYC_SALT}:{payload.reference_token}".encode()).hexdigest()
    verified_user = user.model_copy(
        update={
            "dpi_kyc_verified": True,
            "dpi_kyc_ref_hash": token_hash,
        }
    )
    USERS[user.id] = verified_user
    persist_kyc(user.id, token_hash)
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


@app.post("/api/v1/pickups/request", response_model=PickupResponse, status_code=201, tags=["pickups"])
def request_pickup(payload: PickupRequest) -> PickupResponse:
    citizen = USERS.get(payload.citizen_id)
    if citizen is None:
        raise HTTPException(status_code=404, detail="citizen not found")
    if citizen.role != UserRole.CITIZEN:
        raise HTTPException(status_code=403, detail="only citizens can request pickups")
    for item in payload.items:
        if not any(material.material_code == item.material_code for material in MATERIAL_CATALOG):
            raise HTTPException(status_code=422, detail=f"unknown material: {item.material_code}")
    pickup = PickupResponse(
        id=uuid4(),
        citizen_id=payload.citizen_id,
        collector_id=None,
        status=PickupStatus.REQUESTED,
        otp_code="4826",
        items=payload.items,
        is_rwa_drive=payload.is_rwa_drive,
        rwa_name=payload.rwa_name,
        offline_sync_token=sha256(f"offline:{uuid4()}".encode()).hexdigest(),
    )
    PICKUPS[pickup.id] = pickup
    PICKUP_LOCATIONS[pickup.id] = (payload.latitude, payload.longitude)
    persist_pickup(
        pickup.id,
        pickup.citizen_id,
        str(payload.latitude),
        str(payload.longitude),
        pickup.otp_code,
        [(item.material_code, str(item.ai_estimated_kg)) for item in payload.items],
        payload.is_rwa_drive,
        payload.rwa_name,
        pickup.offline_sync_token,
    )
    return pickup


@app.post("/api/v1/pickups/assign", response_model=PickupResponse, tags=["pickups"])
def assign_pickup(payload: AssignPickupRequest) -> PickupResponse:
    pickup = PICKUPS.get(payload.pickup_id)
    collector = USERS.get(payload.collector_id)
    if pickup is None:
        raise HTTPException(status_code=404, detail="pickup not found")
    if collector is None or collector.role != UserRole.COLLECTOR:
        raise HTTPException(status_code=404, detail="collector not found")
    if pickup.status != PickupStatus.REQUESTED:
        raise HTTPException(status_code=409, detail="pickup is not awaiting assignment")
    assigned = pickup.model_copy(
        update={"collector_id": collector.id, "status": PickupStatus.ASSIGNED}
    )
    PICKUPS[pickup.id] = assigned
    persist_assignment(pickup.id, collector.id)
    return assigned


@app.get(
    "/api/v1/collectors/{collector_id}/pickups",
    response_model=CollectorPickupInbox,
    tags=["collectors"],
)
def collector_pickup_inbox(collector_id: UUID) -> CollectorPickupInbox:
    collector = USERS.get(collector_id)
    if collector is None or collector.role != UserRole.COLLECTOR:
        raise HTTPException(status_code=404, detail="collector not found")
    pickups = [
        pickup
        for pickup in PICKUPS.values()
        if pickup.status in {PickupStatus.REQUESTED, PickupStatus.ASSIGNED}
        and (pickup.collector_id is None or pickup.collector_id == collector_id)
    ]
    return CollectorPickupInbox(collector_id=collector_id, pickups=pickups)


@app.post(
    "/api/v1/pickups/verify-and-settle",
    response_model=SettlementResponse,
    tags=["pickups"],
)
def verify_and_settle(payload: SettlementRequest) -> SettlementResponse:
    pickup = PICKUPS.get(payload.pickup_id)
    collector = USERS.get(payload.collector_id)
    if pickup is None:
        raise HTTPException(status_code=404, detail="pickup not found")
    if collector is None or collector.role != UserRole.COLLECTOR:
        raise HTTPException(status_code=404, detail="collector not found")
    if pickup.collector_id is not None and pickup.collector_id != collector.id:
        raise HTTPException(status_code=403, detail="pickup is assigned to another collector")
    if pickup.status == PickupStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="pickup already settled")
    if payload.otp_code != pickup.otp_code:
        raise HTTPException(status_code=400, detail="invalid OTP")

    catalog = {material.material_code: material for material in MATERIAL_CATALOG}
    estimated = {item.material_code: item.ai_estimated_kg for item in pickup.items}
    payout = Decimal("0.00")
    assessments = []
    settled_items: list[tuple[str, str, str, str, str]] = []
    for item in payload.items:
        material = catalog.get(item.material_code)
        if material is None:
            raise HTTPException(status_code=422, detail=f"unknown material: {item.material_code}")
        if item.material_code not in estimated:
            raise HTTPException(status_code=422, detail=f"material not requested: {item.material_code}")
        net_weight = item.actual_weight_kg * (Decimal("100") - item.quality_deduction_pct) / Decimal("100")
        subtotal = net_weight * (material.aggregator_buy_rate - material.collector_margin)
        payout += subtotal
        co2_saved = net_weight * material.co2e_factor
        settled_items.append(
            (
                item.material_code,
                str(item.actual_weight_kg),
                str(item.quality_deduction_pct),
                str(subtotal.quantize(Decimal("0.01"))),
                str(co2_saved.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            )
        )
        discrepancy = item.actual_weight_kg - estimated[item.material_code]
        history = DISCREPANCIES.setdefault(payload.collector_id, [])
        assessment = assess_discrepancy(history, discrepancy, estimated[item.material_code])
        history.append(discrepancy)
        assessments.append(assessment)
        if assessment.flagged:
            FRAUD_AUDIT_LOGS.append(
                {
                    "collector_id": payload.collector_id,
                    "pickup_id": pickup.id,
                    "calculated_z_score": assessment.z_score,
                    "flagged_reason": assessment.reason or "audit",
                }
            )

    completed_pickup = pickup.model_copy(update={"status": PickupStatus.COMPLETED})
    PICKUPS[pickup.id] = completed_pickup
    SETTLED_WEIGHTS[pickup.id] = {item.material_code: item.actual_weight_kg for item in payload.items}
    persist_settlement(pickup.id, payload.collector_id, settled_items)
    audit_flagged = any(assessment.flagged for assessment in assessments)
    return SettlementResponse(
        pickup_id=pickup.id,
        status=PickupStatus.COMPLETED,
        payout_amount=payout.quantize(Decimal("0.01")),
        upi_reference=f"UPI-REF-{pickup.id.hex[:10].upper()}",
        audit_flagged=audit_flagged,
        z_score=max((assessment.z_score for assessment in assessments), default=Decimal("0.00")),
    )


@app.post("/api/v1/batches/aggregate", response_model=BatchResponse, status_code=201, tags=["batches"])
def aggregate_batch(payload: BatchAggregateRequest) -> BatchResponse:
    aggregator = USERS.get(payload.aggregator_id)
    if aggregator is None or aggregator.role != UserRole.AGGREGATOR:
        raise HTTPException(status_code=404, detail="aggregator not found")
    if not any(material.material_code == payload.material_code for material in MATERIAL_CATALOG):
        raise HTTPException(status_code=422, detail="unknown material")
    weights: list[Decimal] = []
    for pickup_id in payload.pickup_ids:
        pickup = PICKUPS.get(pickup_id)
        if pickup is None or pickup.status != PickupStatus.COMPLETED:
            raise HTTPException(status_code=422, detail=f"pickup not settled: {pickup_id}")
        weight = SETTLED_WEIGHTS.get(pickup_id, {}).get(payload.material_code)
        if weight is None:
            raise HTTPException(status_code=422, detail=f"material not settled: {pickup_id}")
        weights.append(weight)
    gross_weight = sum(weights, Decimal("0")).quantize(Decimal("0.01"))
    batch_id = uuid4()
    batch_hash = sha256(
        f"{batch_id}:{payload.aggregator_id}:{payload.material_code}:{gross_weight}".encode()
    ).hexdigest()
    batch = BatchResponse(
        batch_id=batch_id,
        batch_hash=batch_hash,
        material_code=payload.material_code,
        gross_weight_kg=gross_weight,
        net_weight_kg=gross_weight,
        status=BatchStatus.CREATED,
    )
    BATCHES[batch_id] = batch
    persist_batch(
        batch.batch_id,
        batch.batch_hash,
        payload.aggregator_id,
        batch.material_code,
        str(batch.gross_weight_kg),
        payload.pickup_ids,
    )
    return batch


@app.put("/api/v1/batches/{batch_id}/recycle", response_model=BatchResponse, tags=["batches"])
def recycle_batch(batch_id: UUID, payload: RecycleRequest) -> BatchResponse:
    batch = BATCHES.get(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="batch not found")
    if batch.status == BatchStatus.PROCESSED:
        raise HTTPException(status_code=409, detail="batch already processed")
    net_weight = batch.gross_weight_kg * (
        Decimal("100") - payload.moisture_deduction_pct - payload.foreign_matter_deduction_pct
    ) / Decimal("100")
    material = next(item for item in MATERIAL_CATALOG if item.material_code == batch.material_code)
    processed = batch.model_copy(
        update={
            "net_weight_kg": net_weight.quantize(Decimal("0.01")),
            "status": BatchStatus.PROCESSED,
            "co2e_avoided_kg": (net_weight * material.co2e_factor).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            ),
            "cpcb_epr_token": f"EPR-{batch.batch_hash[:12].upper()}",
            "digilocker_doc_uri": f"digilocker://issuer/kabadiwala/batches/{batch.batch_id}",
        }
    )
    BATCHES[batch_id] = processed
    persist_recycle(
        batch_id,
        str(payload.moisture_deduction_pct),
        str(payload.foreign_matter_deduction_pct),
        str(processed.net_weight_kg),
        str(processed.co2e_avoided_kg),
        processed.cpcb_epr_token or "",
        processed.digilocker_doc_uri or "",
    )
    return processed


@app.get("/api/v1/municipality/summary", response_model=MunicipalSummary, tags=["municipality"])
def municipality_summary() -> MunicipalSummary:
    processed_batches = [batch for batch in BATCHES.values() if batch.status == BatchStatus.PROCESSED]
    return MunicipalSummary(
        pickups_completed=sum(pickup.status == PickupStatus.COMPLETED for pickup in PICKUPS.values()),
        recovered_weight_kg=sum(
            (batch.net_weight_kg for batch in processed_batches), Decimal("0.00")
        ).quantize(Decimal("0.01")),
        processed_batches=len(processed_batches),
        active_collectors=sum(user.role == UserRole.COLLECTOR for user in USERS.values()),
        fraud_audit_flags=len(FRAUD_AUDIT_LOGS),
    )


@app.get("/api/v1/municipality/audits", response_model=list[AuditLogResponse], tags=["municipality"])
def municipality_audits() -> list[AuditLogResponse]:
    return [AuditLogResponse(**audit) for audit in FRAUD_AUDIT_LOGS]


@app.get("/api/v1/municipality/map", response_model=MapResponse, tags=["municipality"])
def municipality_map() -> MapResponse:
    return MapResponse(
        center_latitude=Decimal("12.971600"),
        center_longitude=Decimal("77.594600"),
        points=[
            MapPoint(
                pickup_id=pickup.id,
                latitude=PICKUP_LOCATIONS.get(pickup.id, (Decimal("12.971600"), Decimal("77.594600")))[0],
                longitude=PICKUP_LOCATIONS.get(pickup.id, (Decimal("12.971600"), Decimal("77.594600")))[1],
                status=pickup.status,
                is_rwa_drive=pickup.is_rwa_drive,
                rwa_name=pickup.rwa_name,
            )
            for pickup in PICKUPS.values()
        ],
    )


@app.post("/api/v1/rag/query", response_model=RagResponse, tags=["regulatory"])
def regulatory_query(payload: RagQuery) -> RagResponse:
    matches = query_regulations(payload.query)
    if not matches:
        return RagResponse(
            answer="No indexed rule matched this query. Consult the relevant CPCB notification.",
            citations=[],
        )
    return RagResponse(
        answer=" ".join(chunk.text for chunk in matches),
        citations=[RagCitation(title=chunk.title, citation=chunk.citation, text=chunk.text) for chunk in matches],
    )


@app.post("/api/v1/routing/optimize", response_model=list[RouteTripResponse], tags=["routing"])
def optimize_collector_route(payload: RouteOptimizeRequest) -> list[RouteTripResponse]:
    collector = USERS.get(payload.collector_id)
    if collector is None or collector.role != UserRole.COLLECTOR:
        raise HTTPException(status_code=404, detail="collector not found")
    try:
        trips = optimize_routes(
            [
                RouteStop(
                    stop_id=stop.stop_id,
                    weight_kg=stop.weight_kg,
                    volume_m3=stop.volume_m3,
                )
                for stop in payload.stops
            ],
            payload.max_payload_kg,
            payload.max_volume_m3,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return [RouteTripResponse(**trip.__dict__) for trip in trips]


@app.get("/api/v1/materials", response_model=list[Material], tags=["materials"])
def list_materials(
    material_code: Annotated[str | None, Query(min_length=2, max_length=30)] = None,
) -> list[Material]:
    if material_code is None:
        return list(MATERIAL_CATALOG)
    return [material for material in MATERIAL_CATALOG if material.material_code == material_code]
