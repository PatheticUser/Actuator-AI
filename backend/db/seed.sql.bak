-- ============================================================
-- Actuator AI — Seed Data
-- Realistic SaaS customer support platform data
-- ============================================================

-- ==================== PRODUCTS ====================
INSERT INTO products (name, slug, description, price_monthly, price_yearly, api_calls_limit, storage_gb, support_tier, features) VALUES
('Free Tier', 'free', 'Basic access for individuals and small experiments', 0, 0, 500, 1, 'community', '{"agents": 1, "handoffs": false, "guardrails": false, "audit": false}'),
('Pro', 'pro', 'For startups and growing teams needing production features', 4900, 49000, 10000, 10, 'email', '{"agents": 5, "handoffs": true, "guardrails": true, "audit": false}'),
('Enterprise', 'enterprise', 'Full platform access with priority support and SLAs', 29900, 299000, 50000, 50, 'priority', '{"agents": 20, "handoffs": true, "guardrails": true, "audit": true}'),
('Enterprise Plus', 'enterprise_plus', 'Custom deployments, dedicated CSM, SOC2 compliance', 89900, 899000, 200000, 500, 'dedicated', '{"agents": "unlimited", "handoffs": true, "guardrails": true, "audit": true, "sla": "99.99%", "custom_models": true}');

-- ==================== CUSTOMERS ====================
INSERT INTO customers (id, company_name, industry, company_size, region, website, status, health_score, mrr, created_at) VALUES
(1, 'TechVista Solutions', 'Software Development', '51-200', 'South Asia', 'https://techvista.pk', 'active', 92, 29900, '2025-01-15'),
(2, 'NovaByte', 'AI/ML Startup', '1-10', 'South Asia', 'https://novabyte.io', 'active', 58, 4900, '2026-01-10'),
(3, 'CloudMatrix Ltd', 'Cloud Infrastructure', '201-500', 'Middle East', 'https://cloudmatrix.ae', 'active', 87, 89900, '2024-06-20'),
(4, 'DataPulse Analytics', 'Data Analytics', '11-50', 'South Asia', 'https://datapulse.pk', 'active', 45, 4900, '2025-06-01'),
(5, 'Meridian Healthcare', 'Healthcare Tech', '51-200', 'South Asia', 'https://meridianhealth.pk', 'active', 78, 29900, '2025-03-12'),
(6, 'PixelForge Studios', 'Gaming', '11-50', 'Southeast Asia', 'https://pixelforge.sg', 'trial', 65, 0, '2026-03-28'),
(7, 'AgriSmart', 'AgriTech', '1-10', 'South Asia', 'https://agrismart.pk', 'churned', 15, 0, '2025-08-15'),
(8, 'FinEdge Capital', 'Fintech', '201-500', 'Middle East', 'https://finedge.ae', 'active', 95, 89900, '2024-02-10'),
(9, 'EduNova Platform', 'EdTech', '11-50', 'South Asia', 'https://edunova.pk', 'active', 72, 4900, '2025-11-01'),
(10, 'LogiTrack Systems', 'Logistics', '51-200', 'South Asia', 'https://logitrack.pk', 'suspended', 30, 0, '2025-04-22');

SELECT setval('customers_id_seq', 10);

