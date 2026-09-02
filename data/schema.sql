-- Schema for Sales Coach AI

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ENUMs
CREATE TYPE business_type AS ENUM ('sari_sari', 'pharmacy', 'convenience', 'hardware', 'general_merchandise', 'food_stall');
CREATE TYPE outlet_status AS ENUM ('active', 'inactive', 'suspended', 'churned');
CREATE TYPE dsp_role AS ENUM ('dsp', 'manager', 'admin');
CREATE TYPE txn_type AS ENUM ('cash_in', 'cash_out', 'bills_pay', 'buy_load', 'send_money', 'pay_qr');
CREATE TYPE action_status AS ENUM ('pending', 'in_progress', 'completed', 'skipped');

-- Tables
CREATE TABLE areas (
    area_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    area_name VARCHAR NOT NULL,
    region VARCHAR NOT NULL,
    manager_id UUID -- Foreign key set later to dsps
);

CREATE TABLE dsps (
    dsp_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    role dsp_role NOT NULL,
    area_id UUID REFERENCES areas(area_id),
    manager_id UUID REFERENCES dsps(dsp_id),
    hire_date DATE,
    status VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE areas ADD CONSTRAINT fk_manager FOREIGN KEY (manager_id) REFERENCES dsps(dsp_id);

CREATE TABLE merchants (
    merchant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_name VARCHAR NOT NULL,
    owner_name VARCHAR,
    business_type business_type,
    kyc_status VARCHAR,
    onboarded_date DATE,
    risk_tier VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE outlets (
    outlet_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id UUID REFERENCES merchants(merchant_id) ON DELETE CASCADE,
    outlet_name VARCHAR NOT NULL,
    address VARCHAR,
    city VARCHAR,
    region VARCHAR,
    latitude FLOAT,
    longitude FLOAT,
    outlet_type VARCHAR,
    status outlet_status NOT NULL,
    area_id UUID REFERENCES areas(area_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE transactions (
    txn_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    outlet_id UUID REFERENCES outlets(outlet_id) ON DELETE CASCADE,
    product_id UUID, -- Foreign key set later
    txn_type txn_type NOT NULL,
    amount NUMERIC NOT NULL,
    txn_date TIMESTAMP NOT NULL,
    status VARCHAR NOT NULL
);

CREATE TABLE visit_logs (
    visit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dsp_id UUID REFERENCES dsps(dsp_id),
    outlet_id UUID REFERENCES outlets(outlet_id) ON DELETE CASCADE,
    visit_date TIMESTAMP NOT NULL,
    visit_type VARCHAR,
    outcome VARCHAR,
    notes TEXT,
    duration_minutes INT
);

CREATE TABLE products (
    product_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_name VARCHAR NOT NULL,
    category VARCHAR,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

ALTER TABLE transactions ADD CONSTRAINT fk_product FOREIGN KEY (product_id) REFERENCES products(product_id);

CREATE TABLE outlet_products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    outlet_id UUID REFERENCES outlets(outlet_id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(product_id) ON DELETE CASCADE,
    activation_date DATE,
    status VARCHAR NOT NULL
);

CREATE TABLE outlet_scores (
    score_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    outlet_id UUID REFERENCES outlets(outlet_id) ON DELETE CASCADE,
    priority_score FLOAT NOT NULL,
    contributing_factors JSONB,
    score_date DATE NOT NULL,
    model_version VARCHAR
);

CREATE TABLE action_recommendations (
    action_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    outlet_id UUID REFERENCES outlets(outlet_id) ON DELETE CASCADE,
    dsp_id UUID REFERENCES dsps(dsp_id),
    action_type VARCHAR NOT NULL,
    action_detail TEXT,
    status action_status DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    completion_notes TEXT
);

CREATE TABLE dsp_outlet_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dsp_id UUID REFERENCES dsps(dsp_id) ON DELETE CASCADE,
    outlet_id UUID REFERENCES outlets(outlet_id) ON DELETE CASCADE,
    assigned_date DATE DEFAULT CURRENT_DATE,
    is_primary BOOLEAN DEFAULT TRUE
);

CREATE TABLE user_accounts (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    role VARCHAR NOT NULL,
    linked_dsp_id UUID REFERENCES dsps(dsp_id),
    status VARCHAR,
    last_login TIMESTAMP
);

CREATE TABLE conversations (
    conversation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES user_accounts(user_id),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    messages JSONB,
    status VARCHAR
);

-- Indexes
CREATE INDEX idx_outlets_merchant_id ON outlets(merchant_id);
CREATE INDEX idx_outlets_area_id ON outlets(area_id);
CREATE INDEX idx_transactions_outlet_id ON transactions(outlet_id);
CREATE INDEX idx_visit_logs_dsp_id ON visit_logs(dsp_id);
CREATE INDEX idx_visit_logs_outlet_id ON visit_logs(outlet_id);
CREATE INDEX idx_action_recommendations_dsp_id ON action_recommendations(dsp_id);
CREATE INDEX idx_dsp_outlet_assignments_dsp_id ON dsp_outlet_assignments(dsp_id);

-- RLS Policies
ALTER TABLE outlets ENABLE ROW LEVEL SECURITY;
ALTER TABLE merchants ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE visit_logs ENABLE ROW LEVEL SECURITY;

-- Admins can see everything
CREATE POLICY admin_all ON outlets FOR ALL TO PUBLIC USING (current_setting('app.role', true) = 'admin');
CREATE POLICY admin_all_merchants ON merchants FOR ALL TO PUBLIC USING (current_setting('app.role', true) = 'admin');

-- Managers can see outlets in their area
CREATE POLICY manager_outlets ON outlets FOR SELECT TO PUBLIC
    USING (current_setting('app.role', true) = 'manager' AND area_id = current_setting('app.area_id', true)::UUID);

-- DSPs can see their assigned outlets
CREATE POLICY dsp_outlets ON outlets FOR SELECT TO PUBLIC
    USING (current_setting('app.role', true) = 'dsp' AND outlet_id IN (
        SELECT outlet_id FROM dsp_outlet_assignments WHERE dsp_id = current_setting('app.dsp_id', true)::UUID
    ));
