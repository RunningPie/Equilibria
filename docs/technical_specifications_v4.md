# TECHNICAL SPECIFICATION DOCUMENT: EQUILIBRIA

**Project:** Prototype of Collaborative Adaptive Assessment System with Overpersonalization Mitigation  
**Student:** Dama Dhananjaya Daliman (18222047)  
**Version:** 4.1 (Alignment with Vesin et al. 2022 + Implementation Detail)  
**Date:** March 13, 2026  

---

## 0. EXECUTIVE SUMMARY

Equilibria adalah purwarupa sistem asesmen adaptif berbasis Computerized Adaptive Testing (CAT) yang dirancang khusus untuk domain pendidikan Ilmu Komputer, dengan studi kasus pada materi SQL Querying. Sistem ini mengimplementasikan **Elo Rating System yang dimodifikasi** (skala 500–1500, mengikuti standar catur, baseline 1300) untuk kalibrasi dinamis tingkat kesulitan soal terhadap kemampuan siswa secara real-time — mengikuti secara langsung metode yang diusulkan oleh Vesin et al. (2022) dalam ProTuS.

Sebagai novelty, Equilibria memperkenalkan **Mekanisme Kolaboratif Mitigasi Overpersonalization** yang secara proaktif mendeteksi stagnasi kemampuan siswa melalui analisis variansi perubahan skor (`Δθ`), lalu memicu intervensi sosial (Peer Review) dengan constraint-based re-ranking berbasis Cohen's d ≥ 0.5 untuk memastikan heterogenitas pasangan. Integrasi metrik individu dan sosial dilakukan dengan bobot 50-50, dengan logging komprehensif yang memungkinkan simulasi ulang pasca-hoc untuk eksplorasi optimalisasi bobot.

Sistem dibangun dengan arsitektur Client-Server modern menggunakan **React.js (frontend)** dan **FastAPI (backend)**, dengan **PostgreSQL** sebagai basis data yang dipisahkan menjadi skema `public` (operasional) dan `sandbox` (eksekusi query aman).

**Perubahan dari v3.1:**
- ✅ Initial Elo rating diubah dari 1000 ke **1300** (sesuai Vesin et al. 2022 — rating awal ProTuS)
- ✅ K-factor decay diselaraskan dengan Vesin: threshold `{30→20→15→10}` berdasarkan `total_attempts` `{<10, 10–24, 25–49, ≥50}`
- ✅ Success rate formula diperlengkap dengan parameter multi-attempt dan time factor (Vesin eq. 3)
- ✅ Konvergensi rating dibuktikan: 7–10 soal (sesuai temuan empiris Vesin)
- ✅ Tabel `assessment_sessions` ditambahkan (session management untuk Individual Mode)
- ✅ `init_sandbox.sql` konten lengkap didokumentasikan (schema, tabel, data dummy, role & grants)
- ✅ Logika NLP feedback scoring diperjelas dengan keyword list eksplisit
- ✅ `theta_social` update formula didefinisikan secara eksplisit (delta-based, bukan hard-replace)
- ✅ Route guard logic dan Zustand store structure ditambahkan ke Frontend Spec
- ✅ Status code dan request/response body lengkap untuk semua endpoint kritis
- ✅ Module unlock logic didefinisikan eksplisit (θ-threshold per modul)
- ✅ Peer session timeout handling (24h auto-expire)

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
├── client/                          # React Frontend (Vite)
│   ├── .env
│   ├── .env.example
│   ├── src/
│   │   ├── components/              # Reusable UI
│   │   │   ├── Editor/              # CodeMirror SQL editor
│   │   │   ├── RadarChart/          # Progress radar (3 modul)
│   │   │   └── ProtectedRoute.tsx   # JWT route guard
│   │   ├── pages/                   # Route-based pages
│   │   │   ├── Login.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Pretest.tsx
│   │   │   ├── Modules.tsx
│   │   │   ├── Session.tsx
│   │   │   ├── Collaboration/
│   │   │   └── Profile.tsx
│   │   ├── services/                # Axios API clients
│   │   │   ├── auth.ts
│   │   │   ├── pretest.ts
│   │   │   ├── session.ts
│   │   │   └── collaboration.ts
│   │   ├── routes/                  # React Router configuration
│   │   ├── store/                   # Zustand state management
│   │   │   ├── authStore.ts         # user, token, isAuthenticated
│   │   │   ├── sessionStore.ts      # active session state
│   │   │   └── pretestStore.ts      # pretest progress state
│   │   └── hooks/                   # Custom hooks (useSession, usePretest)
│   ├── package.json
│   └── vite.config.ts
├── server/                          # Python Backend (FastAPI)
│   ├── .env
│   ├── .env.example
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/                     # Database migrations
│   ├── app/
│   │   ├── main.py                  # App entry point
│   │   ├── api/                     # API Routers
│   │   │   ├── auth.py
│   │   │   ├── pretest.py
│   │   │   ├── modules.py
│   │   │   ├── session.py
│   │   │   ├── collaboration.py
│   │   │   └── profile.py
│   │   ├── core/                    # Business Logic & Configuration
│   │   │   ├── config.py            # Pydantic Settings
│   │   │   ├── dependencies.py      # FastAPI DI (get_db, get_current_user)
│   │   │   ├── elo_engine.py        # Elo update + stagnation detection
│   │   │   ├── peer_matching.py     # Cohen's d peer selection
│   │   │   └── logging_config.py    # Dual logging setup
│   │   ├── db/                      # Database layer
│   │   │   ├── base.py              # SQLAlchemy Base
│   │   │   ├── session.py           # Async engine + session factory
│   │   │   └── models.py            # ORM models
│   │   ├── schemas/                 # Pydantic models (request/response)
│   │   ├── sandbox/                 # Secure SQL execution
│   │   │   └── sandbox_executor.py
│   │   └── logs/                    # Log files (auto-generated)
│   └── db/
│       └── init_sandbox.sql         # Sandbox schema initialization
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
| | CodeMirror | 6.x | Lightweight SQL editor dengan syntax highlighting |
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
| `user_id` | UUID | PK, DEFAULT uuid_generate_v4() | Unique identifier |
| `nim` | VARCHAR(20) | UNIQUE, NOT NULL, INDEX | Student ID |
| `full_name` | VARCHAR(100) | NOT NULL | Display name |
| `password_hash` | VARCHAR | NOT NULL | Argon2id hashed password |
| `current_theta` | FLOAT | DEFAULT 1300.0, RANGE [500, 1500] | Elo rating individu (baseline = 1300, mengikuti Vesin et al. 2022) |
| `theta_social` | FLOAT | DEFAULT 0.0, RANGE [-1.0, +1.0] | Akumulasi delta kontribusi sosial |
| `k_factor` | INTEGER | DEFAULT 32 | Sensitivitas Elo (decay dengan attempts) |
| `has_completed_pretest` | BOOLEAN | DEFAULT FALSE | Flag mandatory cold-start |
| `total_attempts` | INTEGER | DEFAULT 0 | Total soal yang pernah dicoba (untuk K-factor decay) |
| `status` | VARCHAR(20) | DEFAULT 'ACTIVE' | `ACTIVE` \| `NEEDS_PEER_REVIEW` |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Account creation timestamp |

**Index:** `CREATE INDEX idx_users_nim ON users(nim);`

#### Table `modules`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `module_id` | VARCHAR(5) | PK | e.g. `'CH01'` |
| `title` | VARCHAR(255) | NOT NULL | Display name |
| `description` | TEXT | | Module overview |
| `difficulty_min` | FLOAT | NOT NULL | Lower bound D (e.g. 500.0) |
| `difficulty_max` | FLOAT | NOT NULL | Upper bound D (e.g. 800.0) |
| `unlock_theta_threshold` | FLOAT | NOT NULL | θ minimum user untuk unlock modul ini |
| `content_html` | TEXT | | HTML content materi pembelajaran |
| `order_index` | INTEGER | NOT NULL | Urutan tampil (1, 2, 3) |

**Catatan:** Field `is_locked` global dihapus di v3.1. Lock status sekarang per-user via `user_module_progress`.

**Data Seed:**

| module_id | title | difficulty_min | difficulty_max | unlock_theta_threshold | order_index |
|-----------|-------|----------------|----------------|------------------------|-------------|
| CH01 | Basic Selection | 500 | 800 | 0 (selalu terbuka) | 1 |
| CH02 | Aggregation | 800 | 1200 | 900 | 2 |
| CH03 | Advanced Querying | 1200 | 1500 | 1200 | 3 |

#### Table `user_module_progress`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `user_id` | UUID | PK, FK → `users` | Composite PK (per-user) |
| `module_id` | VARCHAR(5) | PK, FK → `modules` | Composite PK |
| `is_unlocked` | BOOLEAN | DEFAULT FALSE | Apakah modul sudah bisa diakses user ini |
| `is_completed` | BOOLEAN | DEFAULT FALSE | Apakah user sudah menyelesaikan modul |
| `started_at` | TIMESTAMP | NULLABLE | First access timestamp |
| `completed_at` | TIMESTAMP | NULLABLE | Completion timestamp |