-- ==================== CUSTOMER CONTACTS ====================
INSERT INTO customer_contacts (customer_id, name, email, phone, role, is_primary, timezone, language, last_login, login_failures, account_locked, two_factor_enabled, two_factor_method) VALUES
(1, 'Ahmed Hassan', 'ahmed@techvista.pk', '+92-321-5551234', 'CTO', true, 'Asia/Karachi', 'en', '2026-04-12 14:32:00', 0, false, true, 'totp'),
(1, 'Fatima Zahra', 'fatima@techvista.pk', '+92-300-5554567', 'DevOps Lead', false, 'Asia/Karachi', 'en', '2026-04-11 09:15:00', 0, false, true, 'totp'),
(1, 'Usman Ali', 'usman@techvista.pk', '+92-333-5557890', 'Backend Engineer', false, 'Asia/Karachi', 'en', '2026-04-10 16:20:00', 1, false, false, NULL),
(2, 'Sara Khan', 'sara@novabyte.io', '+92-312-5552345', 'CEO & Founder', true, 'Asia/Karachi', 'en', '2026-04-11 09:15:00', 2, false, false, NULL),
(3, 'Omar Al-Rashid', 'omar@cloudmatrix.ae', '+971-50-5551234', 'VP Engineering', true, 'Asia/Dubai', 'ar', '2026-04-12 10:00:00', 0, false, true, 'totp'),
(3, 'Layla Ibrahim', 'layla@cloudmatrix.ae', '+971-55-5556789', 'Platform Architect', false, 'Asia/Dubai', 'en', '2026-04-12 11:30:00', 0, false, true, 'sms'),
(4, 'Bilal Mahmood', 'bilal@datapulse.pk', '+92-345-5553456', 'Founder', true, 'Asia/Karachi', 'ur', '2026-04-10 23:45:00', 5, true, false, NULL),
(5, 'Dr. Ayesha Siddiqui', 'ayesha@meridianhealth.pk', '+92-300-5558901', 'CIO', true, 'Asia/Karachi', 'en', '2026-04-12 08:00:00', 0, false, true, 'email'),
(6, 'Tan Wei Lin', 'weilin@pixelforge.sg', '+65-9123-4567', 'Technical Director', true, 'Asia/Singapore', 'zh', '2026-04-09 15:30:00', 0, false, false, NULL),
(7, 'Hamza Rafi', 'hamza@agrismart.pk', '+92-321-5559012', 'CEO', true, 'Asia/Karachi', 'ur', '2026-03-01 10:00:00', 0, false, false, NULL),
(8, 'Khalid Al-Mansoor', 'khalid@finedge.ae', '+971-50-5559876', 'CISO', true, 'Asia/Dubai', 'ar', '2026-04-12 16:45:00', 0, false, true, 'totp'),
(8, 'Priya Sharma', 'priya@finedge.ae', '+971-55-5553210', 'Head of Engineering', false, 'Asia/Dubai', 'en', '2026-04-12 12:00:00', 0, false, true, 'totp'),
(9, 'Zainab Bukhari', 'zainab@edunova.pk', '+92-311-5554321', 'Product Manager', true, 'Asia/Karachi', 'en', '2026-04-11 14:00:00', 1, false, false, NULL),
(10, 'Tariq Hussain', 'tariq@logitrack.pk', '+92-333-5551111', 'Operations Director', true, 'Asia/Karachi', 'en', '2026-03-15 09:00:00', 8, true, false, NULL);

-- ==================== SUBSCRIPTIONS ====================
INSERT INTO subscriptions (customer_id, product_id, status, billing_cycle, current_period_start, current_period_end, auto_renew) VALUES
(1, 3, 'active', 'monthly', '2026-04-01', '2026-05-01', true),
(2, 2, 'active', 'monthly', '2026-04-10', '2026-05-10', true),
(3, 4, 'active', 'yearly', '2026-01-01', '2027-01-01', true),
(4, 2, 'active', 'monthly', '2026-04-01', '2026-05-01', false),
(5, 3, 'active', 'yearly', '2026-01-12', '2027-01-12', true),
(6, 1, 'trialing', 'monthly', '2026-03-28', '2026-04-28', false),
(7, 2, 'cancelled', 'monthly', '2025-08-15', '2026-02-15', false),
(8, 4, 'active', 'yearly', '2026-01-01', '2027-01-01', true),
(9, 2, 'active', 'monthly', '2026-04-01', '2026-05-01', true),
(10, 3, 'past_due', 'monthly', '2026-03-22', '2026-04-22', true);

-- ==================== API USAGE ====================
INSERT INTO api_usage (customer_id, month, api_calls, storage_used_gb, agent_sessions, webhook_events, overage_amount) VALUES
(1, '2026-01', 42150, 18.5, 1105, 3200, 0),
(1, '2026-02', 44800, 20.1, 1210, 3500, 0),
(1, '2026-03', 48300, 22.8, 1340, 3800, 0),
(1, '2026-04', 45230, 23.1, 1247, 3650, 0),
(2, '2026-01', 3200, 1.8, 85, 120, 0),
(2, '2026-02', 2800, 2.1, 72, 95, 0),
(2, '2026-03', 2400, 2.0, 58, 70, 0),
(2, '2026-04', 2100, 1.9, 45, 50, 0),
(3, '2026-04', 156000, 120.5, 4500, 12000, 0),
(4, '2026-04', 1200, 0.8, 30, 15, 0),
(5, '2026-04', 35000, 15.2, 890, 2100, 0),
(8, '2026-04', 189000, 245.0, 6200, 18000, 0),
(9, '2026-04', 5600, 3.2, 210, 450, 0);

