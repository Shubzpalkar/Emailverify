# Email Verification Portal - Documentation

This document provides a comprehensive overview of the Email Verification Portal, covering the Product Requirements (PRD) and Technical Architecture.

---

## 1. Product Requirements Document (PRD)

### 1.1 Objective
The Email Verification Portal is a self-hosted, professional-grade tool designed to clean email lists and verify deliverability without relying on expensive external APIs. It aims to achieve 85-95% accuracy by simulating enterprise-level verification pipelines (similar to ZeroBounce or UseBouncer).

### 1.2 Target Audience
- **Growth Marketers**: To maintain high sender reputation and low bounce rates.
- **SaaS Developers**: To integrate clean user onboarding flows.
- **Sales Teams**: To verify prospect lists before cold outreach.

### 1.3 Core Features
- **High-Accuracy Verification**: Multi-layered checks including Syntax, DNS, SMTP, and Catch-All.
- **Bulk Processing**: Support for CSV, XLSX, and TXT files with millions of rows.
- **Credit System**: Internal economy to manage and limit user usage.
- **Admin Panel**: Control panel for administrators to manage their users and allocate verification credits.
- **Superadmin Panel**: Global control center for system configuration, managing Admin pools, monitoring system metrics, and impersonating users for diagnostic support.
- **Intelligent Caching**: Reuses verification results and domain behaviors to improve speed and bypass IP rate limits.
- **Password Reset**: Secure, token-based recovery system with 1-hour expiration.
- **API Access**: Programmatic verification via SHA-256 hashed API keys.
- **PTR Validation**: Reverse DNS checks on target MX IPs for advanced delivery diagnostics.
- **Multi-Plan Billing Portal**: Transparent pricing tier system (Free, Starter, Growth, Enterprise) built with structured comparison and interactive features.

### 1.4 Status Classifications
| Status | Description |
| :--- | :--- |
| **Valid** | Email passed all checks (Syntax, DNS, SMTP). |
| **Invalid** | Definitively undeliverable (Syntax error or User not found). |
| **Risky** | Verification was blocked (Spamhaus) or result is uncertain. |
| **Catch_all** | Domain accepts all mail; individual mailbox cannot be verified. |
| **Disposable** | Known temporary/burnable email address. |
| **Role_based** | Shared inbox (e.g., admin@, support@). |
| **Unknown** | Temporary server error or timeout. |

---

## 2. Technical Documentation

### 2.1 Technology Stack
- **Backend**: Python 3.x with **FastAPI**.
- **Database**: **DuckDB** (Sole database for storage and analytical queries).
- **Network Stack**: `aiodns` (Async DNS) and `aiosmtplib` (Async SMTP).
- **Data Handling**: `pandas` and `openpyxl` for high-speed file parsing.
- **Frontend**: **React** (Vite) with React Router, Phosphor Icons, and CSS (Glassmorphism).

### 2.2 Project Structure & Components

#### 2.2.1 Backend (`/backend`)
The backend is a monolithic FastAPI application designed for high-concurrency background processing and state management via DuckDB.