**Logic unlock:** Saat user selesai pretest atau submit jawaban, backend mengecek apakah `user.current_theta >= module.unlock_theta_threshold` untuk setiap modul yang belum unlock. Jika ya, set `is_unlocked = TRUE`.

#### Table `questions`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `question_id` | VARCHAR(10) | PK | e.g. `'CH02-Q004'` |
| `module_id` | VARCHAR(5) | FK → `modules`, INDEX | |
| `content` | TEXT | NOT NULL | HTML/Markdown narasi soal |
| `target_query` | TEXT | NOT NULL | Canonical solution (kunci jawaban) |
| `initial_difficulty` | FLOAT | NOT NULL | Kesulitan awal yang di-seed manual oleh instruktur |
| `current_difficulty` | FLOAT | NOT NULL | Kesulitan dinamis (diupdate oleh Elo setiap ada submission) |
| `topic_tags` | TEXT[] | | e.g. `['GROUP BY', 'HAVING']` |
| `bloom_level` | VARCHAR(20) | | e.g. `'APPLY'`, `'ANALYZE'` (ACM CCECC 2023) |
| `is_active` | BOOLEAN | DEFAULT TRUE | FALSE jika soal di-retire |

**Index:** `CREATE INDEX idx_questions_module ON questions(module_id) WHERE is_active = TRUE;`

#### Table `assessment_sessions` *(NEW)*

Session container untuk Individual Mode. Satu session = satu kali user memulai latihan dari satu modul hingga selesai atau keluar.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `session_id` | UUID | PK, DEFAULT uuid_generate_v4() | |
| `user_id` | UUID | FK → `users`, INDEX | |
| `module_id` | VARCHAR(5) | FK → `modules` | |
| `question_ids_served` | TEXT[] | DEFAULT '{}' | List question_id yang sudah diberikan ke user di session ini |
| `status` | VARCHAR(20) | DEFAULT 'ACTIVE' | `ACTIVE` \| `COMPLETED` \| `ABANDONED` |
| `started_at` | TIMESTAMP | DEFAULT NOW() | |
| `ended_at` | TIMESTAMP | NULLABLE | |

**Constraint:** Hanya boleh ada satu session `ACTIVE` per user per waktu. Backend menolak `POST /session/start` jika masih ada session active.

#### Table `assessment_logs`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `log_id` | SERIAL | PK | |
| `session_id` | UUID | FK → `assessment_sessions`, INDEX | |
| `user_id` | UUID | FK → `users`, INDEX | |
| `question_id` | VARCHAR(10) | FK → `questions`, INDEX | |
| `user_query` | TEXT | NOT NULL | Query SQL yang disubmit user |
| `is_correct` | BOOLEAN | NOT NULL | Hasil perbandingan sandbox |
| `theta_before` | FLOAT | NOT NULL | θ user sebelum attempt ini |
| `theta_after` | FLOAT | NOT NULL | θ user setelah update |
| `difficulty_before` | FLOAT | NOT NULL | Difficulty soal sebelum update |
| `difficulty_after` | FLOAT | NOT NULL | Difficulty soal setelah update |
| `attempt_number` | INTEGER | NOT NULL | Ke-berapa kali user mencoba soal ini di session ini |
| `execution_time_ms` | INTEGER | | Waktu solve (ms), dihitung di frontend |
| `timestamp` | TIMESTAMP | DEFAULT NOW(), INDEX | |

**Catatan attempt_number:** Di prototipe ini, setiap soal hanya diberikan sekali per session (attempt_number selalu 1). Field ini disimpan untuk kompatibilitas dengan Vesin's multi-attempt formula di versi mendatang.

#### Table `pretest_sessions`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `session_id` | UUID | PK, DEFAULT uuid_generate_v4() | |
| `user_id` | UUID | FK → `users`, UNIQUE | Satu user hanya boleh punya satu pretest session |
| `current_question_index` | INTEGER | DEFAULT 0 | 0-based index soal berikutnya (0–4) |
| `total_questions` | INTEGER | DEFAULT 5 | Selalu 5 untuk prototipe |
| `answers` | JSONB | DEFAULT '{}' | Format: `{"CH01-Q003": true, "CH01-Q007": false, ...}` |
| `current_theta` | FLOAT | DEFAULT 1300.0 | Theta sementara selama pretest (rolling update) |
| `started_at` | TIMESTAMP | DEFAULT NOW() | |
| `completed_at` | TIMESTAMP | NULLABLE | Di-set saat `current_question_index == total_questions` |

**Logic pemilihan soal pretest:** Soal pretest diambil dari CH01 saja (domain yang paling basic) dan dipilih secara adaptive mengikuti section 6.1.

#### Table `peer_sessions`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `session_id` | UUID | PK, DEFAULT uuid_generate_v4() | |
| `requester_id` | UUID | FK → `users`, INDEX | User yang mengalami stagnasi |
| `reviewer_id` | UUID | FK → `users`, INDEX | Peer yang dipilih (heterogeneous) |
| `question_id` | VARCHAR(10) | FK → `questions`, INDEX | Soal konteks review |
| `requester_query` | TEXT | NOT NULL | Query terakhir yang disubmit requester (anonim untuk reviewer) |
| `review_content` | TEXT | NULLABLE | Feedback dari reviewer |
| `system_score` | FLOAT | NULLABLE, RANGE [0.0, 1.0] | NLP keyword matching score |
| `is_helpful` | BOOLEAN | NULLABLE | Binary rating dari requester |
| `final_score` | FLOAT | NULLABLE | `(0.5 × system_score) + (0.5 × CAST(is_helpful AS FLOAT))` |
| `status` | VARCHAR(30) | DEFAULT 'PENDING_REVIEW' | `PENDING_REVIEW` \| `WAITING_CONFIRMATION` \| `COMPLETED` \| `EXPIRED` |
| `created_at` | TIMESTAMP | DEFAULT NOW() | |
| `expires_at` | TIMESTAMP | DEFAULT NOW() + INTERVAL '24 hours' | Auto-expire jika tidak ada respons |
| `completed_at` | TIMESTAMP | NULLABLE | |

**Timeout handling:** Background task (APScheduler atau FastAPI lifespan) mengecek setiap jam, jika `NOW() > expires_at AND status != 'COMPLETED'` maka set `status = 'EXPIRED'` dan lepaskan `users.status = 'ACTIVE'` untuk kedua pihak.

---

### 3.2 Sandbox Schema (`sandbox`)

#### Struktur Tabel

Sandbox berisi data dummy akademis yang merefleksikan konteks akademik mahasiswa STEI-K ITB, untuk digunakan sebagai dataset latihan soal SQL.

**`sandbox.mahasiswa`**

| Column | Type | Description |
|--------|------|-------------|
| `nim` | VARCHAR(15) | PK |
| `nama` | VARCHAR(100) | |
| `jurusan` | VARCHAR(10) | e.g. `'IF'`, `'EL'`, `'MK'` |
| `angkatan` | INTEGER | e.g. 2021 |
| `ipk` | DECIMAL(3,2) | 0.00–4.00 |

**`sandbox.matakuliah`**

| Column | Type | Description |
|--------|------|-------------|
| `kode_mk` | VARCHAR(10) | PK |
| `nama_mk` | VARCHAR(100) | |
| `sks` | INTEGER | |
| `semester` | INTEGER | |

**`sandbox.dosen`**

| Column | Type | Description |
|--------|------|-------------|
| `nip` | VARCHAR(20) | PK |
| `nama` | VARCHAR(100) | |
| `bidang` | VARCHAR(50) | |

**`sandbox.frs`**

| Column | Type | Description |
|--------|------|-------------|
| `nim` | VARCHAR(15) | FK → mahasiswa, composite PK |
| `kode_mk` | VARCHAR(10) | FK → matakuliah, composite PK |
| `nip_dosen` | VARCHAR(20) | FK → dosen |
| `semester` | INTEGER | |
| `nilai` | CHAR(2) | `'A'`, `'AB'`, `'B'`, `'BC'`, `'C'`, `'D'`, `'E'` |

#### Init Script (`db/init_sandbox.sql`)