-- ==================== FEATURE FLAGS ====================
INSERT INTO feature_flags (customer_id, feature_name, enabled, enabled_at) VALUES
(1, 'api_integration', true, '2025-01-20'),
(1, 'dashboard', true, '2025-01-20'),
(1, 'webhooks', true, '2025-06-15'),
(1, 'multi_agent_handoffs', true, '2025-09-01'),
(1, 'custom_guardrails', false, NULL),
(1, 'analytics_export', false, NULL),
(2, 'api_integration', true, '2026-01-15'),
(2, 'dashboard', true, '2026-01-15'),
(2, 'webhooks', false, NULL),
(2, 'multi_agent_handoffs', false, NULL),
(3, 'api_integration', true, '2024-07-01'),
(3, 'dashboard', true, '2024-07-01'),
(3, 'webhooks', true, '2024-07-01'),
(3, 'multi_agent_handoffs', true, '2024-10-01'),
(3, 'custom_guardrails', true, '2025-01-15'),
(3, 'analytics_export', true, '2025-03-01'),
(3, 'custom_models', true, '2025-06-01'),
(8, 'api_integration', true, '2024-02-15'),
(8, 'dashboard', true, '2024-02-15'),
(8, 'webhooks', true, '2024-03-01'),
(8, 'multi_agent_handoffs', true, '2024-05-01'),
(8, 'custom_guardrails', true, '2024-06-01'),
(8, 'analytics_export', true, '2024-07-01'),
(8, 'custom_models', true, '2024-09-01');

-- ==================== INVOICES ====================
INSERT INTO invoices (id, customer_id, subscription_id, amount, tax, total, currency, status, due_date, paid_at, payment_method) VALUES
('INV-2026-0101', 1, 1, 29900, 0, 29900, 'PKR', 'paid', '2026-01-05', '2026-01-01 10:00:00', 'Visa ***4521'),
('INV-2026-0201', 1, 1, 29900, 0, 29900, 'PKR', 'paid', '2026-02-05', '2026-02-01 10:15:00', 'Visa ***4521'),
('INV-2026-0301', 1, 1, 29900, 0, 29900, 'PKR', 'paid', '2026-03-05', '2026-03-01 09:45:00', 'Visa ***4521'),
('INV-2026-0401', 1, 1, 29900, 0, 29900, 'PKR', 'paid', '2026-04-05', '2026-04-01 10:30:00', 'Visa ***4521'),
('INV-2026-0210', 2, 2, 4900, 0, 4900, 'PKR', 'paid', '2026-02-15', '2026-02-16 14:20:00', 'Mastercard ***8832'),
('INV-2026-0310', 2, 2, 4900, 0, 4900, 'PKR', 'paid', '2026-03-15', '2026-03-15 09:10:00', 'Mastercard ***8832'),
('INV-2026-0410', 2, 2, 4900, 0, 4900, 'PKR', 'pending', '2026-04-15', NULL, NULL),
('INV-2026-0103', 3, 3, 899000, 0, 899000, 'AED', 'paid', '2026-01-05', '2026-01-02 08:00:00', 'Bank Transfer'),
('INV-2026-0404', 4, 4, 4900, 0, 4900, 'PKR', 'overdue', '2026-04-05', NULL, NULL),
('INV-2026-0105', 5, 5, 299000, 0, 299000, 'PKR', 'paid', '2026-01-15', '2026-01-12 11:00:00', 'Visa ***7733'),
('INV-2026-0108', 8, 8, 899000, 0, 899000, 'AED', 'paid', '2026-01-05', '2026-01-01 07:00:00', 'Bank Transfer ***ADCB'),
('INV-2026-0410-LT', 10, 10, 29900, 0, 29900, 'PKR', 'overdue', '2026-04-01', NULL, NULL);

-- ==================== INVOICE LINE ITEMS ====================
INSERT INTO invoice_line_items (invoice_id, description, quantity, unit_price, amount) VALUES
('INV-2026-0401', 'Enterprise Plan - April 2026', 1, 29900, 29900),
('INV-2026-0310', 'Pro Plan - March 2026', 1, 4900, 4900),
('INV-2026-0410', 'Pro Plan - April 2026', 1, 4900, 4900),
('INV-2026-0103', 'Enterprise Plus Plan - Annual 2026', 1, 899000, 899000),
('INV-2026-0404', 'Pro Plan - April 2026', 1, 4900, 4900),
('INV-2026-0105', 'Enterprise Plan - Annual 2026', 1, 299000, 299000),
('INV-2026-0108', 'Enterprise Plus Plan - Annual 2026', 1, 899000, 899000);

-- ==================== PAYMENTS ====================
INSERT INTO payments (id, invoice_id, customer_id, amount, currency, method, status, gateway_ref) VALUES
('PAY-00001', 'INV-2026-0401', 1, 29900, 'PKR', 'visa_4521', 'completed', 'ch_3Nq2iRK9x'),
('PAY-00002', 'INV-2026-0301', 1, 29900, 'PKR', 'visa_4521', 'completed', 'ch_3Np1hQJ8w'),
('PAY-00003', 'INV-2026-0310', 2, 4900, 'PKR', 'mastercard_8832', 'completed', 'ch_3Nr4kSL2y'),
('PAY-00004', 'INV-2026-0103', 3, 899000, 'AED', 'bank_transfer', 'completed', 'bt_AE20260102'),
('PAY-00005', 'INV-2026-0105', 5, 299000, 'PKR', 'visa_7733', 'completed', 'ch_3Ns5mTM3z'),
('PAY-00006', 'INV-2026-0108', 8, 899000, 'AED', 'bank_transfer_adcb', 'completed', 'bt_AE20260101'),
('PAY-00007', 'INV-2026-0201', 1, 29900, 'PKR', 'visa_4521', 'completed', 'ch_3No0gPI7v'),
('PAY-00008', 'INV-2026-0101', 1, 29900, 'PKR', 'visa_4521', 'completed', 'ch_3Nn9fOH6u'),
('PAY-00009', 'INV-2026-0210', 2, 4900, 'PKR', 'mastercard_8832', 'completed', 'ch_3Nq3jRK0x');

