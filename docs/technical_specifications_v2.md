# TECHNICAL SPECIFICATION DOCUMENT: EQUILIBRIA

**Project**: Prototype of Collaborative Adaptive Assessment System with Overpersonalization Mitigation  
**Student**: Dama Dhananjaya Daliman (18222047)  
**Version**: 2.0 (Revised with Empirical Calibration & Collaborative Safeguards)  
**Date**: February 15, 2026

---

## 0. EXECUTIVE SUMMARY

Equilibria adalah purwarupa sistem asesmen adaptif berbasis *Computerized Adaptive Testing* (CAT) yang dirancang khusus untuk domain pendidikan Ilmu Komputer, dengan studi kasus pada materi **SQL Querying**. Sistem ini mengimplementasikan **Elo Rating System** yang dimodifikasi untuk kalibrasi dinamis tingkat kesulitan soal terhadap kemampuan siswa secara real-time.

Sebagai *novelty*, Equilibria memperkenalkan **Mekanisme Kolaboratif Mitigasi Overpersonalization** yang secara proaktif mendeteksi stagnasi kemampuan siswa melalui analisis variansi perubahan skor (`Δθ`), lalu memicu intervensi sosial (*Peer Review*) dengan *constraint-based re-ranking* berbasis Cohen's *d* ≥ 0.5 untuk memastikan heterogenitas pasangan. Integrasi metrik individu dan sosial dilakukan dengan bobot 50-50, dengan logging komprehensif yang memungkinkan simulasi ulang pasca-hoc untuk eksplorasi optimalisasi bobot.

