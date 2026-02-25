# TECHNICAL SPECIFICATION DOCUMENT: EQUILIBRIA

**Project:** Prototype of Collaborative Adaptive Assessment System with Overpersonalization Mitigation  
**Student:** Dama Dhananjaya Daliman (18222047)  
**Version:** 3.0 (Implementation-Ready with Production Architecture)  
**Date:** February 22, 2026

---

## 0. EXECUTIVE SUMMARY

Equilibria adalah purwarupa sistem asesmen adaptif berbasis Computerized Adaptive Testing (CAT) yang dirancang khusus untuk domain pendidikan Ilmu Komputer, dengan studi kasus pada materi SQL Querying. Sistem ini mengimplementasikan Elo Rating System yang dimodifikasi untuk kalibrasi dinamis tingkat kesulitan soal terhadap kemampuan siswa secara real-time.

Sebagai novelty, Equilibria memperkenalkan Mekanisme Kolaboratif Mitigasi Overpersonalization yang secara proaktif mendeteksi stagnasi kemampuan siswa melalui analisis variansi perubahan skor (`Δθ`), lalu memicu intervensi sosial (Peer Review) dengan constraint-based re-ranking berbasis Cohen's d ≥ 0.5 untuk memastikan heterogenitas pasangan. Integrasi metrik individu dan sosial dilakukan dengan bobot 50-50, dengan logging komprehensif yang memungkinkan simulasi ulang pasca-hoc untuk eksplorasi optimalisasi bobot.

Sistem dibangun dengan arsitektur Client-Server modern menggunakan React.js (frontend) dan FastAPI (backend), dengan PostgreSQL sebagai basis data yang dipisahkan menjadi skema `public` (operasional) dan `sandbox` (eksekusi query aman).

**Perubahan dari v2.0:**
- ✅ Dual logging system (syslogs + asslogs) dengan auto-rotation 10MB
- ✅ JSend response convention dengan Generic[T] untuk type safety
- ✅ Pydantic v2 compatibility (ConfigDict, field_serializer)
- ✅ Dependency injection pattern terpusat di `app/core/dependencies.py`
- ✅ SQLAlchemy 2.0 async session management
- ✅ Separated environment variables per service (`/server/.env`, `/client/.env`)
- ✅ Docker Compose dengan healthcheck dan volume persistence yang diperbaiki

---

## 1. SYSTEM ARCHITECTURE

### 1.1 High-Level Architecture

```
┌─────────────────┐      HTTP/HTTPS (JSON)      ┌──────────────────┐
│   FRONTEND      │ ◄─────────────────────────► │    BACKEND       │
│   (React SPA)   │                             │   (FastAPI)      │
└────────┬────────┘                             └────────┬─────────┘
         │                                               │
         │                                               │
         ▼                                               ▼
┌─────────────────┐                             ┌──────────────────┐
│  BROWSER        │                             │  POSTGRESQL      │
│  (CodeMirror)   │                             │  ┌──────────────┐ │
└─────────────────┘                             │  │ public       │ │
                                                │  │ sandbox      │ │
                                                │  └──────────────┘ │
                                                └──────────────────┘
```

### 1.2 State Diagram (User Flow)

```
┌───────────────┐
│   LOGIN       │
└───────┬───────┘
        │
        ▼
┌───────────────┐  no pretest?  ┌───────────────┐
│   DASHBOARD   │ ◄──────────── │   PRE-TEST    │
└───────┬───────┘               └───────┬───────┘
        │                               │ (5 adaptive Qs)
        ▼                               ▼
┌───────────────┐               ┌───────────────┐
│ SELECT MODULE │               │  CALCULATE    │
└───────┬───────┘               │  θ_initial    │
        │                       └───────┬───────┘
        ▼                               │
┌───────────────────────────────────────┘
│
▼
┌──────────────────────┐
│  INDIVIDUAL MODE     │
│  (Adaptive Session)  │
└──────────┬───────────┘
           │ Submit Answer
           ▼
    ┌──────────────┐
    │ Update θ     │
    │ (Elo Engine) │
    └──────┬───────┘
           │
    ┌──────┴──────┐
    ▼             ▼
┌─────────┐  ┌──────────────┐
│Next Q?  │  │Stagnation?   │
│Yes → ◄──┘  │Var(Δθ₅) < ε? │
└─────────┘  └──────┬───────┘
                    │ YES (ε=0.05)
                    ▼
           ┌──────────────────┐
           │ COLLABORATIVE    │
           │ MODE (Triggered) │
           └────────┬─────────┘
                    │
           ┌────────┴────────┐
           ▼                 ▼
    ┌─────────────┐   ┌──────────────┐
    │ As Reviewer │   │ As Requester │
    └──────┬──────┘   └──────┬───────┘
           │                 │
    ┌──────┴──────┐   ┌──────┴──────┐
    ▼             ▼   ▼             ▼
┌─────────┐  ┌──────────┐ ┌──────────┐
│Write    │  │System    │ │View      │
│Feedback │  │Grading   │ │Feedback  │
└────┬────┘  └────┬─────┘ └────┬─────┘
     │            │           │
     └──────┬─────┴───────────┘
            ▼
    ┌──────────────────┐
    │ WAITING CONFIRM  │ (24h timeout)
    └────────┬─────────┘
      ┌──────┴──────┐
      ▼             ▼
┌──────────┐  ┌──────────┐
│Thumbs Up │  │Thumbs Dn │
└────┬─────┘  └────┬─────┘
     │             │
     └──────┬──────┘
            ▼
    ┌──────────────────┐
    │ Update θ_social  │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ RETURN TO        │
    │ INDIVIDUAL MODE  │
    └──────────────────┘
```