-- ==================== REFUNDS ====================
INSERT INTO refunds (id, payment_id, customer_id, amount, reason, status, approved_by, requested_at, processed_at) VALUES
('REF-00001', 'PAY-00009', 2, 4900, 'Service outage affected customer for 3 days in February', 'processed', 'billing_manager', '2026-02-20 10:00:00', '2026-02-22 14:00:00'),
('REF-00002', 'PAY-00002', 1, 5000, 'Goodwill credit for API degradation on March 5', 'processed', 'csm_bilal', '2026-03-06 09:00:00', '2026-03-07 11:00:00'),
('REF-00003', 'PAY-00003', 2, 2450, 'Prorated refund for downgrade mid-cycle', 'pending', NULL, '2026-04-10 15:00:00', NULL);

-- ==================== SUPPORT TICKETS ====================
INSERT INTO support_tickets (id, customer_id, contact_email, category, priority, subject, description, status, assigned_to, sla_deadline, first_response_at, resolved_at, satisfaction, tags, created_at) VALUES
('TKT-00142', 1, 'ahmed@techvista.pk', 'billing', 'P3', 'Invoice discrepancy for March', 'March invoice shows charge but payment was already made on March 1st. Need clarification.', 'resolved', 'Finance Team', '2026-04-13 10:00:00', '2026-04-12 11:30:00', '2026-04-12 15:00:00', 4, ARRAY['billing', 'invoice'], '2026-04-12 10:00:00'),
('TKT-00256', 2, 'sara@novabyte.io', 'technical', 'P2', 'API returning 502 errors intermittently', 'Since yesterday our API calls to /v1/agents/run are returning 502 about 12% of the time. Retry logic helps but latency increased 5x.', 'in_progress', 'Engineering Team', '2026-04-13 06:00:00', '2026-04-12 14:45:00', NULL, NULL, ARRAY['api', 'error', 'production'], '2026-04-12 14:30:00'),
('TKT-00389', 4, 'bilal@datapulse.pk', 'account', 'P1', 'Account locked - cannot access platform', 'My account is locked after failed login attempts. I need access urgently for a client demo tomorrow.', 'open', 'Account Team', '2026-04-13 00:00:00', NULL, NULL, NULL, ARRAY['locked', 'urgent', 'access'], '2026-04-12 23:45:00'),
('TKT-00412', 5, 'ayesha@meridianhealth.pk', 'technical', 'P2', 'Webhook delivery failures since April 10', 'Our webhook endpoint is healthy but we stopped receiving events on April 10. No changes on our end.', 'in_progress', 'Engineering Team', '2026-04-13 08:00:00', '2026-04-12 09:00:00', NULL, NULL, ARRAY['webhook', 'integration'], '2026-04-11 08:00:00'),
('TKT-00478', 3, 'omar@cloudmatrix.ae', 'feature_request', 'P4', 'Request: Custom model deployment support', 'We want to deploy our fine-tuned Llama model on your infrastructure. Is this on the roadmap?', 'open', 'Product Team', '2026-04-20 00:00:00', NULL, NULL, NULL, ARRAY['feature_request', 'custom_models'], '2026-04-12 10:00:00'),
('TKT-00501', 8, 'khalid@finedge.ae', 'general', 'P3', 'SOC2 compliance documentation request', 'For our annual audit we need updated SOC2 Type II report and data processing agreement.', 'waiting', 'Compliance Team', '2026-04-15 00:00:00', '2026-04-12 16:00:00', NULL, NULL, ARRAY['compliance', 'soc2', 'enterprise'], '2026-04-12 15:30:00'),
('TKT-00523', 9, 'zainab@edunova.pk', 'billing', 'P3', 'Want to upgrade from Pro to Enterprise', 'We are scaling and need more API calls and priority support. Can you help with enterprise pricing?', 'open', 'Sales Team', '2026-04-14 00:00:00', NULL, NULL, NULL, ARRAY['upgrade', 'sales'], '2026-04-13 02:00:00'),
('TKT-00540', 10, 'tariq@logitrack.pk', 'billing', 'P1', 'Account suspended - payment issue', 'Our account was suspended but we sent bank transfer 5 days ago. Transaction ref: BT-LT-20260408.', 'open', 'Finance Team', '2026-04-13 04:00:00', NULL, NULL, NULL, ARRAY['suspended', 'payment', 'urgent'], '2026-04-13 03:00:00'),
('TKT-00198', 1, 'fatima@techvista.pk', 'technical', 'P3', 'SDK v2.1 incompatible with Python 3.13', 'After upgrading to Python 3.13, import errors in actuator-sdk. Traceback attached.', 'resolved', 'Engineering Team', '2026-04-10 00:00:00', '2026-04-09 10:00:00', '2026-04-09 16:30:00', 5, ARRAY['sdk', 'python', 'compatibility'], '2026-04-09 09:00:00');

