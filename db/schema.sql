CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TYPE user_role AS ENUM ('citizen', 'collector', 'aggregator', 'recycler', 'admin');
CREATE TYPE pickup_status AS ENUM ('requested', 'assigned', 'en_route', 'completed', 'cancelled');
CREATE TYPE batch_status AS ENUM ('created', 'baled', 'in_transit', 'received_at_recycler', 'processed');

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone VARCHAR(15) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role user_role NOT NULL,
    upi_id VARCHAR(50),
    dpi_kyc_verified BOOLEAN NOT NULL DEFAULT FALSE,
    dpi_kyc_ref_hash CHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE collectors (
    id UUID PRIMARY KEY REFERENCES users(id),
    vehicle_type VARCHAR(50) NOT NULL DEFAULT 'electric_loader',
    max_payload_kg NUMERIC(8, 2) NOT NULL DEFAULT 200.00 CHECK (max_payload_kg > 0),
    max_volume_m3 NUMERIC(8, 3) NOT NULL DEFAULT 1.800 CHECK (max_volume_m3 > 0),
    current_location GEOMETRY(Point, 4326),
    trust_score NUMERIC(4, 3) NOT NULL DEFAULT 1.000,
    rolling_discrepancy_mean NUMERIC(8, 3) NOT NULL DEFAULT 0.000,
    rolling_discrepancy_std NUMERIC(8, 3) NOT NULL DEFAULT 1.000,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE material_catalog (
    material_code VARCHAR(30) PRIMARY KEY,
    display_name VARCHAR(50) NOT NULL,
    aggregator_buy_rate NUMERIC(8, 2) NOT NULL CHECK (aggregator_buy_rate > 0),
    collector_margin NUMERIC(8, 2) NOT NULL CHECK (collector_margin >= 0),
    density_kg_per_m3 NUMERIC(8, 2) NOT NULL CHECK (density_kg_per_m3 > 0),
    co2e_factor NUMERIC(8, 3) NOT NULL CHECK (co2e_factor >= 0)
);

CREATE TABLE pickup_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    citizen_id UUID NOT NULL REFERENCES users(id),
    collector_id UUID REFERENCES collectors(id),
    is_rwa_drive BOOLEAN NOT NULL DEFAULT FALSE,
    rwa_name VARCHAR(100),
    location GEOMETRY(Point, 4326) NOT NULL,
    h3_index VARCHAR(15),
    status pickup_status NOT NULL DEFAULT 'requested',
    otp_code CHAR(4) NOT NULL CHECK (otp_code ~ '^[0-9]{4}$'),
    otp_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE pickup_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pickup_id UUID NOT NULL REFERENCES pickup_requests(id) ON DELETE CASCADE,
    material_code VARCHAR(30) NOT NULL REFERENCES material_catalog(material_code),
    ai_estimated_kg NUMERIC(8, 2) NOT NULL CHECK (ai_estimated_kg > 0),
    actual_weight_kg NUMERIC(8, 2) CHECK (actual_weight_kg > 0),
    quality_deduction_pct NUMERIC(5, 2) NOT NULL DEFAULT 0.00 CHECK (quality_deduction_pct BETWEEN 0 AND 100),
    subtotal_price NUMERIC(10, 2),
    co2_saved_kg NUMERIC(10, 2)
);

CREATE TABLE fraud_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collector_id UUID NOT NULL REFERENCES collectors(id),
    pickup_id UUID NOT NULL REFERENCES pickup_requests(id),
    calculated_z_score NUMERIC(8, 2) NOT NULL,
    flagged_reason TEXT NOT NULL,
    logged_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE aggregator_batches (
    batch_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_hash CHAR(64) UNIQUE NOT NULL,
    aggregator_id UUID NOT NULL REFERENCES users(id),
    recycler_id UUID REFERENCES users(id),
    material_code VARCHAR(30) NOT NULL REFERENCES material_catalog(material_code),
    gross_weight_kg NUMERIC(10, 2) NOT NULL CHECK (gross_weight_kg > 0),
    moisture_deduction_pct NUMERIC(5, 2) NOT NULL DEFAULT 0.00 CHECK (moisture_deduction_pct BETWEEN 0 AND 100),
    foreign_matter_deduction_pct NUMERIC(5, 2) NOT NULL DEFAULT 0.00 CHECK (foreign_matter_deduction_pct BETWEEN 0 AND 100),
    net_weight_kg NUMERIC(10, 2) NOT NULL CHECK (net_weight_kg >= 0),
    co2e_avoided_kg NUMERIC(10, 2),
    status batch_status NOT NULL DEFAULT 'created',
    cpcb_epr_token VARCHAR(100) UNIQUE,
    digilocker_doc_uri VARCHAR(255),
    dispatched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    recycled_at TIMESTAMPTZ
);

CREATE TABLE batch_contributing_pickups (
    batch_id UUID NOT NULL REFERENCES aggregator_batches(batch_id) ON DELETE CASCADE,
    pickup_id UUID NOT NULL REFERENCES pickup_requests(id),
    PRIMARY KEY (batch_id, pickup_id)
);

CREATE INDEX pickup_requests_status_idx ON pickup_requests(status);
CREATE INDEX pickup_requests_collector_idx ON pickup_requests(collector_id);
CREATE INDEX fraud_audit_logs_collector_idx ON fraud_audit_logs(collector_id, logged_at DESC);
CREATE INDEX aggregator_batches_status_idx ON aggregator_batches(status);
CREATE INDEX collectors_location_gix ON collectors USING GIST(current_location);
CREATE INDEX pickup_requests_location_gix ON pickup_requests USING GIST(location);