### 1.3 Repository Structure (Monorepo)

```
equilibria-monorepo/
├── .gitignore
├── README.md
├── client/                     # React Frontend (Vite)
│   ├── .env                    # Frontend environment (VITE_ prefix)
│   ├── .env.example
│   ├── src/
│   │   ├── components/         # Reusable UI (Editor, RadarChart)
│   │   ├── pages/              # Route-based pages
│   │   ├── services/           # Axios API clients
│   │   ├── routes/             # React Router configuration
│   │   └── store/              # Zustand state management
│   ├── package.json
│   └── vite.config.ts
├── server/                     # Python Backend (FastAPI)
│   ├── .env                    # Backend environment (DB, JWT, etc)
│   ├── .env.example
│   ├── docker-compose.yml      # Docker orchestration (backend + db)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/                # Database migrations
│   ├── app/
│   │   ├── main.py             # App entry point
│   │   ├── api/                # API Routers
│   │   ├── core/               # Business Logic & Configuration
│   │   ├── db/                 # Database layer
│   │   ├── schemas/            # Pydantic models
│   │   ├── sandbox/            # Secure SQL execution
│   │   └── logs/               # Log files (auto-generated)
│   └── db/
│       └── init_sandbox.sql    # Sandbox schema initialization
├── docs/
│   └── pretest_calibration.md
└── README.md
```

---

## 2. TECHNOLOGY STACK

| Layer | Technology | Version | Rationale |
|-------|------------|---------|-----------|
| **Frontend** | React | 18.x | Fast HMR, component-based architecture |
| | Vite | 5.x | Fast build tool with native ESM |
| | React Router | 6.x | Declarative routing for SPA navigation |
| | Tailwind CSS | 3.x | Utility-first styling for rapid UI development |
| | CodeMirror | 6.x | Lightweight SQL editor with syntax highlighting |
| | Zustand | 4.x | Minimalist state management (no boilerplate) |
| | Axios | 1.x | HTTP client for API communication |
| **Backend** | Python | 3.12 | Rich ecosystem for scientific computing |
| | FastAPI | 0.109.x | Async support, automatic OpenAPI docs |
| | SQLAlchemy | 2.0.x | Async ORM with connection pooling |
| | Alembic | 1.13.x | Database migration management |
| | Pydantic | 2.5.x | Data validation with v2 syntax |
| | Pydantic Settings | 2.1.x | Environment-based configuration |
| | python-jose | 3.3.x | JWT encoding/decoding |
| | passlib | 1.7.x | Password hashing (Argon2id) |
| | asyncpg | 0.29.x | Fast PostgreSQL async driver |
| | NumPy | 1.26.x | Numerical computations for Elo/stagnation |
| **Database** | PostgreSQL | 15.x | ACID compliance, MVCC for concurrent sessions |
| **Deployment** | Docker Compose | 3.8 | Isolated services (app, db) |
| | Vercel | Hobby Tier | Frontend hosting (free) |
| | Render/Railway | Free Tier | Backend hosting (free) |
| | Supabase | Free Tier | Managed PostgreSQL (alternative) |

---

## 3. DATABASE SPECIFICATION

### 3.1 Core Schema (`public`)

#### Table `users`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `user_id` | UUID | PK | Unique identifier |
| `nim` | VARCHAR(20) | UNIQUE, NOT NULL, INDEX | Student ID |
| `full_name` | VARCHAR(100) | NOT NULL | Display name |
| `password_hash` | VARCHAR | NOT NULL | Argon2id hashed password |
| `current_theta` | FLOAT | DEFAULT 0.0, RANGE [-3.0, +3.0] | Normalized Elo rating (individual) |
| `theta_social` | FLOAT | DEFAULT 0.0 | Social contribution score |
| `k_factor` | INTEGER | DEFAULT 32 | Sensitivity factor (decays with attempts) |
| `has_completed_pretest` | BOOLEAN | DEFAULT FALSE | Mandatory cold-start flag |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Account creation timestamp |