-- ==================== TICKET COMMENTS ====================
INSERT INTO ticket_comments (ticket_id, author, author_type, content, is_internal, created_at) VALUES
('TKT-00256', 'sara@novabyte.io', 'customer', 'Here are the error logs from our monitoring: 502 Bad Gateway, upstream timeout after 30s.', false, '2026-04-12 14:35:00'),
('TKT-00256', 'Technical Specialist', 'agent', 'Investigating user-service. Identified connection pool exhaustion as root cause. Engineering ticket ENG-0042 created.', false, '2026-04-12 14:50:00'),
('TKT-00256', 'usman@techvista.pk', 'agent', 'Internal: user-service memory at 89%. Need to increase replica count from 3 to 5.', true, '2026-04-12 15:00:00'),
('TKT-00142', 'ahmed@techvista.pk', 'customer', 'I can see the payment was deducted from my bank on March 1st but invoice still shows pending.', false, '2026-04-12 10:15:00'),
('TKT-00142', 'Billing & Finance Agent', 'agent', 'Confirmed payment PAY-00002 received on March 1. Invoice status corrected. Apologies for confusion.', false, '2026-04-12 11:30:00'),
('TKT-00389', 'bilal@datapulse.pk', 'customer', 'This is really urgent. I have a client demo at 10 AM tomorrow and I literally cannot log in.', false, '2026-04-12 23:50:00'),
('TKT-00412', 'ayesha@meridianhealth.pk', 'customer', 'Our webhook URL is https://api.meridianhealth.pk/webhooks/actuator. We verified it responds 200.', false, '2026-04-11 08:15:00'),
('TKT-00412', 'Technical Specialist', 'agent', 'Found issue: webhook retry queue was stuck due to a failed DNS resolution on April 10. Queue cleared, events replaying now.', false, '2026-04-12 09:00:00'),
('TKT-00198', 'Technical Specialist', 'agent', 'SDK v2.1.1 hotfix released with Python 3.13 compatibility. Please update: pip install actuator-sdk==2.1.1', false, '2026-04-09 16:30:00'),
('TKT-00198', 'fatima@techvista.pk', 'customer', 'Confirmed working. Thanks for the quick fix!', false, '2026-04-09 17:00:00');