```sql
-- Buat extension jika belum ada
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Buat skema sandbox
CREATE SCHEMA IF NOT EXISTS sandbox;

-- Buat role sandbox_executor (jika belum ada)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'sandbox_executor') THEN
    CREATE ROLE sandbox_executor LOGIN PASSWORD 'sandbox_pass';
  END IF;
END
$$;

-- Cabut semua akses ke public dari sandbox_executor
REVOKE ALL ON SCHEMA public FROM sandbox_executor;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM sandbox_executor;

-- Berikan akses SELECT-only ke schema sandbox
GRANT USAGE ON SCHEMA sandbox TO sandbox_executor;
GRANT SELECT ON ALL TABLES IN SCHEMA sandbox TO sandbox_executor;
ALTER DEFAULT PRIVILEGES IN SCHEMA sandbox GRANT SELECT ON TABLES TO sandbox_executor;

-- Set search_path default untuk role ini
ALTER ROLE sandbox_executor SET search_path = sandbox;

-- Buat tabel sandbox
CREATE TABLE sandbox.mahasiswa (
    nim        VARCHAR(15)    PRIMARY KEY,
    nama       VARCHAR(100)   NOT NULL,
    jurusan    VARCHAR(10)    NOT NULL,
    angkatan   INTEGER        NOT NULL,
    ipk        DECIMAL(3,2)   CHECK (ipk BETWEEN 0.0 AND 4.0)
);

CREATE TABLE sandbox.matakuliah (
    kode_mk    VARCHAR(10)    PRIMARY KEY,
    nama_mk    VARCHAR(100)   NOT NULL,
    sks        INTEGER        NOT NULL,
    semester   INTEGER        NOT NULL
);

CREATE TABLE sandbox.dosen (
    nip        VARCHAR(20)    PRIMARY KEY,
    nama       VARCHAR(100)   NOT NULL,
    bidang     VARCHAR(50)
);

CREATE TABLE sandbox.frs (
    nim        VARCHAR(15)    REFERENCES sandbox.mahasiswa(nim),
    kode_mk    VARCHAR(10)    REFERENCES sandbox.matakuliah(kode_mk),
    nip_dosen  VARCHAR(20)    REFERENCES sandbox.dosen(nip),
    semester   INTEGER        NOT NULL,
    nilai      CHAR(2)        CHECK (nilai IN ('A','AB','B','BC','C','D','E')),
    PRIMARY KEY (nim, kode_mk)
);

-- Data dummy (30 mahasiswa, 10 matakuliah, 5 dosen)
INSERT INTO sandbox.dosen VALUES
('D001', 'Budi Santoso', 'Basis Data'),
('D002', 'Siti Rahayu', 'Algoritma'),
('D003', 'Ahmad Fauzi', 'Jaringan Komputer'),
('D004', 'Dewi Lestari', 'Rekayasa Perangkat Lunak'),
('D005', 'Riko Pratama', 'Kecerdasan Buatan');

INSERT INTO sandbox.matakuliah VALUES
('IF2240', 'Basis Data', 3, 4),
('IF2110', 'Algoritma dan Struktur Data', 4, 3),
('IF3110', 'Pengembangan Aplikasi Berbasis Web', 3, 5),
('IF3140', 'Manajemen Basis Data', 3, 6),
('IF2230', 'Organisasi dan Arsitektur Komputer', 3, 4),
('IF3170', 'Kecerdasan Buatan', 3, 5),
('IF2150', 'Rekayasa Perangkat Lunak', 3, 4),
('IF3130', 'Jaringan Komputer', 3, 5),
('IF4073', 'Interaksi Manusia dan Komputer', 3, 6),
('IF4091', 'Tugas Akhir I', 3, 7);

INSERT INTO sandbox.mahasiswa VALUES
('18222001', 'Adi Nugroho',     'IF', 2022, 3.75),
('18222002', 'Bela Kusuma',     'IF', 2022, 2.90),
('18222003', 'Candra Wijaya',   'IF', 2022, 3.20),
('18222004', 'Diana Putri',     'IF', 2022, 3.85),
('18222005', 'Eka Saputra',     'IF', 2022, 2.45),
('18222006', 'Farhan Malik',    'IF', 2021, 3.60),
('18222007', 'Gita Ananda',     'IF', 2021, 3.10),
('18222008', 'Hendra Yusuf',    'IF', 2021, 2.75),
('18222009', 'Ira Salsabila',   'IF', 2021, 3.95),
('18222010', 'Joko Purnomo',    'IF', 2021, 3.30),
('18222011', 'Kartika Dewi',    'EL', 2022, 3.50),
('18222012', 'Lukman Hakim',    'EL', 2022, 2.60),
('18222013', 'Maya Sari',       'EL', 2022, 3.15),
('18222014', 'Naufal Rizki',    'MK', 2022, 3.70),
('18222015', 'Olivia Tanjung',  'MK', 2022, 3.40),
('18222016', 'Pandu Arifin',    'IF', 2020, 3.80),
('18222017', 'Qoriah Nisa',     'IF', 2020, 2.95),
('18222018', 'Rendi Firmansyah','IF', 2020, 3.25),
('18222019', 'Sari Oktaviani',  'IF', 2020, 3.65),
('18222020', 'Taufik Rahman',   'IF', 2020, 2.80),
('18222021', 'Umar Hamdani',    'IF', 2023, 3.10),
('18222022', 'Vina Melati',     'IF', 2023, 3.55),
('18222023', 'Wahyu Santoso',   'IF', 2023, 2.70),
('18222024', 'Xena Pratiwi',    'IF', 2023, 3.90),
('18222025', 'Yoga Wibisono',   'IF', 2023, 3.35),
('18222026', 'Zara Halimah',    'EL', 2021, 3.45),
('18222027', 'Aldi Firmandi',   'EL', 2021, 2.85),
('18222028', 'Bella Tristanti', 'MK', 2021, 3.20),
('18222029', 'Ciko Satria',     'MK', 2021, 3.75),
('18222030', 'Dinda Permata',   'IF', 2022, 3.00);

-- FRS data (sebagian, 3-5 mata kuliah per mahasiswa)
INSERT INTO sandbox.frs VALUES
('18222001', 'IF2240', 'D001', 4, 'A'),
('18222001', 'IF2110', 'D002', 3, 'AB'),
('18222001', 'IF3110', 'D004', 5, 'B'),
('18222002', 'IF2240', 'D001', 4, 'BC'),
('18222002', 'IF2110', 'D002', 3, 'B'),
('18222002', 'IF2230', 'D003', 4, 'C'),
('18222003', 'IF2240', 'D001', 4, 'B'),
('18222003', 'IF3140', 'D001', 6, 'AB'),
('18222004', 'IF2240', 'D001', 4, 'A'),
('18222004', 'IF3170', 'D005', 5, 'A'),
('18222005', 'IF2110', 'D002', 3, 'D'),
('18222005', 'IF2240', 'D001', 4, 'C'),
('18222006', 'IF3140', 'D001', 6, 'A'),
('18222006', 'IF3110', 'D004', 5, 'AB'),
('18222007', 'IF2240', 'D001', 4, 'B'),
('18222008', 'IF2240', 'D001', 4, 'BC'),
('18222009', 'IF3170', 'D005', 5, 'A'),
('18222009', 'IF2240', 'D001', 4, 'A'),
('18222010', 'IF2240', 'D001', 4, 'AB'),
('18222011', 'IF2240', 'D001', 4, 'B'),
('18222011', 'IF3130', 'D003', 5, 'AB'),
('18222012', 'IF2110', 'D002', 3, 'C'),
('18222013', 'IF3110', 'D004', 5, 'B'),
('18222014', 'IF2240', 'D001', 4, 'A'),
('18222015', 'IF3140', 'D001', 6, 'AB'),
('18222016', 'IF4091', 'D004', 7, 'A'),
('18222016', 'IF3140', 'D001', 6, 'A'),
('18222017', 'IF2240', 'D001', 4, 'BC'),
('18222018', 'IF3110', 'D004', 5, 'B'),
('18222019', 'IF4091', 'D004', 7, 'AB');
```

---

## 4. MATERIAL STRUCTURE (HIERARCHICAL DOMAIN)

| Module | Topic Focus | Difficulty Range (D) | Jumlah Soal | Description | Unlock Threshold |
|--------|-------------|---------------------|-------------|-------------|------------------|
| CH01 | Basic Selection | [500, 800] | 40 | `SELECT..WHERE`, logical operators, `ORDER BY`, `LIMIT` | Tidak ada (terbuka untuk semua) |
| CH02 | Aggregation | [800, 1200] | 40 | `GROUP BY..HAVING`, aggregate functions (`COUNT`, `SUM`, `AVG`, `MAX`, `MIN`) | θ ≥ 900 |
| CH03 | Advanced Querying | [1200, 1500] | 40 | CTE (`WITH`), Subquery, Multiple JOIN, window functions | θ ≥ 1200 |

**Bloom's Level Mapping (ACM CCECC 2023):**

| Module | Bloom's Level | Contoh Verb |
|--------|---------------|-------------|
| CH01 | Remember, Understand | Identify, Retrieve |
| CH02 | Apply, Analyze | Calculate, Distinguish |
| CH03 | Analyze, Evaluate | Construct, Critique |

**Note:** Setiap modul menyediakan 2.5× jumlah soal minimum per sesi (16 soal) → kombinasi 40C16 ≈ 4.8 juta. Risiko "bank soal habis" negligible untuk skala 10–20 user.

---

## 5. FRONTEND SPECIFICATION (ROUTING & UI)

### 5.1 React Router Configuration & Route Guards