#### Table `modules`

| Column | Type | Description |
|--------|------|-------------|
| `module_id` | VARCHAR(5) | PK (e.g., 'CH01') |
| `title` | VARCHAR(255) | Display name |
| `description` | TEXT | Module overview |
| `difficulty_min` | FLOAT | Lower bound of D (e.g., -3.0) |
| `difficulty_max` | FLOAT | Upper bound of D (e.g., -1.0) |
| `content_html` | TEXT | HTML content for learning material |
| `is_locked` | BOOLEAN | TRUE if requires previous completion |

#### Table `questions`

| Column | Type | Description |
|--------|------|-------------|
| `question_id` | VARCHAR(10) | PK (e.g., 'CH01-Q005') |
| `module_id` | VARCHAR(5) | FK → `modules` |
| `content` | TEXT | HTML/Markdown question narrative |
| `target_query` | TEXT | Canonical solution |
| `initial_difficulty` | FLOAT | Manually calibrated (post-pretest) |
| `current_difficulty` | FLOAT | Dynamically updated via Elo |
| `topic_tags` | TEXT[] | e.g., ['JOIN', 'GROUP BY'] |
| `is_active` | BOOLEAN | TRUE if available for selection |

#### Table `assessment_logs`

| Column | Type | Description |
|--------|------|-------------|
| `log_id` | SERIAL | PK |
| `session_id` | UUID | Grouping identifier for a practice session |
| `user_id` | UUID | FK → `users`, INDEX |
| `question_id` | VARCHAR(10) | FK → `questions`, INDEX |
| `user_query` | TEXT | Submitted solution |
| `is_correct` | BOOLEAN | Result of sandbox comparison |
| `theta_before` | FLOAT | θ before attempt |
| `theta_after` | FLOAT | θ after update |
| `execution_time_ms` | INTEGER | Time to solve (excluding idle) |
| `timestamp` | TIMESTAMP | Attempt timestamp, INDEX |

#### Table `peer_sessions`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `session_id` | UUID | PK | Unique session identifier |
| `requester_id` | UUID | FK → `users`, INDEX | User experiencing stagnation |
| `reviewer_id` | UUID | FK → `users`, INDEX | Assigned heterogeneous peer |
| `question_id` | VARCHAR(10) | FK → `questions`, INDEX | Context of review |
| `review_content` | TEXT | NOT NULL | Constructive feedback text |
| `system_score` | FLOAT | RANGE [0.0, 1.0] | NLP keyword matching score |
| `is_helpful` | BOOLEAN | NULLABLE | Requester's binary confirmation |
| `final_score` | FLOAT | COMPUTED | (0.5 × system_score) + (0.5 × is_helpful) |
| `status` | VARCHAR(50) | ENUM | `PENDING_REVIEW`, `WAITING_CONFIRMATION`, `COMPLETED` |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Session initiation |

### 3.2 Sandbox Schema (`sandbox`)

**Tables:** `mahasiswa`, `matakuliah`, `dosen`, `frs` (read-only dummy data)

**Security:**
- Dedicated DB role `sandbox_executor` dengan hak akses hanya `SELECT` pada skema `sandbox`
- Tidak ada hak akses ke skema `public`
- Query timeout: 5000 ms (via `statement_timeout` PostgreSQL GUC)
- Initialized via `/docker-entrypoint-initdb.d/init_sandbox.sql`

---

## 4. MATERIAL STRUCTURE (HIERARCHICAL DOMAIN)

| Module | Topic Focus | Difficulty Range (D) | Sample Count | Description |
|--------|-------------|---------------------|--------------|-------------|
| CH01 | Basic Selection | [-3.0, -1.0] | 40 | `SELECT..WHERE`, logical operators |
| CH02 | Aggregation | [-1.0, +1.0] | 40 | `GROUP BY..HAVING`, aggregate functions |
| CH03 | Advanced Querying | [+1.0, +3.0] | 40 | CTE (`WITH`), Subquery, Multiple Joins |

**Note:** Setiap modul menyediakan 2.5× jumlah soal minimum per sesi (16 soal) → kombinasi 40C16 ≈ 4.8 juta. Risiko "bank soal habis" dianggap negligible untuk skala 10-20 user.

---

## 5. FRONTEND SPECIFICATION (ROUTING & UI)

### 5.1 React Router Configuration

