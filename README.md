# Eco Saathi OS

### A digital platform for India’s informal recycling ecosystem

EcoSaathi connects **households, waste collectors, aggregators, recyclers, and municipalities** in one platform. It helps track recyclable material from pickup to recycling while improving collection efficiency, payment transparency, and trust.

> **Every pickup becomes a verified journey from household to recycler.**

## The Problem

Informal collectors recover valuable materials, but their work is mostly offline. This causes:

- Unclear pricing and payment disputes.
- Unstable collector earnings.
- Inefficient pickup routes.
- Weak tracking of recyclable material.
- Limited recycling data for municipalities.

## Our Solution

EcoSaathi provides a simple digital workflow:

```text
Household → Collector → Aggregator → Recycler → Municipality
```

- Citizens book pickups and upload waste images.
- AI identifies material type and contamination.
- H3 and OR-Tools create routes using location, weight, and volume.
- Collectors record actual weight using voice, keypad, or pictorial controls.
- OTP verifies the final settlement.
- QR-based offline mode supports areas with poor internet.
- Batch IDs track material from household pickup to recycler confirmation.
- Dashboards show collection, recycling, recovery, and environmental data.

## Standout Features

- **Dual-capacity routing:** Considers both weight and physical cargo space.
- **Collector-first design:** Voice, icons, keypad, and offline support.
- **Trusted settlement:** Transparent pricing, deductions, OTP, and fraud detection.
- **Mass-balance tracking:** Links household contributions to recycler-confirmed batches.
- **One connected ecosystem:** Supports citizens, collectors, depots, recyclers, and municipalities.

## Technology

- **Flutter:** Citizen and collector apps.
- **FastAPI + Python:** Backend and system logic.
- **Gemini Vision:** Material and contamination detection.
- **H3 + OR-Tools:** Pickup clustering and route optimization.
- **PostgreSQL + PostGIS:** Transaction and location data.
- **SQLite + Redis:** Offline storage and synchronization.
- **Next.js + Mapbox:** Dashboards and maps.
- **QR / BLE-ready flow:** Offline pickup verification.

## Prototype Modules

- Citizen pickup booking.
- AI-assisted waste classification.
- Collector route and settlement console.
- OTP verification and trust checks.
- Aggregator batch creation.
- Recycler confirmation.
- Municipal dashboard.
- Regulatory assistant.
- API documentation and automated tests.

The prototype currently uses deterministic in-memory demo data. A PostgreSQL 16/PostGIS schema is included for the persistence phase.

## Run Locally

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
uvicorn app.main:app --reload
```

Or:

```powershell
.\scripts\start.ps1
```

## Prototype Pages

- Dashboard: `http://127.0.0.1:8000/dashboard/`
- Citizen: `http://127.0.0.1:8000/citizen/citizen.html`
- Collector: `http://127.0.0.1:8000/collector/collector.html`
- Depot and recycler: `http://127.0.0.1:8000/depot/depot.html`
- Regulatory assistant: `http://127.0.0.1:8000/regulatory/regulatory.html`
- API docs: `http://127.0.0.1:8000/docs`

## Vision

EcoSaathi does not replace the existing recycling network. It makes it **more visible, efficient, trusted, and traceable**.

> **EcoSaathi turns informal collection into a measurable circular-economy system.**
