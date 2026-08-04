from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from typing import List, Optional
import uuid
import httpx
import logging
import hmac
import hashlib
import json
from datetime import datetime, timezone, timedelta

from auth import get_current_user, UserResponse
from middleware.rbac import require_permission
from config import settings
from database import get_db, get_db_write_lock

logger = logging.getLogger("billing")

router = APIRouter(prefix="/api/billing", tags=["billing"])

class CheckoutRequest(BaseModel):
    plan_name: Optional[str] = None
    credits_pack: Optional[str] = None

class VerifyPaymentRequest(BaseModel):
    checkout_session_id: str
    dodo_payment_id: Optional[str] = None
    dodo_subscription_id: Optional[str] = None
    dodo_signature: Optional[str] = None

# Plan Metadata
PLANS_DATA = {
    "Free": {"id": "plan_free", "credits": 100, "price": 0.0, "support": "Community", "max_upload": 1000, "api": False, "speed": "normal", "teams": 1},
    "Starter": {"id": "plan_starter", "credits": 50000, "price": 999.0, "support": "Email", "max_upload": 100000, "api": False, "speed": "normal", "teams": 1},
    "Growth": {"id": "plan_growth", "credits": 500000, "price": 4999.0, "support": "Priority", "max_upload": 1000000, "api": True, "speed": "fast", "teams": 3},
    "Enterprise": {"id": "plan_enterprise", "credits": 10000000, "price": 99999.0, "support": "Dedicated", "max_upload": 999999999, "api": True, "speed": "instant", "teams": 99}
}

CREDIT_PACKS = {
    "10k": {"credits": 10000, "price": 299.0},
    "50k": {"credits": 50000, "price": 999.0}
}

def verify_dodo_webhook(payload: bytes, headers: dict, secret: str) -> bool:
    webhook_id = headers.get("webhook-id")
    webhook_signature = headers.get("webhook-signature")
    webhook_timestamp = headers.get("webhook-timestamp")
    
    if not webhook_id or not webhook_signature or not webhook_timestamp:
        return False
        
    to_sign = f"{webhook_id}.{webhook_timestamp}.".encode("utf-8") + payload
    signatures = webhook_signature.split(" ")
    for sig in signatures:
        if "," in sig:
            version, signature_hash = sig.split(",", 1)
            if version == "v1":
                key = secret.encode("utf-8")
                expected_hash = hmac.new(key, to_sign, hashlib.sha256).hexdigest()
                if hmac.compare_digest(expected_hash, signature_hash):
                    return True
    return False

@router.get("/plans")
def get_plans():
    return PLANS_DATA

@router.get("/subscription")
def get_user_subscription(current_user: UserResponse = Depends(require_permission("billing.view"))):
    db = get_db()
    sub = db.execute("""
        SELECT plan_name, status, credits_allotted, credits_used, start_date, end_date, auto_renew 
        FROM subscriptions WHERE user_id = ? AND status = 'active'
        ORDER BY created_at DESC LIMIT 1
    """, [current_user.id]).fetchone()
    
    if not sub:
        # Default user to free plan if they don't have one
        return {
            "plan_name": "Free",
            "status": "active",
            "credits_allotted": 100,
            "credits_used": 0,
            "start_date": current_user.id, # mock starting timestamp
            "end_date": None,
            "auto_renew": False
        }
        
    return {
        "plan_name": sub[0],
        "status": sub[1],
        "credits_allotted": sub[2],
        "credits_used": sub[3],
        "start_date": sub[4],
        "end_date": sub[5],
        "auto_renew": sub[6]
    }

@router.get("/dashboard")
def get_billing_dashboard(current_user: UserResponse = Depends(require_permission("billing.view"))):
    db = get_db()
    
    # Subscription info
    sub = get_user_subscription(current_user)
    
    # Used credits this month
    # Calculate sum of credits used from credits_log / credit_transactions in the last 30 days
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    credits_used_row = db.execute("""
        SELECT COALESCE(SUM(credits_used), 0) FROM credits_log 
        WHERE user_id = ? AND created_at >= ?
    """, [current_user.id, thirty_days_ago]).fetchone()
    
    credits_used_this_month = credits_used_row[0] if credits_used_row else 0
    
    return {
        "plan": sub["plan_name"],
        "status": sub["status"],
        "credits_remaining": current_user.credit_pool,
        "credits_used_this_month": credits_used_this_month,
        "auto_renew": sub["auto_renew"],
        "expiry_date": sub["end_date"],
        "next_billing_date": sub["end_date"]
    }