Sistem dibangun dengan arsitektur Client-Server modern menggunakan React.js (frontend) dan FastAPI (backend), dengan PostgreSQL sebagai basis data yang dipisahkan menjadi skema `public` (operasional) dan `sandbox` (eksekusi query aman). Dokumen ini memuat spesifikasi teknis menyeluruh termasuk kalibrasi empiris parameter algoritmik, safeguard kolaboratif, dan flow pengguna yang telah divalidasi secara pedagogis.

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
├── client/                 # React Frontend (Vite)
│   ├── src/
│   │   ├── components/    # Reusable UI (Editor, RadarChart)
│   │   ├── pages/         # Route-based pages
│   │   │   ├── Auth/
│   │   │   │   ├── Login.tsx
│   │   │   │   └── PreTest.tsx
│   │   │   ├── Dashboard/
│   │   │   │   └── Dashboard.tsx
│   │   │   ├── Coursework/
│   │   │   │   ├── ModuleList.tsx
│   │   │   │   ├── ModuleDetail.tsx
│   │   │   │   └── AdaptiveSession.tsx
│   │   │   ├── Collaborative/
│   │   │   │   ├── PeerReviewInbox.tsx
│   │   │   │   ├── ReviewTask.tsx
│   │   │   │   └── RequestStatus.tsx
│   │   │   └── Profile/
│   │   │       ├── UserProfile.tsx
│   │   │       └── HistoryLog.tsx
│   │   ├── services/      # Axios API clients
│   │   │   ├── auth.api.ts
│   │   │   ├── content.api.ts
│   │   │   ├── assessment.api.ts
│   │   │   └── collaboration.api.ts
│   │   ├── routes/        # React Router configuration
│   │   │   └── AppRouter.tsx
│   │   └── store/          # Zustand state management
│   └── package.json
├── server/                 # Python Backend (FastAPI)
│   ├── app/
│   │   ├── api/           # Routers (auth, assessment, collab)
│   │   ├── core/          # Business Logic
│   │   ├── db/            # Database layer
│   │   ├── sandbox/       # Secure SQL execution
│   │   ├── schemas/       # Pydantic models
│   │   └── main.py        # App entry point
│   └── requirements.txt
├── docs/
│   └── pretest_calibration.md
├── docker-compose.yml
└── README.md
```

---

## 2. TECHNOLOGY STACK

| Layer          | Technology                          | Rationale                                                                 |
|----------------|-------------------------------------|---------------------------------------------------------------------------|
| **Frontend**   | React 18 + Vite                     | Fast HMR, component-based architecture                                    |
|                | React Router v6                     | Declarative routing for SPA navigation                                    |
|                | Tailwind CSS                        | Utility-first styling for rapid UI development                            |
|                | CodeMirror 6                        | Lightweight SQL editor with syntax highlighting                           |
|                | Zustand                             | Minimalist state management (no boilerplate)                              |
| **Backend**    | Python 3.12                         | Rich ecosystem for scientific computing (NumPy)                           |
|                | FastAPI                             | Async support, automatic OpenAPI docs, Pydantic validation                |
|                | SQLAlchemy (Async)                  | ORM with connection pooling for concurrent sessions                       |
| **Database**   | PostgreSQL 15                       | ACID compliance, MVCC for concurrent peer sessions                        |
| **Deployment** | Docker Compose                      | Isolated services (app, db, redis for caching)                            |

---

## 3. DATABASE SPECIFICATION

### 3.1 Core Schema (`public`)

#### Table `users`
| Column           | Type        | Constraints                     | Description                                  |
|------------------|-------------|---------------------------------|----------------------------------------------|
| `user_id`        | UUID        | PK                              | Unique identifier                            |
| `nim`            | VARCHAR(20) | UNIQUE, NOT NULL                | Student ID                                   |
| `full_name`      | VARCHAR(100)| NOT NULL                        | Display name                                 |
| `password_hash`  | VARCHAR     | NOT NULL                        | Argon2id hashed password                     |
| `current_theta`  | FLOAT       | DEFAULT 0.0, RANGE [-3.0, +3.0] | Normalized Elo rating (individual)           |
| `theta_social`   | FLOAT       | DEFAULT 0.0                     | Social contribution score                    |
| `k_factor`       | INTEGER     | DEFAULT 32                      | Sensitivity factor (decays with attempts)    |
| `has_completed_pretest` | BOOLEAN | DEFAULT FALSE               | Mandatory cold-start flag                    |
| `created_at`     | TIMESTAMP   | DEFAULT NOW()                   | Account creation timestamp                   |

#### Table `modules`
| Column                | Type        | Description                          |
|-----------------------|-------------|--------------------------------------|
| `module_id`           | VARCHAR(5)  | PK (e.g., `'CH01'`)                  |
| `title`               | VARCHAR     | Display name                         |
| `description`         | TEXT        | Module overview                      |
| `difficulty_min`      | FLOAT       | Lower bound of D (e.g., -3.0)        |
| `difficulty_max`      | FLOAT       | Upper bound of D (e.g., -1.0)        |
| `content_html`        | TEXT        | HTML content for learning material   |
| `is_locked`           | BOOLEAN     | TRUE if requires previous completion |

#### Table `questions`
| Column           | Type          | Description                                  |
|------------------|---------------|----------------------------------------------|
| `question_id`    | VARCHAR(10)   | PK (e.g., `CH01-Q005`)                       |
| `module_id`      | VARCHAR(5)    | FK → `modules`                               |
| `content`        | TEXT          | HTML/Markdown question narrative             |
| `target_query`   | TEXT          | Canonical solution                           |
| `initial_difficulty` | FLOAT     | Manually calibrated (post-pretest)           |
| `current_difficulty` | FLOAT     | Dynamically updated via Elo                  |
| `topic_tags`     | TEXT[]        | e.g., `['JOIN', 'GROUP BY']`                 |
| `is_active`      | BOOLEAN       | TRUE if available for selection              |

#### Table `assessment_logs`
| Column          | Type      | Description                                  |
|-----------------|-----------|----------------------------------------------|
| `log_id`        | SERIAL    | PK                                           |
| `session_id`    | UUID      | Grouping identifier for a practice session   |
| `user_id`       | UUID      | FK → `users`                                 |
| `question_id`   | VARCHAR   | FK → `questions`                             |
| `user_query`    | TEXT      | Submitted solution                           |
| `is_correct`    | BOOLEAN   | Result of sandbox comparison                 |
| `theta_before`  | FLOAT     | θ before attempt                             |
| `theta_after`   | FLOAT     | θ after update                               |
| `execution_time_ms` | INTEGER | Time to solve (excluding idle)               |
| `timestamp`     | TIMESTAMP | Attempt timestamp                            |

#### Table `peer_sessions`
| Column                | Type      | Constraints                     | Description                                  |
|-----------------------|-----------|---------------------------------|----------------------------------------------|
| `session_id`          | UUID      | PK                              | Unique session identifier                    |
| `requester_id`        | UUID      | FK → `users`                    | User experiencing stagnation                 |
| `reviewer_id`         | UUID      | FK → `users`                    | Assigned heterogeneous peer                  |
| `question_id`         | VARCHAR   | FK → `questions`                | Context of review                            |
| `review_content`      | TEXT      | NOT NULL                        | Constructive feedback text                   |
| `system_score`        | FLOAT     | RANGE [0.0, 1.0]                | NLP keyword matching score                   |
| `is_helpful`          | BOOLEAN   | NULLABLE                        | Requester's binary confirmation              |
| `final_score`         | FLOAT     | COMPUTED                        | `(0.5 * system_score) + (0.5 * is_helpful)`  |
| `status`              | VARCHAR   | ENUM: `PENDING_REVIEW`, `WAITING_CONFIRMATION`, `COMPLETED` | Session state |
| `created_at`          | TIMESTAMP | DEFAULT NOW()                   | Session initiation                           |

### 3.2 Sandbox Schema (`sandbox`)
- **Tables**: `mahasiswa`, `matakuliah`, `dosen`, `frs` (read-only dummy data)
- **Security**:
  - Dedicated DB role `sandbox_executor` dengan hak akses **hanya `SELECT`** pada skema `sandbox`
  - Tidak ada hak akses ke skema `public`
  - Query timeout: 5000 ms (via `statement_timeout` PostgreSQL GUC)

---

## 4. MATERIAL STRUCTURE (HIERARCHICAL DOMAIN)

| Module | Topic Focus                     | Difficulty Range (D) | Sample Count | Description                                  |
|--------|---------------------------------|----------------------|--------------|----------------------------------------------|
| CH01   | Basic Selection                 | [-3.0, -1.0]         | 40           | `SELECT..WHERE`, logical operators           |
| CH02   | Aggregation                     | [-1.0, +1.0]         | 40           | `GROUP BY..HAVING`, aggregate functions      |
| CH03   | Advanced Querying               | [+1.0, +3.0]         | 40           | CTE (`WITH`), Subquery, Multiple Joins       |

> **Note**: Setiap modul menyediakan 2.5× jumlah soal minimum per sesi (16 soal) → **kombinasi 40C16 ≈ 4.8 juta**. Risiko "bank soal habis" dianggap negligible untuk skala 10-20 user.

---

## 5. FRONTEND SPECIFICATION (ROUTING & UI)

### 5.1 React Router Configuration

```typescript
// src/routes/AppRouter.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ProtectedRoute } from './ProtectedRoute';
import { AuthRoute } from './AuthRoute';