Akan ada route-route yang harus auth dengan JWT token. Sedangkan auth routes (login dan register) akan redirect langsung ke dashboard.
Pre-test akan jadi route wajib untuk pengguna baru sebelum bisa akses fitur utama.

### 5.2 Navigation Flow & Menu Structure

```
DASHBOARD (Default Route: /)
├── Progress Radar (3 modul)
├── Elo Stats (θ individu + sosial)
├── Quick Resume → /session/start
└── Navigation Menu:
    ├── Coursework → /modules
    ├── Collaborative → /collaboration/inbox
    └── Profile → /profile

COURSEWORK (/modules)
├── Module Tree (CH01/CH02/CH03)
│   └── Click Module → /modules/:moduleId
├── Module Detail Page (/modules/:moduleId)
│   ├── Content Tab (HTML materi)
│   ├── Practice Tab → /session/start?module=CH01
│   └── Status Indicator (Locked/Unlocked)
└── Start Session → /session/start

COLLABORATIVE SPACE
├── Peer Review Inbox (/collaboration/inbox)
│   └── List of pending review tasks
│       └── Click Task → /collaboration/review/:sessionId
├── Review Task Page (/collaboration/review/:sessionId)
│   ├── Question Context
│   ├── Peer's Answer (Anonymized)
│   ├── Feedback Form (Rubrik)
│   └── Submit Button
└── My Requests Status (/collaboration/requests)
    ├── List of sent requests
    ├── Feedback received (if any)
    └── Thumbs Up/Down voting

PROFILE (/profile)
├── User Info + NIM
├── Current θ (Individual + Social)
├── History Log → /profile/history
└── Settings (Dark/Light, Editor Config)
```

### 5.3 Environment Variables (Frontend)

Semua env var frontend pake prefix `VITE_` agar kompatibel dengan Vite.
env var diset dalam file `.env` dan kalau di deploy berarti via dashboard PaaS-nya.

---

## 6. ALGORITHMIC LOGIC (BACKEND CORE)

Di bawah ini akan dijelaskan logika-logika backend dengan pseudocode.

### 6.1 Pre-Test Flow (Mandatory Cold-Start Calibration)

**Rationale:** Menghindari cold-start bias dengan kalibrasi awal berbasis 5 soal adaptif sebelum akses platform utama.

```text
FUNCTION calculate_initial_theta(correct_count, difficulties):
    baseline = 2.5  # Expected correct for θ=0.0
    adjustment = (correct_count - baseline) * 0.4
    theta_initial = CLAMP(0.0 + adjustment, -1.5, +1.5)
    RETURN theta_initial
END FUNCTION
```

### 6.2 Adaptive Engine (Individual Mode)

#### Item Selection Strategy

```text
FUNCTION select_next_question(user_theta, module_id, completed_questions):
    FILTER questions WHERE module_id = module_id
    FILTER questions WHERE question_id NOT IN completed_questions
    FOR EACH question:
        distance = ABS(question.difficulty - user_theta)
    SELECT TOP 5 questions WITH smallest distance
    RANDOMLY PICK 1 from TOP 5
    RETURN selected_question
END FUNCTION
```

#### Elo Update Formula

```text
FUNCTION calculate_expected_score(theta, difficulty):
    RETURN 1 / (1 + 10^((difficulty - theta) / 400))
END FUNCTION

FUNCTION update_elo(rating, expected, actual, k_factor):
    RETURN rating + k_factor * (actual - expected)
END FUNCTION
```

#### K-Factor Adaptation (Piecewise Decay)

```text
FUNCTION get_k_factor(total_attempts):
    IF total_attempts < 10:
        RETURN 32  # Responsive for cold-start
    ELSE IF total_attempts < 25:
        RETURN 24  # Stable transition
    ELSE:
        RETURN 16  # Smooth convergence
END FUNCTION
```

### 6.3 Stagnation Detection (ε = 0.05)

```text
FUNCTION detect_stagnation(user_id, last_5_logs):
    IF length(last_5_logs) < 5:
        RETURN FALSE
    
    deltas = []
    FOR EACH log IN last_5_logs:
        delta = log.theta_after - log.theta_before
        APPEND delta TO deltas
    
    variance = CALCULATE_VARIANCE(deltas)
    
    IF variance < 0.05:  # ε threshold
        RETURN TRUE  # Stagnation detected
    ELSE:
        RETURN FALSE
END FUNCTION
```

### 6.4 Constraint-Based Re-ranking (Heterogeneity Enforcement)