@router.post("/checkout")
async def create_checkout(req: CheckoutRequest, current_user: UserResponse = Depends(require_permission("billing.manage"))):
    if not req.plan_name and not req.credits_pack:
        raise HTTPException(status_code=400, detail="Must select a plan or credits pack")
        
    db = get_db()
    checkout_id = str(uuid.uuid4())
    
    # Find amount and product details
    amount = 0.0
    plan_name = ""
    is_subscription = False
    
    if req.plan_name:
        plan = PLANS_DATA.get(req.plan_name)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        amount = plan["price"]
        plan_name = req.plan_name
        is_subscription = True
    else:
        pack = CREDIT_PACKS.get(req.credits_pack)
        if not pack:
            raise HTTPException(status_code=404, detail="Credits pack not found")
        amount = pack["price"]
        plan_name = f"{req.credits_pack} Credits Pack"
        is_subscription = False
        
    # Check if Dodo API keys are configured
    if settings.DODO_PAYMENTS_API_KEY:
        try:
            # Map plan to Dodo Product ID
            prod_id = settings.DODO_PRODUCT_STARTER_ID
            if req.plan_name == "Growth":
                prod_id = settings.DODO_PRODUCT_GROWTH_ID
            elif req.credits_pack == "10k":
                prod_id = settings.DODO_PRODUCT_10K_CREDITS_ID
            elif req.credits_pack == "50k":
                prod_id = settings.DODO_PRODUCT_50K_CREDITS_ID
                
            async with httpx.AsyncClient() as client:
                payload = {
                    "product_cart": [
                        {
                            "product_id": prod_id,
                            "quantity": 1
                        }
                    ],
                    "customer": {
                        "email": current_user.email,
                        "name": current_user.email.split('@')[0]
                    },
                    "metadata": {
                        "user_id": current_user.id,
                        "plan_name": plan_name,
                        "is_subscription": str(is_subscription),
                        "checkout_id": checkout_id
                    },
                    "return_url": f"http://localhost:5173/billing?session_id={checkout_id}"
                }
                headers = {
                    "Authorization": f"Bearer {settings.DODO_PAYMENTS_API_KEY}",
                    "Content-Type": "application/json"
                }
                
                resp = await client.post(
                    f"{settings.DODO_API_URL}/v1/checkout-sessions",
                    json=payload,
                    headers=headers
                )
                
                if resp.status_code != 200:
                    logger.error(f"Dodo payments checkout session creation failed: {resp.text}")
                    # Fallback to mock mode
                else:
                    dodo_data = resp.json()
                    checkout_url = dodo_data.get("checkout_url")
                    session_id = dodo_data.get("session_id")
                    
                    db.execute("""
                        INSERT INTO payments (id, user_id, checkout_session_id, payment_status, amount, plan_name)
                        VALUES (?, ?, ?, 'pending', ?, ?)
                    """, [checkout_id, current_user.id, session_id, amount, plan_name])
                    
                    return {"checkout_url": checkout_url, "session_id": session_id}
        except Exception as e:
            logger.error(f"Dodo payments api error: {e}")
            
    # Mock checkout mode fallback
    checkout_url = f"/billing?mock_checkout=true&session_id={checkout_id}"
    db.execute("""
        INSERT INTO payments (id, user_id, checkout_session_id, payment_status, amount, plan_name)
        VALUES (?, ?, ?, 'pending', ?, ?)
    """, [checkout_id, current_user.id, checkout_id, amount, plan_name])
    
    return {"checkout_url": checkout_url, "session_id": checkout_id}