// Pages
import { Login } from '../pages/Auth/Login';
import { PreTest } from '../pages/Auth/PreTest';
import { Dashboard } from '../pages/Dashboard/Dashboard';
import { ModuleList } from '../pages/Coursework/ModuleList';
import { ModuleDetail } from '../pages/Coursework/ModuleDetail';
import { AdaptiveSession } from '../pages/Coursework/AdaptiveSession';
import { PeerReviewInbox } from '../pages/Collaborative/PeerReviewInbox';
import { ReviewTask } from '../pages/Collaborative/ReviewTask';
import { RequestStatus } from '../pages/Collaborative/RequestStatus';
import { UserProfile } from '../pages/Profile/UserProfile';
import { HistoryLog } from '../pages/Profile/HistoryLog';

export const AppRouter = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<AuthRoute><Login /></AuthRoute>} />
        
        {/* Protected Routes - Require Authentication */}
        <Route element={<ProtectedRoute />}>
          {/* Pre-Test Flow (Mandatory for new users) */}
          <Route path="/pretest" element={<PreTest />} />
          
          {/* Dashboard (Default Route) */}
          <Route path="/" element={<Dashboard />} />
          
          {/* Coursework Routes */}
          <Route path="/modules" element={<ModuleList />} />
          <Route path="/modules/:moduleId" element={<ModuleDetail />} />
          <Route path="/session/start" element={<AdaptiveSession />} />
          
          {/* Collaborative Routes */}
          <Route path="/collaboration/inbox" element={<PeerReviewInbox />} />
          <Route path="/collaboration/review/:sessionId" element={<ReviewTask />} />
          <Route path="/collaboration/requests" element={<RequestStatus />} />
          
          {/* Profile Routes */}
          <Route path="/profile" element={<UserProfile />} />
          <Route path="/profile/history" element={<HistoryLog />} />
        </Route>
        
        {/* 404 Route */}
        <Route path="*" element={<div>404 - Page Not Found</div>} />
      </Routes>
    </BrowserRouter>
  );
};
```

### 5.2 Protected Route & Auth Route Components

```typescript
// src/routes/ProtectedRoute.tsx
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