| File / Folder | Purpose / Responsibility |
| :--- | :--- |
| **`main.py`** | Application entry point. Configures the FastAPI app, CORS middleware, router registration, and the async lifespan context for Database initialization. |
| **`config.py`** | Environment configuration. Loads `.env` variables (or defaults) using Pydantic `BaseSettings`. Handles JWT secrets, token expiry, database pathing, and global rate limits. |
| **`database.py`** | Interface for DuckDB. Manages connection pooling (via thread-local variables since DuckDB connections aren't thread-safe for writing), schema creation (`users`, `verification_jobs`, `verification_results`, `email_cache`), and provides the `get_db()` dependency injection. |
| **`auth.py`** | Authentication logic. Integrates with Firebase Admin SDK (`firebase_auth.py`) to verify tokens, syncs Firebase users with the DuckDB database (`sync_firebase_user`), and provides dependency functions like `get_current_user` and `require_superadmin` to lock down protected routes. |
| **`routes.py`** | HTTP API Endpoints. Groups endpoints via `APIRouter` for `/auth`, `/jobs` (file upload and progress polling), `/dashboard` (metrics aggregation), `/admin` (user management), and `/superadmin` (admin setup, credit pools, and user impersonation). |
| **`engine.py`** | Core Verification Logic. Executes the 7-step pipeline on a single email. Handles syntax regex, cached result lookups, DNS MX record resolution, disposable domain checking, role-based account fuzzy matching, and deep SMTP handshakes. |
| **`smtp_verifier.py`** | SMTP Connection Handler. Uses `aiosmtplib` to connect to target MX servers, send `HELO/EHLO`, `MAIL FROM`, and `RCPT TO` commands. Implements smart retries for Greylisting (450) and handles SSL/TLS downgrades. |
| **`dns_checks.py`** | Async DNS Resolver. Now includes **PTR Validation** (Reverse DNS) to detect if target mail servers or sender IPs lack valid hostnames, providing diagnostic context in SMTP responses. |
| **`email_service.py`** | Transactional Mail Service. Employs `aiosmtplib` to send welcome messages and password reset tokens. Incorporates terminal output fallback logging for local development. |
| **`worker.py`** | Background Processing Engine. Consumes uploaded CSV lists in the background using `asyncio.gather`. Enforces concurrency limits (`asyncio.Semaphore`) per domain and global rate limits to prevent IP blacklisting. Logs detailed progress to the terminal and batches write-backs to DuckDB. |

#### 2.2.2 Frontend (`/frontend`)
The frontend is a React Single Page Application (SPA) built with Vite, utilizing a custom CSS variables design system for a premium glassmorphism aesthetic.

| File / Folder | Purpose / Responsibility |
| :--- | :--- |
| **`src/main.jsx` & `App.jsx`** | Application roots. `main.jsx` wraps the app in context providers (`BrowserRouter`, `AuthProvider`, `ToastProvider`). `App.jsx` defines local routing rules, distinguishing public paths vs. `ProtectedRoute` wrapper logic. |
| **`src/index.css`** | Global Design System. Contains CSS custom properties (`--primary`, `--bg-surface`), glassmorphism card utilities, button styles, table layouts, and typography resets. |
| **`src/api/client.js`** | Centralized API Client. A wrapper around the native `fetch` API. Automatically handles cookie inclusion for auth, sets standard headers, natively handles `FormData` for file uploads, and intercepts/normalizes API error responses. |
| **`src/context/AuthContext.jsx`** | Global User State. Listens to Firebase Auth state via `onIdTokenChanged`. Syncs identity with the backend (`/auth/sync-user`). Provides `login`, `signup`, `googleLogin`, `logout`, and context variables to all components without prop-drilling. |
| **`src/components/`** | Reusable UI Elements. Contains the responsive `Navbar.jsx`, auth-guard `ProtectedRoute.jsx`, and the floating notification system `Toast.jsx` with its animations. |
| **`src/pages/Landing.jsx`** | Marketing entry point containing hero sections and a 3D CSS mockup card visualizing sample verification results. |
| **`src/pages/Pricing.jsx`** | Plan presentation page displaying feature comparisons, FAQs, and subscription tiers. |
| **`src/pages/Auth.css` / `.jsx`** | Shared styles and logic for `Login.jsx` and `Signup.jsx` forms. |
| **`src/pages/Dashboard.jsx`** | User Hub. Displays total verification metrics, remaining credits, and a table of recent jobs. Utilizes a recursive `setInterval` polling loop (every 5s) if any job is currently in "processing" state to update progress bars. |
| **`src/pages/ForgotPassword.jsx`** | Password Recovery. Allows users to request a timed reset link via email (currently prints to backend console). |
| **`src/pages/ResetPassword.jsx`** | Secure Reset. Captures tokens from URL to allow setting a new account password. |
| **`src/pages/APIKeys.jsx`** | Developer Settings. Interface to generate (with sk_live_ prefix), monitor, and revoke programmatic API keys. |
| **`src/pages/Verify.jsx`** | Action Center. Provides a drag-and-drop file upload zone for bulk CSV verification (converting files to `FormData` and POSTing to backend) and a single-email checking form with detailed confidence-scoring results. |
| **`src/pages/Admin.jsx`** | Management Interface. Protected route (`role === 'admin' || role === 'superadmin'`) to view all registered users and assign virtual credits. |
| **`src/pages/SuperAdmin.jsx`** | Global Control Panel. Protected route (`role === 'superadmin'`) that displays overall platform metrics, creates/suspends admins, adjusts credit pools, and enables user session impersonation. |
| **`vite.config.js`** | Dev Server config. Noteworthy for its explicit proxying of any `/api` prefix request straight to localhost:8000 to bypass CORS during local development. |

### 2.3 System Architecture
The application follows a modular, asynchronous architecture:
- **API Layer**: Handles HTTP requests, JWT authentication, and file ingestion.
- **Worker Layer**: A background processing pool using `asyncio` and `RateLimiter`.
- **Engine Layer**: The core logic that executes the 7-step verification pipeline.
- **Intelligence Layer**: DuckDB-backed cache that persists domain behaviors.

### 2.3.1 Role Hierarchy & Authorization Flow
The portal implements a three-tier access control structure to manage credit economics and platform security:
```mermaid
graph TD
    SA[Superadmin] -->|Allocates Credits & Manages| A[Admins]
    SA -->|Impersonates & Suspends| U[Users]
    A -->|Spawns & Funds Credits| U
    U -->|Uses Credits to Verify| V[Verification Engine]
```
1. **Superadmin (`superadmin`)**: 
   - Root privileges. Accesses global statistics across all users.
   - Manages, suspends, and allocates credit pools for individual `Admins`.
   - **User Impersonation**: Temporarily generates an authorized session for any tenant's ID via the `/api/superadmin/impersonate/{user_id}` route to aid in support and diagnostic operations.
2. **Admin (`admin`)**:
   - Intermediate privileges. Manages a subset of `Users` linked through `admin_id`.
   - Distributes credits from their own pool to these managed accounts.
3. **User (`user`)**:
   - Standard privileges. Accesses files, API keys, and dashboard.
   - Runs verification jobs costing 1 credit per checked email.

### 2.3.2 Firebase Authentication Integration
Identity management is decoupled from internal role/credit state through Firebase:
- **Frontend**: The React client uses the Firebase Client SDK to handle login, signup, and Google OAuth. The `AuthContext` uses `onIdTokenChanged` to reactively capture token refreshes and session changes.
- **Backend Sync**: Upon login, the frontend passes the Firebase token to the FastAPI backend (`/api/auth/sync-user`). The backend uses the `firebase-admin` SDK to verify the token, then upserts the user profile into the DuckDB `users` table.
- **Authorization Layer**: API endpoints are secured via FastAPI dependencies (e.g., `verify_firebase_token`, `get_current_user`) which assert the validity of the Firebase token and retrieve the mapped user from DuckDB (enforcing `is_active` and `email_verified` states).

### 2.3.3 Pricing & Credit Architecture
- **Free**: 100 one-time credits, single + file checks, dashboard.
- **Starter**: 50,000 monthly credits, priority processing, standard validation.
- **Growth**: 500,000 monthly credits, Developer API access (`sk_live_` prefixed keys), advanced cache lookups.
- **Enterprise**: Unlimited credits, custom SLA, dedicated hosting support.

### 2.4 Verification Pipeline (The "Pro Engine")
1. **Syntax Validation**: Strict Regex + Double-dot check.
2. **Cache Check**: Instant lookup in `email_cache` for recent results.
3. **Domain Intelligence**: Lookup in `domain_intelligence` (skips DNS/Catch-All if known).
4. **DNS lookup**: Resolves A/MX records using Google/Cloudflare resolvers.
5. **SMTP Handshake**: Connects to the MX server.
6. **Smart Retries**: Handles Greylisting (450) and Temporary Blocks (421) with a 5s/30s/120s backoff.
7. **Scoring**: Calculates a `0.0 - 1.0` confidence score based on all above factors.

### 2.5 Security & Optimizations
- **Rate Limiting**: Throttles verifications to 100/min globally and 5 concurrent per domain to avoid IP blacklisting.
- **HTTP-Only Cookies**: JWT tokens are stored securely to prevent XSS.
- **API Key Security**: Keys are stored as SHA-256 hashes; raw keys are only shown once upon creation and never stored.
- **Timed Tokens**: Password reset tokens use `itsdangerous` signed serializers with a strict 60-minute TTL.
- **DuckDB Concurrency**: Uses multi-threading (`PRAGMA threads`) for fast data analysis.

### 2.6 Logging & Monitoring
Real-time verification progress is streamed directly to the backend terminal using Python's `logging` module. 
When a list is processed, the background worker outputs detailed, emoji-coded progress indicators:
- `🚀` Job Start, `📊` Domain Stats
- `✅` Valid, `❌` Invalid, `🗑️` Disposable, `📬` Catch-all, `👥` Role-based, `❓` Unknown
- `📈` Progress Milestones (every 50 emails)
- `🎉` Job Completion Summary

---

## 3. Operations & Deployment

### 3.1 Local Setup

#### Option A: Running on Windows Command Prompt (cmd)

**Backend**:
```cmd
cd backend
venv\Scripts\activate
uvicorn main:app --port 8000
```
*(Alternatively, launch without activation: `backend\venv\Scripts\python -m uvicorn main:app --port 8000`)*

**Frontend**:
```cmd
cd frontend
npm install
npm run dev
```

#### Option B: Running on Linux / macOS / Git Bash

**Backend**:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8000
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev
```

The frontend dev server runs on `http://localhost:5173` and proxies API calls to the backend on `:8000`.

### 3.2 Professional Deployment (Recommended)
To achieve high accuracy, deploy the portal on a **VPS with a dedicated IP** (DigitalOcean, AWS, Vultr).
> [!IMPORTANT]
> Residential IPs are often on the "Spamhaus PBL", which causes most professional mail servers to block SMTP handshakes. A VPS IP provides the "trust" needed for 250 OK responses.

---

## 4. Enterprise Documentation

### SECTION 1: END-TO-END USER WORKFLOW

#### 1. Simple Explanation
This section outlines the entire journey of a user interacting with our Email Verification SaaS platform. It begins when an anonymous visitor lands on the homepage, signs up for a free account, tests the verification tool with free credits, exhausts their trial limit, purchases a subscription plan, and continues processing larger email lists.

#### 2. Detailed Technical Workflow
```mermaid
graph TD
    A[Visitor arrives at Landing Page] --> B[Signs up for Free Account]
    B --> C[Account Created + 100 Free Credits Allocated]
    C --> D[Accesses Dashboard]
    D --> E[Uploads CSV/XLSX or inputs Single Email]
    E --> F[Verification Job Queued in DuckDB]
    F --> G[Async Worker processes list via SMTP Engine]
    G --> H[Results written to DB & downloadable as Clean CSV]
    H --> I{Credits Exhausted?}
    I -->|No| D
    I -->|Yes| J[Redirected to Pricing Page]
    J --> K[Initiates checkout flow via Payment Gateway]
    K --> L{Payment Confirmed via Webhook?}
    L -->|Yes| M[Allocation of plan credits to User Account]
    L -->|No| N[Payment Failure Screen & retry invitation]
    M --> O[System unlocks dashboard & resumes queues]
    N --> J
```

1. **Discovery & Onboarding**: The visitor arrives at the Landing Page. Clicking "Start Free" takes them to the signup page where the backend registers the user, flags them as active, and adds a transaction entry allocating 100 free credits.
2. **First Interaction**: The user accesses the dashboard. They can either type a single email address for immediate check or drag-and-drop a CSV file containing lists.
3. **Queue & Processing**: Once a CSV is uploaded, a job is generated in `verification_jobs` with status `queued`. The Python background worker detects the job, sets it to `processing`, and begins validating addresses concurrently using `aiosmtplib`.
4. **Acquisition & Limit Check**: On completing the list, the user downloads the results. The backend deducts credits equal to the successfully processed records. If the balance reaches 0, the dashboard blocks further uploads and redirects them to `/pricing`.
5. **Monetization**: The user purchases a paid tier. The gateway issues a webhook upon completion, which increments the user's credits and updates the billing history.

---

### SECTION 2: BILLING ARCHITECTURE

#### 1. Simple Explanation
The billing system manages subscription plans, payment processing, credit provisioning, payment failures, refunds, and invoice rendering. It ensures that credit adjustments happen transactionally and security checks validate all webhook events from payment processors.

#### 2. Detailed Billing Workflow
```mermaid
stateDiagram-v2
    [*] --> OrderCreated: User selects plan & checks out
    OrderCreated --> PaymentPending: Redirect to Gateway
    PaymentPending --> WebhookReceived: Gateway issues payment status
    PaymentPending --> Timeout: 15-minute expiry exceeded
    Timeout --> PaymentFailed
    WebhookReceived --> PaymentAuthorized: Payment is valid & authenticated
    WebhookReceived --> PaymentFailed: Gateway reports decline
    PaymentAuthorized --> CreditsAllocated: Transaction committed in credit_transactions
    CreditsAllocated --> InvoiceGenerated: PDF invoice rendered & logged
    InvoiceGenerated --> [*]
    PaymentFailed --> RetryCheckout: User initiates new payment
    RetryCheckout --> PaymentPending
```

- **Subscription Plans**:
  - **Free**: 100 one-time credits.
  - **Starter**: ₹999/mo (50,000 credits).
  - **Growth**: ₹4,999/mo (500,000 credits, API Access).
  - **Enterprise**: Custom pricing (unlimited scaling, dedicated Support).
- **Payment Verification Flow**:
  1. **Order Creation**: Frontend calls `POST /api/billing/order` with the selected `plan_id`. The backend creates a record in the `payments` table with `status="pending"`.
  2. **Gateway Hook**: The gateway processes card inputs and fires a POST webhook with a signature header containing an HMAC-SHA256 hash.
  3. **Signature Checking**: The backend computes the hash of the raw body using the shared webhook secret and rejects mismatches with `401 Unauthorized`.
  4. **Allocation**: Once validated, the backend starts a transaction updating the payment record to `completed`, creating a record in `credit_transactions`, and updating the `users.credits` balance.
- **Failures & Refunds**: If the webhook reports a failure, the transaction is marked `failed`. For approved refunds, the Superadmin allocates negative offset logs in `credit_transactions` and flags the original invoice.
- **Schema & Database Tables**:
  - `plans`: ID, name, price, credit_allotment, rate_limit, api_access (boolean).
  - `payments`: ID, user_id, order_id, status, amount, gateway, response_payload, created_at.
  - `credit_transactions`: ID, user_id, amount, source (payment/admin_bonus/verify_deduct), reference_id, created_at.
  - `billing_history`: ID, user_id, payment_id, invoice_number, pdf_path, generated_at.

---

### SECTION 3: CREDIT MANAGEMENT

#### 1. Simple Explanation
Credits are the primary currency of the platform. One validation check costs exactly one credit. The system tracks purchases, usage deductions, support refunds (e.g., if checking an email returns an "Unknown" status), and administrative allocations.

#### 2. Detailed Technical Architecture
```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Portal as React Dashboard
    participant Backend as FastAPI Instance
    participant DB as DuckDB (credit_transactions)

    User->>Portal: Uploads CSV list (1,000 lines)
    Portal->>Backend: Request job authorization
    Backend->>DB: Check if user.credits >= 1000
    alt Insufficient Credits
        DB-->>Backend: Balance: 300
        Backend-->>Portal: HTTP 402 Payment Required
    else Sufficient Credits
        DB-->>Backend: Balance: 5000
        Backend->>DB: Lock 1,000 credits (Deduct pending)
        Backend->>Portal: HTTP 202 Job Started
        Note over Backend, DB: Worker processes checks...
        Backend->>DB: Finalize deductions based on valid/invalid results. Refund 50 'Unknown' statuses.
    end
```

- **Credit Categories**:
  - **Purchased**: Standard credits loaded via card transactions. Never expire.
  - **Monthly Allocations**: Issued on active recurring subscription cycles. Expire at the end of the billing period unless rollover terms apply.
  - **Bonus/Promo**: Added by system triggers or admin promotions.
  - **Admin/Superadmin Allocations**: Superadmins can grant direct additions or offsets to users or admin pools.
- **Audit Logging**: Any credit adjustment must write to the `credit_transactions` table. Deductions use negative integers, allocations use positive integers. Direct mutation of the `users.credits` column without a matching record in `credit_transactions` is strictly forbidden to preserve audit integrity.

---

### SECTION 4: VERIFICATION JOB LIFECYCLE

#### 1. Simple Explanation
When a user uploads a file, it does not get processed instantly. It goes through a series of states in a queue to manage system resources and prevent overloading mail servers.

#### 2. Technical States & Transition Flow
```mermaid
stateDiagram-v2
    [*] --> Created: File received & parsed
    Created --> Queued: User credits validated and reserved
    Queued --> Processing: Worker grabs job from FIFO queue
    Processing --> Retry: Rate-limiting / Temporary grey-list block (450)
    Retry --> Processing: Backoff timer expires
    Processing --> Completed: All records processed & saved
    Processing --> Failed: System crash, disk space exhaustion, or DB lock
    Processing --> Cancelled: Aborted by User
    Completed --> Archived: Deleted from disk (retention duration met)
    Failed --> Archived
    Cancelled --> Archived
    Archived --> [*]
```

- **State Definitions**:
  - `Created`: The file has been successfully uploaded to the storage path, and schema structure checks are complete.
  - `Queued`: The credit requirement has been calculated and locked from the user’s account. The job sits in the queue.
  - `Processing`: An active thread pool in the worker processes batches of verification records.
  - `Retry`: A temporary error (such as a 450 greylisting or 421 transient block) prompts the worker to wait and retry.
  - `Completed`: Results are fully written to DuckDB. The user’s credit balance is finalized based on actual checks.
  - `Failed`: An unhandled exception or system shutdown aborts the process.
  - `Cancelled`: The user clicks the cancel button. Active threads terminate processing for this job.
  - `Archived`: The job metadata remains, but the detailed results and source CSV file are wiped from disk.

---

### SECTION 5: VERIFICATION HISTORY

#### 1. Simple Explanation
Verification history logs past jobs, allowing users to view analytics, search old files, re-download cleaned results, and permanently delete their data.

#### 2. Detailed Technical Design
- **Query Optimizations**: DuckDB indexes are generated on the `user_id` and `created_at` fields in the `verification_jobs` table to ensure fast list loading.
- **Search & Filters**: Users can query jobs by filename and filter by status (`completed`, `processing`, `failed`) or date ranges.
- **CSV Expiry and Retention**:
  - Uploaded files and detailed records in `verification_results` are kept for **30 days**.
  - A cron job runs daily at `00:00 UTC` and deletes detailed result records and files for jobs where `created_at < NOW() - INTERVAL 30 DAYS`.
  - The job metadata (ID, totals, cost, date) is preserved permanently for billing audits.

---

### SECTION 6: PUBLIC API DOCUMENTATION

#### 1. Simple Explanation
The Developer API allows businesses to integrate our verification engine directly into their signup forms, CRMs, or backend databases.

#### 2. API Technical Specifications
- **Base URL**: `https://api.emailverif.com/v1`
- **Authentication**: Bearer Token in HTTP Header.
  ```http
  Authorization: Bearer <YOUR_API_KEY>
  ```
- **Rate Limiting**: Integrated via Redis/FastAPI Middleware. Single endpoint: 60 requests/minute. Bulk endpoint: 10 requests/hour.
- **Global Error Formats**:
  ```json
  {
    "error": {
      "code": "RATE_LIMIT_EXCEEDED",
      "message": "You have exceeded your limit of 60 requests per minute.",
      "details": {}
    }
  }
  ```

#### 3. API Endpoints

##### 1. Single Verification: `POST /verify`
Verify one email address in real-time.
- **Request Example**:
  ```json
  {
    "email": "test.user@gmail.com"
  }
  ```
- **Response Example (200 OK)**:
  ```json
  {
    "email": "test.user@gmail.com",
    "status": "valid",
    "score": 0.98,
    "checks": {
      "syntax": true,
      "dns_mx": true,
      "disposable": false,
      "role": false,
      "smtp_handshake": true,
      "catch_all": false,
      "ptr_valid": true
    }
  }
  ```

##### 2. Bulk Verification: `POST /bulk`
Upload a list of emails to verify in the background.
- **Request (Multipart Form-Data)**:
  - `file`: CSV file containing email column.
- **Response Example (202 Accepted)**:
  ```json
  {
    "job_id": "job_abc123xyz",
    "status": "queued",
    "total_emails": 15200,
    "created_at": "2026-06-30T06:00:00Z"
  }
  ```

##### 3. Get Job Status: `GET /job/{job_id}`
Retrieve progress of a bulk verification job.
- **Response Example (200 OK)**:
  ```json
  {
    "job_id": "job_abc123xyz",
    "status": "processing",
    "progress": {
      "total": 15200,
      "processed": 8400,
      "valid": 6100,
      "invalid": 2000,
      "risky": 300
    }
  }
  ```

##### 4. Get Credits: `GET /credits`
- **Response Example (200 OK)**:
  ```json
  {
    "credits": 42100,
    "tier": "Growth"
  }
  ```

---

### SECTION 7: EMAIL SERVICE

#### 1. Simple Explanation
The platform automatically sends system emails to notify users about events like list completion, payment updates, password recoveries, or welcome greetings.

#### 2. Service Logic & Resiliency
- **Backend Class**: `EmailService` (implemented in `backend/email_service.py`).
- **Templates**: Built with responsive HTML/CSS using inline styles.
- **Resiliency Retry Pattern**:
  ```python
  import asyncio
  import logging

  logger = logging.getLogger("email")

  async def send_with_retry(email_func, *args, retries=3, delay=5):
      for attempt in range(retries):
          try:
              return await email_func(*args)
          except Exception as e:
              logger.warning(f"Email failure (attempt {attempt+1}/{retries}): {e}")
              if attempt < retries - 1:
                  await asyncio.sleep(delay * (2 ** attempt))
      logger.error("Failed to send email after maximum retries.")
      return False
  ```
- **SMTP Configuration Variables**:
  - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS`, `SMTP_SENDER`.

---

### SECTION 8: PRODUCTION VPS ARCHITECTURE

#### 1. Simple Explanation
This section outlines the setup required to run the application in a secure, stable, and highly performant production environment on a Virtual Private Server (VPS).

#### 2. System Architecture Diagram
```mermaid
graph TD
    Client([Internet User]) -->|HTTPS:443| CF[Cloudflare Proxy / WAF]
    CF -->|Proxy Pass| Nginx[Nginx Reverse Proxy]
    Nginx -->|Serves Static files| ReactSPA[React Vite Built Files]
    Nginx -->|Proxy Pass:8000| FastAPI[FastAPI Backend]
    FastAPI -->|Write Jobs / Cache| DuckDB[(DuckDB Database)]
    FastAPI -->|Trigger Processes| Worker[Background Asyncio Worker]
    Worker -->|Read/Write Jobs| DuckDB
    Worker -->|Perform SMTP Checks| TargetMX[External SMTP Mail Servers]
```

#### 3. Setup Specifications
- **SSL Configuration**: Nginx uses Let's Encrypt certificates updated automatically by a `certbot` renew timer.
- **Firewall Rules**: `UFW` blocks all ports except `22` (SSH - key-based auth only), `80` (HTTP - redirected to 443), and `443` (HTTPS).
- **Systemd Services**:
  - **FastAPI Backend Service (`/etc/systemd/system/fastapi.service`)**:
    ```ini
    [Unit]
    Description=FastAPI Backend
    After=network.target

    [Service]
    User=apprunner
    WorkingDirectory=/home/apprunner/email/backend
    ExecStart=/home/apprunner/email/backend/venv/Scripts/python -m uvicorn main:app --host 127.0.0.1 --port 8000
    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```
  - **Worker Service (`/etc/systemd/system/worker.service`)**:
    ```ini
    [Unit]
    Description=FastAPI Background Worker
    After=network.target

    [Service]
    User=apprunner
    WorkingDirectory=/home/apprunner/email/backend
    ExecStart=/home/apprunner/email/backend/venv/Scripts/python worker.py
    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```

---

### SECTION 9: BACKUP STRATEGY

#### 1. Simple Explanation
To prevent data loss from server failures or database corruption, the system automatically makes encrypted copies of the database and configurations and uploads them to secure storage.

#### 2. Backup Configurations
- **Database Backup (DuckDB)**:
  Because DuckDB creates a local file database, backups are created using the `checkpoint` command or by copying the file after shutting down writing processes.
  - **Daily Backup Script**:
    ```bash
    #!/bin/bash
    BACKUP_DIR="/opt/backups/db"
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    DB_PATH="/home/apprunner/email/backend/email_verifier.db"
    
    mkdir -p "$BACKUP_DIR"
    # Copy DB file safely using DuckDB copy commands or simple copy when safe
    sqlite3 "$DB_PATH" ".backup $BACKUP_DIR/db_$TIMESTAMP.db" 2>/dev/null || cp "$DB_PATH" "$BACKUP_DIR/db_$TIMESTAMP.db"
    
    # Encrypt backup
    gpg --symmetric --batch --passphrase-file /etc/backup_passphrase.txt "$BACKUP_DIR/db_$TIMESTAMP.db"
    rm "$BACKUP_DIR/db_$TIMESTAMP.db"
    
    # Push to S3/Cloud Storage
    aws s3 cp "$BACKUP_DIR/db_$TIMESTAMP.db.gpg" s3://emailverif-backups/daily/
    ```
- **Frequencies**:
  - **Daily**: Database file backups kept for 14 days.
  - **Weekly**: DB files + logs kept for 8 weeks.
  - **Monthly**: Full snapshots of the virtual server kept for 6 months.

---

### SECTION 10: MONITORING

#### 1. Simple Explanation
Monitoring tracks system resource utilization, background queue statuses, API response delays, and SMTP connection failures to help maintain high platform uptime.

#### 2. Metrics to Track
| Metric Group | Metric Name | Threshold | Action if Exceeded |
| :--- | :--- | :--- | :--- |
| **System** | CPU Utilization | > 85% for 10m | Scale instance / Thread limit reduction |
| **System** | Disk Space | < 15% remaining | Clean up archived CSV files manually |
| **Engine** | 550 SMTP Errors | Higher than usual | Check if sender IP is blacklisted |
| **Engine** | 450 (Greylist) | Higher than usual | System backoff scaling verification |
| **Queue** | Queue Size | > 50,000 tasks | Spawn additional worker nodes |
| **API** | API Latency | > 500ms average | Optimize SQL/DuckDB analytical index |

---

### SECTION 11: LOGGING

#### 1. Simple Explanation
Logging records events in the application, including user activity, verification results, payment status, errors, and logins. This helps developers debug issues and allows security teams to track access patterns.

#### 2. Logging Architecture
- **Log Locations**:
  - `/var/log/emailverif/app.log` (general errors and API events)
  - `/var/log/emailverif/worker.log` (verification details and SMTP metrics)
  - `/var/log/emailverif/payments.log` (gateway signatures and webhooks)
  - `/var/log/emailverif/security.log` (failed login attempts, JWT invalidations)
- **Log Format**:
  `JSON-structured format` is utilized to allow automated analysis by tools like Elasticsearch or Loki.
  ```json
  {"timestamp": "2026-06-30T06:12:00Z", "level": "INFO", "module": "worker", "job_id": "job_12", "message": "Bulk verification completed for 5000 emails. Valid: 4100, Invalid: 900"}
  ```
- **Log Rotation**: Logs are rotated daily (`logrotate` script) and compressed, keeping history for 90 days.

---

### SECTION 12: SECURITY ARCHITECTURE

#### 1. Simple Explanation
The security architecture keeps user accounts safe, protects payment transactions, validates file uploads, and blocks common web exploits.

#### 2. Security Implementations
- **Authentication**: JWT tokens stored in `HttpOnly`, `Secure`, `SameSite=Lax` cookies to prevent XSS attacks.
- **Passwords**: Hashed using **Bcrypt** with a work factor of 12. Plaintext passwords are never saved.
- **Rate Limiting**: Prevents denial of service. The backend blocks clients that exceed rate limits using a sliding-window counter.
- **File Upload Security**:
  - The backend verifies that uploaded files have valid headers (checking magic bytes for text/csv).
  - Maximum upload size is limited to 20MB.
  - Uploaded files are saved to folder paths outside the web application's executable root.
- **Input Validation**: All parameters are filtered using Pydantic models. Database queries are written using parameterized placeholders to prevent SQL injection.

---

### SECTION 13: LANDING PAGE ARCHITECTURE

#### 1. Simple Explanation
The landing page introduces the product, demonstrates its value, and encourages visitors to register.

#### 2. Landing Page Component Breakdown
- **Navbar**: Main brand link, Pricing link, API Docs link, Login button, and "Get Started" call to action.
- **Hero Section**: Headline highlighting key benefits, a short description, and a primary CTA input.
- **Interactive Verification Demo**: A mini validator component that lets visitors check single email addresses in real-time, displaying how the engine resolves SMTP connections and PTR headers.
- **Features Grid**: Explains syntax checking, DNS validations, Catch-all parsing, and disposable domains.
- **Pricing Cards**: Side-by-side comparison tables of the Free, Starter, Growth, and Enterprise plans.
- **Frequently Asked Questions (FAQ)**: Toggle elements answering questions about speed, credit terms, and list data security.

---

### SECTION 14: TESTING STRATEGY

#### 1. Simple Explanation
To ensure the application runs reliably after updates, we run automated tests that check individual code functions, system integrations, and client interfaces.

#### 2. QA Test Design
```mermaid
graph TD
    UT[Unit Tests: FastAPI models, SMTP parsing, DNS regex] --> IT[Integration Tests: DuckDB reads, Email template creation]
    IT --> E2E[End-to-End Tests: Guest flows, CSV uploads, payment webhooks]
    E2E --> MT[Manual Quality Reviews: Responsive styling, email inbox checks]
```
- **Unit Testing Framework**: Python `pytest` runs validations against local mocks of DNS resolvers and SMTP mail servers.
- **Mocking External Mail Servers**:
  ```python
  import pytest
  from unittest.mock import AsyncMock

  @pytest.fixture
  def mock_smtp():
      smtp = AsyncMock()
      smtp.connect.return_value = (220, b"SMTP ready")
      smtp.helo.return_value = (250, b"Hello")
      smtp.mail.return_value = (250, b"Sender OK")
      smtp.rcpt.return_value = (250, b"Recipient OK")
      return smtp
  ```
- **Frontend Browser Testing**: Playwright scripts execute automated checks on registration, logins, and settings screens.

---

### SECTION 15: LOAD TESTING

#### 1. Simple Explanation
Load testing verifies how the application performs when processing large volumes of data simultaneously, helping identify potential system bottlenecks.

#### 2. Performance Benchmarks
We test the verification system using lists of various sizes to measure performance and resource usage:

| Email List Size | Execution Duration | Peak RAM Usage | Peak CPU Load | Target Accuracy |
| :--- | :--- | :--- | :--- | :--- |
| **1,000 Emails** | 45 Seconds | ~250 MB | 20% | > 99.2% |
| **10,000 Emails** | 5 Minutes | ~420 MB | 45% | > 99.1% |
| **50,000 Emails** | 22 Minutes | ~950 MB | 72% | > 99.0% |
| **100,000 Emails** | 48 Minutes | ~1.4 GB | 80% | > 99.0% |

- **Concurrency Settings**: The background worker concurrency is limited to 100 parallel checks to prevent IP address flagging and resource leaks.

---

### SECTION 16: DATABASE DESIGN

#### 1. Entity Relationship (ER) Diagram
```mermaid
erDiagram
    USERS {
        uuid id PK
        varchar email UK
        varchar password_hash
        varchar role
        integer credits
        boolean is_active
        timestamp created_at
    }
    ADMINS {
        uuid id PK
        uuid user_id FK
        integer credit_pool
        timestamp created_at
    }
    VERIFICATION_JOBS {
        uuid id PK
        uuid user_id FK
        varchar filename
        integer total_emails
        integer processed_emails
        varchar status
        timestamp created_at
    }
    VERIFICATION_RESULTS {
        uuid id PK
        uuid job_id FK
        varchar email
        varchar status
        double confidence_score
        boolean ptr_valid
        timestamp verified_at
    }
    EMAIL_CACHE {
        varchar email PK
        varchar status
        double confidence_score
        timestamp cached_at
    }
    PAYMENTS {
        uuid id PK
        uuid user_id FK
        varchar order_id UK
        varchar status
        integer amount
        timestamp created_at
    }
    CREDIT_TRANSACTIONS {
        uuid id PK
        uuid user_id FK
        integer amount
        varchar transaction_type
        timestamp created_at
    }
    API_KEYS {
        uuid id PK
        uuid user_id FK
        varchar api_key_hash UK
        boolean is_active
        timestamp created_at
    }

    USERS ||--o{ VERIFICATION_JOBS : creates
    USERS ||--o{ PAYMENTS : initiates
    USERS ||--o{ CREDIT_TRANSACTIONS : completes
    USERS ||--o{ API_KEYS : configures
    USERS ||--|| ADMINS : has
    VERIFICATION_JOBS ||--o{ VERIFICATION_RESULTS : contains
```

#### 2. Performance Optimizations
- **Indexing Rules**:
  - Composite index on `verification_results(job_id, status)` for fast search queries.
  - Primary key lookup on `email_cache(email)` for high-speed cache lookups.
  - Hash index on `api_keys(api_key_hash)` for quick authentication checks.
- **Write Optimization**: Batch writes are used when saving verification results to DuckDB, group-writing 500 rows at a time to reduce disk write overhead.

---

### SECTION 17: BUSINESS METRICS

#### 1. Simple Explanation
Business metrics and Key Performance Indicators (KPIs) measure the platform's financial health, user activity, and processing accuracy.

#### 2. Key Business Metrics
- **MRR (Monthly Recurring Revenue)**: Calculated by summing active paid monthly subscription tiers.
- **ARR (Annual Recurring Revenue)**: Calculated by multiplying MRR by 12.
- **Customer Retention Rate (CRR)**: Measures the percentage of paying accounts that remain subscribed month over month.
- **Average Verification Time**: The time required to verify an email address, measured in seconds.
- **System Accuracy Rate**: Verified by testing random lists with known delivery outcomes to ensure accuracy remains above 99%.

---

### SECTION 18: ROADMAP

#### 1. Release Timeline
```mermaid
gantt
    title Email Verification Platform Roadmap
    dateFormat  YYYY-MM
    section Version 1.0 (MVP)
    Core Engine & Syntax checks :active, 2026-01, 30d
    DuckDB Schema & Upload Portal :active, 2026-02, 30d
    section Version 2.0 (Scale)
    Billing webhook integration : 2026-03, 30d
    Developer REST API launch : 2026-04, 30d
    Superadmin Impersonation : 2026-05, 30d
    section Version 3.0 (Enterprise)
    Distributed check nodes : 2026-06, 60d
    White-label dashboards : 2026-08, 45d
```

- **Version 1.0**: Focuses on core single verification, bulk file processing, basic credit tracking, and local dashboard interfaces.
- **Version 2.0**: Focuses on payment integrations, public API key setups, role hierarchy models (Superadmin dashboard), and user session impersonation features.
- **Version 3.0**: Focuses on distributed worker architectures (multi-IP scaling), white-label portals for growth accounts, and AI-driven behavior assessments.

---

### SECTION 19: DISASTER RECOVERY

#### 1. Simple Explanation
Disaster Recovery (DR) plans outline step-by-step procedures to recover services in the event of major failures, such as server crashes or database corruption.

#### 2. System Failover Procedures
- **Database Corruption Event**:
  1. Terminate running instances of the `fastapi` and `worker` systemd services.
  2. Move the corrupted `email_verifier.db` to `/tmp/corrupt_backup.db`.
  3. Download the most recent daily database backup from secure cloud storage.
  4. Decrypt the database file:
     ```bash
     gpg --decrypt --batch --passphrase-file /etc/backup_passphrase.txt -o /home/apprunner/email/backend/email_verifier.db /opt/backups/db/db_latest.gpg
     ```
  5. Restart the systemd services:
     ```bash
     sudo systemctl start fastapi worker
     ```
- **SMTP Server Blocklist Event**:
  If the VPS IP address gets blocklisted, outbound SMTP requests will fail with 550 or connection timeout errors. In this case, route traffic through a secondary backup VPS IP address or configure a proxy connection to bypass the block.

---

### SECTION 20: APPENDICES

#### 1. Common SMTP Status Codes
- `250 OK`: The mailbox exists and can accept emails.
- `550 User Not Found`: The mailbox does not exist or has been disabled.
- `450 Greylisted`: The receiving server is temporarily deferring the connection. The system will retry.
- `421 Service Unavailable`: The receiving server's connection limit has been reached.

#### 2. System Deployment Checklist
- [ ] Configure `UFW` firewall settings (only allow SSH, HTTP, and HTTPS).
- [ ] Set up daily database backups and verify file transfers to remote storage.
- [ ] Configure HTTPS using Let's Encrypt certificates.
- [ ] Update JWT secrets in the production `.env` configuration.
- [ ] Test the backend systemd services to ensure they restart automatically after a reboot.
- [ ] Verify that the reverse DNS (PTR record) is correctly set up on the VPS IP address.

---
*Updated: 2026-07-12*