@router.post("/verify")
async def verify_payment(req: VerifyPaymentRequest, current_user: UserResponse = Depends(require_permission("billing.manage"))):
    db = get_db()
    
    payment = db.execute("""
        SELECT id, user_id, amount, plan_name, payment_status FROM payments 
        WHERE checkout_session_id = ?
    """, [req.checkout_session_id]).fetchone()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment transaction not found")
        
    payment_id, user_id, amount, plan_name, status = payment
    
    if status == 'completed':
        return {"status": "success", "message": "Payment already processed"}
        
    # Perform credit allocation
    async with get_db_write_lock():
        # Update payment
        db.execute("""
            UPDATE payments SET payment_status = 'completed', transaction_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, [req.dodo_payment_id or "mock_txn_" + str(uuid.uuid4())[:8], payment_id])
        
        # Calculate credits to allocate
        credits_to_add = 0
        if "Credits Pack" in plan_name:
            pack_name = plan_name.split(" ")[0]
            credits_to_add = CREDIT_PACKS.get(pack_name, {}).get("credits", 0)
            db.execute("""
                UPDATE users SET credit_pool = credit_pool + ? WHERE id = ?
            """, [credits_to_add, user_id])
            
            db.execute("""
                INSERT INTO credit_transactions (id, user_id, amount, transaction_type, description)
                VALUES (?, ?, ?, 'purchase', ?)
            """, [str(uuid.uuid4()), user_id, credits_to_add, f"Purchased {plan_name}"])
        else:
            # Upgrade Subscription Plan
            plan_meta = PLANS_DATA.get(plan_name)
            if plan_meta:
                credits_to_add = plan_meta["credits"]
                
                # Terminate any old active subscription
                db.execute("""
                    UPDATE subscriptions SET status = 'expired' WHERE user_id = ? AND status = 'active'
                """, [user_id])
                
                # Create subscription
                sub_id = str(uuid.uuid4())
                start_date = datetime.now(timezone.utc)
                end_date = start_date + timedelta(days=30)
                
                db.execute("""
                    INSERT INTO subscriptions (id, user_id, plan_name, status, credits_allotted, start_date, end_date, auto_renew, dodo_subscription_id)
                    VALUES (?, ?, ?, 'active', ?, ?, ?, TRUE, ?)
                """, [sub_id, user_id, plan_name, 'active', credits_to_add, start_date, end_date, req.dodo_subscription_id or "mock_sub_" + str(uuid.uuid4())[:8]])
                
                # Update user tier & credits
                db.execute("""
                    UPDATE users SET tier = ?, credit_pool = credit_pool + ? WHERE id = ?
                """, [plan_name.lower(), credits_to_add, user_id])
                
                db.execute("""
                    INSERT INTO credit_transactions (id, user_id, amount, transaction_type, description)
                    VALUES (?, ?, ?, 'subscription', ?)
                """, [str(uuid.uuid4()), user_id, credits_to_add, f"Allotted credits from subscription: {plan_name}"])
                
        # Generate Invoice
        invoice_id = str(uuid.uuid4())
        invoice_num = f"INV-2026-{str(uuid.uuid4())[:6].upper()}"
        tax = round(amount * 0.18, 2) # 18% standard tax
        
        db.execute("""
            INSERT INTO invoices (id, user_id, payment_id, invoice_number, amount, tax, plan_name, status, billing_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'paid', CURRENT_TIMESTAMP)
        """, [invoice_id, user_id, payment_id, invoice_num, amount, tax, plan_name])
        
        # Link invoice back to payment
        db.execute("""
            UPDATE payments SET invoice_id = ? WHERE id = ?
        """, [invoice_id, payment_id])
        
        # Add to billing history
        db.execute("""
            INSERT INTO billing_history (id, user_id, payment_id, plan_name, amount, status)
            VALUES (?, ?, ?, ?, ?, 'completed')
        """, [str(uuid.uuid4()), user_id, payment_id, plan_name, amount])
        
    return {"status": "success", "message": "Payment verified and credits allocated successfully."}

@router.post("/cancel")
async def cancel_subscription(current_user: UserResponse = Depends(require_permission("billing.manage"))):
    db = get_db()
    
    # Get active subscription
    sub = db.execute("""
        SELECT id, dodo_subscription_id FROM subscriptions 
        WHERE user_id = ? AND status = 'active'
    """, [current_user.id]).fetchone()
    
    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription found")
        
    sub_id, dodo_sub_id = sub
    
    # Hit Dodo API if exists
    if settings.DODO_PAYMENTS_API_KEY and dodo_sub_id and not dodo_sub_id.startswith("mock_"):
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {settings.DODO_PAYMENTS_API_KEY}",
                    "Content-Type": "application/json"
                }
                # Call cancel endpoint
                await client.post(
                    f"{settings.DODO_API_URL}/v1/subscriptions/{dodo_sub_id}/cancel",
                    headers=headers
                )
        except Exception as e:
            logger.error(f"Dodo cancel API error: {e}")
            
    db.execute("""
        UPDATE subscriptions SET auto_renew = FALSE, status = 'cancelled' WHERE id = ?
    """, [sub_id])
    
    return {"status": "success", "message": "Subscription renewal cancelled successfully."}

@router.post("/change-plan")
async def change_plan(req: CheckoutRequest, current_user: UserResponse = Depends(require_permission("billing.manage"))):
    # Creates a checkout session to upgrade/downgrade plans
    return await create_checkout(req, current_user)

@router.get("/invoices")
def get_user_invoices(current_user: UserResponse = Depends(require_permission("billing.view"))):
    db = get_db()
    rows = db.execute("""
        SELECT i.id, i.invoice_number, i.billing_date, i.amount, i.tax, i.plan_name, i.status 
        FROM invoices i WHERE i.user_id = ?
        ORDER BY i.billing_date DESC
    """, [current_user.id]).fetchall()
    
    return [
        {
            "id": r[0],
            "invoice_number": r[1],
            "billing_date": r[2],
            "amount": r[3],
            "tax": r[4],
            "plan_name": r[5],
            "status": r[6]
        } for r in rows
    ]

@router.get("/payments")
def get_user_payments(current_user: UserResponse = Depends(require_permission("billing.view"))):
    db = get_db()
    rows = db.execute("""
        SELECT p.created_at, p.transaction_id, p.plan_name, p.amount, p.currency, p.payment_status, p.invoice_id 
        FROM payments p WHERE p.user_id = ?
        ORDER BY p.created_at DESC
    """, [current_user.id]).fetchall()
    
    return [
        {
            "payment_date": r[0],
            "transaction_id": r[1],
            "plan": r[2],
            "amount": r[3],
            "currency": r[4],
            "status": r[5],
            "invoice_id": r[6]
        } for r in rows
    ]

@router.get("/credits-history")
def get_user_credits_data(current_user: UserResponse = Depends(require_permission("credits.view"))):
    db = get_db()
    
    # Total purchased (sum of credit purchases)
    purchased_row = db.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM credit_transactions 
        WHERE user_id = ? AND amount > 0
    """, [current_user.id]).fetchone()
    
    # Total consumed (sum of negative credits_used)
    consumed_row = db.execute("""
        SELECT COALESCE(SUM(credits_used), 0) FROM credits_log 
        WHERE user_id = ?
    """, [current_user.id]).fetchone()
    
    purchased = purchased_row[0] if purchased_row else 0
    consumed = consumed_row[0] if consumed_row else 0
    
    # Recent credit transactions log
    transactions = db.execute("""
        SELECT id, amount, transaction_type, description, created_at 
        FROM credit_transactions WHERE user_id = ?
        ORDER BY created_at DESC LIMIT 20
    """, [current_user.id]).fetchall()
    
    return {
        "current_credits": current_user.credit_pool,
        "credits_purchased": purchased,
        "credits_consumed": consumed,
        "credits_remaining": current_user.credit_pool,
        "expiry": None,
        "transactions": [
            {
                "id": t[0],
                "amount": t[1],
                "type": t[2],
                "description": t[3],
                "date": t[4]
            } for t in transactions
        ]
    }