```text
FUNCTION find_heterogeneous_peer(requester_theta, population_std_dev):
    min_difference = 0.5 * population_std_dev  # Cohen's d threshold
    
    QUERY candidates FROM users WHERE:
        user_id != requester_id
        status != 'NEEDS_PEER_REVIEW'
        ABS(candidate.theta - requester_theta) >= min_difference
    
    ORDER candidates BY ABS(theta difference) DESCENDING
    LIMIT 10
    
    RETURN RANDOM_SELECT(candidates)
END FUNCTION
```

### 6.5 NLP Feedback Quality (Keyword Matching)

```text
FUNCTION calculate_system_score(feedback_text):
    IF LENGTH(TRIM(feedback_text)) < 15:
        RETURN 0.2  # Too short
    
    text = LOWERCASE(feedback_text)
    
    has_constructive = CONTAINS_ANY(text, CONSTRUCTIVE_KEYWORDS)
    has_identification = CONTAINS_ANY(text, IDENTIFICATION_KEYWORDS)
    
    IF has_constructive AND has_identification:
        RETURN 0.9  # Excellent
    ELSE IF has_constructive OR has_identification:
        RETURN 0.6  # Good
    ELSE:
        RETURN 0.3  # Poor (purely affective)
END FUNCTION
```

### 6.6 Integrasi Elo Individu & Sosial (50-50)

```text
FUNCTION calculate_final_theta(theta_individual, theta_social):
    RETURN (0.5 * theta_individual) + (0.5 * theta_social)
END FUNCTION
```

---

## 7. BACKEND API SPECIFICATION

### 7.1 Authentication & Authorization

**JWT Flow:**
1. `POST /api/v1/auth/login` → `{nim, password}` → JWT token
2. Setiap request selanjutnya setelah mendapatkan JWT Token harus menyertakan: `Authorization: Bearer <token>`
3. Gunakan FastAPI dependency untuk inject: `get_current_user()` ke API endpoint → validate JWT

### 7.2 Response Convention (JSend)

All API endpoints MUST return JSendResponse format with Generic[T] type safety.

Semua endpoint API WAJIB mengembalikan responsenya sesuai struktur JSend dengan field `data` nya menggunakan Generic[T] yang nantinya akan diisi skema data yang sesuai dengan endpoint yang dipanggil.

**Response Schema:**

```text
STRUCT JSendResponse[T]:
    status: ENUM("success", "fail", "error")
    code: INTEGER (HTTP status code)
    data: OPTIONAL[T] (Response payload)
    message: OPTIONAL[STRING] (Error or info message)
END STRUCT
```

**Generic Success Response Example:**

```json
{
  "status": "success",
  "code": 200,
  "data": {
    "access_token": "eyJ...",
    "user": {
      "user_id": "uuid-string",
      "nim": "18222047",
      "current_theta": 1.25
    }
  },
  "message": "Operation completed successfully"
}
```

**Generic Fail Response Example (Client Error):**

```json
{
  "status": "fail",
  "code": 401,
  "data": null,
  "message": "Invalid NIM or password"
}
```

**Generic Error Response Example (Server Error):**

```json
{
  "status": "error",
  "code": 500,
  "data": null,
  "message": "Internal server error during processing"
}
```

### 7.3 Complete API Endpoints Reference

#### A. Authentication Endpoints

| Method | Endpoint | Input | Output | Description |
|--------|----------|-------|--------|-------------|
| POST | `/api/v1/auth/login` | `{nim, password}` | `JSendResponse[LoginResponse]` | Login & generate JWT |
| POST | `/api/v1/auth/logout` | - | `JSendResponse` | Invalidate token |
| GET | `/api/v1/auth/me` | - | `JSendResponse[UserResponse]` | Get current user profile |
| PUT | `/api/v1/auth/me` | `UserUpdate` | `JSendResponse[UserResponse]` | Update profile |
| POST | `/api/v1/auth/register` | `{nim, password}` | `JSendResponse[LoginResponse]` | Register new user |

#### B. Pre-Test Endpoints

| Method | Endpoint | Input | Output | Description |
|--------|----------|-------|--------|-------------|
| GET | `/api/v1/pretest/questions` | - | `JSendResponse[Question[]]` | Get 5 adaptive pre-test questions |
| POST | `/api/v1/pretest/submit` | `{answers}` | `JSendResponse[PreTestResult]` | Submit pre-test → calculate θ_initial |

#### C. Content & Module Endpoints

| Method | Endpoint | Input | Output | Description |
|--------|----------|-------|--------|-------------|
| GET | `/api/v1/modules` | - | `JSendResponse[Module[]]` | Get all modules (with lock status) |
| GET | `/api/v1/modules/{module_id}` | - | `JSendResponse[ModuleDetail]` | Get module detail |
| GET | `/api/v1/modules/{module_id}/content` | - | `JSendResponse[ModuleContent]` | Get HTML content for module |