```typescript
// routes/index.tsx — definisi route utama

const routes = [
  // Public routes (redirect ke dashboard jika sudah login)
  { path: "/login",    element: <AuthGuard><Login /></AuthGuard> },
  { path: "/register", element: <AuthGuard><Register /></AuthGuard> },

  // Protected routes (redirect ke login jika belum auth)
  {
    element: <ProtectedRoute />,
    children: [
      // Pretest gate: redirect ke /pretest jika belum selesai pretest
      { element: <PretestGate />, children: [
        { path: "/",                         element: <Dashboard /> },
        { path: "/modules",                  element: <Modules /> },
        { path: "/modules/:moduleId",        element: <ModuleDetail /> },
        { path: "/session/start",            element: <SessionStart /> },
        { path: "/session/:sessionId",       element: <SessionActive /> },
        { path: "/collaboration/inbox",      element: <CollabInbox /> },
        { path: "/collaboration/inbox/:id",  element: <ReviewTask /> },
        { path: "/collaboration/requests",   element: <MyRequests /> },
        { path: "/profile",                  element: <Profile /> },
        { path: "/profile/history",          element: <History /> },
      ]},
      // Pretest route (hanya accessible jika belum selesai pretest)
      { path: "/pretest", element: <Pretest /> },
    ]
  }
];

// ProtectedRoute: cek JWT valid. Jika tidak ada/expired → redirect /login
// PretestGate: cek user.has_completed_pretest. Jika false → redirect /pretest
// AuthGuard: jika sudah login → redirect /
```

### 5.2 Zustand Store Structure

```typescript
// store/authStore.ts
interface AuthStore {
  user: UserResponse | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (token: string, user: UserResponse) => void;
  logout: () => void;
  updateUser: (patch: Partial<UserResponse>) => void;
}

// store/pretestStore.ts
interface PretestStore {
  sessionId: string | null;
  currentQuestionIndex: number;
  totalQuestions: number;
  currentQuestion: PreTestQuestion | null;
  isCompleted: boolean;
  setSession: (session: PretestSession) => void;
  setCurrentQuestion: (q: PreTestQuestion) => void;
  markCompleted: () => void;
}

// store/sessionStore.ts
interface SessionStore {
  activeSession: AssessmentSession | null;
  currentQuestion: Question | null;
  startSession: (session: AssessmentSession) => void;
  setCurrentQuestion: (q: Question) => void;
  clearSession: () => void;
}
```

### 5.3 Navigation Flow & Menu Structure

```
DASHBOARD (Default Route: /)
├── Progress Radar (3 modul — CH01/CH02/CH03, nilai = persentase soal benar)
├── Elo Stats (θ individu + sosial, ditampilkan sebagai angka dan trend arrow)
├── Quick Resume → /session/start (jika ada session ACTIVE)
└── Navigation Menu:
    ├── Coursework → /modules
    ├── Collaborative → /collaboration/inbox
    └── Profile → /profile

COURSEWORK (/modules)
├── Module Tree (CH01/CH02/CH03)
│   ├── CH01: selalu unlocked
│   ├── CH02: locked jika θ < 900 (tampilkan lock icon + "Butuh θ ≥ 900")
│   └── CH03: locked jika θ < 1200
├── Module Detail (/modules/:moduleId)
│   ├── Content Tab (HTML materi pembelajaran)
│   ├── Practice Tab → /session/start?module=CH01
│   └── Status Badge (Locked / In Progress / Completed)
└── Start Session → /session/:sessionId

COLLABORATIVE SPACE
├── Peer Review Inbox (/collaboration/inbox)
│   └── List of pending review tasks (badge count)
│       └── Click Task → /collaboration/review/:sessionId
├── Review Task (/collaboration/review/:sessionId)
│   ├── Narasi soal (konteks)
│   ├── Query peer (anonim — tidak ada nama/NIM)
│   ├── Feedback Form (textarea + rubrik hint)
│   └── Submit Button (disabled jika < 15 karakter)
└── My Requests (/collaboration/requests)
    ├── Status badge (PENDING / WAITING / COMPLETED / EXPIRED)
    ├── Feedback diterima (jika WAITING_CONFIRMATION)
    └── Thumbs Up / Thumbs Down (hanya jika status WAITING_CONFIRMATION)

PROFILE (/profile)
├── User Info (nama, NIM)
├── θ Individu (Elo rating + label: Beginner/Intermediate/Advanced)
├── θ Sosial (akumulasi delta kontribusi peer review)
├── History Log → /profile/history (tabel assessment_logs)
└── Settings (Dark/Light mode, Editor font size)
```

### 5.4 Environment Variables (Frontend)

| Variable | Description | Required |
|----------|-------------|----------|
| `VITE_API_BASE_URL` | Backend API endpoint | ✅ |
| `VITE_APP_NAME` | Application display name | ✅ |
| `VITE_VERSION` | Frontend version | ✅ |

---

## 6. ALGORITHMIC LOGIC (BACKEND CORE)

### 6.1 Pre-Test Flow (Mandatory Cold-Start Calibration)

**Rationale:** Menghindari cold-start bias dengan kalibrasi awal berbasis 5 soal adaptif sebelum akses platform utama. Baseline 1300 mengikuti Vesin et al. (2022) yang membuktikan konvergensi dalam 7–10 attempt.

**Pemilihan Soal Pretest (Adaptive):**

```python
FUNCTION select_pretest_question(current_theta, answered_question_ids):
    # Soal pretest diambil dari CH01 saja
    FILTER questions WHERE module_id = 'CH01'
    FILTER questions WHERE question_id NOT IN answered_question_ids
    FILTER questions WHERE is_active = TRUE
    
    # Pilih soal terdekat dengan theta saat ini
    FOR EACH question:
        distance = ABS(question.current_difficulty - current_theta)
    SELECT TOP 5 WITH smallest distance
    RANDOMLY PICK 1 from TOP 5
    
    RETURN selected_question
END FUNCTION
```

**Rolling Theta Update Selama Pretest:**

Theta diupdate setelah setiap soal pretest menggunakan formula Elo standard (section 6.2), dengan K-factor tetap = 32 selama pretest. Hasil akhir setelah soal ke-5 ditentukan oleh formula:

```python
FUNCTION calculate_initial_theta(correct_count, total_questions=5):
    base_rating   = 1300.0   # Baseline Vesin et al. 2022
    baseline_correct = 2.5   # Expected correct untuk θ = 1300
    multiplier    = 120.0    # Span: (5 - 2.5) * 120 = 300 point max adjustment

    adjustment = (correct_count - baseline_correct) * multiplier
    theta      = base_rating + adjustment

    RETURN CLAMP(theta, 700, 1500)
END FUNCTION
```

**Calibration Table:**

| Correct | Theta Awal | Interpretasi |
|---------|------------|--------------|
| 0/5 | 700 | Sangat di bawah rata-rata |
| 1/5 | 820 | Di bawah rata-rata |
| 2/5 | 940 | Sedikit di bawah rata-rata |
| 3/5 | 1060 | Sedikit di atas rata-rata |
| 4/5 | 1180 | Di atas rata-rata |
| 5/5 | 1300 | Baseline penuh (5/5 = kembali ke 1300) |

**Catatan:** Theta final pretest disimpan ke `users.current_theta`. `pretest_sessions.completed_at` di-set saat index mencapai 5. `users.has_completed_pretest` di-set TRUE.

---

### 6.2 Adaptive Engine (Individual Mode)

#### Item Selection Strategy

Mengikuti ProTuS (Vesin et al. 2022): rekomendasikan top-5 soal terdekat dengan theta user, pilih satu secara random untuk menghindari determinisme.

```python
FUNCTION select_next_question(user_theta, module_id, served_question_ids):
    # served_question_ids: semua soal yang sudah diberikan di session ini
    FILTER questions WHERE module_id = module_id
    FILTER questions WHERE question_id NOT IN served_question_ids
    FILTER questions WHERE is_active = TRUE
    
    IF no questions available:
        RETURN None  # Trigger session end (bank soal habis untuk user ini)
    
    FOR EACH question:
        distance = ABS(question.current_difficulty - user_theta)
    SELECT TOP 5 WITH smallest distance
    RANDOMLY PICK 1 from TOP 5
    
    RETURN selected_question
END FUNCTION
```

#### Elo Update Formula (Vesin et al. 2022, Eq. 1–4)

```python
FUNCTION calculate_expected_score(theta, difficulty):
    # Persamaan 4 (Vesin et al. 2022)
    # Probabilitas bahwa student dengan rating theta berhasil mengerjakan soal
    # dengan difficulty level = difficulty
    RETURN 1 / (1 + 10 ^ ((difficulty - theta) / 400))
END FUNCTION

FUNCTION update_elo_ratings(student_theta, question_difficulty, success_rate, k_factor):
    expected = calculate_expected_score(student_theta, question_difficulty)

    # Persamaan 1: update rating student
    new_theta = student_theta + k_factor * (success_rate - expected)

    # Persamaan 2: update difficulty soal (zero-sum: soal naik jika student kalah)
    new_difficulty = question_difficulty + k_factor * (expected - success_rate)

    # Clamp ke valid range
    new_theta      = CLAMP(new_theta, 500, 1500)
    new_difficulty = CLAMP(new_difficulty, 500, 1500)

    RETURN new_theta, new_difficulty
END FUNCTION
```

#### Success Rate Calculation (Vesin et al. 2022, Eq. 3 — Simplified for Prototype)

Formula asli Vesin mempertimbangkan: (a) rasio successful/overall attempts, (b) rasio unit test yang lulus, (c) time factor. Di prototipe ini, karena setiap soal hanya satu attempt dan grading berbasis sandbox (binary pass/fail), formula disederhanakan:

```python
FUNCTION calculate_success_rate(is_correct, execution_time_ms, time_limit_ms=300000):
    IF NOT is_correct:
        RETURN 0.0   # Gagal = success_rate = 0

    # Base success = 1.0 (binary correct/incorrect untuk prototipe)
    base_success = 1.0

    # Time bonus: semakin cepat, sedikit bonus (simplified dari Vesin eq. 3)
    # Normalisasi: sisa waktu / time_limit → [0, 1]
    # Bonus maksimum = 0.5 (untuk time_limit - actual ≈ time_limit, i.e., sangat cepat)
    time_ratio   = (time_limit_ms - execution_time_ms) / time_limit_ms
    time_bonus   = CLAMP(time_ratio * 0.5, 0.0, 0.5)

    # Total success rate range: [1.0, 1.5]
    # Nilai > 1.0 memberikan Elo gain lebih besar (reward speed)
    RETURN CLAMP(base_success + time_bonus, 1.0, 1.5)
END FUNCTION
```

**Catatan implementasi:** `execution_time_ms` dikirimkan oleh frontend (diukur dari saat soal ditampilkan hingga user klik Submit). Jika frontend tidak mengirimkannya, backend menggunakan `time_bonus = 0`.

#### K-Factor Adaptation (Vesin et al. 2022 — Piecewise Decay)

Vesin menggunakan K ∈ `{30, 20, 15, 10}`. Equilibria mengadaptasi dengan threshold yang disesuaikan untuk skala prototype (10–20 user, lebih sedikit attempt):

```python
FUNCTION get_k_factor(total_attempts):
    # Threshold berdasarkan total_attempts (field di tabel users)
    IF total_attempts < 10:
        RETURN 32   # High sensitivity: fase cold-start, konvergensi cepat
    ELSE IF total_attempts < 25:
        RETURN 24   # Medium: transisi ke stable zone
    ELSE IF total_attempts < 50:
        RETURN 16   # Low: mendekati konvergensi
    ELSE:
        RETURN 10   # Minimal: rating sudah stabil, hindari overfitting
END FUNCTION
```

**Justifikasi:** Vesin et al. (2022) secara empiris membuktikan bahwa rating akurat tercapai setelah 7–10 attempt. Threshold `<10` dengan K=32 memastikan konvergensi cepat di fase awal; K=10 di fase akhir menghindari fluktuasi berlebihan.

#### K-Factor Update Flow

```python
# Dipanggil setelah setiap successful submission di assessment_logs
FUNCTION update_k_factor(user):
    user.total_attempts += 1
    user.k_factor = get_k_factor(user.total_attempts)
    SAVE user
END FUNCTION
```

---

### 6.3 Stagnation Detection (ε = 0.05)

Stagnation detection dipanggil setelah setiap update Elo di Individual Mode. Window: **5 attempt terakhir** di session yang sama.

```python
FUNCTION detect_stagnation(user_id, current_session_id):
    # Ambil 5 log terakhir user di session aktif
    last_5_logs = QUERY assessment_logs
        WHERE user_id = user_id
        AND session_id = current_session_id
        ORDER BY timestamp DESC
        LIMIT 5

    IF COUNT(last_5_logs) < 5:
        RETURN FALSE   # Belum cukup data

    # Hitung Δθ untuk setiap log
    deltas = [log.theta_after - log.theta_before FOR log IN last_5_logs]

    # Hitung variance Δθ menggunakan NumPy
    variance = numpy.var(deltas)   # Population variance

    IF variance < 0.05:   # ε = 0.05 (empirically calibrated, see Section 13.1)
        RETURN TRUE   # Stagnation detected → trigger collaborative mode
    ELSE:
        RETURN FALSE
END FUNCTION
```

**Post-stagnation action:**

```python
IF detect_stagnation(user_id, session_id):
    SET user.status = 'NEEDS_PEER_REVIEW'
    peer = find_heterogeneous_peer(user)
    IF peer IS NOT None:
        CREATE peer_session(requester=user, reviewer=peer, ...)
        RETURN response dengan flag stagnation_triggered = TRUE
    ELSE:
        # Tidak ada peer tersedia → lanjut individual mode
        RETURN response dengan flag stagnation_triggered = FALSE, message = "No peer available"
```

---

### 6.4 Constraint-Based Re-ranking (Heterogeneity Enforcement)

Mengikuti Biasio et al. (2023): constraint-based re-ranking untuk menghindari overpersonalization, dengan ukuran effect minimum Cohen's d ≥ 0.5.

```python
FUNCTION find_heterogeneous_peer(requester):
    # Hitung standar deviasi populasi dari semua active users
    all_thetas = QUERY SELECT current_theta FROM users WHERE status != 'NEEDS_PEER_REVIEW'
    population_std = numpy.std(all_thetas)

    IF population_std == 0:
        population_std = 100.0   # Fallback jika semua user punya theta sama (edge case)

    min_difference = 0.5 * population_std   # Cohen's d = 0.5 threshold

    # Kandidat reviewer: user aktif, bukan diri sendiri, bukan yang sedang butuh review
    candidates = QUERY users WHERE:
        user_id   != requester.user_id
        status    != 'NEEDS_PEER_REVIEW'
        ABS(current_theta - requester.current_theta) >= min_difference

    IF COUNT(candidates) == 0:
        RETURN None   # Tidak ada peer yang memenuhi syarat heterogenitas

    # Pilih secara random dari top-5 kandidat yang paling heterogen
    ORDER BY ABS(current_theta - requester.current_theta) DESCENDING
    LIMIT 5
    RETURN RANDOM_SELECT(candidates)
END FUNCTION
```

---

### 6.5 NLP Feedback Quality Scoring

Feedback reviewer di-score secara otomatis oleh sistem menggunakan keyword matching. Score ini menjadi komponen `system_score` di `peer_sessions`.

```python
# Keyword lists (Indonesia & English mixed untuk fleksibilitas)
CONSTRUCTIVE_KEYWORDS = [
    # Saran perbaikan
    'seharusnya', 'coba', 'gunakan', 'ubah', 'perbaiki', 'tambahkan',
    'should', 'try', 'use', 'change', 'fix', 'add', 'consider',
    # Penjelasan alternatif
    'alternatif', 'cara lain', 'bisa juga', 'alternatively', 'instead',
]

IDENTIFICATION_KEYWORDS = [
    # Identifikasi masalah spesifik SQL
    'join', 'group by', 'having', 'where', 'select', 'aggregate',
    'subquery', 'alias', 'null', 'distinct', 'order by', 'filter',
    # Terminologi error
    'error', 'salah', 'kurang', 'hilang', 'missing', 'incorrect', 'wrong',
    # Analisis logika
    'karena', 'karena itu', 'sebab', 'because', 'since', 'therefore',
]

FUNCTION calculate_system_score(feedback_text):
    IF feedback_text IS NULL OR LENGTH(TRIM(feedback_text)) < 15:
        RETURN 0.1   # Too short — tidak memberikan feedback yang bermakna

    text = LOWERCASE(feedback_text)

    has_constructive  = ANY(keyword IN text FOR keyword IN CONSTRUCTIVE_KEYWORDS)
    has_identification = ANY(keyword IN text FOR keyword IN IDENTIFICATION_KEYWORDS)

    IF has_constructive AND has_identification:
        RETURN 0.9   # Excellent: ada saran konkret + identifikasi masalah
    ELSE IF has_constructive OR has_identification:
        RETURN 0.6   # Good: salah satu aspek terpenuhi
    ELSE:
        RETURN 0.3   # Poor: purely affective ("bagus", "kurang tepat" tanpa penjelasan)
END FUNCTION
```

---

### 6.6 Theta Social Update (Delta-Based)

`theta_social` bukan merupakan Elo rating. Ini adalah akumulasi kontribusi sosial user dalam sistem. Diupdate ketika requester memberikan rating (thumbs up/down) pada feedback yang diterima.

```python
FUNCTION update_theta_social(reviewer_user, is_helpful):
    # Delta dihitung dari final_score peer session
    # final_score = (0.5 × system_score) + (0.5 × CAST(is_helpful AS FLOAT))
    # is_helpful: TRUE=1.0, FALSE=0.0
    final_score = (0.5 * peer_session.system_score) + (0.5 * (1.0 IF is_helpful ELSE 0.0))

    # Delta sosial: positif jika helpful, negatif jika tidak
    # Scale: [-0.5, +0.5] per interaksi
    delta_social = (final_score - 0.5)   # Centered around 0

    # Akumulasi dengan decay factor untuk mencegah saturation
    # Alpha = 0.1: kontribusi satu interaksi maksimum ±0.05
    alpha = 0.1
    reviewer_user.theta_social = CLAMP(
        reviewer_user.theta_social + (alpha * delta_social),
        -1.0,
        +1.0
    )

    SAVE reviewer_user
    UPDATE peer_session SET final_score = final_score, status = 'COMPLETED', completed_at = NOW()
END FUNCTION
```