-- ==================== KNOWLEDGE ARTICLES ====================
INSERT INTO knowledge_articles (title, slug, category, content, tags, views, helpful_votes, is_published, last_updated_by) VALUES
('API Authentication Guide', 'api-auth-guide', 'api', 'Use Bearer token in Authorization header. Tokens expire in 24h. Refresh via POST /api/v1/auth/refresh with your refresh_token in the request body. Never expose tokens in client-side code. For server-to-server, use API keys instead (Settings > API Keys). Rate limits apply per token.', ARRAY['auth', 'api', 'tokens'], 1250, 89, true, 'docs_team'),
('Rate Limiting & Quotas', 'rate-limits', 'api', 'Rate limits by plan: Free=500/min, Pro=10,000/min, Enterprise=50,000/min, Enterprise+=200,000/min. HTTP 429 means limit exceeded. Response includes Retry-After header. Implement exponential backoff. Burst allowance: 2x limit for 10 seconds.', ARRAY['rate-limit', 'api', 'quotas'], 2100, 156, true, 'docs_team'),
('SDK Installation & Setup', 'sdk-setup', 'sdk', 'Install: pip install actuator-sdk>=2.1.1 (requires Python 3.10+). For GPU support: pip install actuator-sdk[gpu]. Quick start: from actuator import Client; client = Client(api_key="your-key"). Full docs at docs.actuator.ai/sdk.', ARRAY['sdk', 'installation', 'python'], 3400, 234, true, 'docs_team'),
('Webhook Configuration', 'webhook-setup', 'integrations', 'Webhooks fire on events: ticket.created, ticket.resolved, agent.handoff, payment.received. Configure at Settings > Integrations > Webhooks. Payload is JSON with event_type, data, and timestamp. Retry policy: 3 attempts with exponential backoff (1s, 5s, 30s). Verify signatures using X-Actuator-Signature header.', ARRAY['webhook', 'integration', 'events'], 890, 67, true, 'docs_team'),
('Multi-Agent Handoff Patterns', 'handoff-patterns', 'sdk', 'Handoffs route conversations between specialist agents. Define handoff_description on each agent. The supervisor uses this to decide routing. Best practices: keep descriptions clear and non-overlapping. Use classify_request tool for deterministic routing.', ARRAY['handoff', 'multi-agent', 'patterns'], 670, 45, true, 'docs_team'),
('Setting Up Guardrails', 'guardrails-setup', 'security', 'Input guardrails run before agent processing. Output guardrails validate responses. Built-in: jailbreak detection, PII blocking, SQL injection prevention. Custom guardrails: decorate with @input_guardrail or @output_guardrail. Return GuardrailFunctionOutput with tripwire_triggered=True to block.', ARRAY['guardrails', 'security', 'safety'], 540, 38, true, 'docs_team'),
('Database Connection Best Practices', 'db-connection', 'deployment', 'Supported: PostgreSQL 14+, MySQL 8+. Use connection pooling (pgBouncer recommended). Max pool size default=20, adjust based on load. Connection string format: postgresql://user:pass@host:5432/dbname. Enable SSL in production.', ARRAY['database', 'postgresql', 'deployment'], 420, 29, true, 'docs_team'),
('Deployment Guide (Docker)', 'docker-deploy', 'deployment', 'Docker: docker compose up -d. Kubernetes: Helm chart at charts/actuator. Minimum resources per replica: 2 CPU, 4GB RAM. Health check endpoint: GET /health. Graceful shutdown timeout: 30s. Environment variables via ConfigMap or .env file.', ARRAY['docker', 'kubernetes', 'deployment'], 1100, 78, true, 'docs_team'),
('Troubleshooting 502 Errors', 'troubleshoot-502', 'api', 'HTTP 502 = upstream service unreachable. Common causes: 1) Service restart in progress (wait 30s), 2) Connection pool exhausted (check DB connections), 3) Memory limit exceeded (increase resources), 4) Network policy blocking (check firewall).', ARRAY['502', 'troubleshooting', 'api'], 1800, 120, true, 'docs_team'),
('Two-Factor Authentication Setup', '2fa-setup', 'security', 'Supported methods: TOTP (authenticator app), SMS, Email. Enable at Settings > Security > 2FA. TOTP recommended for highest security. Backup codes generated on setup — store securely. Recovery: contact support with identity verification.', ARRAY['2fa', 'security', 'authentication'], 760, 52, true, 'docs_team'),
('Understanding Your Invoice', 'invoice-guide', 'billing', 'Invoices generated on your billing cycle date (1st or 15th). Line items include: base plan, overages, add-ons. Payment methods: credit card (auto-charge), bank transfer (net-15 terms). Download PDF at Settings > Billing > Invoices. Disputes: contact billing within 30 days.', ARRAY['invoice', 'billing', 'payment'], 950, 65, true, 'docs_team'),
('Customer Health Score Explained', 'health-score', 'success', 'Health score (0-100) factors: API usage trend (30%), login frequency (20%), support ticket sentiment (15%), feature adoption (15%), payment history (10%), NPS score (10%). Thresholds: 80+ Healthy, 40-79 At Risk, <40 Critical.', ARRAY['health', 'churn', 'retention'], 320, 22, true, 'csm_team');