@router.get("/portal")
def get_customer_portal(current_user: UserResponse = Depends(require_permission("billing.manage"))):
    # Dodo Payments billing portal redirect link
    if settings.DODO_PAYMENTS_API_KEY:
        return {"portal_url": "https://test.dodopayments.com/customer-portal"}
    return {"portal_url": "/billing?mock_portal=true"}

@router.get("/invoices/{invoice_id}/download")
def download_invoice(invoice_id: str):
    # Generates a printable HTML version of the invoice
    db = get_db()
    row = db.execute("""
        SELECT i.invoice_number, i.billing_date, i.amount, i.tax, i.plan_name, u.email 
        FROM invoices i JOIN users u ON i.user_id = u.id 
        WHERE i.id = ?
    """, [invoice_id]).fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    num, date, amount, tax, plan, email = row
    subtotal = amount - tax
    
    html_content = f"""
    <html>
    <head>
        <title>Invoice {num}</title>
        <style>
            body {{ font-family: Arial, sans-serif; color: #333; padding: 40px; background-color: #fafafa; }}
            .invoice-box {{ max-width: 800px; margin: auto; padding: 30px; border: 1px solid #eee; background-color: #fff; box-shadow: 0 0 10px rgba(0, 0, 0, 0.15); }}
            .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #6366f1; padding-bottom: 20px; }}
            .title {{ font-size: 28px; font-weight: bold; color: #6366f1; }}
            .meta {{ text-align: right; }}
            .details {{ margin-top: 30px; display: flex; justify-content: space-between; }}
            .table {{ width: 100%; border-collapse: collapse; margin-top: 40px; }}
            .table th {{ background-color: #f3f4f6; text-align: left; padding: 10px; border-bottom: 1px solid #ddd; }}
            .table td {{ padding: 10px; border-bottom: 1px solid #eee; }}
            .total-section {{ text-align: right; margin-top: 30px; font-size: 16px; }}
            .total-line {{ display: flex; justify-content: flex-end; gap: 20px; margin-bottom: 5px; }}
            .grand-total {{ font-size: 18px; font-weight: bold; color: #6366f1; }}
            .footer {{ text-align: center; margin-top: 50px; font-size: 12px; color: #999; border-top: 1px dashed #ddd; padding-top: 20px; }}
        </style>
    </head>
    <body onload="window.print()">
        <div class="invoice-box">
            <div class="header">
                <div>
                    <div class="title">EmailVerif</div>
                    <div>Email Verification SaaS</div>
                </div>
                <div class="meta">
                    <div><strong>Invoice:</strong> {num}</div>
                    <div><strong>Date:</strong> {date}</div>
                </div>
            </div>
            
            <div class="details">
                <div>
                    <strong>Billed To:</strong><br>
                    {email}
                </div>
                <div>
                    <strong>Payee Details:</strong><br>
                    EmailVerif Portal Inc.<br>
                    Bangalore, India
                </div>
            </div>
            
            <table class="table">
                <thead>
                    <tr>
                        <th>Item Description</th>
                        <th>Qty</th>
                        <th>Rate</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{plan} Package Allotment</td>
                        <td>1</td>
                        <td>INR {subtotal:.2f}</td>
                        <td>INR {subtotal:.2f}</td>
                    </tr>
                </tbody>
            </table>
            
            <div class="total-section">
                <div class="total-line">
                    <span>Subtotal:</span>
                    <span>INR {subtotal:.2f}</span>
                </div>
                <div class="total-line">
                    <span>GST (18%):</span>
                    <span>INR {tax:.2f}</span>
                </div>
                <div class="total-line grand-total">
                    <span>Grand Total:</span>
                    <span>INR {amount:.2f}</span>
                </div>
            </div>
            
            <div class="footer">
                Thank you for your business! If you have any inquiries regarding this invoice, please reach out to support@emailverif.com.
            </div>
        </div>
    </body>
    </html>
    """
    return Response(content=html_content, media_type="text/html")

