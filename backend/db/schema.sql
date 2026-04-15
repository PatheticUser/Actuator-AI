-- ============================================================
-- Actuator AI — Full Database Schema
-- 21 tables simulating a real SaaS customer support platform
-- ============================================================

-- ==================== CORE BUSINESS ====================

CREATE TABLE IF NOT EXISTS customers (
    id              SERIAL PRIMARY KEY,
    company_name    VARCHAR(200) NOT NULL,
    industry        VARCHAR(100),
    company_size    VARCHAR(50),           -- '1-10', '11-50', '51-200', '201-500', '500+'
    region          VARCHAR(100),
    website         VARCHAR(255),
    status          VARCHAR(20) DEFAULT 'active',  -- active, churned, suspended, trial
    health_score    INTEGER DEFAULT 70,    -- 0-100
    mrr             DECIMAL(12,2) DEFAULT 0,       -- Monthly recurring revenue
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS customer_contacts (
    id              SERIAL PRIMARY KEY,
    customer_id     INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    name            VARCHAR(200) NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,
    phone           VARCHAR(30),
    role            VARCHAR(100),          -- CEO, CTO, DevOps Lead, etc.
    is_primary      BOOLEAN DEFAULT false,
    timezone        VARCHAR(50) DEFAULT 'Asia/Karachi',
    language        VARCHAR(10) DEFAULT 'en',
    last_login      TIMESTAMP,
    login_failures  INTEGER DEFAULT 0,
    account_locked  BOOLEAN DEFAULT false,
    two_factor_enabled BOOLEAN DEFAULT false,
    two_factor_method  VARCHAR(20),        -- totp, sms, email
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS products (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    slug            VARCHAR(50) UNIQUE NOT NULL,    -- free, pro, enterprise, enterprise_plus
    description     TEXT,
    price_monthly   DECIMAL(10,2) NOT NULL,
    price_yearly    DECIMAL(10,2),
    api_calls_limit INTEGER,
    storage_gb      INTEGER,
    support_tier    VARCHAR(30),           -- community, email, priority, dedicated
    features        JSONB DEFAULT '{}',
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id              SERIAL PRIMARY KEY,
    customer_id     INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    product_id      INTEGER REFERENCES products(id),
    status          VARCHAR(20) DEFAULT 'active',  -- active, cancelled, past_due, trialing
    billing_cycle   VARCHAR(10) DEFAULT 'monthly', -- monthly, yearly
    current_period_start TIMESTAMP,
    current_period_end   TIMESTAMP,
    cancel_at       TIMESTAMP,
    cancelled_reason VARCHAR(255),
    auto_renew      BOOLEAN DEFAULT true,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS api_usage (
    id              SERIAL PRIMARY KEY,
    customer_id     INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    month           VARCHAR(7) NOT NULL,   -- '2026-04'
    api_calls       INTEGER DEFAULT 0,
    storage_used_gb DECIMAL(6,2) DEFAULT 0,
    agent_sessions  INTEGER DEFAULT 0,
    webhook_events  INTEGER DEFAULT 0,
    overage_amount  DECIMAL(10,2) DEFAULT 0,
    recorded_at     TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS feature_flags (
    id              SERIAL PRIMARY KEY,
    customer_id     INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    feature_name    VARCHAR(100) NOT NULL,
    enabled         BOOLEAN DEFAULT false,
    enabled_at      TIMESTAMP,
    UNIQUE(customer_id, feature_name)
);

-- ==================== BILLING ====================

CREATE TABLE IF NOT EXISTS invoices (
    id              VARCHAR(20) PRIMARY KEY,       -- INV-2026-0401
    customer_id     INTEGER REFERENCES customers(id),
    subscription_id INTEGER REFERENCES subscriptions(id),
    amount          DECIMAL(12,2) NOT NULL,
    tax             DECIMAL(10,2) DEFAULT 0,
    total           DECIMAL(12,2) NOT NULL,
    currency        VARCHAR(3) DEFAULT 'PKR',
    status          VARCHAR(20) DEFAULT 'pending', -- pending, paid, overdue, void
    due_date        DATE,
    paid_at         TIMESTAMP,
    payment_method  VARCHAR(100),
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS invoice_line_items (
    id              SERIAL PRIMARY KEY,
    invoice_id      VARCHAR(20) REFERENCES invoices(id) ON DELETE CASCADE,
    description     VARCHAR(255) NOT NULL,
    quantity        INTEGER DEFAULT 1,
    unit_price      DECIMAL(10,2) NOT NULL,
    amount          DECIMAL(10,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS payments (
    id              VARCHAR(20) PRIMARY KEY,       -- PAY-xxxxx
    invoice_id      VARCHAR(20) REFERENCES invoices(id),
    customer_id     INTEGER REFERENCES customers(id),
    amount          DECIMAL(12,2) NOT NULL,
    currency        VARCHAR(3) DEFAULT 'PKR',
    method          VARCHAR(50),                   -- visa_4521, mastercard_8832, bank_transfer
    status          VARCHAR(20) DEFAULT 'completed', -- completed, failed, refunded
    gateway_ref     VARCHAR(100),
    processed_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS refunds (
    id              VARCHAR(20) PRIMARY KEY,       -- REF-xxxxx
    payment_id      VARCHAR(20) REFERENCES payments(id),
    customer_id     INTEGER REFERENCES customers(id),
    amount          DECIMAL(12,2) NOT NULL,
    reason          TEXT,
    status          VARCHAR(20) DEFAULT 'pending', -- pending, approved, processed, rejected
    approved_by     VARCHAR(100),
    requested_at    TIMESTAMP DEFAULT NOW(),
    processed_at    TIMESTAMP
);

-- ==================== SUPPORT ====================

CREATE TABLE IF NOT EXISTS support_tickets (
    id              VARCHAR(20) PRIMARY KEY,       -- TKT-xxxxx
    customer_id     INTEGER REFERENCES customers(id),
    contact_email   VARCHAR(255),
    category        VARCHAR(30) NOT NULL,          -- billing, technical, account, general, feature_request
    priority        VARCHAR(5) NOT NULL,           -- P1, P2, P3, P4
    subject         VARCHAR(300) NOT NULL,
    description     TEXT,
    status          VARCHAR(20) DEFAULT 'open',    -- open, in_progress, waiting, resolved, closed
    assigned_to     VARCHAR(100),
    sla_deadline    TIMESTAMP,
    first_response_at TIMESTAMP,
    resolved_at     TIMESTAMP,
    satisfaction    INTEGER,                        -- 1-5 CSAT
    tags            TEXT[],
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ticket_comments (
    id              SERIAL PRIMARY KEY,
    ticket_id       VARCHAR(20) REFERENCES support_tickets(id) ON DELETE CASCADE,
    author          VARCHAR(100) NOT NULL,         -- agent name or customer email
    author_type     VARCHAR(20) NOT NULL,          -- customer, agent, system
    content         TEXT NOT NULL,
    is_internal     BOOLEAN DEFAULT false,         -- internal notes vs customer-visible
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS conversations (
    id              VARCHAR(50) PRIMARY KEY,       -- UUID
    customer_id     INTEGER REFERENCES customers(id),
    customer_email  VARCHAR(255),
    channel         VARCHAR(20) DEFAULT 'web',     -- web, api, slack, email
    status          VARCHAR(20) DEFAULT 'active',  -- active, resolved, escalated, abandoned
    last_agent      VARCHAR(100),
    summary         TEXT,
    started_at      TIMESTAMP DEFAULT NOW(),
    ended_at        TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id              SERIAL PRIMARY KEY,
    conversation_id VARCHAR(50) REFERENCES conversations(id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL,           -- user, assistant, system, tool
    content         TEXT NOT NULL,
    agent_name      VARCHAR(100),
    tool_calls      JSONB,
    tokens_used     INTEGER,
    latency_ms      INTEGER,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ==================== KNOWLEDGE & OPS ====================

CREATE TABLE IF NOT EXISTS knowledge_articles (
    id              SERIAL PRIMARY KEY,
    title           VARCHAR(300) NOT NULL,
    slug            VARCHAR(100) UNIQUE,
    category        VARCHAR(50) NOT NULL,          -- api, sdk, billing, security, deployment, integrations
    content         TEXT NOT NULL,
    tags            TEXT[],
    views           INTEGER DEFAULT 0,
    helpful_votes   INTEGER DEFAULT 0,
    is_published    BOOLEAN DEFAULT true,
    last_updated_by VARCHAR(100),
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS escalations (
    id              VARCHAR(20) PRIMARY KEY,        -- ESC-xxxxx
    ticket_id       VARCHAR(20) REFERENCES support_tickets(id),
    conversation_id VARCHAR(50) REFERENCES conversations(id),
    customer_id     INTEGER REFERENCES customers(id),
    reason          TEXT NOT NULL,
    severity        VARCHAR(10) NOT NULL,           -- critical, high, medium
    assigned_to     VARCHAR(100),
    status          VARCHAR(20) DEFAULT 'open',     -- open, acknowledged, resolved
    resolution      TEXT,
    created_at      TIMESTAMP DEFAULT NOW(),
    resolved_at     TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications_log (
    id              SERIAL PRIMARY KEY,
    recipient       VARCHAR(255) NOT NULL,
    channel         VARCHAR(20) NOT NULL,           -- email, slack, webhook, sms
    event_type      VARCHAR(50) NOT NULL,           -- ticket_created, payment_received, etc.
    subject         VARCHAR(300),
    content         TEXT,
    status          VARCHAR(20) DEFAULT 'sent',     -- sent, failed, queued
    sent_at         TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agents_config (
    id              SERIAL PRIMARY KEY,
    agent_key       VARCHAR(50) UNIQUE NOT NULL,
    display_name    VARCHAR(100) NOT NULL,
    description     TEXT,
    model_name      VARCHAR(100) DEFAULT 'qwen2.5:7b',
    temperature     DECIMAL(3,2) DEFAULT 0.20,
    max_tokens      INTEGER DEFAULT 1000,
    is_active       BOOLEAN DEFAULT true,
    total_requests  INTEGER DEFAULT 0,
    avg_latency_ms  INTEGER DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ==================== SECURITY & AUDIT ====================

CREATE TABLE IF NOT EXISTS security_events (
    id              SERIAL PRIMARY KEY,
    contact_email   VARCHAR(255) NOT NULL,
    event_type      VARCHAR(50) NOT NULL,           -- login_success, login_failed, 2fa_verified, password_changed, account_locked, account_unlocked
    ip_address      VARCHAR(45),
    user_agent      VARCHAR(500),
    location        VARCHAR(100),
    details         JSONB DEFAULT '{}',
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id              SERIAL PRIMARY KEY,
    conversation_id VARCHAR(50),
    agent_name      VARCHAR(100) NOT NULL,
    action          VARCHAR(50) NOT NULL,           -- response_generated, tool_called, handoff, guardrail_triggered
    input_summary   TEXT,
    output_summary  TEXT,
    hallucination_risk VARCHAR(10),                 -- low, medium, high
    policy_compliant   BOOLEAN DEFAULT true,
    quality_score   INTEGER,                        -- 0-100
    latency_ms      INTEGER,
    tokens_used     INTEGER,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS feedback (
    id              SERIAL PRIMARY KEY,
    conversation_id VARCHAR(50) REFERENCES conversations(id),
    customer_id     INTEGER REFERENCES customers(id),
    rating          INTEGER CHECK (rating >= 1 AND rating <= 5),
    nps_score       INTEGER CHECK (nps_score >= 0 AND nps_score <= 10),
    comment         TEXT,
    agent_name      VARCHAR(100),
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ==================== INDEXES ====================

CREATE INDEX IF NOT EXISTS idx_contacts_customer ON customer_contacts(customer_id);
CREATE INDEX IF NOT EXISTS idx_contacts_email ON customer_contacts(email);
CREATE INDEX IF NOT EXISTS idx_subscriptions_customer ON subscriptions(customer_id);
CREATE INDEX IF NOT EXISTS idx_invoices_customer ON invoices(customer_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON support_tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_priority ON support_tickets(priority);
CREATE INDEX IF NOT EXISTS idx_tickets_customer ON support_tickets(customer_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_security_email ON security_events(contact_email);
CREATE INDEX IF NOT EXISTS idx_security_type ON security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_agent ON audit_logs(agent_name);
CREATE INDEX IF NOT EXISTS idx_audit_conversation ON audit_logs(conversation_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_customer ON api_usage(customer_id);
CREATE INDEX IF NOT EXISTS idx_kb_category ON knowledge_articles(category);
