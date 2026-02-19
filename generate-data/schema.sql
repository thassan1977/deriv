-- =====================================================
-- smal schema for investigation
-- =====================================================

-- user with KYC data
CREATE TABLE users (
    user_id VARCHAR(50) PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    email VARCHAR(255),
    full_name VARCHAR(255),
    date_of_birth DATE,
    nationality VARCHAR(3), 
    
    -- Information
    declared_monthly_income DECIMAL(15,2),
    occupation VARCHAR(100),
    employment_status VARCHAR(50),
    source_of_funds VARCHAR(100),
    
    -- status
    account_status VARCHAR(20) DEFAULT 'ACTIVE', -- ACTIVE, SUSPENDED, BLOCKED, UNDER_REVIEW
    risk_level VARCHAR(20) DEFAULT 'LOW', -- LOW, MEDIUM, HIGH, CRITICAL
    kyc_status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, VERIFIED, REJECTED
    kyc_verified_at TIMESTAMP,
    
    -- stats
    total_deposits DECIMAL(15,2) DEFAULT 0,
    total_withdrawals DECIMAL(15,2) DEFAULT 0,
    transaction_count INTEGER DEFAULT 0,
    last_login_at TIMESTAMP
);

CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_risk_level ON users(risk_level);
CREATE INDEX idx_users_account_status ON users(account_status);

-- verify doc records
CREATE TABLE document_verifications (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(user_id),
    submitted_at TIMESTAMP DEFAULT NOW(),
    
    document_type VARCHAR(50), -- PASSPORT, DRIVERS_LICENSE, NATIONAL_ID, PROOF_OF_ADDRESS
    document_number VARCHAR(100),
    issuing_country VARCHAR(3),
    expiry_date DATE,
    
    -- AI verify results
    verification_status VARCHAR(20), -- PASSED, FAILED, MANUAL_REVIEW
    confidence_score DECIMAL(5,4), -- 0.0000 to 1.0000
    face_match_score DECIMAL(5,4), -- ID documents with photo
    
    -- fraude indicator
    is_forged BOOLEAN DEFAULT FALSE,
    is_ai_generated BOOLEAN DEFAULT FALSE,
    is_expired BOOLEAN DEFAULT FALSE,
    document_quality_score DECIMAL(5,4),
    
    -- flags details
    flags JSONB, -- {"blurry_image": true, "mismatched_data": false, "duplicate_detected": true}
    
    verified_by VARCHAR(100), -- AI_AUTO or investigator ID
    notes TEXT
);

CREATE INDEX idx_doc_verif_user_id ON document_verifications(user_id);
CREATE INDEX idx_doc_verif_status ON document_verifications(verification_status);

-- devices
CREATE TABLE devices (
    device_id VARCHAR(100) PRIMARY KEY,
    first_seen_at TIMESTAMP DEFAULT NOW(),
    last_seen_at TIMESTAMP DEFAULT NOW(),
    
    -- details
    device_type VARCHAR(50), -- MOBILE, DESKTOP, TABLET
    os VARCHAR(50), -- iOS, Android, Windows, macOS
    browser VARCHAR(50),
    browser_version VARCHAR(20),
    
    -- fingerprinting
    user_agent TEXT,
    screen_resolution VARCHAR(20),
    timezone VARCHAR(50),
    language VARCHAR(10),
    
    -- risk
    is_emulator BOOLEAN DEFAULT FALSE,
    is_vpn BOOLEAN DEFAULT FALSE,
    is_proxy BOOLEAN DEFAULT FALSE,
    is_tor BOOLEAN DEFAULT FALSE,
    
    -- use stats
    total_users_count INTEGER DEFAULT 1,
    flagged_users_count INTEGER DEFAULT 0
);

CREATE INDEX idx_devices_flagged_users ON devices(flagged_users_count);

-- user --> device map
CREATE TABLE user_devices (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(user_id),
    device_id VARCHAR(100) REFERENCES devices(device_id),
    first_used_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP DEFAULT NOW(),
    usage_count INTEGER DEFAULT 1,
    
    UNIQUE(user_id, device_id)
);

CREATE INDEX idx_user_devices_user_id ON user_devices(user_id);
CREATE INDEX idx_user_devices_device_id ON user_devices(device_id);