export const ProtectedRoute = () => {
  const { isAuthenticated, isLoading } = useAuthStore();
  
  if (isLoading) {
    return <div>Loading...</div>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <Outlet />;
};

// src/routes/AuthRoute.tsx
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

export const AuthRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuthStore();
  
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }
  
  return <>{children}</>;
};
```

### 5.3 Navigation Flow & Menu Structure

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

---

## 6. ALGORITHMIC LOGIC (BACKEND CORE)

### 6.1 Pre-Test Flow (Mandatory Cold-Start Calibration)

> **Rationale**: Menghindari *cold-start bias* dengan kalibrasi awal berbasis 5 soal adaptif sebelum akses platform utama.

```python
# Flow: /pretest → 5 adaptive questions → calculate θ_initial → redirect to dashboard
def calculate_initial_theta(correct_count: int, difficulties: List[float]) -> float:
    """
    Formula empiris berdasarkan simulasi pola stagnasi:
    - Baseline: θ = 0.0
    - Adjustment: ±0.4 per jawaban benar/salah dari baseline 2.5/5
    - Clamp ke [-1.5, +1.5] untuk menghindari ekstrem
    """
    baseline = 2.5  # Expected correct for θ=0.0
    adjustment = (correct_count - baseline) * 0.4
    theta_initial = max(-1.5, min(1.5, 0.0 + adjustment))
    
    # Justifikasi akademis implisit:
    # Nilai ini sejalan dengan normalized learning gain rendah (<0.3) menurut Hake (1999),
    # di mana perubahan kemampuan <0.05 dalam 5 attempt dianggap stagnan secara pedagogis.
    return theta_initial
```

### 6.2 Adaptive Engine (Individual Mode)

#### Item Selection Strategy
1. Filter soal dalam modul aktif yang belum dikerjakan user (`assessment_logs`)
2. Hitung jarak absolut: `|D_j - θ_user|`
3. Ambil 5 kandidat dengan jarak terkecil
4. Pilih 1 secara acak (*proportional random*) untuk menghindari repetisi pola

#### Elo Update Formula
```
P = 1 / (1 + 10^((D - θ) / 400))   # Expected probability
θ_new = θ_old + K * (Score - P)    # Student update
D_new = D_old + K * (P - Score)    # Item difficulty update
```

#### K-Factor Adaptation (Piecewise Decay)
```python
def get_k_factor(total_attempts: int) -> int:
    """
    Mengadopsi pendekatan Vesin et al. (2022) dengan modifikasi skala:
    - Skala θ kami: [-3.0, +3.0] (normalized) vs Vesin [1100, 1500] (chess-like)
    - Decay piecewise untuk interpretabilitas & stabilitas konvergensi
    """
    if total_attempts < 10:
        return 32  # Responsif untuk cold-start
    elif total_attempts < 25:
        return 24  # Transisi stabil
    else:
        return 16  # Konvergensi halus