**Catatan:** `theta_social` ditampilkan di UI sebagai indikator kontribusi sosial, bukan sebagai input langsung ke item selection atau Elo calculation. Logging komprehensif memungkinkan eksplorasi integrasi bobot 50-50 pasca-hoc.

---

### 6.7 Module Unlock Check

Dipanggil setelah setiap update theta (pretest completion dan individual mode submission):

```python
FUNCTION check_and_unlock_modules(user):
    all_modules = QUERY modules ORDER BY order_index
    FOR EACH module IN all_modules:
        progress = GET user_module_progress WHERE user_id = user.user_id AND module_id = module.module_id
        IF progress IS NULL:
            CREATE user_module_progress(user_id, module_id, is_unlocked=FALSE)
            progress = newly created record

        IF NOT progress.is_unlocked AND user.current_theta >= module.unlock_theta_threshold:
            SET progress.is_unlocked = TRUE
            SAVE progress
END FUNCTION
```

---

## 7. BACKEND API SPECIFICATION

### 7.1 Authentication & Authorization

**JWT Flow:**
1. `POST /api/v1/auth/login` → `{nim, password}` → JWT token (access: 30 menit, refresh: 7 hari)
2. Setiap request selanjutnya setelah mendapatkan JWT Token harus menyertakan: `Authorization: Bearer <token>`
3. FastAPI dependency `get_current_user()` digunakan di semua protected endpoint → validate JWT → return `UserResponse`

### 7.2 Response Convention (JSend)

Semua endpoint API harus mengembalikan format `JSendResponse[T]`:

```python
class JSendResponse[T](BaseModel, Generic[T]):
    status:  Literal["success", "fail", "error"]
    code:    int                    # HTTP status code
    data:    Optional[T] = None     # Payload (None jika error)
    message: Optional[str] = None   # Error/info message
```

| `status` | HTTP Range | Kapan digunakan |
|----------|------------|-----------------|
| `success` | 2xx | Request berhasil, ada data |
| `fail` | 4xx | Validasi gagal, unauthorized, not found (kesalahan client) |
| `error` | 5xx | Server error, DB error (kesalahan server) |

**Contoh Success:**
```json
{
  "status": "success",
  "code": 200,
  "data": { "access_token": "eyJ...", "user": { "user_id": "uuid", "nim": "18222047", "current_theta": 1300 } },
  "message": "Login berhasil"
}
```

**Contoh Fail (400):**
```json
{
  "status": "fail",
  "code": 400,
  "data": null,
  "message": "Out of order submission: expected question_number=2, got 4"
}
```

---

### 7.3 Complete API Endpoints Reference

#### A. Authentication Endpoints

| Method | Endpoint | Input Body | Output | Status Codes |
|--------|----------|-----------|--------|--------------|
| POST | `/api/v1/auth/register` | `{nim, full_name, password}` | `JSend[LoginResponse]` | 201, 409 (NIM exists) |
| POST | `/api/v1/auth/login` | `{nim, password}` | `JSend[LoginResponse]` | 200, 401 |
| POST | `/api/v1/auth/logout` | — | `JSend` | 200 |
| GET | `/api/v1/auth/me` | — | `JSend[UserResponse]` | 200, 401 |
| PUT | `/api/v1/auth/me` | `{full_name?}` | `JSend[UserResponse]` | 200, 401 |

**`LoginResponse` schema:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "user_id": "uuid",
    "nim": "18222047",
    "full_name": "Dama",
    "current_theta": 1300.0,
    "theta_social": 0.0,
    "k_factor": 32,
    "has_completed_pretest": false,
    "total_attempts": 0,
    "status": "ACTIVE"
  }
}
```

---

#### B. Pre-Test Endpoints

| Method | Endpoint | Input Body | Output | Status Codes |
|--------|----------|-----------|--------|--------------|
| POST | `/api/v1/pretest/start` | — | `JSend[PretestSession]` | 201, 400 (sudah ada active session), 403 (sudah selesai pretest) |
| GET | `/api/v1/pretest/question/current` | — | `JSend[PretestQuestion]` | 200, 404 (tidak ada active session) |
| POST | `/api/v1/pretest/submit` | `{question_id, question_number, user_query}` | `JSend[PretestSubmitResult]` | 200, 400 |

**`/api/v1/pretest/submit` validation rules:**
- `question_number` harus = `current_question_index + 1` dari session aktif. Jika tidak, tolak dengan 400 ("Out of order submission")
- `question_id` harus sesuai soal yang sedang aktif di session
- Jika `current_question_index` setelah submit = `total_questions` (5), set `completed_at` dan hitung `θ_initial`

**`PretestSubmitResult` schema:**
```json
{
  "is_correct": true,
  "theta_updated": 1360.0,
  "question_number": 3,
  "is_completed": false,
  "correct_count": 2
}
```

---

#### C. Content & Module Endpoints

| Method | Endpoint | Output | Status Codes |
|--------|----------|--------|--------------|
| GET | `/api/v1/modules` | `JSend[ModuleListItem[]]` | 200 |
| GET | `/api/v1/modules/{module_id}` | `JSend[ModuleDetail]` | 200, 404 |
| GET | `/api/v1/modules/{module_id}/content` | `JSend[ModuleContent]` | 200, 403 (locked), 404 |

**`ModuleListItem` schema:**
```json
{
  "module_id": "CH02",
  "title": "Aggregation",
  "difficulty_min": 800,
  "difficulty_max": 1200,
  "unlock_theta_threshold": 900,
  "is_unlocked": true,
  "is_completed": false,
  "order_index": 2
}
```

---

#### D. Assessment (Individual Mode) Endpoints

| Method | Endpoint | Input Body | Output | Status Codes |
|--------|----------|-----------|--------|--------------|
| POST | `/api/v1/session/start` | `{module_id}` | `JSend[SessionStartResult]` | 201, 400 (session aktif sudah ada), 403 (modul locked) |
| GET | `/api/v1/session/{session_id}` | — | `JSend[SessionStatus]` | 200, 404 |
| GET | `/api/v1/session/{session_id}/question` | — | `JSend[QuestionResponse]` | 200, 404 (soal habis → trigger session end) |
| POST | `/api/v1/session/{session_id}/submit` | `{question_id, user_query, execution_time_ms?}` | `JSend[SubmitResult]` | 200, 400 |
| POST | `/api/v1/session/{session_id}/end` | — | `JSend[SessionSummary]` | 200, 404 |

**`SubmitResult` schema:**
```json
{
  "is_correct": false,
  "theta_before": 1080.0,
  "theta_after": 1065.0,
  "question_difficulty_before": 950.0,
  "question_difficulty_after": 965.0,
  "stagnation_detected": false,
  "peer_session_created": false,
  "next_question_available": true
}
```

---

#### E. Collaborative Endpoints

| Method | Endpoint | Input Body | Output | Status Codes |
|--------|----------|-----------|--------|--------------|
| GET | `/api/v1/collaboration/inbox` | — | `JSend[PeerSessionInboxItem[]]` | 200 |
| GET | `/api/v1/collaboration/inbox/{session_id}` | — | `JSend[PeerSessionDetail]` | 200, 403, 404 |
| POST | `/api/v1/collaboration/inbox/{session_id}/submit` | `{review_content}` | `JSend[ReviewSubmitResult]` | 200, 400 (review terlalu pendek < 15 char), 404 |
| GET | `/api/v1/collaboration/requests` | — | `JSend[PeerSessionRequest[]]` | 200 |
| POST | `/api/v1/collaboration/requests/{session_id}/rate` | `{is_helpful: bool}` | `JSend[RateResult]` | 200, 400 (status bukan WAITING_CONFIRMATION), 403 |

**`PeerSessionDetail` schema (untuk reviewer):**
```json
{
  "session_id": "uuid",
  "question": { "content": "Tampilkan rata-rata IPK...", "topic_tags": ["AVG", "GROUP BY"] },
  "requester_query": "SELECT AVG(ipk) FROM mahasiswa",
  "status": "PENDING_REVIEW",
  "expires_at": "2026-03-14T07:00:00Z"
}
```

*Note: `requester_query` ditampilkan ke reviewer, tapi **tidak ada** nama/NIM requester (anonim).*

---

#### F. Profile & Statistics Endpoints

| Method | Endpoint | Input | Output | Status Codes |
|--------|----------|-------|--------|--------------|
| GET | `/api/v1/profile/stats` | — | `JSend[ProfileStats]` | 200 |
| GET | `/api/v1/profile/history` | `?limit=20&offset=0` | `JSend[AssessmentLogPage]` | 200 |
| GET | `/api/v1/profile/social` | — | `JSend[SocialStats]` | 200 |

**`ProfileStats` schema:**
```json
{
  "current_theta": 1150.0,
  "theta_social": 0.12,
  "total_attempts": 34,
  "k_factor": 16,
  "module_progress": [
    { "module_id": "CH01", "is_unlocked": true, "is_completed": true },
    { "module_id": "CH02", "is_unlocked": true, "is_completed": false },
    { "module_id": "CH03", "is_unlocked": false, "is_completed": false }
  ],
  "accuracy_rate": 0.68
}
```

---

## 8. LOGGING SPECIFICATION

### 8.1 Dual Logging System

| Log Type | Location | Format | Rotation | Retention |
|----------|----------|--------|----------|-----------|
| System Logs | `/app/logs/syslogs/` | JSON | 10MB per file | 5 backup files |
| Assessment Logs | `/app/logs/asslogs/` | JSON | 10MB per file | 5 backup files |
| Assessment DB | PostgreSQL `assessment_logs` | Structured | Persistent | Indefinite |

### 8.2 Log File Naming Convention

```
syslogs/syslog_YYYYMMDD_HHMMSS.json
asslogs/asslog_YYYYMMDD_HHMMSS.json
```

### 8.3 Log Level Configuration

| Level | Syslog | Asslog | Use Case |
|-------|--------|--------|----------|
| DEBUG | ❌ Optional | ❌ No | Development troubleshooting only |
| INFO | ✅ Yes | ✅ Yes | Normal operations (logins, submissions, peer matches) |
| WARNING | ✅ Yes | ✅ Yes | Near-stagnation (variance 0.05–0.10), slow queries |
| ERROR | ✅ Yes | ✅ Yes | DB errors, sandbox errors, auth failures |
| CRITICAL | ✅ Yes | ✅ Yes | Service down, data corruption |

**Default:** `INFO` (configurable via `LOG_LEVEL` environment variable)

### 8.4 Log Entry Format (Syslog)

```json
{
  "timestamp": "2026-03-13T14:13:58.187996Z",
  "level": "INFO",
  "logger": "equilibria.system",
  "message": "Login successful",
  "module": "auth",
  "function": "login",
  "line": 123,
  "user_id": "cb876914-b0a3-4b56-a59a-87c1bbde63bc",
  "event_type": "AUTH_LOGIN_SUCCESS"
}
```

### 8.5 Assessment Log Entry Format

```json
{
  "timestamp": "2026-03-13T14:13:58.187996Z",
  "level": "INFO",
  "logger": "equilibria.assessment",
  "message": "Assessment submit: CORRECT",
  "user_id": "cb876914-b0a3-4b56-a59a-87c1bbde63bc",
  "session_id": "uuid-session-123",
  "question_id": "CH02-Q004",
  "theta_before": 1080.0,
  "theta_after": 1112.5,
  "delta_theta": 32.5,
  "is_correct": true,
  "k_factor": 24,
  "execution_time_ms": 1200,
  "stagnation_checked": true,
  "stagnation_detected": false,
  "event_type": "ASSESSMENT_SUBMIT"
}
```

**Event types yang di-log:**

| event_type | Logger | Trigger |
|------------|--------|---------|
| `AUTH_LOGIN_SUCCESS` | system | Login berhasil |
| `AUTH_LOGIN_FAIL` | system | Login gagal (NIM/password salah) |
| `PRETEST_START` | assessment | User memulai pretest |
| `PRETEST_SUBMIT` | assessment | Setiap submit soal pretest |
| `PRETEST_COMPLETE` | assessment | Pretest selesai, θ_initial ditetapkan |
| `ASSESSMENT_SUBMIT` | assessment | Setiap submit soal di individual mode |
| `STAGNATION_DETECTED` | assessment | Stagnation terdeteksi |
| `PEER_MATCH_SUCCESS` | assessment | Peer reviewer berhasil ditemukan |
| `PEER_MATCH_FAIL` | assessment | Tidak ada peer tersedia |
| `PEER_REVIEW_SUBMITTED` | assessment | Reviewer submit feedback |
| `PEER_RATED` | assessment | Requester rate feedback |
| `SANDBOX_ERROR` | system | Query sandbox gagal (treated as incorrect) |
| `MODULE_UNLOCKED` | assessment | Module baru terbuka untuk user |

---

## 9. CONFIGURATION MANAGEMENT

### 9.1 Environment Variables (Backend)

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string (`postgresql+asyncpg://...`) | ✅ | — |
| `JWT_SECRET_KEY` | JWT signing key (minimum 32 char) | ✅ | — |
| `JWT_ALGORITHM` | JWT algorithm | ❌ | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | ❌ | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | ❌ | `7` |
| `LOG_LEVEL` | Logging verbosity | ❌ | `INFO` |
| `SANDBOX_DB_ROLE` | Nama role DB untuk sandbox | ✅ | — |
| `SANDBOX_QUERY_TIMEOUT_MS` | Timeout query sandbox (ms) | ❌ | `5000` |