-- IP and geolocation
CREATE TABLE ip_addresses (
    ip_address VARCHAR(45) PRIMARY KEY,
    first_seen_at TIMESTAMP DEFAULT NOW(),
    last_seen_at TIMESTAMP DEFAULT NOW(),
    
    -- geo
    country_code VARCHAR(3),
    country_name VARCHAR(100),
    city VARCHAR(100),
    region VARCHAR(100),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    
    -- network info
    isp VARCHAR(255),
    organization VARCHAR(255),
    asn VARCHAR(50),
    
    -- risk
    is_vpn BOOLEAN DEFAULT FALSE,
    is_proxy BOOLEAN DEFAULT FALSE,
    is_tor BOOLEAN DEFAULT FALSE,
    is_datacenter BOOLEAN DEFAULT FALSE,
    is_anonymous BOOLEAN DEFAULT FALSE,
    
    -- sanctions
    is_sanctioned_country BOOLEAN DEFAULT FALSE,
    is_high_risk_country BOOLEAN DEFAULT FALSE,
    risk_score DECIMAL(5,4) DEFAULT 0,
    
    -- use stats
    total_users_count INTEGER DEFAULT 1,
    flagged_users_count INTEGER DEFAULT 0
);

CREATE INDEX idx_ip_country_code ON ip_addresses(country_code);
CREATE INDEX idx_ip_is_vpn ON ip_addresses(is_vpn);
CREATE INDEX idx_ip_flagged_users ON ip_addresses(flagged_users_count);

-- user -> ip map
CREATE TABLE user_ip_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(user_id),
    ip_address VARCHAR(45) REFERENCES ip_addresses(ip_address),
    device_id VARCHAR(100) REFERENCES devices(device_id),
    
    accessed_at TIMESTAMP DEFAULT NOW(),
    session_duration_seconds INTEGER
);

CREATE INDEX idx_user_ip_user_id ON user_ip_history(user_id);
CREATE INDEX idx_user_ip_ip_address ON user_ip_history(ip_address);
CREATE INDEX idx_user_ip_accessed_at ON user_ip_history(accessed_at);

-- transactions (deposits, withdrawals, trades)
CREATE TABLE transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- details
    transaction_type VARCHAR(20), -- DEPOSIT, WITHDRAWAL, TRADE
    amount DECIMAL(15,2),
    currency VARCHAR(10) DEFAULT 'USD',
    
    -- pay method
    payment_method VARCHAR(50), -- BANK_TRANSFER, CREDIT_CARD, CRYPTO, E_WALLET
    payment_provider VARCHAR(100),
    
    -- context
    ip_address VARCHAR(45) REFERENCES ip_addresses(ip_address),
    device_id VARCHAR(100) REFERENCES devices(device_id),
    country_code VARCHAR(3),
    
    -- status
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, COMPLETED, FAILED, REVERSED, FLAGGED
    completed_at TIMESTAMP,
    
    -- risk
    velocity_flag BOOLEAN DEFAULT FALSE, -- Rapid transactions
    amount_anomaly_flag BOOLEAN DEFAULT FALSE, -- Unusual amount
    geographic_anomaly_flag BOOLEAN DEFAULT FALSE -- Impossible travel
);

CREATE INDEX idx_txn_user_id ON transactions(user_id);
CREATE INDEX idx_txn_created_at ON transactions(created_at);
CREATE INDEX idx_txn_status ON transactions(status);
CREATE INDEX idx_txn_type ON transactions(transaction_type);

-- fraud rings
CREATE TABLE fraud_rings (
    fraud_ring_id VARCHAR(50) PRIMARY KEY,
    discovered_at TIMESTAMP DEFAULT NOW(),
    
    ring_name VARCHAR(255), -- Descriptive name
    fraud_type VARCHAR(50),
    
    -- net stats
    member_count INTEGER,
    total_accounts INTEGER,
    shared_devices INTEGER,
    shared_ips INTEGER,
    
    -- impact
    total_fraud_amount DECIMAL(15,2),
    estimated_losses DECIMAL(15,2),
    
    -- status
    status VARCHAR(20) DEFAULT 'ACTIVE', -- ACTIVE, MONITORING, NEUTRALIZED
    
    -- patern
    modus_operandi TEXT,
    common_indicators JSONB
);

CREATE INDEX idx_fraud_rings_status ON fraud_rings(status);

-- fraud history cases (for ML training and pattern matching)
CREATE TABLE historical_fraud_cases (
    id SERIAL PRIMARY KEY,
    case_id VARCHAR(50) UNIQUE NOT NULL,
    user_id VARCHAR(50) REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    
    -- classify
    fraud_type VARCHAR(50), -- IDENTITY_FRAUD, MONEY_LAUNDERING, ACCOUNT_TAKEOVER, SYNTHETIC_IDENTITY, etc.
    is_confirmed_fraud BOOLEAN, -- TRUE = confirmed fraud, FALSE = false positive
    
    -- ]detect
    detection_method VARCHAR(50), -- RULE_BASED, ML_MODEL, MANUAL_REVIEW, USER_REPORT
    initial_confidence DECIMAL(5,4),
    
    -- evidence
    fraud_indicators JSONB, -- All the signals that triggered detection
    involved_transactions TEXT[], -- Array of transaction IDs
    involved_devices TEXT[], -- Array of device IDs
    involved_ips TEXT[], -- Array of IP addresses
    
    -- net
    fraud_ring_id VARCHAR(50) REFERENCES fraud_rings(fraud_ring_id), -- If part of organized fraud ring
    related_user_ids TEXT[], -- Connected users
    
    -- result
    financial_loss DECIMAL(15,2) DEFAULT 0,
    recovered_amount DECIMAL(15,2) DEFAULT 0,
    
    -- iginvestigate 
    investigated_by VARCHAR(100),
    investigation_notes TEXT,
    resolution_notes TEXT
);