#### D. Assessment Endpoints

| Method | Endpoint | Input | Output | Description |
|--------|----------|-------|--------|-------------|
| POST | `/api/v1/session/start` | `{module_id}` | `JSendResponse[SessionStart]` | Start adaptive session |
| GET | `/api/v1/session/{session_id}` | - | `JSendResponse[SessionStatus]` | Get current session status |
| POST | `/api/v1/session/{session_id}/submit` | `{question_id, query}` | `JSendResponse[SubmitResult]` | Submit answer → update θ + check stagnation |
| GET | `/api/v1/session/{session_id}/history` | - | `JSendResponse[AssessmentLog[]]` | Get session history |

#### E. Collaborative Endpoints

| Method | Endpoint | Input | Output | Description |
|--------|----------|-------|--------|-------------|
| GET | `/api/v1/collaboration/inbox` | - | `JSendResponse[PeerSession[]]` | Get pending review tasks |
| GET | `/api/v1/collaboration/inbox/{session_id}` | - | `JSendResponse[PeerSessionDetail]` | Get review task detail |
| POST | `/api/v1/collaboration/inbox/{session_id}/submit` | `{review_content}` | `JSendResponse[ReviewResult]` | Submit review → NLP scoring |
| GET | `/api/v1/collaboration/requests` | - | `JSendResponse[PeerSession[]]` | Get my review requests status |
| POST | `/api/v1/collaboration/requests/{session_id}/rate` | `{is_helpful}` | `JSendResponse[RateResult]` | Rate received feedback → update θ_social |

#### F. Profile & Statistics Endpoints

| Method | Endpoint | Input | Output | Description |
|--------|----------|-------|--------|-------------|
| GET | `/api/v1/profile/stats` | - | `JSendResponse[ProfileStats]` | Get user statistics |
| GET | `/api/v1/profile/history` | `{limit?, offset?}` | `JSendResponse[AssessmentLog[]]` | Get assessment history |
| GET | `/api/v1/profile/social` | - | `JSendResponse[SocialAwareness]` | Get social awareness data |

---

## 8. LOGGING SPECIFICATION

### 8.1 Dual Logging System

| Log Type | Location | Format | Rotation | Retention |
|----------|----------|--------|----------|-----------|
| **System Logs** | `/app/logs/syslogs/` | JSON | 10MB per file | 5 backup files |
| **Assessment Logs** | `/app/logs/asslogs/` | JSON | 10MB per file | 5 backup files |
| **Assessment DB** | PostgreSQL `assessment_logs` | Structured | Persistent | Indefinite |

### 8.2 Log File Naming Convention

```
syslogs/syslog_YYYYMMDD_HHMMSS.json
asslogs/asslog_YYYYMMDD_HHMMSS.json
```

### 8.3 Log Level Configuration

| Level | Syslog | Asslog | Use Case |
|-------|--------|--------|----------|
| `DEBUG` | ❌ Optional | ❌ No | Development troubleshooting only |
| `INFO` | ✅ Yes | ✅ Yes | Normal operations (health checks, logins, submissions) |
| `WARNING` | ✅ Yes | ✅ Yes | Potential issues (validation warnings, near-stagnation) |
| `ERROR` | ✅ Yes | ✅ Yes | Errors that need attention (DB errors, auth failures) |
| `CRITICAL` | ✅ Yes | ✅ Yes | System failures (service down, data corruption) |

**Default:** `INFO` (configurable via `LOG_LEVEL` environment variable)

### 8.4 Log Entry Format (JSON)

```json
{
  "timestamp": "2026-02-22T14:13:58.187996Z",
  "level": "INFO",
  "logger": "equilibria.system",
  "message": "Login successful for user: 18222047",
  "module": "auth",
  "function": "login",
  "line": 123,
  "user_id": "cb876914-b0a3-4b56-a59a-87c1bbde63bc",
  "event_type": "AUTH_LOGIN_SUCCESS"
}
```

### 8.5 Assessment Log Fields

```json
{
  "timestamp": "2026-02-22T14:13:58.187996Z",
  "level": "INFO",
  "logger": "equilibria.assessment",
  "message": "Assessment event: ASSESSMENT_SUBMIT",
  "user_id": "cb876914-b0a3-4b56-a59a-87c1bbde63bc",
  "session_id": "uuid-session-123",
  "question_id": "CH01-Q005",
  "theta_before": 1.25,
  "theta_after": 1.32,
  "is_correct": true,
  "execution_time_ms": 1200,
  "event_type": "ASSESSMENT_SUBMIT"
}
```

---

## 9. CONFIGURATION MANAGEMENT

### 9.1 Environment Variables (Backend)