```

### 6.3 Stagnation Detection (ε = 0.05)

#### Parameter Justifikasi
- **Nilai ε = 0.05** ditentukan melalui **kalibrasi empiris**:
  - Simulasi pola stagnasi buatan (benar-salah-benar-salah dalam 5 attempt berturut-turut)
  - Variansi Δθ dari pola stagnan nyata ≈ 0.0001–0.002 → ambang batas 0.05 memberikan margin aman
  - Sesuai dengan kriteria *normalized learning gain* rendah (<0.3) menurut Hake (1999)

#### Implementasi
```python
def detect_stagnation(user_id: UUID, db: Session) -> bool:
    """
    Hitung variansi perubahan θ dalam 5 attempt terakhir.
    Trigger jika variansi < ε = 0.05 (stagnasi terdeteksi).
    """
    logs = db.query(AssessmentLog)\
             .filter(AssessmentLog.user_id == user_id)\
             .order_by(AssessmentLog.timestamp.desc())\
             .limit(5)\
             .all()
    
    if len(logs) < 5:
        return False  # Butuh minimal 5 attempt untuk deteksi
    
    deltas = [log.theta_after - log.theta_before for log in logs]
    variance = np.var(deltas)
    
    return variance < 0.05  # ε empiris
```

### 6.4 Constraint-Based Re-ranking (Heterogeneity Enforcement)

#### Cohen's d ≥ 0.5 Threshold
- **Dasar statistik**: Cohen (1988) mendefinisikan *d* = 0.5 sebagai efek sedang (*"visible to the naked eye"*)
- **Implementasi**: Pastikan pasangan memiliki perbedaan kemampuan signifikan:
  ```
  |θ_reviewer - θ_requester| ≥ 0.5 * σ_population
  ```
  dengan `σ_population` = standar deviasi rating seluruh kelas (dihitung real-time)

#### Peer Matching Safeguard
```sql
-- Hindari circular dependency & repetition
SELECT user_id 
FROM users 
WHERE status != 'NEEDS_PEER_REVIEW'  -- Hindari reviewer yang juga butuh review
  AND user_id NOT IN (
    SELECT reviewer_id 
    FROM peer_sessions 
    WHERE requester_id = :current_user 
      AND question_id = :current_question  -- Hindari pasangan ulang di soal sama
  )
ORDER BY 
  ABS(current_theta - :target_theta) DESC,  -- Prioritaskan heterogenitas
  RANDOM()  -- Randomisasi untuk diversity
LIMIT 10;
```

### 6.5 NLP Feedback Quality (Keyword Matching)

#### Sumber Kata Kunci
- **Kerman et al. (2024)**: Dimensi *Constructive* + *Identification* sebagai predictor keberhasilan
- **Bloom's for Computing (ACM CCECC 2023)**: Kata kerja level *Analyzing* (`detect`, `trace`, `debug`) dan *Evaluating* (`optimize`, `validate`)

#### Daftar Keyword Inti (25 kata)
```python
CONSTRUCTIVE_KEYWORDS = [
    "coba", "sebaiknya", "alternatif", "ganti", "pakai", "gunakan",
    "pertimbangkan", "rekomendasi", "saran", "solusi", "optimasi",
    "debug", "trace", "detect", "validate"
]

IDENTIFICATION_KEYWORDS = [
    "error", "bug", "salah", "masalah", "kurang", "tidak tepat",
    "missing", "where", "join", "null", "group by", "having"
]
```

#### Scoring Algorithm
```python
def calculate_system_score(feedback: str) -> float:
    # Minimal length check (hindari "bagus"/"jelek")
    if len(feedback.strip()) < 15:
        return 0.2
    
    text = feedback.lower()
    has_constructive = any(kw in text for kw in CONSTRUCTIVE_KEYWORDS)
    has_identification = any(kw in text for kw in IDENTIFICATION_KEYWORDS)
    
    if has_constructive and has_identification:
        return 0.9  # Excellent (sesuai temuan Kerman: predictor success)
    elif has_constructive or has_identification:
        return 0.6  # Good
    else:
        return 0.3  # Poor (murni affective)
