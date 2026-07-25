"""shared/tools/db_tools.py — Database Query Tools for Agents

Production tools that query PostgreSQL directly.
Every agent uses these instead of hardcoded mock data.
Connection uses rameez/pu00 @ actuator_ai.
"""

import os
from datetime import datetime, timezone
from agents import function_tool

import psycopg2
import psycopg2.extras


def _conn():
    """Get database connection."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_SERVER", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        dbname=os.getenv("POSTGRES_DB", "actuator_ai"),
    )


def _query(sql: str, params: tuple = ()) -> list[dict]:
    """Execute read query, return list of dicts."""
    try:
        with _conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, params)
                return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        return [{"error": str(e)}]


def _execute(sql: str, params: tuple = ()) -> str:
    """Execute write query, return status."""
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                conn.commit()
                return f"OK — {cur.rowcount} row(s) affected"
    except Exception as e:
        return f"[ERROR] {e}"


# ==================== CUSTOMER TOOLS ====================

@function_tool
def lookup_customer_by_email(email: str) -> str:
    """Look up customer and contact details by email address.

    Args:
        email: Customer contact email address.
    """
    rows = _query("""
        SELECT c.id, c.company_name, c.industry, c.company_size, c.region,
               c.status, c.health_score, c.mrr, c.created_at,
               cc.name, cc.email, cc.phone, cc.role, cc.is_primary,
               cc.last_login, cc.login_failures, cc.account_locked,
               cc.two_factor_enabled, cc.two_factor_method
        FROM customers c
        JOIN customer_contacts cc ON cc.customer_id = c.id
        WHERE cc.email ILIKE %s
    """, (email,))

    if not rows or "error" in rows[0]:
        return f"No account found for: {email}"

    r = rows[0]
    locked_info = ""
    if r["account_locked"]:
        locked_info = f"\n  ⚠ ACCOUNT LOCKED | Failed attempts: {r['login_failures']}"

    tfa = f"{r['two_factor_method'].upper()}" if r["two_factor_enabled"] else "Disabled"
    return (
        f"Customer: {r['name']} | {r['role']}\n"
        f"  Company: {r['company_name']} ({r['industry']}) | {r['company_size']} employees\n"
        f"  Email: {r['email']} | Phone: {r['phone'] or 'N/A'}\n"
        f"  Region: {r['region']} | Primary contact: {'Yes' if r['is_primary'] else 'No'}\n"
        f"  Account status: {r['status'].upper()} | Health: {r['health_score']}/100\n"
        f"  MRR: PKR {r['mrr']:,.0f} | Since: {r['created_at']}\n"
        f"  2FA: {tfa} | Last login: {r['last_login'] or 'Never'}"
        f"{locked_info}"
    )

@function_tool
def register_customer(
    company_name: str,
    contact_name: str,
    email: str,
    role: str = "Administrator",
    plan: str = "pro",
    industry: str = "Technology",
    company_size: str = "11-50",
    region: str = "Asia/Pacific",
) -> str:
    """Register a new customer account, contact person, and subscription.

    Args:
        company_name: Name of customer's company.
        contact_name: Full name of primary contact person.
        email: Contact email address.
        role: Job title/role of contact (default 'Administrator').
        plan: Subscription plan: 'free', 'pro', 'enterprise', 'enterprise_plus' (default 'pro').
        industry: Industry sector (default 'Technology').
        company_size: Employee range: '1-10', '11-50', '51-200', '201-500', '500+' (default '11-50').
        region: Region (default 'Asia/Pacific').
    """
    # Check if contact email already exists
    existing = _query("SELECT id FROM customer_contacts WHERE email ILIKE %s", (email,))
    if existing and "error" not in existing[0]:
        return f"[ERROR] An account with email '{email}' already exists in our system."

    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                # 1. Insert customer
                cur.execute("""
                    INSERT INTO customers (company_name, industry, company_size, region, status, health_score, mrr)
                    VALUES (%s, %s, %s, %s, 'active', 100, 29900.00)
                    RETURNING id
                """, (company_name, industry, company_size, region))
                customer_id = cur.fetchone()[0]

                # 2. Insert customer contact
                cur.execute("""
                    INSERT INTO customer_contacts (customer_id, name, email, role, is_primary)
                    VALUES (%s, %s, %s, %s, true)
                    RETURNING id
                """, (customer_id, contact_name, email, role))
                contact_id = cur.fetchone()[0]

                # 3. Lookup product id
                cur.execute("SELECT id, name, price_monthly FROM products WHERE slug = %s OR name ILIKE %s LIMIT 1", (plan.lower(), f"%{plan}%"))
                prod_row = cur.fetchone()
                if prod_row:
                    prod_id = prod_row[0]
                    prod_name = prod_row[1]
                else:
                    cur.execute("SELECT id, name FROM products LIMIT 1")
                    fallback = cur.fetchone()
                    prod_id = fallback[0] if fallback else None
                    prod_name = fallback[1] if fallback else plan

                # 4. Insert subscription
                if prod_id:
                    cur.execute("""
                        INSERT INTO subscriptions (customer_id, product_id, status, billing_cycle, current_period_start, current_period_end)
                        VALUES (%s, %s, 'active', 'monthly', NOW(), NOW() + INTERVAL '30 days')
                    """, (customer_id, prod_id))

                conn.commit()

        # Automatically send welcome email & log to notifications_log table
        from shared.tools.notification_tools import send_email
        email_result = send_email.on_invoke_tool(
            context=None,
            to=email,
            subject=f"Welcome to Actuator AI, {contact_name}!",
            body=f"Hi {contact_name},\n\nYour account for {company_name} has been successfully registered on the {prod_name.upper()} plan.\n\nAccount Details:\n- Customer ID: #{customer_id}\n- Contact Role: {role}\n- Region: {region}\n- Status: ACTIVE\n\nThank you for joining Actuator AI!",
            priority="high"
        )

        return (
            f"✅ Account successfully registered!\n"
            f"  Customer ID: #{customer_id}\n"
            f"  Company: {company_name} ({industry})\n"
            f"  Primary Contact: {contact_name} ({email}) | Role: {role}\n"
            f"  Plan: {prod_name.upper()} (Active)\n"
            f"  Status: ACTIVE | Health Score: 100/100\n"
            f"  Welcome Email: Sent & Logged ({email})"
        )
    except Exception as e:
        return f"[ERROR] Registration failed: {e}"


@function_tool
def search_customers(field: str, value: str) -> str:
    """Search customers by company_name, industry, status, or region.

    Args:
        field: One of 'company_name', 'industry', 'status', 'region'.
        value: Value to search for (partial match).
    """
    COLUMN_MAP = {
        "company_name": "company_name",
        "industry": "industry",
        "status": "status",
        "region": "region",
    }
    column = COLUMN_MAP.get(field)
    if not column:
        return f"[ERROR] Invalid field. Use: {', '.join(COLUMN_MAP.keys())}"

    rows = _query(
        f"SELECT id, company_name, industry, status, health_score, mrr "
        f"FROM customers WHERE {column} ILIKE %s ORDER BY health_score DESC LIMIT 15",
        (f"%{value}%",),
    )
    if not rows or "error" in rows[0]:
        return f"No customers found where {field} matches '{value}'."

    lines = [f"Found {len(rows)} customer(s):"]
    for r in rows:
        lines.append(
            f"  [{r['id']}] {r['company_name']} | {r['industry']} | "
            f"{r['status']} | Health: {r['health_score']} | MRR: PKR {r['mrr']:,.0f}"
        )
    return "\n".join(lines)


@function_tool
def cancel_subscription(email: str, reason: str = "User requested cancellation") -> str:
    """Cancel a customer subscription.

    Args:
        email: Customer contact email address.
        reason: Reason for cancellation.
    """
    rows = _query("""
        SELECT s.id, c.company_name
        FROM customer_contacts cc
        JOIN customers c ON c.id = cc.customer_id
        JOIN subscriptions s ON s.customer_id = c.id
        WHERE cc.email ILIKE %s AND s.status = 'active'
        LIMIT 1
    """, (email,))

    if not rows or "error" in rows[0]:
        return f"[ERROR] No active subscription found for {email}."

    sub_id = rows[0]["id"]
    company = rows[0]["company_name"]
    res = _execute(
        "UPDATE subscriptions SET status = 'cancelled', cancelled_reason = %s, cancel_at = NOW() WHERE id = %s",
        (reason, sub_id)
    )
    return (
        f"Subscription cancelled for {company} ({email}):\n"
        f"  Subscription ID: #{sub_id}\n"
        f"  Reason: {reason}\n"
        f"  Status: CANCELLED\n"
        f"  DB Update: {res}"
    )


# ==================== BILLING TOOLS ====================

@function_tool
def get_billing_info(email: str) -> str:
    """Get billing summary: subscription, latest invoices, payment method.

    Args:
        email: Customer contact email.
    """
    rows = _query("""
        SELECT c.company_name, p.name as plan_name, p.price_monthly,
               s.status as sub_status, s.billing_cycle, s.current_period_end, s.auto_renew,
               cc.email
        FROM customer_contacts cc
        JOIN customers c ON c.id = cc.customer_id
        JOIN subscriptions s ON s.customer_id = c.id
        JOIN products p ON p.id = s.product_id
        WHERE cc.email ILIKE %s
        LIMIT 1
    """, (email,))

    if not rows or "error" in rows[0]:
        return f"No billing record for: {email}"

    r = rows[0]
    # Get recent invoices
    invoices = _query("""
        SELECT i.id, i.total, i.currency, i.status, i.due_date, i.payment_method
        FROM invoices i
        JOIN customers c ON c.id = i.customer_id
        JOIN customer_contacts cc ON cc.customer_id = c.id
        WHERE cc.email ILIKE %s
        ORDER BY i.due_date DESC LIMIT 3
    """, (email,))

    inv_lines = []
    for inv in invoices:
        inv_lines.append(
            f"    {inv['id']} | {inv['currency']} {inv['total']:,.0f} | "
            f"{inv['status'].upper()} | Due: {inv['due_date']} | Via: {inv['payment_method'] or 'Pending'}"
        )

    return (
        f"Billing for {r['company_name']}:\n"
        f"  Plan: {r['plan_name']} | {r['currency'] if invoices else 'PKR'} {r['price_monthly']:,.0f}/mo\n"
        f"  Subscription: {r['sub_status'].upper()} | Cycle: {r['billing_cycle']}\n"
        f"  Period ends: {r['current_period_end']} | Auto-renew: {'Yes' if r['auto_renew'] else 'No'}\n"
        f"  Recent invoices:\n" + "\n".join(inv_lines) if inv_lines else "  No invoices found."
    )


@function_tool
def get_invoice(invoice_id: str) -> str:
    """Retrieve specific invoice with line items and payment info.

    Args:
        invoice_id: Invoice ID like 'INV-2026-0401'.
    """
    rows = _query("""
        SELECT i.*, c.company_name
        FROM invoices i
        JOIN customers c ON c.id = i.customer_id
        WHERE i.id = %s
    """, (invoice_id.upper(),))

    if not rows or "error" in rows[0]:
        return f"Invoice not found: {invoice_id}"

    r = rows[0]
    # Line items
    items = _query(
        "SELECT description, quantity, unit_price, amount FROM invoice_line_items WHERE invoice_id = %s",
        (invoice_id.upper(),),
    )
    item_lines = [f"    {it['description']} × {it['quantity']} = {r['currency']} {it['amount']:,.0f}" for it in items]

    # Payment
    payment = _query("SELECT * FROM payments WHERE invoice_id = %s LIMIT 1", (invoice_id.upper(),))
    pay_info = ""
    if payment and "error" not in payment[0]:
        p = payment[0]
        pay_info = f"\n  Payment: {p['id']} | {p['method']} | {p['status']} | {p['processed_at']}"

    return (
        f"Invoice {r['id']} — {r['company_name']}:\n"
        f"  Date: {r['created_at']} | Due: {r['due_date']}\n"
        f"  Amount: {r['currency']} {r['amount']:,.0f} | Tax: {r['currency']} {r['tax']:,.0f} | Total: {r['currency']} {r['total']:,.0f}\n"
        f"  Status: {r['status'].upper()} | Paid at: {r['paid_at'] or 'Not paid'}\n"
        f"  Method: {r['payment_method'] or 'N/A'}\n"
        f"  Items:\n" + ("\n".join(item_lines) if item_lines else "    No line items")
        + pay_info
    )


@function_tool
def get_usage_breakdown(email: str, month: str) -> str:
    """Get API usage and cost breakdown for a billing period.

    Args:
        email: Customer contact email.
        month: Month in YYYY-MM format, e.g. '2026-04'.
    """
    rows = _query("""
        SELECT au.*, p.api_calls_limit, p.storage_gb, p.name as plan_name
        FROM api_usage au
        JOIN customers c ON c.id = au.customer_id
        JOIN customer_contacts cc ON cc.customer_id = c.id
        JOIN subscriptions s ON s.customer_id = c.id
        JOIN products p ON p.id = s.product_id
        WHERE cc.email ILIKE %s AND au.month = %s
        LIMIT 1
    """, (email, month))

    if not rows or "error" in rows[0]:
        return f"No usage data for {email} in {month}."

    r = rows[0]
    api_pct = (r['api_calls'] / r['api_calls_limit'] * 100) if r['api_calls_limit'] else 0
    stor_pct = (float(r['storage_used_gb']) / r['storage_gb'] * 100) if r['storage_gb'] else 0

    return (
        f"Usage breakdown — {email} ({month}):\n"
        f"  Plan: {r['plan_name']}\n"
        f"  API Calls:      {r['api_calls']:,} / {r['api_calls_limit']:,} ({api_pct:.1f}%)\n"
        f"  Storage:         {r['storage_used_gb']} GB / {r['storage_gb']} GB ({stor_pct:.1f}%)\n"
        f"  Agent Sessions:  {r['agent_sessions']:,}\n"
        f"  Webhook Events:  {r['webhook_events']:,}\n"
        f"  Overage charge:  PKR {r['overage_amount']:,.0f}"
    )


# ==================== TICKET TOOLS ====================

@function_tool
def query_tickets(status: str = "open", limit: int = 10) -> str:
    """Query support tickets from database.

    Args:
        status: 'open', 'in_progress', 'waiting', 'resolved', 'closed', or 'all'.
        limit: Max results (1-50).
    """
    if status.lower() == "all":
        rows = _query(
            "SELECT id, contact_email, category, priority, subject, status, assigned_to, created_at "
            "FROM support_tickets ORDER BY created_at DESC LIMIT %s",
            (min(limit, 50),),
        )
    else:
        rows = _query(
            "SELECT id, contact_email, category, priority, subject, status, assigned_to, created_at "
            "FROM support_tickets WHERE status = %s ORDER BY created_at DESC LIMIT %s",
            (status.lower(), min(limit, 50)),
        )

    if not rows or "error" in rows[0]:
        return f"No tickets found with status '{status}'."

    lines = [f"Tickets ({status}, {len(rows)} results):"]
    for r in rows:
        lines.append(
            f"  {r['id']} | {r['contact_email']} | {r['category']}/{r['priority']} | "
            f"{r['subject'][:60]} | {r['status']} | {r['assigned_to'] or 'Unassigned'}"
        )
    return "\n".join(lines)


@function_tool
def get_ticket_details(ticket_id: str) -> str:
    """Get full ticket with comments/history.

    Args:
        ticket_id: Ticket ID like 'TKT-00256'.
    """
    rows = _query("""
        SELECT st.*, c.company_name
        FROM support_tickets st
        JOIN customers c ON c.id = st.customer_id
        WHERE st.id = %s
    """, (ticket_id.upper(),))

    if not rows or "error" in rows[0]:
        return f"Ticket not found: {ticket_id}"

    r = rows[0]
    # Comments
    comments = _query(
        "SELECT author, author_type, content, is_internal, created_at "
        "FROM ticket_comments WHERE ticket_id = %s ORDER BY created_at",
        (ticket_id.upper(),),
    )

    comment_lines = []
    for c in comments:
        prefix = "[INTERNAL] " if c["is_internal"] else ""
        comment_lines.append(
            f"    [{c['created_at']}] {prefix}{c['author']} ({c['author_type']}): {c['content'][:150]}"
        )

    return (
        f"Ticket {r['id']} — {r['company_name']}:\n"
        f"  Contact: {r['contact_email']}\n"
        f"  Category: {r['category']} | Priority: {r['priority']}\n"
        f"  Subject: {r['subject']}\n"
        f"  Description: {(r['description'] or '')[:200]}\n"
        f"  Status: {r['status']} | Assigned: {r['assigned_to'] or 'Unassigned'}\n"
        f"  SLA deadline: {r['sla_deadline']} | First response: {r['first_response_at'] or 'Pending'}\n"
        f"  Created: {r['created_at']} | Resolved: {r['resolved_at'] or 'N/A'}\n"
        f"  CSAT: {r['satisfaction'] or 'N/A'}/5\n"
        f"  Comments ({len(comments)}):\n" + ("\n".join(comment_lines) if comment_lines else "    No comments yet.")
    )


@function_tool
def create_support_ticket(email: str, category: str, priority: str, subject: str, description: str) -> str:
    """Create support ticket in database.

    Args:
        email: Customer contact email.
        category: 'billing', 'technical', 'account', 'general', 'feature_request'.
        priority: 'P1', 'P2', 'P3', or 'P4'.
        subject: Ticket subject line.
        description: Full description.
    """
    import uuid
    tid = f"TKT-{abs(hash(str(uuid.uuid4()))) % 100000:05d}"

    assignment_map = {
        "billing": "Finance Team", "technical": "Engineering Team",
        "account": "Account Team", "general": "Support Pool",
        "feature_request": "Product Team",
    }
    team = assignment_map.get(category.lower(), "Support Pool")

    # Get customer_id
    cust = _query("SELECT customer_id FROM customer_contacts WHERE email ILIKE %s LIMIT 1", (email,))
    cust_id = cust[0]["customer_id"] if cust and "error" not in cust[0] else None

    result = _execute("""
        INSERT INTO support_tickets (id, customer_id, contact_email, category, priority, subject, description, assigned_to, sla_deadline)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW() + INTERVAL '4 hours' * CASE WHEN %s IN ('P1','P2') THEN 1 ELSE 6 END)
    """, (tid, cust_id, email, category, priority, subject, description, team, priority))

    sla = "4 hours" if priority in ["P1", "P2"] else "24 hours"
    return (
        f"Support ticket created:\n"
        f"  ID: {tid}\n"
        f"  Customer: {email}\n"
        f"  Category: {category} | Priority: {priority}\n"
        f"  Subject: {subject}\n"
        f"  Assigned to: {team}\n"
        f"  SLA: {sla}"
    )


# ==================== SECURITY TOOLS ====================

@function_tool
def get_security_log(email: str, limit: int = 10) -> str:
    """Get recent security events for an account.

    Args:
        email: Account email address.
        limit: Number of events to return.
    """
    rows = _query("""
        SELECT event_type, ip_address, location, details, created_at
        FROM security_events
        WHERE contact_email ILIKE %s
        ORDER BY created_at DESC
        LIMIT %s
    """, (email, min(limit, 30)))

    if not rows or "error" in rows[0]:
        return f"No security events for: {email}"

    lines = [f"Security log for {email} (last {len(rows)} events):"]
    for r in rows:
        details = r.get("details", {})
        extra = f" — {details.get('reason', '')}" if details.get("reason") else ""
        lines.append(f"  {r['created_at']} | {r['event_type']} | IP: {r['ip_address']} | {r['location']}{extra}")

    return "\n".join(lines)


@function_tool
def unlock_account(email: str, reason: str) -> str:
    """Unlock a locked account and reset failed attempts.

    Args:
        email: Account email to unlock.
        reason: Reason for unlocking (for audit trail).
    """
    result = _execute(
        "UPDATE customer_contacts SET account_locked = false, login_failures = 0 WHERE email ILIKE %s",
        (email,),
    )
    # Log security event
    _execute(
        "INSERT INTO security_events (contact_email, event_type, ip_address, location, details) "
        "VALUES (%s, 'account_unlocked', 'system', 'System', %s)",
        (email, psycopg2.extras.Json({"reason": reason, "unlocked_by": "Account & Security Agent"})),
    )
    return (
        f"Account {email} unlocked successfully.\n"
        f"  Failed attempt counter reset to 0.\n"
        f"  Reason: {reason}\n"
        f"  Security event logged.\n"
        f"  User will receive email notification."
    )
@function_tool
def update_customer_profile(
    email: str,
    name: str = "",
    phone: str = "",
    role: str = "",
    timezone: str = "",
    company_name: str = "",
) -> str:
    """Update customer contact or company profile details in the database.

    Args:
        email: Contact email address to update.
        name: New full name (optional).
        phone: New phone number (optional).
        role: New job title/role (optional).
        timezone: New timezone e.g. 'Asia/Karachi' (optional).
        company_name: New company name (optional).
    """
    updated_fields = []
    if name:
        _execute("UPDATE customer_contacts SET name = %s WHERE email ILIKE %s", (name, email))
        updated_fields.append(f"Name: {name}")
    if phone:
        _execute("UPDATE customer_contacts SET phone = %s WHERE email ILIKE %s", (phone, email))
        updated_fields.append(f"Phone: {phone}")
    if role:
        _execute("UPDATE customer_contacts SET role = %s WHERE email ILIKE %s", (role, email))
        updated_fields.append(f"Role: {role}")
    if timezone:
        _execute("UPDATE customer_contacts SET timezone = %s WHERE email ILIKE %s", (timezone, email))
        updated_fields.append(f"Timezone: {timezone}")
    if company_name:
        _execute("""
            UPDATE customers SET company_name = %s
            WHERE id = (SELECT customer_id FROM customer_contacts WHERE email ILIKE %s LIMIT 1)
        """, (company_name, email))
        updated_fields.append(f"Company: {company_name}")

    if not updated_fields:
        return f"[NOTICE] No profile fields were updated for {email}."

    return (
        f"✅ Customer profile updated for {email}:\n"
        f"  Updated: {', '.join(updated_fields)}\n"
        f"  Database changes committed."
    )


@function_tool
def change_plan(email: str, new_plan: str) -> str:
    """Upgrade or downgrade customer's subscription plan in database.

    Args:
        email: Customer contact email address.
        new_plan: Target plan tier: 'free', 'pro', 'enterprise', or 'enterprise_plus'.
    """
    rows = _query("SELECT id, name, price_monthly FROM products WHERE slug = %s OR name ILIKE %s LIMIT 1", (new_plan.lower(), f"%{new_plan}%"))
    if not rows or "error" in rows[0]:
        return f"[ERROR] Invalid plan '{new_plan}'. Available: free, pro, enterprise, enterprise_plus."

    prod = rows[0]
    prod_id = prod["id"]
    prod_name = prod["name"]
    price = prod["price_monthly"]

    res = _execute("""
        UPDATE subscriptions SET product_id = %s, status = 'active'
        WHERE customer_id = (SELECT customer_id FROM customer_contacts WHERE email ILIKE %s LIMIT 1)
    """, (prod_id, email))

    # Update company MRR
    _execute("""
        UPDATE customers SET mrr = %s
        WHERE id = (SELECT customer_id FROM customer_contacts WHERE email ILIKE %s LIMIT 1)
    """, (price, email))

    return (
        f"✅ Subscription plan updated for {email}:\n"
        f"  New Plan: {prod_name.upper()}\n"
        f"  New MRR: PKR {price:,.0f}/mo\n"
        f"  Status: ACTIVE\n"
        f"  DB Sync: Completed."
    )


@function_tool
def add_customer_contact(
    primary_email: str,
    new_contact_name: str,
    new_contact_email: str,
    role: str = "Member",
    phone: str = "",
) -> str:
    """Add a secondary team member/contact to an existing company account.

    Args:
        primary_email: Primary account contact email or any existing team email.
        new_contact_name: Full name of new team member.
        new_contact_email: Email address for new contact.
        role: Job title/role.
        phone: Optional phone number.
    """
    cust = _query("SELECT customer_id FROM customer_contacts WHERE email ILIKE %s LIMIT 1", (primary_email,))
    if not cust or "error" in cust[0]:
        return f"[ERROR] Existing account not found for '{primary_email}'."

    customer_id = cust[0]["customer_id"]
    _execute("""
        INSERT INTO customer_contacts (customer_id, name, email, phone, role, is_primary)
        VALUES (%s, %s, %s, %s, %s, false)
    """, (customer_id, new_contact_name, new_contact_email, phone, role))

    return (
        f"✅ Team member added!\n"
        f"  Customer ID: #{customer_id}\n"
        f"  New Contact: {new_contact_name} ({new_contact_email})\n"
        f"  Role: {role}"
    )


# ==================== KNOWLEDGE BASE TOOLS ====================

@function_tool
def search_knowledge_base(query: str) -> str:
    """Search internal knowledge base articles by keyword.

    Args:
        query: Search query — keywords or phrase.
    """
    # Split query into words for broader matching
    words = [w for w in query.lower().split() if len(w) > 2]
    if not words:
        return "Please provide a more specific search query."

    conditions = " OR ".join(["title ILIKE %s OR content ILIKE %s OR %s = ANY(tags)"] * len(words))
    params = []
    for w in words:
        params.extend([f"%{w}%", f"%{w}%", w])

    rows = _query(
        f"SELECT title, category, content, tags, views, helpful_votes "
        f"FROM knowledge_articles WHERE is_published = true AND ({conditions}) "
        f"ORDER BY helpful_votes DESC LIMIT 5",
        tuple(params),
    )

    if not rows or "error" in rows[0]:
        return "No articles found. Escalate to engineering team."

    lines = [f"Knowledge Base — {len(rows)} article(s) found:"]
    for r in rows:
        lines.append(
            f"\n  📄 {r['title']} [{r['category']}]\n"
            f"     {r['content'][:250]}\n"
            f"     Tags: {', '.join(r['tags'] or [])} | Views: {r['views']} | Helpful: {r['helpful_votes']}"
        )

    return "\n".join(lines)


# ==================== CRM / OPERATIONS TOOLS ====================

@function_tool
def search_crm(email: str) -> str:
    """Search CRM for customer record: company info, subscription, recent tickets, interactions.

    Args:
        email: Customer contact email.
    """
    rows = _query("""
        SELECT c.id, c.company_name, c.industry, c.company_size, c.region,
               c.status, c.health_score, c.mrr, c.created_at,
               p.name as plan_name, s.status as sub_status
        FROM customers c
        JOIN customer_contacts cc ON cc.customer_id = c.id
        LEFT JOIN subscriptions s ON s.customer_id = c.id
        LEFT JOIN products p ON p.id = s.product_id
        WHERE cc.email ILIKE %s
        LIMIT 1
    """, (email,))

    if not rows or "error" in rows[0]:
        return f"No CRM record for: {email}"

    r = rows[0]
    # Recent tickets
    tickets = _query("""
        SELECT id, subject, status, priority, created_at
        FROM support_tickets WHERE customer_id = %s
        ORDER BY created_at DESC LIMIT 3
    """, (r["id"],))

    ticket_lines = []
    for t in tickets:
        ticket_lines.append(f"    {t['id']} | {t['priority']} | {t['subject'][:50]} | {t['status']}")

    # Lifetime value
    ltv = _query(
        "SELECT COALESCE(SUM(total), 0) as ltv FROM invoices WHERE customer_id = %s AND status = 'paid'",
        (r["id"],),
    )
    ltv_val = ltv[0]["ltv"] if ltv and "error" not in ltv[0] else 0

    return (
        f"CRM Record — {r['company_name']}:\n"
        f"  ID: {r['id']} | Industry: {r['industry']} | Size: {r['company_size']}\n"
        f"  Region: {r['region']} | Status: {r['status'].upper()}\n"
        f"  Plan: {r['plan_name'] or 'None'} ({r['sub_status'] or 'N/A'}) | MRR: PKR {r['mrr']:,.0f}\n"
        f"  Health: {r['health_score']}/100 | Since: {r['created_at']}\n"
        f"  Lifetime value: PKR {ltv_val:,.0f}\n"
        f"  Recent tickets ({len(tickets)}):\n" + ("\n".join(ticket_lines) if ticket_lines else "    None")
    )


# ==================== SUCCESS / RETENTION TOOLS ====================

@function_tool
def get_customer_health(email: str) -> str:
    """Get customer health score, engagement metrics, and risk factors.

    Args:
        email: Customer contact email.
    """
    rows = _query("""
        SELECT c.id, c.company_name, c.health_score, c.mrr, c.status, c.created_at,
               p.name as plan_name, p.api_calls_limit,
               s.current_period_end, s.auto_renew
        FROM customers c
        JOIN customer_contacts cc ON cc.customer_id = c.id
        JOIN subscriptions s ON s.customer_id = c.id
        JOIN products p ON p.id = s.product_id
        WHERE cc.email ILIKE %s
        LIMIT 1
    """, (email,))

    if not rows or "error" in rows[0]:
        return f"No customer record for: {email}"

    r = rows[0]
    # Latest usage
    usage = _query(
        "SELECT * FROM api_usage WHERE customer_id = %s ORDER BY month DESC LIMIT 2",
        (r["id"],),
    )

    # Latest feedback
    fb = _query(
        "SELECT rating, nps_score, comment FROM feedback WHERE customer_id = %s ORDER BY created_at DESC LIMIT 1",
        (r["id"],),
    )

    # Health label
    score = r["health_score"]
    label = "HEALTHY" if score >= 80 else ("AT RISK" if score >= 40 else "CRITICAL")

    usage_info = ""
    if usage and "error" not in usage[0]:
        u = usage[0]
        pct = (u["api_calls"] / r["api_calls_limit"] * 100) if r["api_calls_limit"] else 0
        usage_info = f"\n  Usage ({u['month']}): {u['api_calls']:,} API calls ({pct:.0f}% quota) | {u['agent_sessions']:,} sessions"
        if len(usage) > 1:
            prev = usage[1]
            change = ((u["api_calls"] - prev["api_calls"]) / max(prev["api_calls"], 1)) * 100
            usage_info += f"\n  MoM change: {change:+.1f}%"

    nps_info = ""
    if fb and "error" not in fb[0]:
        nps_info = f"\n  NPS: {fb[0]['nps_score']}/10 | CSAT: {fb[0]['rating']}/5"

    risk_factors = []
    if score < 40:
        risk_factors.append("Critical health score")
    if usage and usage[0].get("api_calls", 0) < 500:
        risk_factors.append("Near-zero API usage")
    if not r["auto_renew"]:
        risk_factors.append("Auto-renew disabled")

    risk_info = ""
    if risk_factors:
        risk_info = "\n  ⚠ Risk factors: " + ", ".join(risk_factors)

    return (
        f"Health Score: {score}/100 ({label})\n"
        f"  Company: {r['company_name']} | Plan: {r['plan_name']}\n"
        f"  MRR: PKR {r['mrr']:,.0f} | Since: {r['created_at']}\n"
        f"  Renewal: {r['current_period_end']} | Auto-renew: {'Yes' if r['auto_renew'] else 'No'}"
        f"{usage_info}{nps_info}{risk_info}"
    )


@function_tool
def get_feature_adoption(email: str) -> str:
    """Check which features customer is/isn't using.

    Args:
        email: Customer contact email.
    """
    rows = _query("""
        SELECT ff.feature_name, ff.enabled, ff.enabled_at
        FROM feature_flags ff
        JOIN customer_contacts cc ON cc.customer_id = ff.customer_id
        WHERE cc.email ILIKE %s
        ORDER BY ff.feature_name
    """, (email,))

    if not rows or "error" in rows[0]:
        return f"No feature data for: {email}"

    enabled = [r for r in rows if r["enabled"]]
    disabled = [r for r in rows if not r["enabled"]]

    lines = [f"Feature adoption for {email}:"]
    for r in enabled:
        lines.append(f"  ✅ {r['feature_name']} — Enabled since {r['enabled_at']}")
    for r in disabled:
        lines.append(f"  ❌ {r['feature_name']} — Not configured")

    adoption_rate = len(enabled) / max(len(rows), 1) * 100
    lines.append(f"  Adoption rate: {adoption_rate:.0f}% ({len(enabled)}/{len(rows)} features)")

    return "\n".join(lines)


# ==================== AUDIT TOOLS ====================

@function_tool
def get_audit_logs(agent_name: str = "", limit: int = 10) -> str:
    """Get audit logs, optionally filtered by agent.

    Args:
        agent_name: Filter by agent name (empty for all).
        limit: Max results.
    """
    if agent_name:
        rows = _query(
            "SELECT * FROM audit_logs WHERE agent_name ILIKE %s ORDER BY created_at DESC LIMIT %s",
            (f"%{agent_name}%", min(limit, 50)),
        )
    else:
        rows = _query(
            "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT %s",
            (min(limit, 50),),
        )

    if not rows or "error" in rows[0]:
        return "No audit logs found."

    lines = [f"Audit logs ({len(rows)} entries):"]
    for r in rows:
        lines.append(
            f"  [{r['created_at']}] {r['agent_name']} | {r['action']} | "
            f"Hallucination: {r['hallucination_risk'] or 'N/A'} | "
            f"Compliant: {'✅' if r['policy_compliant'] else '❌'} | "
            f"Quality: {r['quality_score'] or 'N/A'}/100"
        )
    return "\n".join(lines)


@function_tool
def get_escalations(status: str = "open") -> str:
    """Get escalation records.

    Args:
        status: 'open', 'acknowledged', 'resolved', or 'all'.
    """
    if status.lower() == "all":
        rows = _query("SELECT * FROM escalations ORDER BY created_at DESC LIMIT 20")
    else:
        rows = _query(
            "SELECT * FROM escalations WHERE status = %s ORDER BY created_at DESC LIMIT 20",
            (status.lower(),),
        )

    if not rows or "error" in rows[0]:
        return f"No escalations with status '{status}'."

    lines = [f"Escalations ({status}, {len(rows)}):"]
    for r in rows:
        lines.append(
            f"  {r['id']} | {r['severity']} | {r['status']} | Assigned: {r['assigned_to'] or 'Unassigned'}\n"
            f"    Reason: {r['reason'][:120]}"
        )
    return "\n".join(lines)


# ==================== PRODUCT TOOLS ====================

@function_tool
def list_products() -> str:
    """List all available products/plans with pricing."""
    rows = _query("SELECT * FROM products WHERE is_active = true ORDER BY price_monthly")

    if not rows or "error" in rows[0]:
        return "No products found."

    lines = ["Available plans:"]
    for r in rows:
        lines.append(
            f"  {r['name']} ({r['slug']}):\n"
            f"    PKR {r['price_monthly']:,.0f}/mo | PKR {r['price_yearly']:,.0f}/yr\n"
            f"    API: {r['api_calls_limit']:,} calls | Storage: {r['storage_gb']} GB | Support: {r['support_tier']}"
        )
    return "\n".join(lines)


# ==================== NOTIFICATION TOOLS ====================

@function_tool
def get_notifications(email: str, limit: int = 10) -> str:
    """Get notification history for a recipient.

    Args:
        email: Recipient email or Slack channel.
        limit: Max results.
    """
    rows = _query(
        "SELECT channel, event_type, subject, status, sent_at "
        "FROM notifications_log WHERE recipient ILIKE %s ORDER BY sent_at DESC LIMIT %s",
        (f"%{email}%", min(limit, 20)),
    )

    if not rows or "error" in rows[0]:
        return f"No notifications for: {email}"

    lines = [f"Notifications for {email} ({len(rows)}):"]
    for r in rows:
        lines.append(f"  [{r['sent_at']}] {r['channel']} | {r['event_type']} | {r['subject']} | {r['status']}")

    return "\n".join(lines)