-- ==================== SECURITY EVENTS ====================
INSERT INTO security_events (contact_email, event_type, ip_address, user_agent, location, details, created_at) VALUES
('ahmed@techvista.pk', 'login_success', '203.0.113.42', 'Mozilla/5.0 Chrome/124', 'Islamabad, PK', '{}', '2026-04-12 14:32:00'),
('ahmed@techvista.pk', 'login_failed', '203.0.113.42', 'Mozilla/5.0 Chrome/124', 'Islamabad, PK', '{"reason": "wrong_password"}', '2026-04-12 14:30:00'),
('ahmed@techvista.pk', '2fa_verified', '203.0.113.42', 'Mozilla/5.0 Chrome/124', 'Islamabad, PK', '{"method": "totp"}', '2026-04-12 14:32:00'),
('sara@novabyte.io', 'login_success', '198.51.100.12', 'Mozilla/5.0 Firefox/125', 'Lahore, PK', '{}', '2026-04-11 09:15:00'),
('sara@novabyte.io', 'login_failed', '198.51.100.12', 'Mozilla/5.0 Firefox/125', 'Lahore, PK', '{"reason": "wrong_password"}', '2026-04-11 09:14:00'),
('sara@novabyte.io', 'login_failed', '45.33.32.156', 'python-requests/2.31', 'Unknown', '{"reason": "wrong_password", "suspicious": true}', '2026-04-10 03:22:00'),
('bilal@datapulse.pk', 'login_failed', '192.168.1.100', 'Mozilla/5.0 Chrome/124', 'Karachi, PK', '{"reason": "wrong_password"}', '2026-04-10 23:40:00'),
('bilal@datapulse.pk', 'login_failed', '192.168.1.100', 'Mozilla/5.0 Chrome/124', 'Karachi, PK', '{"reason": "wrong_password"}', '2026-04-10 23:41:00'),
('bilal@datapulse.pk', 'login_failed', '192.168.1.100', 'Mozilla/5.0 Chrome/124', 'Karachi, PK', '{"reason": "wrong_password"}', '2026-04-10 23:42:00'),
('bilal@datapulse.pk', 'login_failed', '192.168.1.100', 'Mozilla/5.0 Chrome/124', 'Karachi, PK', '{"reason": "wrong_password"}', '2026-04-10 23:43:00'),
('bilal@datapulse.pk', 'account_locked', '192.168.1.100', 'Mozilla/5.0 Chrome/124', 'Karachi, PK', '{"reason": "exceeded_max_attempts", "attempts": 5}', '2026-04-10 23:44:00'),
('ahmed@techvista.pk', 'password_changed', '203.0.113.42', 'Mozilla/5.0 Chrome/124', 'Islamabad, PK', '{}', '2026-04-10 22:00:00'),
('khalid@finedge.ae', 'login_success', '85.115.52.10', 'Mozilla/5.0 Safari/17', 'Dubai, AE', '{}', '2026-04-12 16:45:00'),
('khalid@finedge.ae', '2fa_verified', '85.115.52.10', 'Mozilla/5.0 Safari/17', 'Dubai, AE', '{"method": "totp"}', '2026-04-12 16:45:30'),
('tariq@logitrack.pk', 'login_failed', '39.40.50.60', 'Mozilla/5.0 Chrome/123', 'Lahore, PK', '{"reason": "wrong_password"}', '2026-03-15 09:00:00'),
('tariq@logitrack.pk', 'account_locked', '39.40.50.60', 'Mozilla/5.0 Chrome/123', 'Lahore, PK', '{"reason": "exceeded_max_attempts", "attempts": 8}', '2026-03-15 09:05:00');

-- ==================== ESCALATIONS ====================
INSERT INTO escalations (id, ticket_id, conversation_id, customer_id, reason, severity, assigned_to, status, resolution, created_at, resolved_at) VALUES
('ESC-00001', 'TKT-00389', NULL, 4, 'Account locked before critical client demo. Customer extremely frustrated.', 'critical', 'On-duty Supervisor', 'open', NULL, '2026-04-13 00:00:00', NULL),
('ESC-00002', 'TKT-00540', NULL, 10, 'Account suspended despite pending bank transfer. Revenue at risk.', 'high', 'Finance Manager', 'open', NULL, '2026-04-13 03:15:00', NULL),
('ESC-00003', 'TKT-00198', NULL, 1, 'SDK compatibility issue affecting production deployment.', 'medium', 'Engineering Lead', 'resolved', 'Hotfix v2.1.1 released within 8 hours.', '2026-04-09 09:30:00', '2026-04-09 17:00:00');

-- ==================== NOTIFICATIONS LOG ====================
INSERT INTO notifications_log (recipient, channel, event_type, subject, content, status, sent_at) VALUES
('ahmed@techvista.pk', 'email', 'invoice_paid', 'Payment Confirmed - INV-2026-0401', 'Your payment of PKR 29,900 has been processed successfully.', 'sent', '2026-04-01 10:30:00'),
('sara@novabyte.io', 'email', 'ticket_created', 'Ticket TKT-00256 Created', 'Your support ticket regarding API 502 errors has been created. Priority: P2.', 'sent', '2026-04-12 14:31:00'),
('bilal@datapulse.pk', 'email', 'account_locked', 'Security Alert: Account Locked', 'Your account has been locked due to multiple failed login attempts.', 'sent', '2026-04-10 23:45:00'),
('#engineering', 'slack', 'ticket_escalated', 'P1 Ticket Escalated', 'TKT-00389: Account locked - DataPulse Analytics. Client demo tomorrow.', 'sent', '2026-04-13 00:01:00'),
('#billing', 'slack', 'payment_overdue', 'Overdue Invoice Alert', 'INV-2026-0404 (DataPulse) and INV-2026-0410-LT (LogiTrack) are overdue.', 'sent', '2026-04-12 09:00:00'),
('tariq@logitrack.pk', 'email', 'account_suspended', 'Account Suspended - Action Required', 'Your Actuator AI account has been suspended due to overdue payment.', 'sent', '2026-04-08 00:00:00'),
('ayesha@meridianhealth.pk', 'email', 'ticket_update', 'Update on TKT-00412', 'Webhook issue identified, events being replayed.', 'sent', '2026-04-12 09:05:00'),
('omar@cloudmatrix.ae', 'email', 'ticket_created', 'Ticket TKT-00478 Created', 'Feature request for custom model deployment received.', 'sent', '2026-04-12 10:05:00');