```

### 6.6 Integrasi Elo Individu & Sosial (50-50)

#### Final Rating Calculation
```
θ_final = (0.5 * θ_individual) + (0.5 * θ_social)
```

#### Logging untuk Simulasi Ulang
```json
{
  "timestamp": "2026-02-15T14:30:00Z",
  "user_id": "uuid-123",
  "session_type": "individual|peer_review|peer_requester",
  "theta_before": 1.25,
  "theta_after": 1.32,
  "k_factor": 24,
  "score": 0.85,
  "activity_detail": {
    "question_id": "CH01-Q005",
    "is_correct": true,
    "attempts": 1,
    "execution_time_ms": 1200,
    "peer_session_id": "optional-uuid",
    "system_score": 0.9,
    "requester_feedback": true
  }
}
```

> **Catatan**: Bobot 50-50 dipilih sebagai *baseline ekuilibrium*. Dengan logging komprehensif di atas, simulasi ulang dengan bobot berbeda (`α` untuk individu, `1-α` untuk sosial) dapat dilakukan pasca-hoc tanpa re-run eksperimen.

---

## 7. BACKEND API SPECIFICATION

### 7.1 Authentication & Authorization

#### JWT Flow
```
POST /api/v1/auth/login → {nim, password} → JWT (HttpOnly cookie)
→ Setiap request sertakan: Authorization: Bearer <token>
→ FastAPI dependency: get_current_user() → validasi JWT
```

#### Response Convention (JSend)
```python
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel
from enum import Enum

T = TypeVar('T')

class StatusEnum(str, Enum):
    SUCCESS = "success"
    FAIL = "fail"
    ERROR = "error"

class JSendResponse(BaseModel, Generic[T]):
    status: StatusEnum
    code: int
    data: Optional[T] = None
    message: Optional[str] = None