@router.post("/webhook")
async def dodo_webhook(request: Request):
    payload = await request.body()
    headers = request.headers
    
    # Check Webhook Secret
    if settings.DODO_WEBHOOK_KEY:
        signature = headers.get("webhook-signature")
        if not signature:
            raise HTTPException(status_code=400, detail="Missing webhook signature")
        if not verify_dodo_webhook(payload, headers, settings.DODO_WEBHOOK_KEY):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
            
    # Parse Payload
    try:
        event = json.loads(payload.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed JSON payload")
        
    event_type = event.get("type")
    data = event.get("data", {})
    
    logger.info(f"Received Dodo Payments webhook: {event_type}")
    
    db = get_db()
    
    # Verify Idempotency - check if already logged in payment_transactions
    event_id = event.get("id")
    if event_id:
        existing = db.execute("SELECT id FROM payment_transactions WHERE id = ?", [event_id]).fetchone()
        if existing:
            return {"status": "skipped", "message": "Duplicate event"}
            
    # Process Webhook Events
    if event_type == "checkout.completed":
        session_id = data.get("session_id")
        payment_id = data.get("payment_id")
        subscription_id = data.get("subscription_id")
        metadata = data.get("metadata", {})
        user_id = metadata.get("user_id")
        plan_name = metadata.get("plan_name")
        amount = data.get("amount")
        
        # Verify the record exists
        payment_row = db.execute("""
            SELECT id FROM payments WHERE checkout_session_id = ?
        """, [session_id]).fetchone()
        
        if payment_row:
            pay_db_id = payment_row[0]
            # Perform verification flow programmatically
            verify_req = VerifyPaymentRequest(
                checkout_session_id=session_id,
                dodo_payment_id=payment_id,
                dodo_subscription_id=subscription_id
            )
            # Fetch current context manually and execute verify_payment logic
            class MockResponse:
                id = user_id
                email = data.get("customer", {}).get("email")
            # Trigger allocation
            try:
                db_p = db.execute("SELECT payment_status FROM payments WHERE id = ?", [pay_db_id]).fetchone()
                if db_p and db_p[0] != 'completed':
                    await verify_payment(verify_req, current_user=MockResponse())
            except Exception as e:
                logger.error(f"Error during webhook credit allocation: {e}")
                
        # Log event transaction
        db.execute("""
            INSERT INTO payment_transactions (id, payment_id, event_type, status, raw_payload)
            VALUES (?, ?, 'checkout.completed', 'success', ?)
        """, [event_id or str(uuid.uuid4()), session_id, json.dumps(event)])

    elif event_type == "payment.succeeded":
        payment_id = data.get("payment_id")
        pass
    elif event_type == "payment.failed":
        payment_id = data.get("payment_id")
        pass
    elif event_type == "subscription.cancelled":
        sub_id = data.get("subscription_id")
        db.execute("""
            UPDATE subscriptions SET status = 'cancelled', auto_renew = FALSE WHERE dodo_subscription_id = ?
        """, [sub_id])
        
    return {"status": "success"}

# --- Admin Dashboard Stats Endpoint ---
@router.get("/admin/stats")
def get_admin_billing_stats(current_user: UserResponse = Depends(require_permission("admin.view"))):
    if current_user.role not in ('admin', 'superadmin'):
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    db = get_db()
    
    # Total Revenue
    total_rev_row = db.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE payment_status = 'completed'").fetchone()
    total_rev = total_rev_row[0] if total_rev_row else 0
    
    # Monthly Revenue (last 30 days)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    monthly_rev_row = db.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE payment_status = 'completed' AND created_at >= ?", [thirty_days_ago]).fetchone()
    monthly_rev = monthly_rev_row[0] if monthly_rev_row else 0
    
    # Active Subscribers
    active_subs_row = db.execute("SELECT COUNT(*) FROM subscriptions WHERE status = 'active'").fetchone()
    active_subs = active_subs_row[0] if active_subs_row else 0
    
    # Failed Payments
    failed_pays_row = db.execute("SELECT COUNT(*) FROM payments WHERE payment_status = 'failed'").fetchone()
    failed_pays = failed_pays_row[0] if failed_pays_row else 0
    
    # Credits Sold
    credits_sold_row = db.execute("SELECT COALESCE(SUM(amount), 0) FROM credit_transactions WHERE amount > 0").fetchone()
    credits_sold = credits_sold_row[0] if credits_sold_row else 0
    
    # Credits Consumed
    credits_consumed_row = db.execute("SELECT COALESCE(SUM(credits_used), 0) FROM credits_log").fetchone()
    credits_consumed = credits_consumed_row[0] if credits_consumed_row else 0
    
    # Most Popular Plan
    popular_plan_row = db.execute("""
        SELECT plan_name, COUNT(*) as cnt FROM subscriptions 
        GROUP BY plan_name ORDER BY cnt DESC LIMIT 1
    """).fetchone()
    popular_plan = popular_plan_row[0] if popular_plan_row else "Free"
    
    return {
        "total_revenue": total_rev,
        "monthly_revenue": monthly_rev,
        "active_subscribers": active_subs,
        "failed_payments": failed_pays,
        "credits_sold": credits_sold,
        "credits_consumed": credits_consumed,
        "popular_plan": popular_plan
    }