Semua konfigurasi yang bersifat rahasia harus ditetapkan dengan env var. Gunakan pydantic di backend untuk validasi dan type-safety.

**Variabel Wajib Backend:**
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - JWT signing key
- `LOG_LEVEL` - Logging verbosity (INFO/DEBUG)
- `SANDBOX_DB_ROLE` - Sandbox executor role name

### 9.2 Environment Variables (Frontend)

Semua env var frontend menggunakan prefix `VITE_`, seperti yang sudah disebutkan di awal.

**Variabel Wajib Frontend:**
- `VITE_API_BASE_URL` - Backend API endpoint
- `VITE_APP_NAME` - Application display name
- `VITE_VERSION` - Frontend version

---

## 10. SECURITY & LIMITATIONS

### 10.1 Sandbox Security (Minimal Viable)

| Feature | Status | Implementation |
|---------|--------|----------------|
| `SELECT`-only access | ✅ | Dedicated role `sandbox_executor` |
| No `public` schema access | ✅ | `REVOKE ALL ON SCHEMA public` |
| Query timeout | ✅ | `statement_timeout = 5000` |
| Dangerous keyword blocklist | ✅ | `DROP`, `DELETE`, `ALTER`, `pg_`, `;` |
| Container isolation | ⚠️ | Not implemented (prototype scale) |

**Limitation:** Keamanan sandbox tidak menjadi fokus utama karena sistem diimplementasikan sebagai purwarupa terbatas (10-20 user) untuk validasi algoritma adaptif. Implementasi produksi memerlukan isolasi proses (Docker) dan mekanisme timeout yang lebih ketat.

### 10.2 Edge Cases Handling

| Edge Case | Risk Level | Mitigation Strategy |
|-----------|------------|---------------------|
| Bank soal habis | Rendah | Kombinasi 40C16 ≈ 4.8 juta → negligible untuk 10-20 user |
| Peer review deadlock | Sedang | Safeguard: hindari reviewer dengan status `NEEDS_PEER_REVIEW` |
| Cold-start θ=0.0 | Rendah | Diatasi oleh mandatory pre-test (5 soal adaptif) |
| JWT token expiration | Rendah | Refresh token mechanism (7 days) |
| Database connection pool exhausted | Sedang | Connection pooling with `pool_size=10`, `max_overflow=20` |
| Log file disk space | Rendah | Auto-rotation at 10MB, 5 backup files |

### 10.3 Password Security