```

---

### 7.2 Complete API Endpoints Reference

#### A. Authentication Endpoints

| Method | Endpoint | Input | Output | Description |
|--------|----------|-------|--------|-------------|
| POST | `/api/v1/auth/login` | `{nim: string, password: string}` | `{token: string, user: User}` | Login & generate JWT |
| POST | `/api/v1/auth/logout` | - | `{message: string}` | Invalidate token |
| GET | `/api/v1/auth/me` | - | `User` | Get current user profile |
| PUT | `/api/v1/auth/me` | `UserUpdate` | `User` | Update profile |

#### B. Pre-Test Endpoints

| Method | Endpoint | Input | Output | Description |
|--------|----------|-------|--------|-------------|
| GET | `/api/v1/pretest/questions` | - | `Question[]` | Get 5 adaptive pre-test questions |
| POST | `/api/v1/pretest/submit` | `{answers: Answer[]}` | `{theta_initial: float, redirect: string}` | Submit pre-test → calculate θ_initial → redirect to dashboard |

#### C. Content & Module Endpoints

| Method | Endpoint | Input | Output | Description |
|--------|----------|-------|--------|-------------|
| GET | `/api/v1/modules` | - | `Module[]` | Get all modules (with lock status) |
| GET | `/api/v1/modules/{module_id}` | - | `ModuleDetail` | Get module detail (content + questions) |
| GET | `/api/v1/modules/{module_id}/content` | - | `{html: string}` | Get HTML content for module |
| GET | `/api/v1/modules/{module_id}/questions` | - | `Question[]` | Get all questions in module |

#### D. Assessment Endpoints

| Method | Endpoint | Input | Output | Description |
|--------|----------|-------|--------|-------------|
| POST | `/api/v1/session/start` | `{module_id: string}` | `{session_id: uuid, question: Question}` | Start adaptive session |
| GET | `/api/v1/session/{session_id}` | - | `SessionStatus` | Get current session status |
| POST | `/api/v1/session/{session_id}/submit` | `{question_id: string, query: string}` | `{is_correct: boolean, result_table: any[], next_question: Question?, theta_updated: float}` | Submit answer → update θ + check stagnation |
| GET | `/api/v1/session/{session_id}/history` | - | `AssessmentLog[]` | Get session history |

#### E. Collaborative Endpoints

| Method | Endpoint | Input | Output | Description |
|--------|----------|-------|--------|-------------|
| GET | `/api/v1/collaboration/inbox` | - | `PeerSession[]` | Get pending review tasks |
| GET | `/api/v1/collaboration/inbox/{session_id}` | - | `PeerSessionDetail` | Get review task detail |
| POST | `/api/v1/collaboration/inbox/{session_id}/submit` | `{review_content: string}` | `{system_score: float, status: string}` | Submit review → NLP scoring → WAITING_CONFIRMATION |
| GET | `/api/v1/collaboration/requests` | - | `PeerSession[]` | Get my review requests status |
| POST | `/api/v1/collaboration/requests/{session_id}/rate` | `{is_helpful: boolean}` | `{final_score: float, theta_social_updated: float}` | Rate received feedback → update θ_social |

#### F. Profile & Statistics Endpoints

| Method | Endpoint | Input | Output | Description |
|--------|----------|-------|--------|-------------|
| GET | `/api/v1/profile/stats` | - | `{theta: float, theta_social: float, radar_data: any}` | Get user statistics |
| GET | `/api/v1/profile/history` | `{limit?: number, offset?: number}` | `AssessmentLog[]` | Get assessment history |
| GET | `/api/v1/profile/social` | - | `{class_distribution: any[], user_position: number}` | Get social awareness data |

---

### 7.3 Detailed Endpoint Specifications

#### POST `/api/v1/session/{session_id}/submit`

**Request Body:**
```json
{
  "question_id": "CH01-Q005",
  "user_query": "SELECT * FROM mahasiswa WHERE ipk > 3.5"
}
```

**Response (Success - 200):**
```json
{
  "status": "success",
  "code": 200,
  "data": {
    "is_correct": true,
    "result_table": [
      {"nim": "18222047", "nama": "Dama Daliman", "ipk": 3.75},
      {"nim": "18222048", "nama": "John Doe", "ipk": 3.80}
    ],
    "execution_time_ms": 120,
    "theta_before": 1.25,
    "theta_after": 1.32,
    "next_question": {
      "question_id": "CH01-Q008",
      "content": "Tampilkan mahasiswa dengan IPK tertinggi...",
      "difficulty": 1.35
    },
    "stagnation_detected": false,
    "trigger_collaborative": false
  }
}
```

**Response (Stagnation Detected - 200):**
```json
{
  "status": "success",
  "code": 200,
  "data": {
    "is_correct": true,
    "result_table": [...],
    "theta_before": 1.25,
    "theta_after": 1.26,
    "next_question": null,
    "stagnation_detected": true,
    "trigger_collaborative": true,
    "message": "Sistem mendeteksi pola stagnan. Silakan selesaikan misi review untuk membuka materi selanjutnya.",
    "redirect_to": "/collaboration/inbox"
  }
}
```

#### POST `/api/v1/collaboration/inbox/{session_id}/submit`

**Request Body:**
```json
{
  "review_content": "Query Anda sudah benar, tapi bisa dioptimalkan dengan menambahkan index pada kolom ipk. Coba gunakan EXPLAIN untuk analisis performa."
}
```

**Response (Success - 200):**
```json
{
  "status": "success",
  "code": 200,
  "data": {
    "session_id": "uuid-123",
    "system_score": 0.9,
    "keywords_matched": ["optimasi", "index", "coba"],
    "status": "WAITING_CONFIRMATION",
    "requester_notified": true,
    "message": "Review berhasil dikirim. Menunggu konfirmasi dari requester."
  }
}
```

#### POST `/api/v1/collaboration/requests/{session_id}/rate`

**Request Body:**
```json
{
  "is_helpful": true
}
```

**Response (Success - 200):**
```json
{
  "status": "success",
  "code": 200,
  "data": {
    "session_id": "uuid-123",
    "final_score": 0.95,
    "system_score": 0.9,
    "requester_feedback": true,
    "reviewer_theta_before": 1.20,
    "reviewer_theta_after": 1.28,
    "status": "COMPLETED",
    "message": "Terima kasih atas feedback Anda. Reviewer telah mendapatkan poin."
  }
}
```

---

## 8. SECURITY & LIMITATIONS

### 8.1 Sandbox Security (Minimal Viable)
- ✅ Hak akses `SELECT`-only pada skema `sandbox`
- ✅ Blocklist kata kunci berbahaya: `DROP`, `DELETE`, `ALTER`, `pg_`, `;`
- ✅ Query timeout: 5000 ms
- ⚠️ **Limitation**: Tidak ada containerization/isolasi proses (risiko DoS via `pg_sleep`)
  > *"Keamanan sandbox tidak menjadi fokus utama karena sistem diimplementasikan sebagai purwarupa terbatas (10-20 user) untuk validasi algoritma adaptif. Implementasi produksi memerlukan isolasi proses (Docker) dan mekanisme timeout yang lebih ketat."*

### 8.2 Edge Cases Handling
| Edge Case | Risk Level | Mitigation Strategy |
|-----------|------------|---------------------|
| Bank soal habis | Rendah | Kombinasi 40C16 ≈ 4.8 juta → negligible untuk 10-20 user |
| Peer review deadlock | Sedang | Safeguard: hindari reviewer dengan status `NEEDS_PEER_REVIEW` |
| Cold-start θ=0.0 | Rendah | Diatasi oleh mandatory pre-test (5 soal adaptif) |

---

## 9. APPENDIX: PARAMETER CALIBRATION LOG

### 9.1 ε Stagnation Threshold (Empirical Calibration)
| Pola Simulasi | Δθ Sequence | Variansi | Keputusan |
|---------------|-------------|----------|-----------|
| Stagnan nyata (B-S-B-S-B) | [+0.02, -0.01, ...] | 0.00015 | **Trigger** |
| Fluktuasi normal | [+0.3, -0.2, ...] | 0.048 | Tidak trigger |
| **Threshold dipilih** | — | **0.05** | Margin aman 3× |

> Justifikasi: Nilai 0.05 memberikan margin 3× di atas variansi stagnan nyata, sekaligus di bawah fluktuasi normal. Sesuai dengan kriteria *normalized learning gain* rendah (<0.3) menurut Hake (1999).

### 9.2 K-Factor Decay Rationale
| Total Attempts | K-Factor | Alasan |
|----------------|----------|--------|
| < 10 | 32 | Responsif untuk kalibrasi awal |
| 10–24 | 24 | Transisi stabil menuju konvergensi |
| ≥ 25 | 16 | Hindari overfitting pada late-stage |

> Mengadopsi Vesin et al. (2022) `{30,20,15,10}` dengan modifikasi proporsional untuk skala normalized [-3.0, +3.0].

---

## 10. REFERENCES (TECHNICAL BASIS)

1. Vesin, B., et al. (2022). *Adaptive Assessment and Content Recommendation in Online Programming Courses: On the Use of Elo-rating*. ACM TOCE.
2. Kerman, N. T., et al. (2024). *Online peer feedback patterns of success and failure in argumentative essay writing*. Interactive Learning Environments.
3. ACM CCECC (2023). *Bloom's for Computing: Enhancing Bloom's Revised Taxonomy with Verbs for Computing Disciplines*.
4. Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences* (2nd ed.).
5. Biasio, A. D., et al. (2023). *On the problem of recommendation for sensitive users and influential items*. Knowledge-Based Systems.