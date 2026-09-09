-- ==============================================================================
-- Sales Coach AI - Enterprise Database DDL (GCash Merchant Sales & Distribution)
-- 35 Domain Tables | PostgreSQL 15+ Compatible | Full Referential Integrity & Indexes
-- ==============================================================================

-- Enable UUID extension if supported
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ------------------------------------------------------------------------------
-- DOMAIN 1: GEOGRAPHIC & TERRITORY HIERARCHY (4 TABLES)
-- ------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS regions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    region_code VARCHAR(32) NOT NULL UNIQUE,
    region_name VARCHAR(128) NOT NULL,
    island_group VARCHAR(32) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS provinces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    region_id UUID NOT NULL REFERENCES regions(id) ON DELETE CASCADE,
    province_name VARCHAR(128) NOT NULL,
    province_code VARCHAR(32) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cities_municipalities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    province_id UUID NOT NULL REFERENCES provinces(id) ON DELETE CASCADE,
    city_name VARCHAR(128) NOT NULL,
    postal_code VARCHAR(16),
    urban_tier VARCHAR(32) DEFAULT 'Metro_Tier1',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS areas (
    area_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    area_name VARCHAR(128) NOT NULL,
    region VARCHAR(64) NOT NULL,
    manager_id UUID,
    city_id UUID REFERENCES cities_municipalities(id) ON DELETE SET NULL,
    target_monthly_gmv NUMERIC(15,2) DEFAULT 5000000.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- DOMAIN 2: PERSONNEL, ORGANIZATIONS & GOVERNANCE (5 TABLES)
-- ------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS distributors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name VARCHAR(255) NOT NULL,
    tax_id VARCHAR(64),
    contact_person VARCHAR(128),
    contact_email VARCHAR(128),
    contact_phone VARCHAR(64),
    status VARCHAR(32) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS managers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(128) NOT NULL,
    email VARCHAR(128) NOT NULL UNIQUE,
    phone VARCHAR(64),
    area_id UUID NOT NULL REFERENCES areas(area_id) ON DELETE RESTRICT,
    distributor_id UUID REFERENCES distributors(id) ON DELETE SET NULL,
    status VARCHAR(32) DEFAULT 'active',
    hire_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dsps (
    dsp_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(128) NOT NULL,
    email VARCHAR(128) NOT NULL UNIQUE,
    phone VARCHAR(64),
    role VARCHAR(50) DEFAULT 'dsp',
    area_id UUID REFERENCES areas(area_id) ON DELETE RESTRICT,
    manager_id UUID REFERENCES dsps(dsp_id) ON DELETE SET NULL,
    distributor_id UUID REFERENCES distributors(id) ON DELETE SET NULL,
    status VARCHAR(32) DEFAULT 'active',
    hire_date DATE,
    daily_target_visits INT DEFAULT 10,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE areas DROP CONSTRAINT IF EXISTS fk_manager;
ALTER TABLE areas ADD CONSTRAINT fk_manager FOREIGN KEY (manager_id) REFERENCES dsps(dsp_id);

CREATE TABLE IF NOT EXISTS user_accounts (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(128) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(32) NOT NULL,
    linked_dsp_id UUID REFERENCES dsps(dsp_id) ON DELETE SET NULL,
    status VARCHAR(32) DEFAULT 'active',
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES user_accounts(user_id) ON DELETE SET NULL,
    action VARCHAR(64) NOT NULL,
    resource_type VARCHAR(64) NOT NULL,
    resource_id VARCHAR(128),
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- DOMAIN 3: MERCHANT & BUSINESS ENTITIES (5 TABLES)
-- ------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS merchants (
    merchant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_name VARCHAR(255) NOT NULL,
    owner_name VARCHAR(128),
    contact_number VARCHAR(64),
    business_type VARCHAR(64) NOT NULL,
    kyc_status VARCHAR(32) DEFAULT 'verified',
    risk_tier VARCHAR(32) DEFAULT 'low',
    onboarded_date DATE,
    status VARCHAR(32) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS merchant_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_code VARCHAR(64) NOT NULL UNIQUE,
    category_name VARCHAR(128) NOT NULL,
    description TEXT,
    benchmark_monthly_txns INT DEFAULT 500,
    default_cash_in_fee_rate NUMERIC(5,4) DEFAULT 0.0100,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS merchant_kyc_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id UUID NOT NULL REFERENCES merchants(merchant_id) ON DELETE CASCADE,
    document_type VARCHAR(64) NOT NULL,
    document_number VARCHAR(128) NOT NULL,
    verification_status VARCHAR(32) DEFAULT 'approved',
    verified_at TIMESTAMP WITH TIME ZONE,
    expires_at DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS merchant_bank_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id UUID NOT NULL REFERENCES merchants(merchant_id) ON DELETE CASCADE,
    bank_name VARCHAR(128) NOT NULL,
    account_number_mask VARCHAR(64) NOT NULL,
    account_type VARCHAR(32) DEFAULT 'savings',
    is_primary BOOLEAN DEFAULT TRUE,
    status VARCHAR(32) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS merchant_contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id UUID NOT NULL REFERENCES merchants(merchant_id) ON DELETE CASCADE,
    contact_name VARCHAR(128) NOT NULL,
    contact_role VARCHAR(64) NOT NULL,
    phone_number VARCHAR(64) NOT NULL,
    email VARCHAR(128),
    is_primary_decision_maker BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- DOMAIN 4: OUTLET OPERATIONS & HARDWARE/COLLATERALS (5 TABLES)
-- ------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS outlets (
    outlet_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id UUID NOT NULL REFERENCES merchants(merchant_id) ON DELETE CASCADE,
    area_id UUID REFERENCES areas(area_id) ON DELETE RESTRICT,
    outlet_name VARCHAR(255) NOT NULL,
    address VARCHAR(255),
    city VARCHAR(128),
    region VARCHAR(64),
    latitude NUMERIC(10,6),
    longitude NUMERIC(10,6),
    outlet_type VARCHAR(64),
    status VARCHAR(32) DEFAULT 'active',
    onboarding_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dsp_outlet_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dsp_id UUID NOT NULL REFERENCES dsps(dsp_id) ON DELETE CASCADE,
    outlet_id UUID NOT NULL REFERENCES outlets(outlet_id) ON DELETE CASCADE,
    assigned_date DATE,
    is_primary BOOLEAN DEFAULT TRUE,
    route_frequency VARCHAR(32) DEFAULT 'daily',
    status VARCHAR(32) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS outlet_operating_hours (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    outlet_id UUID NOT NULL REFERENCES outlets(outlet_id) ON DELETE CASCADE,
    day_of_week INT NOT NULL,
    opening_time VARCHAR(16) NOT NULL,
    closing_time VARCHAR(16) NOT NULL,
    peak_traffic_window VARCHAR(64),
    is_24_hours BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pos_terminals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    outlet_id UUID NOT NULL REFERENCES outlets(outlet_id) ON DELETE CASCADE,
    terminal_sn VARCHAR(64) NOT NULL UNIQUE,
    device_model VARCHAR(64) NOT NULL,
    firmware_version VARCHAR(64),
    battery_health_pct INT DEFAULT 100,
    connectivity_type VARCHAR(32) DEFAULT '4G_LTE',
    hardware_status VARCHAR(32) DEFAULT 'operational',
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS qr_collaterals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    outlet_id UUID NOT NULL REFERENCES outlets(outlet_id) ON DELETE CASCADE,
    collateral_type VARCHAR(64) NOT NULL,
    qr_payload_version VARCHAR(32) DEFAULT 'QRPh-v2',
    qr_code_id VARCHAR(128) NOT NULL,
    condition VARCHAR(32) DEFAULT 'good',
    placement_location VARCHAR(64) DEFAULT 'counter_checkout',
    deployed_at DATE,
    last_inspected_at DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- DOMAIN 5: PRODUCTS, TRANSACTIONS & LIQUIDITY (5 TABLES)
-- ------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS products (
    product_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_name VARCHAR(128) NOT NULL,
    category VARCHAR(64),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    revenue_yield_pct NUMERIC(5,4) DEFAULT 0.0150,
    min_recommended_daily_float NUMERIC(12,2) DEFAULT 10000.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS outlet_products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    outlet_id UUID NOT NULL REFERENCES outlets(outlet_id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    status VARCHAR(32) DEFAULT 'active',
    commission_rate NUMERIC(5,4) DEFAULT 0.0100,
    activated_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    txn_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    outlet_id UUID NOT NULL REFERENCES outlets(outlet_id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(product_id) ON DELETE SET NULL,
    txn_type VARCHAR(32) NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    currency VARCHAR(8) DEFAULT 'PHP',
    status VARCHAR(32) DEFAULT 'SUCCESS',
    response_code VARCHAR(32) DEFAULT '00_SUCCESS',
    txn_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_outlet_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    outlet_id UUID NOT NULL REFERENCES outlets(outlet_id) ON DELETE CASCADE,
    metric_date DATE NOT NULL,
    total_gmv NUMERIC(15,2) DEFAULT 0.00,
    total_transactions INT DEFAULT 0,
    failed_transactions INT DEFAULT 0,
    unique_customers INT DEFAULT 0,
    avg_ticket_size NUMERIC(10,2) DEFAULT 0.00,
    cash_in_volume NUMERIC(15,2) DEFAULT 0.00,
    qr_payment_volume NUMERIC(15,2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cash_in_liquidity_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    outlet_id UUID NOT NULL REFERENCES outlets(outlet_id) ON DELETE CASCADE,
    log_date DATE NOT NULL,
    opening_float NUMERIC(12,2) NOT NULL,
    closing_float NUMERIC(12,2) NOT NULL,
    float_stockout_occurred BOOLEAN DEFAULT FALSE,
    replenishment_amount NUMERIC(12,2) DEFAULT 0.00,
    replenishment_source VARCHAR(64) DEFAULT 'none',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- DOMAIN 6: AI INTELLIGENCE, SCORING & ML OBSERVABILITY (4 TABLES)
-- ------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS outlet_scores (
    score_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    outlet_id UUID NOT NULL REFERENCES outlets(outlet_id) ON DELETE CASCADE,
    priority_score NUMERIC(5,2) NOT NULL,
    transaction_score NUMERIC(5,2) DEFAULT 50.00,
    engagement_score NUMERIC(5,2) DEFAULT 50.00,
    product_adoption_score NUMERIC(5,2) DEFAULT 50.00,
    risk_score NUMERIC(5,2) DEFAULT 50.00,
    contributing_factors TEXT,
    score_date DATE DEFAULT CURRENT_DATE,
    model_version VARCHAR(32) DEFAULT 'v1.0',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scoring_feature_store (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    outlet_id UUID NOT NULL REFERENCES outlets(outlet_id) ON DELETE CASCADE,
    days_since_last_txn INT DEFAULT 0,
    days_since_last_visit INT DEFAULT 0,
    gmv_wow_growth_pct NUMERIC(6,2) DEFAULT 0.00,
    gmv_mom_growth_pct NUMERIC(6,2) DEFAULT 0.00,
    cash_in_stockout_count_7d INT DEFAULT 0,
    qr_standee_damage_flag BOOLEAN DEFAULT FALSE,
    pos_terminal_offline_hours_7d NUMERIC(6,2) DEFAULT 0.00,
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ml_model_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(128) NOT NULL,
    model_version VARCHAR(32) NOT NULL UNIQUE,
    algorithm VARCHAR(64) NOT NULL,
    auc_roc NUMERIC(5,4),
    f1_score NUMERIC(5,4),
    hyperparameters TEXT,
    deployment_status VARCHAR(32) DEFAULT 'champion',
    deployed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_drift_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES ml_model_registry(id) ON DELETE CASCADE,
    feature_name VARCHAR(128) NOT NULL,
    metric_type VARCHAR(32) NOT NULL,
    metric_value NUMERIC(8,4) NOT NULL,
    threshold NUMERIC(8,4) DEFAULT 0.2000,
    drift_detected BOOLEAN DEFAULT FALSE,
    evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- DOMAIN 7: ACTION ENGINE, STRATEGY & RECOMMENDATIONS (4 TABLES)
-- ------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS action_catalog (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action_code VARCHAR(64) NOT NULL UNIQUE,
    action_name VARCHAR(128) NOT NULL,
    category VARCHAR(64) NOT NULL,
    recommended_duration_minutes INT DEFAULT 20,
    business_impact VARCHAR(32) DEFAULT 'high',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS action_recommendations (
    action_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    outlet_id UUID NOT NULL REFERENCES outlets(outlet_id) ON DELETE CASCADE,
    dsp_id UUID NOT NULL REFERENCES dsps(dsp_id) ON DELETE CASCADE,
    action_type VARCHAR(64) NOT NULL,
    action_detail TEXT NOT NULL,
    priority VARCHAR(32) NOT NULL,
    status VARCHAR(32) DEFAULT 'pending',
    completed_at TIMESTAMP WITH TIME ZONE,
    completion_notes TEXT,
    action_catalog_id UUID REFERENCES action_catalog(id) ON DELETE SET NULL,
    due_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pitch_playbooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_id UUID REFERENCES merchant_categories(id) ON DELETE SET NULL,
    product_id UUID REFERENCES products(product_id) ON DELETE SET NULL,
    merchant_objection TEXT NOT NULL,
    recommended_pitch TEXT NOT NULL,
    incentive_offer VARCHAR(255),
    effectiveness_rating NUMERIC(3,2) DEFAULT 4.50,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS action_feedback_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recommendation_id UUID NOT NULL REFERENCES action_recommendations(action_id) ON DELETE CASCADE,
    dsp_id UUID NOT NULL REFERENCES dsps(dsp_id) ON DELETE CASCADE,
    is_accepted BOOLEAN NOT NULL,
    rejection_reason VARCHAR(64),
    feedback_notes TEXT,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- DOMAIN 8: FIELD EXECUTION, AUDITS & VISIT EVIDENCE (3 TABLES)
-- ------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS visit_logs (
    visit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dsp_id UUID NOT NULL REFERENCES dsps(dsp_id) ON DELETE CASCADE,
    outlet_id UUID NOT NULL REFERENCES outlets(outlet_id) ON DELETE CASCADE,
    visit_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    visit_type VARCHAR(32) DEFAULT 'SCHEDULED',
    outcome VARCHAR(32) DEFAULT 'COMPLETED',
    notes TEXT,
    duration_minutes INT DEFAULT 20,
    check_in_lat NUMERIC(10,6),
    check_in_lng NUMERIC(10,6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS merchandising_audit_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    visit_id UUID NOT NULL REFERENCES visit_logs(visit_id) ON DELETE CASCADE,
    collateral_id UUID REFERENCES qr_collaterals(id) ON DELETE SET NULL,
    audit_category VARCHAR(64) NOT NULL,
    is_compliant BOOLEAN NOT NULL,
    deficiency_reason VARCHAR(64),
    action_taken VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS outlet_photos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    visit_id UUID NOT NULL REFERENCES visit_logs(visit_id) ON DELETE CASCADE,
    outlet_id UUID NOT NULL REFERENCES outlets(outlet_id) ON DELETE CASCADE,
    photo_type VARCHAR(64) NOT NULL,
    photo_url VARCHAR(512) NOT NULL,
    ai_validation_label VARCHAR(64),
    ai_confidence_score NUMERIC(5,4),
    captured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- HIGH-PERFORMANCE INDEXES
-- ------------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_outlets_area_id ON outlets(area_id);
CREATE INDEX IF NOT EXISTS idx_outlets_merchant_id ON outlets(merchant_id);
CREATE INDEX IF NOT EXISTS idx_dsp_assignments_dsp ON dsp_outlet_assignments(dsp_id);
CREATE INDEX IF NOT EXISTS idx_dsp_assignments_outlet ON dsp_outlet_assignments(outlet_id);
CREATE INDEX IF NOT EXISTS idx_transactions_outlet ON transactions(outlet_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(txn_date);
CREATE INDEX IF NOT EXISTS idx_scores_outlet_date ON outlet_scores(outlet_id, score_date);
CREATE INDEX IF NOT EXISTS idx_scores_priority ON outlet_scores(priority_score DESC);
CREATE INDEX IF NOT EXISTS idx_actions_dsp_status ON action_recommendations(dsp_id, status);
CREATE INDEX IF NOT EXISTS idx_actions_outlet ON action_recommendations(outlet_id);
CREATE INDEX IF NOT EXISTS idx_visits_dsp_date ON visit_logs(dsp_id, visit_date);
CREATE INDEX IF NOT EXISTS idx_pos_hardware ON pos_terminals(outlet_id, hardware_status);
CREATE INDEX IF NOT EXISTS idx_collaterals_condition ON qr_collaterals(outlet_id, condition);
CREATE INDEX IF NOT EXISTS idx_liquidity_stockouts ON cash_in_liquidity_logs(outlet_id, float_stockout_occurred);
CREATE INDEX IF NOT EXISTS idx_metrics_outlet_date ON daily_outlet_metrics(outlet_id, metric_date);
