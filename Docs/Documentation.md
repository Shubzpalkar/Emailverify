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
- **Admin Panel**: Centralized control for user management and credit allocation.
- **Intelligent Caching**: Reuses verification results and domain behaviors to improve speed and bypass IP rate limits.
- **Password Reset**: Secure, token-based recovery system with 1-hour expiration.
- **API Access**: Programmatic verification via SHA-256 hashed API keys.
- **PTR Validation**: Reverse DNS checks on target MX IPs for advanced delivery diagnostics.

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
| **`auth.py`** | Authentication logic. Defines Pydantic schemas for user registration/login, handles Bcrypt password hashing, issues JWT tokens, and provides dependency functions like `get_current_user` to lock down protected routes. |
| **`routes.py`** | HTTP API Endpoints. Groups endpoints via `APIRouter` for `/auth`, `/jobs` (file upload and progress polling), `/dashboard` (metrics aggregation), and `/admin` (user management and credit allocation). |
| **`engine.py`** | Core Verification Logic. Executes the 7-step pipeline on a single email. Handles syntax regex, cached result lookups, DNS MX record resolution, disposable domain checking, role-based account fuzzy matching, and deep SMTP handshakes. |
| **`smtp_verifier.py`** | SMTP Connection Handler. Uses `aiosmtplib` to connect to target MX servers, send `HELO/EHLO`, `MAIL FROM`, and `RCPT TO` commands. Implements smart retries for Greylisting (450) and handles SSL/TLS downgrades. |
| **`dns_checks.py`** | Async DNS Resolver. Now includes **PTR Validation** (Reverse DNS) to detect if target mail servers or sender IPs lack valid hostnames, providing diagnostic context in SMTP responses. |
| **`worker.py`** | Background Processing Engine. Consumes uploaded CSV lists in the background using `asyncio.gather`. Enforces concurrency limits (`asyncio.Semaphore`) per domain and global rate limits to prevent IP blacklisting. Logs detailed progress to the terminal and batches write-backs to DuckDB. |

#### 2.2.2 Frontend (`/frontend`)
The frontend is a React Single Page Application (SPA) built with Vite, utilizing a custom CSS variables design system for a premium glassmorphism aesthetic.

| File / Folder | Purpose / Responsibility |
| :--- | :--- |
| **`src/main.jsx` & `App.jsx`** | Application roots. `main.jsx` wraps the app in context providers (`BrowserRouter`, `AuthProvider`, `ToastProvider`). `App.jsx` defines local routing rules, distinguishing public paths vs. `ProtectedRoute` wrapper logic. |
| **`src/index.css`** | Global Design System. Contains CSS custom properties (`--primary`, `--bg-surface`), glassmorphism card utilities, button styles, table layouts, and typography resets. |
| **`src/api/client.js`** | Centralized API Client. A wrapper around the native `fetch` API. Automatically handles cookie inclusion for auth, sets standard headers, natively handles `FormData` for file uploads, and intercepts/normalizes API error responses. |
| **`src/context/AuthContext.jsx`** | Global User State. Manages current user session via an initial `/auth/me` ping on mount. Provides `login`, `signup`, `logout`, and context variables to all components without prop-drilling. |
| **`src/components/`** | Reusable UI Elements. Contains the responsive `Navbar.jsx`, auth-guard `ProtectedRoute.jsx`, and the floating notification system `Toast.jsx` with its animations. |
| **`src/pages/Landing.jsx`** | Marketing entry point containing hero sections and a 3D CSS mockup card visualizing sample verification results. |
| **`src/pages/Auth.css` / `.jsx`** | Shared styles and logic for `Login.jsx` and `Signup.jsx` forms. |
| **`src/pages/Dashboard.jsx`** | User Hub. Displays total verification metrics, remaining credits, and a table of recent jobs. Utilizes a recursive `setInterval` polling loop (every 5s) if any job is currently in "processing" state to update progress bars. |
| **`src/pages/ForgotPassword.jsx`** | Password Recovery. Allows users to request a timed reset link via email (currently prints to backend console). |
| **`src/pages/ResetPassword.jsx`** | Secure Reset. Captures tokens from URL to allow setting a new account password. |
| **`src/pages/APIKeys.jsx`** | Developer Settings. Interface to generate (with sk_live_ prefix), monitor, and revoke programmatic API keys. |
| **`src/pages/Verify.jsx`** | Action Center. Provides a drag-and-drop file upload zone for bulk CSV verification (converting files to `FormData` and POSTing to backend) and a single-email checking form with detailed confidence-scoring results. |
| **`src/pages/Admin.jsx`** | Management Interface. Protected route (role === 'admin') to view all registered users and assign virtual credits. |
| **`vite.config.js`** | Dev Server config. Noteworthy for its explicit proxying of any `/api` prefix request straight to localhost:8000 to bypass CORS during local development. |

### 2.3 System Architecture
The application follows a modular, asynchronous architecture:
- **API Layer**: Handles HTTP requests, JWT authentication, and file ingestion.
- **Worker Layer**: A background processing pool using `asyncio` and `RateLimiter`.
- **Engine Layer**: The core logic that executes the 7-step verification pipeline.
- **Intelligence Layer**: DuckDB-backed cache that persists domain behaviors.

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

**Backend**:
```bash
cd backend
py -m venv venv
.\venv\Scripts\activate       # Windows
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
*Updated: 2026-04-04*
F