### 9.2 Environment Variables (Frontend)

| Variable | Description | Required |
|----------|-------------|----------|
| `VITE_API_BASE_URL` | Backend API endpoint | ✅ |
| `VITE_APP_NAME` | Application display name | ✅ |
| `VITE_VERSION` | Frontend version | ✅ |

---

## 10. SECURITY & LIMITATIONS

### 10.1 Sandbox Security

| Feature | Status | Implementation |
|---------|--------|----------------|
| `SELECT`-only access | ✅ | Role `sandbox_executor` dengan GRANT SELECT only |
| No `public` schema access | ✅ | `REVOKE ALL ON SCHEMA public FROM sandbox_executor` |
| Query timeout | ✅ | `SET LOCAL statement_timeout = 5000` (sebelum query) |
| Dangerous keyword blocklist | ✅ | Case-insensitive check: `DROP`, `DELETE`, `INSERT`, `UPDATE`, `ALTER`, `CREATE`, `TRUNCATE`, `GRANT`, `REVOKE`, `PG_`, `--` |
| Dedicated engine isolation | ✅ | Engine terpisah dari main app session (tidak share connection pool) |
| Transaction isolation | ✅ | Sandbox error tidak abort main session (`SandboxExecutionError` → `is_correct = False`) |
| Schema routing | ✅ | `SET ROLE sandbox_executor` + `SET search_path = sandbox` (bukan `schema_translate_map`) |
| Container isolation | ⚠️ | Not implemented (prototype scale) |

**Execution flow sandbox (setelah fix v3.1):**

```python
async def execute_query_in_sandbox(query: str, timeout_ms: int = 5000) -> dict:
    clean_query = _validate_query(query)   # 1. Keyword blocklist check

    async with sandbox_engine.begin() as conn:
        await conn.execute(text(f"SET ROLE {SANDBOX_DB_ROLE}"))         # 2. Drop privileges
        await conn.execute(text("SET search_path = sandbox"))            # 3. Route ke schema sandbox
        await conn.execute(text(f"SET LOCAL statement_timeout = {timeout_ms}"))  # 4. Timeout SEBELUM query
        result = await conn.execute(text(clean_query))                   # 5. Execute user query
        RETURN result.mappings().all()
```

**Limitation:** Keamanan sandbox tidak menjadi fokus utama karena sistem diimplementasikan sebagai purwarupa terbatas (10–20 user) untuk validasi algoritma adaptif. Implementasi produksi memerlukan isolasi proses (Docker container per query) dan mekanisme timeout yang lebih ketat di OS level.

### 10.2 Edge Cases Handling

| Edge Case | Risk Level | Mitigation Strategy |
|-----------|------------|---------------------|
| Bank soal habis | Rendah | 40C16 ≈ 4.8 juta kombinasi → negligible untuk 10–20 user |
| Peer review deadlock | Sedang | Safeguard: hindari reviewer dengan `status = 'NEEDS_PEER_REVIEW'` |
| Tidak ada peer tersedia | Sedang | Lanjut individual mode, log `PEER_MATCH_FAIL`, UI memberi tahu user |
| Peer session timeout | Sedang | Auto-expire 24h via background task; set `status = 'EXPIRED'` |
| Cold-start (θ = 1300) | Rendah | Diatasi mandatory pretest → θ_initial yang lebih akurat |
| JWT token expiration | Rendah | Refresh token mechanism (7 hari) |
| Sandbox query error | Sedang | `SandboxExecutionError` → `is_correct = False`, main session tidak abort |
| Search path leakage | Rendah | Dedicated sandbox engine dengan `SET ROLE` (fixed v3.1) |
| Database connection pool exhausted | Sedang | `pool_size=10`, `max_overflow=20` |
| Log file disk space | Rendah | Auto-rotation at 10MB, 5 backup files |
| Session conflict (double start) | Rendah | Backend menolak `POST /session/start` jika sudah ada session `ACTIVE` |

### 10.3 Password Security

- **Algorithm:** Argon2id
- **Parameters:** `m=2^16, t=3, p=4` (RFC 9106)
- **Storage:** Hanya hash yang disimpan, tidak pernah plaintext
- **Transmission:** HTTPS only di production

### 10.4 JWT Security

- **Algorithm:** HS256 (HMAC with SHA-256)
- **Expiration:** 30 menit (access token), 7 hari (refresh token)
- **Storage:** `localStorage` di frontend (acceptable untuk prototipe), `HttpOnly cookie` di production
- **Validation:** Signature + expiration + user existence check di `get_current_user()`

---

## 11. DEPLOYMENT SPECIFICATION

### 11.1 Infrastructure Overview

| Service | Platform | Configuration |
|---------|----------|---------------|
| Frontend | Vercel | Hobby Tier (free), env vars via dashboard |
| Backend | Render/Railway | Free Tier, Docker deployment |
| Database | Supabase | Free Tier (500MB), atau Render PostgreSQL |
| Domain | Provider Subdomain | e.g., `equilibria.onrender.com` |