- **Algorithm:** Argon2id (standar industri sejak 2021)
- **Parameters:** `m=2^(16), t=3, p=4` (rekomendasi [RFC 9106](https://datatracker.ietf.org/doc/rfc9106/#:~:text=2.%20%20%20If%20much%20less%20memory%20is%20available%2C%20a%20uniformly%20safe%20option%20is%0A%20%20%20%20%20%20%20%20Argon2id%20with%20t%3D3%20iterations%2C%20p%3D4%20lanes%2C%20m%3D2%5E(16)%20(64%20MiB%20of%0A%20%20%20%20%20%20%20%20RAM)%2C%20128%2Dbit%20salt%2C%20and%20256%2Dbit%20tag%20size.%20%20This%20is%20the%20SECOND%0A%20%20%20%20%20%20%20%20RECOMMENDED%20option.))
- **Storage:** Only hash stored in database, never plaintext
- **Transmission:** HTTPS only in production

### 10.4 JWT Security

- **Algorithm:** HS256 (HMAC with SHA-256)
- **Expiration:** 30 minutes (access token), 7 days (refresh token)
- **Storage:** HttpOnly cookie (frontend), Bearer header (API)
- **Validation:** Signature + expiration + user existence check

---

## 11. DEPLOYMENT SPECIFICATION

### 11.1 Infrastructure Overview

| Service | Platform | Configuration |
|---------|----------|---------------|
| Frontend | Vercel | Hobby Tier (free), environment variables via dashboard |
| Backend | Render/Railway | Free Tier, Docker deployment |
| Database | Supabase | Free Tier (500MB), or Render PostgreSQL |
| Domain | Provider Subdomain | Free (e.g., `equilibria.onrender.com`) |

Catatan: untuk deployment backend ada alternatif menggunakan Azure VM karena ada credits mahasiswa gratis, tapi akan jauh lebih technical karena IaaS bukan PaaS. Akan menyesuaikan timeline selesainya keseluruhan source code.

### 11.2 Docker Configuration

Backend dan database dikontainerisasi agar mudah dideploy.

**Key Configuration:**
- Health check untuk memastikan db ready sebelum backend jalan
- Env var di-inject via `.env` files
- Log directory di-mount juga supaya bisa diakses

### 11.3 Deployment Pipeline

1. **Development:** Local Docker Compose with hot reload
2. **Staging:** Platform auto-deploy on git push to staging branch
3. **Production:** Manual approval required for production deployment

---

## 12. TESTING & EVALUATION

### 12.1 Controlled Lab Study Design

- **Method:** One-Group Pretest-Posttest
- **Participants:** 10-15 mahasiswa STEI
- **Duration:** 90-120 menit per sesi
- **Location:** Controlled lab environment

### 12.2 Testing Phases

| Phase | Duration | Activity |
|-------|----------|----------|
| Pre-test | 15 min | Baseline knowledge assessment (5 adaptive questions) |
| System Interaction | 45 min | Adaptive SQL practice sessions |
| Social Intervention | 30 min | Peer assessment (triggered by stagnation detection) |
| Post-test | 15 min | Final knowledge assessment |

### 12.3 Success Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| **Normalized Learning Gain** | `g = (post - pre) / (100 - pre)` | g ≥ 0.3 (Medium) |
| **Peer Feedback Quality** | Multi-LLM Voting (Kerman et al. 2024 rubric) | Score ≥ 0.6 |
| **Matching Validity** | `|θ_reviewer - θ_requester| ≥ 0.5 * σ` | 100% compliance |
| **System Availability** | Uptime during testing | ≥ 99% |
| **Response Time** | API latency (p95) | ≤ 500ms |

### 12.4 Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Participant availability | Medium (3) | High (5) | Prepare dummy accounts with varied Elo profiles |
| Cold-start accuracy | Medium (3) | Medium (3) | Use pre-test results as R0 for faster convergence |
| Subjective rubric bias | Low (2) | Low (2) | Double-blind system + Multi-LLM validation |

---

## 13. APPENDIX: PARAMETER CALIBRATION LOG

### 13.1 ε Stagnation Threshold (Empirical Calibration)

| Simulation Pattern | Δθ Sequence | Variance | Decision |
|-------------------|-------------|----------|----------|
| Real stagnation (B-S-B-S-B) | [+0.02, -0.01, ...] | 0.00015 | Trigger |
| Normal fluctuation | [+0.3, -0.2, ...] | 0.048 | No trigger |
| **Threshold selected** | — | **0.05** | **3× safety margin** |

**Justification:** Nilai 0.05 memberikan margin 3× di atas variansi stagnan nyata, sekaligus di bawah fluktuasi normal. Sesuai dengan kriteria normalized learning gain rendah (<0.3) menurut Hake (1999).

### 13.2 K-Factor Decay Rationale

| Total Attempts | K-Factor | Reason |
|----------------|----------|--------|
| < 10 | 32 | Responsive for initial calibration |
| 10–24 | 24 | Stable transition toward convergence |
| ≥ 25 | 16 | Avoid overfitting on late-stage |

**Source:** Mengadopsi Vesin et al. (2022) `{30,20,15,10}` dengan modifikasi proporsional untuk skala normalized [-3.0, +3.0].

### 13.3 Cohen's d Threshold

| Effect Size | d Value | Interpretation |
|-------------|---------|----------------|
| Small | 0.2 | Detectable only with statistical analysis |
| **Medium** | **0.5** | **Visible to naked eye (selected)** |
| Large | 0.8 | Very obvious difference |

**Source:** Cohen (1988), Statistical Power Analysis for the Behavioral Sciences

---

## 14. REFERENCES (TECHNICAL BASIS)

1. Vesin, B., et al. (2022). Adaptive Assessment and Content Recommendation in Online Programming Courses: On the Use of Elo-rating. ACM TOCE.
2. Kerman, N. T., et al. (2024). Online peer feedback patterns of success and failure in argumentative essay writing. Interactive Learning Environments.
3. ACM CCECC (2023). Bloom's for Computing: Enhancing Bloom's Revised Taxonomy with Verbs for Computing Disciplines.
4. Cohen, J. (1988). Statistical Power Analysis for the Behavioral Sciences (2nd ed.).
5. Biasio, A. D., et al. (2023). On the problem of recommendation for sensitive users and influential items. Knowledge-Based Systems.
6. Hake, R. R. (1999). Analyzing change/gain scores. Woodbury, MN: AERA/NCME.
7. Minn, S. (2022). AI-assisted knowledge assessment techniques for adaptive learning environments. Computers and Education: Artificial Intelligence.
8. Brusilovsky, P., et al. (2016). Open Social Student Modeling for Personalized Learning. IEEE Transactions on Emerging Topics in Computing.

---

**Document Version:** 3.0  
**Last Updated:** February 22, 2026  
**Author:** Dama Dhananjaya Daliman (18222047)  
**Status:** Implementation Ready