CREATE INDEX idx_hist_cases_user_id ON historical_fraud_cases(user_id);
CREATE INDEX idx_hist_cases_fraud_type ON historical_fraud_cases(fraud_type);
CREATE INDEX idx_hist_cases_is_confirmed ON historical_fraud_cases(is_confirmed_fraud);
CREATE INDEX idx_hist_cases_fraud_ring ON historical_fraud_cases(fraud_ring_id);

-- patern discover (new fraud patterns)
CREATE TABLE fraud_patterns (
    id SERIAL PRIMARY KEY,
    pattern_id VARCHAR(50) UNIQUE NOT NULL,
    discovered_at TIMESTAMP DEFAULT NOW(),
    
    pattern_name VARCHAR(255),
    pattern_type VARCHAR(50), -- EMERGING_THREAT, BEHAVIORAL_CLUSTER, NETWORK_PATTERN
    
    -- details
    description TEXT,
    affected_user_count INTEGER,
    sample_user_ids TEXT[],
    
    -- stat signature
    common_features JSONB, -- What makes this pattern unique
    statistical_significance DECIMAL(5,4),
    
    -- severe
    severity VARCHAR(20), -- LOW, MEDIUM, HIGH, CRITICAL
    estimated_risk_score DECIMAL(5,4),
    
    -- status
    status VARCHAR(20) DEFAULT 'MONITORING', -- MONITORING, CONFIRMED, FALSE_ALARM, MITIGATED
    confirmed_by VARCHAR(100),
    confirmed_at TIMESTAMP
);

CREATE INDEX idx_patterns_discovered_at ON fraud_patterns(discovered_at);
CREATE INDEX idx_patterns_severity ON fraud_patterns(severity);

-- realtime fraud cases
CREATE TABLE fraud_cases (
    id BIGSERIAL PRIMARY KEY,
    case_id VARCHAR(50) UNIQUE NOT NULL,
    user_id VARCHAR(50) REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- classify
    status VARCHAR(20) NOT NULL, -- AUTO_APPROVED, AUTO_BLOCKED, UNDER_INVESTIGATION, ESCALATED, RESOLVED
    confidence_score DECIMAL(5,4),
    fraud_probability DECIMAL(5,4),
    
    -- triger
    triggered_by VARCHAR(50), -- RULE_ENGINE, ML_MODEL, PATTERN_MATCH, MANUAL_FLAG
    trigger_transaction_id VARCHAR(50) REFERENCES transactions(transaction_id),
    
    -- detect signal
    detection_signals JSONB,
    transaction_summary JSONB,
    identity_flags JSONB,
    behavioral_flags JSONB,
    network_flags JSONB,
    
    -- investigate
    investigation_timeline JSONB,
    evidence JSONB,
    ai_reasoning TEXT,
    ai_recommendations TEXT,
    
    -- network analysis
    related_accounts INTEGER[],
    fraud_ring_id VARCHAR(50) REFERENCES fraud_rings(fraud_ring_id),
    
    -- human in the loop review
    assigned_to VARCHAR(100),
    human_decision VARCHAR(20),
    human_notes TEXT,
    resolved_at TIMESTAMP,
    
    -- perform tracking
    processing_time_ms INTEGER,
    investigation_layers TEXT[] -- ['RULE_BASED', 'ML_MODELS', 'LLM_REASONING']
);

CREATE INDEX idx_fraud_cases_status ON fraud_cases(status);
CREATE INDEX idx_fraud_cases_created_at ON fraud_cases(created_at);
CREATE INDEX idx_fraud_cases_user_id ON fraud_cases(user_id);
CREATE INDEX idx_fraud_cases_fraud_ring ON fraud_cases(fraud_ring_id);

-- Sanctions lists
CREATE TABLE sanctions_list (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(20), -- PERSON, ORGANIZATION, COUNTRY
    
    -- id
    full_name VARCHAR(255),
    aliases TEXT[],
    date_of_birth DATE,
    nationality VARCHAR(3),
    
    -- org details
    organization_name VARCHAR(255),
    
    -- Sanctions info
    sanctioning_body VARCHAR(100), -- OFAC, UN, EU, etc.
    sanction_type VARCHAR(100),
    listed_date DATE,
    
    risk_level VARCHAR(20)
);

CREATE INDEX idx_sanctions_full_name ON sanctions_list(full_name);
CREATE INDEX idx_sanctions_nationality ON sanctions_list(nationality);