**Catatan:** Alternatif menggunakan Azure VM (credits mahasiswa ITB) tersedia untuk backend, tapi memerlukan setup manual lebih (IaaS vs PaaS). Akan menyesuaikan timeline.

### 11.2 Docker Configuration

Backend dan database dikontainerisasi via Docker Compose.

**Key Configuration:**
- Health check untuk memastikan PostgreSQL ready sebelum FastAPI start
- `init_sandbox.sql` di-mount ke `/docker-entrypoint-initdb.d/` (auto-run saat container DB pertama kali diinisialisasi)
- Env var di-inject via `.env` files
- Log directory di-mount sebagai volume untuk akses pasca-hoc

### 11.3 Deployment Pipeline

| Stage | Trigger | Approval |
|-------|---------|----------|
| Development | Local Docker Compose dengan hot reload | None |
| Staging | Auto-deploy on git push ke `staging` branch | None |
| Production | Manual trigger | Required |

---

## 12. TESTING & EVALUATION

### 12.1 Controlled Lab Study Design

- **Method:** One-Group Pretest-Posttest (Hake, 1999)
- **Participants:** 10–15 mahasiswa STEI-K ITB
- **Duration:** 90–120 menit per sesi
- **Location:** Controlled lab environment (komputer lab, koneksi internet stabil)

### 12.2 Testing Phases

| Phase | Duration | Activity |
|-------|----------|----------|
| Pre-test | 15 menit | Kalibrasi awal (5 soal adaptif → `θ_initial`) |
| System Interaction | 45 menit | Sesi latihan SQL adaptif individual |
| Social Intervention | 30 menit | Peer review (dipicu oleh stagnation detection) |
| Post-test | 15 menit | Asesmen akhir (5 soal dari bank soal reserved, tidak dipakai selama latihan) |

**Post-test design:** Soal post-test dipilih dari bank soal yang tidak pernah diberikan ke user selama sesi latihan (ditrack via `assessment_logs`). Soal dipilih secara adaptive berdasarkan `θ_final`.

### 12.3 Success Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| Normalized Learning Gain | `g = (post_score - pre_score) / (100 - pre_score)` | g ≥ 0.3 (Medium, Hake 1999) |
| Peer Feedback Quality | Rata-rata `system_score` dari semua `peer_sessions` | Score ≥ 0.6 |
| Matching Validity | % peer pairs dengan `|θ_reviewer - θ_requester| ≥ 0.5σ` | 100% compliance |
| Elo Convergence | Soal ke berapa theta mulai stabil (variance < 0.05 selama 5 attempt berturutan) | ≤ 10 attempt (Vesin 2022) |
| System Availability | Uptime selama testing | ≥ 99% |
| Response Time | API latency (p95) | ≤ 500ms |

### 12.4 Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Participant availability | Medium (3) | High (5) | Siapkan dummy accounts dengan varied Elo profiles untuk simulasi |
| Cold-start inaccuracy | Medium (3) | Medium (3) | Pre-test adaptive 5 soal sebagai R0 untuk konvergensi lebih cepat |
| Subjective rubric bias | Low (2) | Low (2) | NLP keyword scoring sebagai first-pass filter |
| Peer unavailability | Medium (3) | Medium (3) | Lanjut individual mode jika tidak ada peer valid, log untuk analisis |

---

## 13. APPENDIX: PARAMETER CALIBRATION LOG

### 13.1 ε Stagnation Threshold (Empirical Calibration)

| Simulation Pattern | Δθ Sequence | Variance | Decision |
|--------------------|-------------|----------|----------|
| Real stagnation (B-S-B-S-B) | [+2.1, -1.8, +2.3, -2.0, +1.9] | ~3.7 (scale 500–1500) → ~0.00015 (normalized) | Trigger |
| Normal fluctuation | [+30, -20, +25, -18, +22] | ~330 | No trigger |
| **Threshold selected** | — | **0.05 (normalized Δθ)** | **3× margin di atas stagnan nyata** |

**Justifikasi:** Nilai 0.05 memberikan margin ~3× di atas variansi stagnan nyata, sekaligus jauh di bawah fluktuasi normal. Sesuai dengan kriteria normalized learning gain rendah (<0.3) menurut Hake (1999). Threshold ini diukur dalam unit Δθ absolut pada skala 500–1500.

### 13.2 K-Factor Decay Rationale

| Total Attempts | K-Factor | Vesin Reference | Alasan |
|----------------|----------|-----------------|--------|
| < 10 | 32 | K=30 | Responsive: konvergensi cepat di fase cold-start |
| 10–24 | 24 | K=20 | Stabil: transisi menuju zona akurat |
| 25–49 | 16 | K=15 | Halus: rating sudah mulai reliable |
| ≥ 50 | 10 | K=10 | Minimal: hindari overfitting late-stage |

**Source:** Mengadopsi `{30, 20, 15, 10}` dari Vesin et al. (2022) dengan threshold yang disesuaikan untuk skala prototipe (10–20 user, rata-rata lebih sedikit attempt vs. 701 user Vesin).

**Konvergensi:** Vesin et al. (2022, Fig. 12) menunjukkan bahwa perubahan rating terbesar terjadi di 6–7 soal pertama; setelah soal ke-10, rating hanya bergeser sedikit. Oleh karena itu, `total_attempts < 10` dengan K=32 menjamin rating yang cukup representatif sejak dini.

### 13.3 Cohen's d Threshold

| Effect Size | d Value | Interpretasi |
|-------------|---------|--------------|
| Small | 0.2 | Detectable only with statistical analysis |
| **Medium** | **0.5** | **Visible to naked eye — dipilih untuk Equilibria** |
| Large | 0.8 | Sangat jelas perbedaannya |

**Source:** Cohen (1988). Nilai d=0.5 dipilih sebagai balance antara memastikan heterogenitas yang meaningful (di atas d=0.2 yang trivial) dan tidak terlalu restrictive sehingga tidak ada peer yang tersedia (d=0.8 terlalu ketat untuk populasi kecil 10–20 user).

### 13.4 Elo Scale & Initial Rating

| Parameter | Nilai | Justifikasi |
|-----------|-------|-------------|
| Rating minimum | 500 | Floor untuk mencegah negative rating |
| Rating baseline/awal | **1300** | Mengikuti Vesin et al. (2022) ProTuS initial rating |
| Rating maximum | 1500 | Ceiling untuk upper bound representasi |
| Rating range empiris | [1100, 1500] | Observasi Vesin setelah konvergensi (n=87 active users) |

**Pretest Calibration Table:**

| Benar | θ Awal | Interpretasi |
|-------|--------|--------------|
| 0/5 | 700 | Jauh di bawah rata-rata |
| 1/5 | 820 | Di bawah rata-rata |
| 2/5 | 940 | Sedikit di bawah rata-rata |
| 3/5 | 1060 | Sedikit di atas rata-rata |
| 4/5 | 1180 | Di atas rata-rata |
| 5/5 | 1300 | Excellent — kembali ke baseline (5/5 = kalibrasi tidak mengubah rating) |

**Formula:** `θ = CLAMP(1300 + (correct - 2.5) × 120, 700, 1500)`

### 13.5 Theta Social Scale

| Parameter | Nilai | Justifikasi |
|-----------|-------|-------------|
| Range | [-1.0, +1.0] | Bounded untuk mencegah dominasi sosial atas Elo individu |
| Alpha (learning rate) | 0.1 | Satu interaksi berkontribusi maksimum ±0.05 (5% dari range) |
| Neutral point | 0.0 | User baru tanpa riwayat sosial |

---

## 14. REFERENCES (TECHNICAL BASIS)

1. Vesin, B., Mangaroska, K., Akhuseyinoglu, K., & Giannakos, M. (2022). Adaptive Assessment and Content Recommendation in Online Programming Courses: On the Use of Elo-rating. *ACM Transactions on Computing Education*, 22(3), Article 33.
2. Kerman, N. T., et al. (2024). Online peer feedback patterns of success and failure in argumentative essay writing. *Interactive Learning Environments*.
3. ACM CCECC (2023). Bloom's for Computing: Enhancing Bloom's Revised Taxonomy with Verbs for Computing Disciplines.
4. Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences* (2nd ed.). Lawrence Erlbaum Associates.
5. Biasio, A. D., et al. (2023). On the problem of recommendation for sensitive users and influential items. *Knowledge-Based Systems*.
6. Hake, R. R. (1999). Analyzing change/gain scores. Woodbury, MN: AERA/NCME.
7. Minn, S. (2022). AI-assisted knowledge assessment techniques for adaptive learning environments. *Computers and Education: Artificial Intelligence*.
8. Brusilovsky, P., et al. (2016). Open Social Student Modeling for Personalized Learning. *IEEE Transactions on Emerging Topics in Computing*.

---

**Document Version:** 4.1  
**Last Updated:** March 13, 2026  
**Author:** Dama Dhananjaya Daliman (18222047)  
**Status:** Implementation Ready