-- ==================== AGENTS CONFIG ====================
INSERT INTO agents_config (agent_key, display_name, description, model_name, temperature, max_tokens, is_active, total_requests, avg_latency_ms) VALUES
('supervisor_router', 'Supervisor Router', 'Central orchestrator — classifies, routes, and escalates', 'qwen2.5:7b', 0.20, 800, true, 12450, 1200),
('technical_specialist', 'Technical Specialist', 'API errors, SDK issues, infrastructure, debugging', 'qwen2.5:7b', 0.20, 1200, true, 4890, 2800),
('account_security', 'Account & Security Agent', 'Login, 2FA, password reset, account lockout, security', 'qwen2.5:7b', 0.20, 1000, true, 3210, 1500),
('billing_finance', 'Billing & Finance Agent', 'Invoices, payments, refunds, plan changes, usage', 'qwen2.5:7b', 0.20, 1000, true, 2870, 1800),
('success_retention', 'Success & Retention Agent', 'Health checks, renewals, churn prevention, feature adoption', 'qwen2.5:7b', 0.40, 1200, true, 1540, 2200),
('operations_sync', 'Operations Sync Agent', 'CRM updates, Jira tickets, support tickets, task tracking', 'qwen2.5:7b', 0.20, 1000, true, 2100, 1600),
('linguistic', 'Linguistic Agent', 'Translation, sentiment analysis, tone detection, QA', 'qwen2.5:7b', 0.30, 1000, true, 980, 900),
('audit', 'Audit Agent', 'Hallucination detection, policy compliance, QA reports', 'qwen2.5:7b', 0.10, 1200, true, 1247, 3500);

-- ==================== AUDIT LOGS ====================
INSERT INTO audit_logs (conversation_id, agent_name, action, input_summary, output_summary, hallucination_risk, policy_compliant, quality_score, latency_ms, tokens_used, created_at) VALUES
('conv-sample-001', 'Supervisor Router', 'response_generated', 'Customer asking about 502 errors', 'Classified as technical P2, handed off to Technical Specialist', 'low', true, 92, 1100, 450, '2026-04-12 14:30:00'),
('conv-sample-001', 'Technical Specialist', 'tool_called', 'check_system_status(user-service)', 'Returned DEGRADED status with 8.2% error rate', 'low', true, 95, 200, 80, '2026-04-12 14:30:30'),
('conv-sample-001', 'Technical Specialist', 'response_generated', 'Diagnosis of user-service 502', 'Identified connection pool exhaustion, created ENG ticket', 'low', true, 88, 2800, 680, '2026-04-12 14:31:00'),
('conv-sample-002', 'Billing & Finance Agent', 'response_generated', 'Customer disputing March charge', 'Confirmed payment, corrected invoice status', 'low', true, 90, 1800, 520, '2026-04-12 11:30:00'),
('conv-sample-003', 'Account & Security Agent', 'tool_called', 'lookup_account(bilal@datapulse.pk)', 'Returned locked account with 5 failed attempts', 'low', true, 96, 150, 60, '2026-04-12 23:50:00'),
('conv-sample-004', 'Linguistic Agent', 'response_generated', 'Sentiment analysis of angry message', 'Scored -0.8 NEGATIVE, HIGH urgency flagged', 'low', true, 94, 900, 340, '2026-04-12 16:00:00'),
('conv-sample-005', 'Audit Agent', 'response_generated', 'QA check on billing response', 'No hallucination detected, policy compliant', 'low', true, 91, 3500, 890, '2026-04-12 17:00:00');

-- ==================== FEEDBACK ====================
INSERT INTO feedback (conversation_id, customer_id, rating, nps_score, comment, agent_name, created_at) VALUES
('conv-sample-001', 2, 4, 8, 'Quick diagnosis of the API issue. Would have liked a faster fix though.', 'Technical Specialist', '2026-04-12 15:00:00'),
('conv-sample-002', 1, 5, 9, 'Billing issue resolved in one message. Excellent.', 'Billing & Finance Agent', '2026-04-12 12:00:00'),
('conv-sample-004', 3, 3, 6, 'Translation was okay but missed some technical nuance.', 'Linguistic Agent', '2026-04-12 16:30:00'),
(NULL, 1, 5, 10, 'Overall platform is incredible. SDK hotfix turnaround impressed us.', NULL, '2026-04-10 10:00:00'),
(NULL, 7, 2, 3, 'Platform was too complex for our simple needs. Cancelling.', NULL, '2026-02-01 10:00:00'),
(NULL, 8, 5, 10, 'Enterprise Plus is worth every dirham. Compliance support is exceptional.', NULL, '2026-03-15 10:00:00');
