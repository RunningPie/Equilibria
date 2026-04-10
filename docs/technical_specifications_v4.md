# TECHNICAL SPECIFICATION DOCUMENT: EQUILIBRIA

**Project:** Prototype of Collaborative Adaptive Assessment System with Overpersonalization Mitigation  
**Student:** Dama Dhananjaya Daliman (18222047)  
**Version:** 4.3 (Full Vesin Alignment + Social Elo + Multi-Attempt)  
**Date:** March 21, 2026

---

## 0. EXECUTIVE SUMMARY

Equilibria adalah purwarupa sistem asesmen adaptif berbasis Computerized Adaptive Testing (CAT) yang dirancang khusus untuk domain pendidikan Ilmu Komputer, dengan studi kasus pada materi SQL Querying. Sistem ini mengimplementasikan **Elo Rating System yang dimodifikasi** mengikuti secara langsung Vesin et al. (2022), dengan skala **[0, 2000]** dan baseline 1300, untuk kalibrasi dinamis tingkat kesulitan soal terhadap kemampuan siswa secara real-time.

Sebagai novelty, Equilibria memperkenalkan **Mekanisme Kolaboratif Mitigasi Overpersonalization** yang secara proaktif mendeteksi stagnasi kemampuan siswa melalui analisis variansi perubahan skor (`Δθ`), lalu memicu intervensi sosial (Peer Review) dengan constraint-based re-ranking berbasis Cohen's d ≥ 0.5 untuk memastikan heterogenitas pasangan. Kontribusi sosial dikuantifikasi melalui **Social Elo** — mekanisme Elo independen yang menilai kualitas reviewer terhadap standar netral (expected = 0.5), dan diintegrasikan ke dalam `theta_display` melalui weighted average `(0.8 × θ_individu) + (0.2 × θ_sosial)` untuk leaderboard.

Sistem dibangun dengan arsitektur Client-Server modern menggunakan **React.js (frontend)** dan **FastAPI (backend)**, dengan **PostgreSQL** sebagai basis data yang dipisahkan menjadi skema `public` (operasional) dan `sandbox` (eksekusi query aman).

**Perubahan dari v4.1:**
- ✅ Rating scale diubah ke **[0, 2000]** untuk theta_individu dan theta_social (dari [500, 1500])
- ✅ K-factor disamakan persis dengan Vesin: **{30, 20, 15, 10}** pada threshold `{<10, 10–24, 25–49, ≥50}`
- ✅ K_pretest dan K_social keduanya **= 30** (justified: lab study, attempts tidak akan melebihi 10)
- ✅ **Success rate formula Vesin Eq. 3 penuh** diimplementasikan — test ratio dimapping ke binary sandbox pass/fail (documented simplification)
- ✅ **Multi-attempt per soal** (maksimum 3): Elo diupdate saat user pindah soal, bukan per-submit
- ✅ **Social Elo** (reviewer-vs-standar, expected=0.5): theta_social berskala [0, 2000], starting 1300
- ✅ **theta_display** sebagai weighted average: `(0.8 × θ_ind) + (0.2 × θ_soc)`, dihitung on-the-fly
- ✅ **Leaderboard endpoint** ditambahkan
- ✅ Endpoint `POST /session/{id}/submit` dan `POST /session/{id}/next` dibedakan fungsinya
- ✅ `assessment_logs` ditambah kolom `is_final_attempt`
- ✅ `assessment_sessions` ditambah tracking soal aktif dan attempt count

---

## 1. SYSTEM ARCHITECTURE

### 1.1 High-Level Architecture

```
┌─────────────────┐      HTTP/HTTPS (JSON)      ┌──────────────────┐
│   FRONTEND      │ ◄─────────────────────────► │    BACKEND       │
│   (React SPA)   │                             │   (FastAPI)      │
└────────┬────────┘                             └────────┬─────────┘
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
┌───────────────┐  belum pretest?  ┌───────────────┐
│   DASHBOARD   │ ◄──────────────  │   PRE-TEST    │
└───────┬───────┘                  └───────┬───────┘
        │                                  │ (5 soal adaptive)
        ▼                                  ▼
┌───────────────┐                  ┌───────────────┐
│ SELECT MODULE │                  │  HITUNG       │
└───────┬───────┘                  │  θ_initial    │
        │                          └───────┬───────┘
        ▼                                  │
┌───────────────────────────────────────────┘
│
▼
┌──────────────────────┐
│  INDIVIDUAL MODE     │
│  (Adaptive Session)  │
└──────────┬───────────┘
           │
           ▼
    ┌─────────────────────────────────────┐
    │  Tampilkan soal                     │
    │  (max 3 attempt per soal)           │
    └──────────┬──────────────────────────┘
               │
               ▼
        ┌─────────────┐
        │   Submit    │ ← sandbox exec, log attempt
        └──────┬──────┘   (Elo belum diupdate)
               │
        ┌──────┴──────┐
        ▼             ▼
   ┌─────────┐   ┌──────────────────────┐
   │ Benar?  │   │ attempt < 3 && salah? │
   │ atau    │   │ → bisa retry         │
   │ attempt │   └──────────────────────┘
   │ ke-3?   │
   └────┬────┘
        │ Ya → klik Next (atau auto-next setelah attempt 3)
        ▼
    ┌──────────────┐
    │ Update θ     │ ← Elo dihitung dari semua attempt soal ini
    │ (Elo Engine) │   menggunakan Vesin Eq. 1-4
    └──────┬───────┘
           │
    ┌──────┴──────┐
    ▼             ▼
┌─────────┐  ┌──────────────┐
│ Next Q? │  │ Stagnation?  │
│ Yes → ◄─┘  │Var(Δθ₅) < ε? │
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
     │            │            │
     └──────┬─────┴────────────┘
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
    │ Update θ_social  │ ← Social Elo (reviewer-vs-standar)
    └────────┬─────────┘
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
│   │   ├── components/
│   │   │   ├── Editor/              # CodeMirror SQL editor
│   │   │   ├── RadarChart/          # Progress radar (3 modul)
│   │   │   └── ProtectedRoute.tsx   # JWT route guard
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Pretest.tsx
│   │   │   ├── Modules.tsx
│   │   │   ├── Session.tsx
│   │   │   ├── Leaderboard.tsx
│   │   │   ├── Collaboration/
│   │   │   └── Profile.tsx
│   │   ├── services/                # Axios API clients
│   │   │   ├── auth.ts
│   │   │   ├── pretest.ts
│   │   │   ├── session.ts
│   │   │   ├── leaderboard.ts
│   │   │   └── collaboration.ts
│   │   ├── routes/
│   │   ├── store/                   # Zustand state management
│   │   │   ├── authStore.ts
│   │   │   ├── sessionStore.ts
│   │   │   └── pretestStore.ts
│   │   └── hooks/
│   ├── package.json
│   └── vite.config.ts
├── server/                          # Python Backend (FastAPI)
│   ├── .env
│   ├── .env.example
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── pretest.py
│   │   │   ├── modules.py
│   │   │   ├── session.py
│   │   │   ├── collaboration.py
│   │   │   ├── leaderboard.py
│   │   │   └── profile.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── dependencies.py
│   │   │   ├── elo_engine.py        # Vesin Eq. 1-4 + Social Elo
│   │   │   ├── peer_matching.py
│   │   │   └── logging_config.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   └── models.py
│   │   ├── schemas/
│   │   ├── sandbox/
│   │   │   └── sandbox_executor.py
│   │   └── logs/
│   └── db/
│       └── init_sandbox.sql
├── docs/
│   └── pretest_calibration.md
└── README.md
```

---

## 2. TECHNOLOGY STACK

| Layer | Technology | Version | Rationale |
|-------|------------|---------|-----------|
| **Frontend** | React | 18.x | Fast HMR, component-based architecture |
| | Vite | 5.x | Fast build tool dengan native ESM |
| | React Router | 6.x | Declarative routing untuk SPA |
| | Tailwind CSS | 3.x | Utility-first styling |
| | CodeMirror | 6.x | SQL editor dengan syntax highlighting |
| | Zustand | 4.x | Minimalist state management |
| | Axios | 1.x | HTTP client |
| **Backend** | Python | 3.12 | Rich ecosystem untuk scientific computing |
| | FastAPI | 0.109.x | Async support, automatic OpenAPI docs |
| | SQLAlchemy | 2.0.x | Async ORM dengan connection pooling |
| | Alembic | 1.13.x | Database migration management |
| | Pydantic | 2.5.x | Data validation v2 syntax |
| | Pydantic Settings | 2.1.x | Environment-based configuration |
| | python-jose | 3.3.x | JWT encoding/decoding |
| | passlib | 1.7.x | Password hashing (Argon2id) |
| | asyncpg | 0.29.x | Fast PostgreSQL async driver |
| | NumPy | 1.26.x | Numerical computations (Elo, stagnation) |
| **Database** | PostgreSQL | 15.x | ACID compliance, MVCC |
| **Deployment** | Docker Compose | 3.8 | Isolated services (app, db) |
| | Vercel | Hobby Tier | Frontend hosting |
| | Render/Railway | Free Tier | Backend hosting |
| | Supabase | Free Tier | Managed PostgreSQL (alternatif) |

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
| `theta_individu` | FLOAT | DEFAULT 1300.0, RANGE [0, 2000] | Elo rating kemampuan SQL individual |
| `theta_social` | FLOAT | DEFAULT 1300.0, RANGE [0, 2000] | Elo rating kontribusi sosial (reviewer quality) |
| `k_factor` | INTEGER | DEFAULT 30 | K-factor individu saat ini (decay seiring attempts) |
| `has_completed_pretest` | BOOLEAN | DEFAULT FALSE | Flag mandatory cold-start |
| `total_attempts` | INTEGER | DEFAULT 0 | Total soal final yang sudah dikerjakan (untuk K-factor decay) |
| `status` | VARCHAR(20) | DEFAULT 'ACTIVE' | `ACTIVE` \| `NEEDS_PEER_REVIEW` |
| `group_assignment` | VARCHAR(1) | NOT NULL | Assignment grup ablation study: `'A'` (with intervention) atau `'B'` (without intervention). Di-set manual oleh instruktur sebelum lab study. |
| `stagnation_ever_detected` | BOOLEAN | DEFAULT FALSE | Flag apakah user pernah mengalami stagnation terdeteksi (untuk analisis cepat tanpa mining logs). |
| `created_at` | TIMESTAMP | DEFAULT NOW() | |

**Catatan `total_attempts`:** Hanya diincrement saat `is_final_attempt = TRUE` di `assessment_logs` — bukan per-submit.

**`theta_display` (computed, tidak disimpan):**
```
theta_display = (0.8 × theta_individu) + (0.2 × theta_social)
```
Dihitung on-the-fly di endpoint profile stats dan leaderboard.

**Index:** `CREATE INDEX idx_users_nim ON users(nim);`

---

#### Table `modules`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `module_id` | VARCHAR(5) | PK | e.g. `'CH01'` |
| `title` | VARCHAR(255) | NOT NULL | Display name |
| `description` | TEXT | | Module overview |
| `difficulty_min` | FLOAT | NOT NULL | Lower bound D |
| `difficulty_max` | FLOAT | NOT NULL | Upper bound D |
| `unlock_theta_threshold` | FLOAT | NOT NULL | theta_individu minimum untuk unlock |
| `content_html` | TEXT | | HTML materi pembelajaran |
| `order_index` | INTEGER | NOT NULL | Urutan tampil (1, 2, 3) |

**Data Seed:**

| module_id | title | difficulty_min | difficulty_max | unlock_theta_threshold | order_index |
|-----------|-------|----------------|----------------|------------------------|-------------|
| CH01 | Basic Selection | 1000 | 1400 | 0 (selalu terbuka) | 1 |
| CH02 | Aggregation | 1200 | 1600 | 1300 | 2 |
| CH03 | Advanced Querying | 1400 | 1800 | 1600 | 3 |

---

#### Table `user_module_progress`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `user_id` | UUID | PK, FK → `users` | |
| `module_id` | VARCHAR(5) | PK, FK → `modules` | |
| `is_unlocked` | BOOLEAN | DEFAULT FALSE | |
| `is_completed` | BOOLEAN | DEFAULT FALSE | |
| `started_at` | TIMESTAMP | NULLABLE | |
| `completed_at` | TIMESTAMP | NULLABLE | |

---

#### Table `questions`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `question_id` | VARCHAR(10) | PK | e.g. `'CH02-Q004'` |
| `module_id` | VARCHAR(5) | FK → `modules`, INDEX | |
| `content` | TEXT | NOT NULL | HTML/Markdown narasi soal |
| `target_query` | TEXT | NOT NULL | Canonical solution |
| `initial_difficulty` | FLOAT | NOT NULL | Di-seed manual oleh instruktur |
| `current_difficulty` | FLOAT | NOT NULL | Diupdate dinamis oleh Elo setiap ada final attempt |
| `topic_tags` | TEXT[] | | e.g. `['GROUP BY', 'HAVING']` |
| `bloom_level` | VARCHAR(20) | | e.g. `'APPLY'`, `'ANALYZE'` |
| `is_active` | BOOLEAN | DEFAULT TRUE | |

**Index:** `CREATE INDEX idx_questions_module ON questions(module_id) WHERE is_active = TRUE;`

---

#### Table `assessment_sessions`

Session container untuk Individual Mode. Satu session = satu kali user memulai latihan dari satu modul.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `session_id` | UUID | PK, DEFAULT uuid_generate_v4() | |
| `user_id` | UUID | FK → `users`, INDEX | |
| `module_id` | VARCHAR(5) | FK → `modules` | |
| `question_ids_served` | TEXT[] | DEFAULT '{}' | Question IDs yang sudah di-*final* di session ini |
| `current_question_id` | VARCHAR(10) | NULLABLE, FK → `questions` | Soal yang sedang aktif dikerjakan |
| `current_question_attempt_count` | INTEGER | DEFAULT 0 | Sudah berapa kali attempt di soal aktif ini |
| `status` | VARCHAR(20) | DEFAULT 'ACTIVE' | `ACTIVE` \| `COMPLETED` \| `ABANDONED` |
| `started_at` | TIMESTAMP | DEFAULT NOW() | |
| `ended_at` | TIMESTAMP | NULLABLE | |

**Constraint:** Hanya boleh ada satu session `ACTIVE` per user per waktu.

**Session lifecycle:**
- `ACTIVE` → `COMPLETED`: bank soal habis (semua soal di modul sudah served) atau user klik End Session secara manual
- `ACTIVE` → `ABANDONED`: user konfirmasi terminasi saat akan mulai session baru, atau auto-abandon setelah 24 jam dari `started_at`
- Session yang `ABANDONED` atau `COMPLETED` tidak bisa di-resume — user harus mulai session baru di modul yang sama

**Auto-abandon background task** (dijalankan periodik setiap jam):
```sql
UPDATE assessment_sessions
SET status = 'ABANDONED', ended_at = NOW()
WHERE status = 'ACTIVE'
  AND started_at < NOW() - INTERVAL '24 hours';
```

**`question_ids_served` vs `current_question_id`:**
- `current_question_id` = soal yang sedang dikerjakan, belum final (masih bisa retry)
- `question_ids_served` = soal-soal yang sudah di-finalize (user sudah klik Next atau habis 3 attempt). Dipakai untuk filter soal berikutnya agar tidak ada soal yang diulang.

---

#### Table `assessment_logs`

Menyimpan **semua** attempt (intermediate dan final) untuk keperluan analisis.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `log_id` | SERIAL | PK | |
| `session_id` | UUID | FK → `assessment_sessions`, INDEX | |
| `user_id` | UUID | FK → `users`, INDEX | |
| `question_id` | VARCHAR(10) | FK → `questions`, INDEX | |
| `user_query` | TEXT | NOT NULL | Query SQL yang disubmit |
| `is_correct` | BOOLEAN | NOT NULL | Hasil sandbox (binary) |
| `is_final_attempt` | BOOLEAN | NOT NULL, DEFAULT FALSE | TRUE jika ini attempt terakhir di soal ini (user klik Next atau attempt ke-3) |
| `attempt_number` | INTEGER | NOT NULL | Urutan attempt di soal ini dalam session ini (1, 2, atau 3) |
| `theta_before` | FLOAT | NULLABLE | θ_individu sebelum update — hanya diisi jika `is_final_attempt = TRUE` |
| `theta_after` | FLOAT | NULLABLE | θ_individu setelah update — hanya diisi jika `is_final_attempt = TRUE` |
| `difficulty_before` | FLOAT | NULLABLE | Difficulty soal sebelum update — hanya jika `is_final_attempt = TRUE` |
| `difficulty_after` | FLOAT | NULLABLE | Difficulty soal setelah update — hanya jika `is_final_attempt = TRUE` |
| `execution_time_ms` | INTEGER | NULLABLE | Waktu solve dari soal pertama kali tampil hingga submit ini (dikirim frontend) |
| `stagnation_detected` | BOOLEAN | NOT NULL, DEFAULT FALSE | TRUE jika pada `ASSESSMENT_NEXT` ini stagnation terdeteksi untuk pertama kalinya di session ini. Hanya relevan jika `is_final_attempt = TRUE`. Memudahkan analisis log tanpa perlu mining variance Δθ secara manual. |
| `timestamp` | TIMESTAMP | DEFAULT NOW(), INDEX | |

**Catatan `execution_time_ms`:** Untuk final attempt dengan multi-attempt, `execution_time_ms` mengacu pada total waktu dari attempt pertama soal ini hingga submit terakhir. Frontend mengtrack waktu dari soal pertama kali ditampilkan, bukan dari masing-masing attempt.

**Stagnation detection** hanya membaca baris dengan `is_final_attempt = TRUE`:
```sql
SELECT theta_before, theta_after
FROM assessment_logs
WHERE user_id = :user_id
  AND session_id = :session_id
  AND is_final_attempt = TRUE
ORDER BY timestamp DESC
LIMIT 5
```

Memungkinkan query analisis stagnation detection:
```sql
-- Temukan semua titik stagnation terdeteksi
SELECT user_id, session_id, question_id, timestamp, theta_before, theta_after
FROM assessment_logs
WHERE stagnation_detected = TRUE
ORDER BY timestamp;

-- Bandingkan slope theta sebelum dan sesudah stagnation per user
SELECT
    user_id,
    AVG(theta_after - theta_before) FILTER (WHERE timestamp < stagnation_time) AS avg_delta_pre,
    AVG(theta_after - theta_before) FILTER (WHERE timestamp > stagnation_time) AS avg_delta_post
FROM assessment_logs
JOIN (
    SELECT user_id, timestamp AS stagnation_time
    FROM assessment_logs WHERE stagnation_detected = TRUE
) stag USING (user_id)
WHERE is_final_attempt = TRUE
GROUP BY user_id;

```

---

#### Table `pretest_sessions`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `session_id` | UUID | PK, DEFAULT uuid_generate_v4() | |
| `user_id` | UUID | FK → `users`, UNIQUE | Satu user hanya boleh punya satu pretest session |
| `current_question_index` | INTEGER | DEFAULT 0 | 0-based index soal berikutnya (0–4) |
| `total_questions` | INTEGER | DEFAULT 5 | Selalu 5 untuk prototipe |
| `answers` | JSONB | DEFAULT '{}' | Format: `{"CH01-Q003": true, "CH01-Q007": false, ...}` |
| `current_theta` | FLOAT | DEFAULT 1300.0 | Theta sementara selama pretest (rolling update per soal) |
| `started_at` | TIMESTAMP | DEFAULT NOW() | |
| `completed_at` | TIMESTAMP | NULLABLE | Di-set saat index mencapai 5 |

---

#### Table `peer_sessions`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `session_id` | UUID | PK, DEFAULT uuid_generate_v4() | |
| `requester_id` | UUID | FK → `users`, INDEX | User yang mengalami stagnasi |
| `reviewer_id` | UUID | FK → `users`, INDEX | Peer yang dipilih |
| `question_id` | VARCHAR(10) | FK → `questions`, INDEX | Soal konteks review |
| `requester_query` | TEXT | NOT NULL | Query terakhir requester (anonim untuk reviewer) |
| `review_content` | TEXT | NULLABLE | Feedback dari reviewer |
| `system_score` | FLOAT | NULLABLE, RANGE [0.0, 1.0] | NLP keyword matching score |
| `is_helpful` | BOOLEAN | NULLABLE | Binary rating dari requester |
| `final_score` | FLOAT | NULLABLE | `(0.5 × system_score) + (0.5 × CAST(is_helpful AS FLOAT))` |
| `theta_social_before` | FLOAT | NULLABLE | θ_social reviewer sebelum update |
| `theta_social_after` | FLOAT | NULLABLE | θ_social reviewer setelah update |
| `status` | VARCHAR(30) | DEFAULT 'PENDING_REVIEW' | `PENDING_REVIEW` \| `WAITING_CONFIRMATION` \| `COMPLETED` \| `EXPIRED` |
| `created_at` | TIMESTAMP | DEFAULT NOW() | |
| `expires_at` | TIMESTAMP | DEFAULT NOW() + INTERVAL '24 hours' | |
| `completed_at` | TIMESTAMP | NULLABLE | |

---

### 3.2 Sandbox Schema (`sandbox`)

#### Struktur Tabel

**`sandbox.student`**

| Column | Type | Description |
|--------|------|-------------|
| `ID` | VARCHAR(10) | PK, e.g. `'00128'`, `'12345'` |
| `name` | VARCHAR(100) | Student full name |
| `dept_name` | VARCHAR(50) | FK → department |
| `tot_cred` | INTEGER | Total credits earned |

**`sandbox.course`**

| Column | Type | Description |
|--------|------|-------------|
| `course_id` | VARCHAR(10) | PK, e.g. `'CS-101'`, `'BIO-301'` |
| `title` | VARCHAR(100) | Course title |
| `dept_name` | VARCHAR(50) | FK → department |
| `credits` | INTEGER | Credit hours |

**`sandbox.instructor`**

| Column | Type | Description |
|--------|------|-------------|
| `ID` | VARCHAR(10) | PK, e.g. `'10101'`, `'12121'` |
| `name` | VARCHAR(100) | Instructor full name |
| `dept_name` | VARCHAR(50) | FK → department |
| `salary` | DECIMAL(10,2) | Annual salary |

**`sandbox.department`**

| Column | Type | Description |
|--------|------|-------------|
| `dept_name` | VARCHAR(50) | PK, e.g. `'Comp. Sci.'`, `'Physics'` |
| `building` | VARCHAR(50) | Building name |
| `budget` | DECIMAL(12,2) | Department budget |

**`sandbox.classroom`**

| Column | Type | Description |
|--------|------|-------------|
| `building` | VARCHAR(50) | PK component |
| `room_no` | VARCHAR(10) | PK component |
| `capacity` | INTEGER | Room capacity |

**`sandbox.section`**

| Column | Type | Description |
|--------|------|-------------|
| `course_id` | VARCHAR(10) | FK → course, composite PK |
| `sec_id` | VARCHAR(5) | Section identifier, e.g. `'1'`, `'2'` |
| `semester` | VARCHAR(10) | e.g. `'Fall'`, `'Spring'` |
| `year` | INTEGER | e.g. `2009`, `2010` |
| `building` | VARCHAR(50) | FK → classroom |
| `room_no` | VARCHAR(10) | FK → classroom |
| `time_slot_id` | VARCHAR(10) | FK → time_slot |

**`sandbox.time_slot`**

| Column | Type | Description |
|--------|------|-------------|
| `time_slot_id` | VARCHAR(10) | PK, e.g. `'A'`, `'B'`, `'C'` |
| `day` | VARCHAR(10) | Day of week |
| `start_time` | TIME | Start time |
| `end_time` | TIME | End time |

**`sandbox.takes`**

| Column | Type | Description |
|--------|------|-------------|
| `ID` | VARCHAR(10) | FK → student, composite PK |
| `course_id` | VARCHAR(10) | FK → section |
| `sec_id` | VARCHAR(5) | FK → section |
| `semester` | VARCHAR(10) | FK → section |
| `year` | INTEGER | FK → section |
| `grade` | VARCHAR(2) | Letter grade |

**`sandbox.teaches`**

| Column | Type | Description |
|--------|------|-------------|
| `ID` | VARCHAR(10) | FK → instructor |
| `course_id` | VARCHAR(10) | FK → section |
| `sec_id` | VARCHAR(5) | FK → section |
| `semester` | VARCHAR(10) | FK → section |
| `year` | INTEGER | FK → section |

**`sandbox.prereq`**

| Column | Type | Description |
|--------|------|-------------|
| `course_id` | VARCHAR(10) | FK → course, composite PK |
| `prereq_id` | VARCHAR(10) | FK → course |

**`sandbox.advisor`**

| Column | Type | Description |
|--------|------|-------------|
| `s_ID` | VARCHAR(10) | FK → student, composite PK |
| `i_ID` | VARCHAR(10) | FK → instructor |

---

## 4. MATERIAL STRUCTURE (HIERARCHICAL DOMAIN)

| Module | Topic Focus | Difficulty Range (D) | Jumlah Soal | Unlock Threshold |
|--------|-------------|---------------------|-------------|------------------|
| CH01 | Basic Selection | [1000, 1400] | 25 | Tidak ada (terbuka untuk semua) |
| CH02 | Aggregation | [1200, 1600] | 25 | θ_individu ≥ 1300 |
| CH03 | Advanced Querying | [1400, 1800] | 25 | θ_individu ≥ 1600 |

**Bloom's Level Mapping (ACM CCECC 2023):**

| Module | Bloom's Level | Contoh Verb |
|--------|---------------|-------------|
| CH01 | Remember, Understand | Identify, Retrieve |
| CH02 | Apply, Analyze | Calculate, Distinguish |
| CH03 | Analyze, Evaluate | Construct, Critique |

**Note:** 40C16 ≈ 4.8 juta kombinasi per modul → risiko bank soal habis negligible untuk 10–20 user.

---

## 5. FRONTEND SPECIFICATION

### 5.1 React Router Configuration & Route Guards

```typescript
const routes = [
  // Public routes — redirect ke dashboard jika sudah login
  { path: "/login",    element: <AuthGuard><Login /></AuthGuard> },
  { path: "/register", element: <AuthGuard><Register /></AuthGuard> },

  // Protected routes — redirect ke login jika belum auth
  {
    element: <ProtectedRoute />,
    children: [
      // PretestGate: redirect ke /pretest jika belum selesai pretest
      { element: <PretestGate />, children: [
        { path: "/",                         element: <Dashboard /> },
        { path: "/modules",                  element: <Modules /> },
        { path: "/modules/:moduleId",        element: <ModuleDetail /> },
        { path: "/session/start",            element: <SessionStart /> },
        { path: "/session/:sessionId",       element: <SessionActive /> },
        { path: "/collaboration/inbox",      element: <CollabInbox /> },
        { path: "/collaboration/inbox/:id",  element: <ReviewTask /> },
        { path: "/collaboration/requests",   element: <MyRequests /> },
        { path: "/leaderboard",              element: <Leaderboard /> },
        { path: "/profile",                  element: <Profile /> },
        { path: "/profile/history",          element: <History /> },
      ]},
      { path: "/pretest", element: <Pretest /> },
    ]
  }
];
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
  attemptCount: number;          // attempt ke berapa di soal aktif (1–3)
  canRetry: boolean;             // attemptCount < 3 && !isCorrect
  questionStartTime: number;     // Date.now() saat soal pertama kali ditampilkan
  startSession: (session: AssessmentSession) => void;
  setCurrentQuestion: (q: Question) => void;
  incrementAttempt: () => void;
  clearSession: () => void;
}
```

### 5.3 Navigation Flow & Menu Structure

```
DASHBOARD (Default Route: /)
├── Progress Radar (3 modul)
├── Elo Stats (theta_individu + theta_social + theta_display)
├── Quick Resume → /session/start
└── Navigation Menu:
    ├── Coursework → /modules
    ├── Collaborative → /collaboration/inbox
    ├── Leaderboard → /leaderboard
    └── Profile → /profile

LEADERBOARD (/leaderboard)
├── Ranking berdasarkan theta_display (weighted average)
├── Kolom: Rank | Nama (anonim kecuali diri sendiri) | theta_display
└── Highlight baris user yang sedang login

PROFILE (/profile)
├── User Info (nama, NIM)
├── theta_individu (Elo rating kemampuan SQL)
├── theta_social (Elo rating kontribusi sosial)
├── theta_display (weighted average, ditampilkan sebagai "Overall Rating")
├── History Log → /profile/history
└── Settings (Dark/Light mode, editor font size)
```

---

## 6. ALGORITHMIC LOGIC (BACKEND CORE)

### 6.1 Pre-Test Flow (Mandatory Cold-Start Calibration)

**Rationale:** Kalibrasi awal berbasis 5 soal adaptive untuk mendapatkan θ_initial yang lebih baik dari flat-start. Vesin et al. (2022) menggunakan flat-start (semua user di 1300); pretest Equilibria memberikan estimasi awal yang lebih akurat, sementara konvergensi penuh tetap terjadi selama sesi latihan.

**Pemilihan Soal Pretest (Adaptive dari CH01):**

```python
FUNCTION select_pretest_question(current_theta, answered_question_ids):
    FILTER questions WHERE module_id = 'CH01' AND is_active = TRUE
    FILTER questions WHERE question_id NOT IN answered_question_ids
    FOR EACH question:
        distance = ABS(question.current_difficulty - current_theta)
    SELECT TOP 5 WITH smallest distance
    RANDOMLY PICK 1 from TOP 5
    RETURN selected_question
END FUNCTION
```

**Rolling Theta Update Selama Pretest:**

Setelah setiap soal pretest, theta diupdate menggunakan Elo standard dengan:
- `K_pretest = 30` (fase novice, konsisten dengan Vesin)
- `Ai = 1, A = 1` (pretest one-shot, tidak ada retry)
- `Tc = 1 jika benar, Tc = 0 jika salah; Tp = 1`
- `execution_time_ms` dikirimkan oleh frontend

**Formula Theta Initial (Final setelah 5 soal):**

```python
FUNCTION calculate_initial_theta(correct_count, total_questions=5):
    base_rating      = 1300.0
    baseline_correct = 2.5        # expected correct untuk θ = 1300
    multiplier       = 80.0      # span: (5 - 2.5) × 80 = 200 max adjustment

    adjustment = (correct_count - baseline_correct) * multiplier
    theta      = base_rating + adjustment

    RETURN CLAMP(theta, 1100, 1500)
END FUNCTION
```

**Calibration Table:**

| Correct | θ Awal | Interpretasi |
|---------|--------|--------------|
| 0/5 | 1100 | Sangat di bawah rata-rata — stay di CH01 |
| 1/5 | 1180 | Di bawah rata-rata — stay di CH01 |
| 2/5 | 1260 | Sedikit di bawah rata-rata — stay di CH01 |
| 3/5 | 1340 | Di atas rata-rata — langsung unlock CH02 |
| 4/5 | 1420 | Di atas rata-rata — langsung unlock CH02 |
| 5/5 | 1500 | Sangat di atas rata-rata — langsung unlock CH02, belum unlock CH03 (perlu latihan CH02) |

---

### 6.2 Adaptive Engine (Individual Mode)

#### Item Selection Strategy

```python
FUNCTION select_next_question(user_theta, module_id, served_question_ids):
    # served_question_ids: soal yang sudah di-finalize di session ini
    FILTER questions WHERE module_id = module_id AND is_active = TRUE
    FILTER questions WHERE question_id NOT IN served_question_ids

    IF no questions available:
        RETURN None  # Trigger session end

    FOR EACH question:
        distance = ABS(question.current_difficulty - user_theta)
    SELECT TOP 5 WITH smallest distance
    RANDOMLY PICK 1 from TOP 5
    RETURN selected_question
END FUNCTION
```

#### Multi-Attempt Flow per Soal

```python
# Dipanggil oleh POST /session/{id}/submit
FUNCTION handle_submit(session, question_id, user_query, execution_time_ms):
    # Validasi: soal yang disubmit harus current_question_id
    ASSERT question_id == session.current_question_id

    is_correct = sandbox.compare_query_results(user_query, question.target_query)
    attempt_number = session.current_question_attempt_count + 1

    is_final = is_correct OR (attempt_number >= 3)

    # Log attempt (semua attempt, bukan hanya final)
    CREATE assessment_logs(
        session_id       = session.session_id,
        user_id          = user.user_id,
        question_id      = question_id,
        user_query       = user_query,
        is_correct       = is_correct,
        attempt_number   = attempt_number,
        is_final_attempt = is_final,
        execution_time_ms = execution_time_ms,
        # theta_before/after dan difficulty_before/after diisi HANYA jika is_final
    )

    # Update attempt count di session
    session.current_question_attempt_count = attempt_number

    IF is_final:
        # Trigger Elo update (lihat section 6.2 Elo Update)
        # Lakukan di sini atau tunda ke /next — pilihan implementasi
        # Rekomendasinya: tunda ke /next agar user lihat feedback dulu

    RETURN {
        "is_correct":    is_correct,
        "attempt_number": attempt_number,
        "can_retry":     NOT is_final,
        "is_final":      is_final
    }
END FUNCTION

# Dipanggil oleh POST /session/{id}/next
FUNCTION handle_next(session):
    # Ambil semua attempt di soal aktif untuk hitung W
    attempts = GET assessment_logs WHERE
        session_id  = session.session_id AND
        question_id = session.current_question_id
        ORDER BY attempt_number ASC

    Ai = COUNT(attempts WHERE is_correct = TRUE)
    A  = COUNT(attempts)

    # Ambil execution_time_ms dari attempt terakhir (total waktu dari awal soal)
    time_ms = attempts[-1].execution_time_ms OR DEFAULT_TIME_LIMIT

    # Hitung W menggunakan Vesin Eq. 3
    W = calculate_success_rate(
        successful_attempts = Ai,
        overall_attempts    = A,
        correct_tests       = 1 IF Ai > 0 ELSE 0,  # Tc: binary sandbox result
        performed_tests     = 1,                     # Tp: selalu 1 per soal
        time_used_ms        = time_ms
    )

    # Update Elo
    k = get_k_factor(user.total_attempts)
    new_theta, new_difficulty = update_elo_ratings(
        student_rating      = user.theta_individu,
        question_difficulty = question.current_difficulty,
        success_rate        = W,
        k_factor            = k
    )

    # Update log final attempt dengan theta before/after
    UPDATE assessment_logs SET
        theta_before      = user.theta_individu,
        theta_after       = new_theta,
        difficulty_before = question.current_difficulty,
        difficulty_after  = new_difficulty
    WHERE session_id = session.session_id
      AND question_id = session.current_question_id
      AND is_final_attempt = TRUE

    # Commit perubahan ke user dan question
    user.theta_individu  = new_theta
    user.total_attempts += 1
    user.k_factor        = get_k_factor(user.total_attempts)
    question.current_difficulty = new_difficulty

    # Finalize soal di session
    APPEND session.current_question_id TO session.question_ids_served
    session.current_question_id           = NULL
    session.current_question_attempt_count = 0

    # Cek unlock modul
    check_and_unlock_modules(user)

    # Cek stagnation (hanya untuk Grup A)
    stagnation = FALSE
    peer_session_created = FALSE

    IF user.group_assignment == 'A':
        stagnation = detect_stagnation(user.user_id)

        IF NOT stagnation:
            # Fallback trigger: jika user sudah mengerjakan N soal
            # di chapter ini tanpa unlock chapter berikutnya
            soal_di_chapter_ini = COUNT(assessment_logs WHERE
                user_id    = user.user_id AND
                module_id  = session.module_id AND
                is_final_attempt = TRUE)

            next_module = GET modules WHERE order_index = current_module.order_index + 1
            next_unlocked = (user.theta_individu >= next_module.unlock_theta_threshold)

            IF soal_di_chapter_ini >= 8 AND NOT next_unlocked AND current_module.module_id != 'CH03':
                stagnation = TRUE
                LOG event_type = 'STAGNATION_FALLBACK_TRIGGER'

        IF stagnation:
            # Update flag di log
            UPDATE assessment_logs SET stagnation_detected = TRUE
                WHERE log_id = current_final_log.log_id

            # Update flag di user
            user.stagnation_ever_detected = TRUE

            trigger_collaborative_mode(user, session)
            peer_session_created = TRUE

    ELSE:
        # Grup B: stagnation di-log tapi tidak memicu intervensi
        stagnation_would_trigger = detect_stagnation(user.user_id)
        IF stagnation_would_trigger:
            UPDATE assessment_logs SET stagnation_detected = TRUE
                WHERE log_id = current_final_log.log_id
            user.stagnation_ever_detected = TRUE
            LOG event_type = 'STAGNATION_DETECTED_NO_INTERVENTION'
            # Tidak ada peer session yang dibuat

    # Pilih soal berikutnya
    next_q = select_next_question(user.theta_individu, session.module_id, session.question_ids_served)

    IF next_q IS NULL:
        END session (status = 'COMPLETED')
        RETURN { "session_completed": True }

    session.current_question_id            = next_q.question_id
    session.current_question_attempt_count = 0

    RETURN {
        "theta_updated":       new_theta,
        "stagnation_detected": stagnation,
        "next_question":       next_q
    }
END FUNCTION
```

#### Success Rate Formula (Vesin et al. 2022, Eq. 3)

```python
# Constants
TIME_DISCRIMINATION = 1e-6  # ai — parameter diskriminasi waktu
DEFAULT_TIME_LIMIT  = 300000  # di — 5 menit dalam milidetik

FUNCTION calculate_success_rate(
    successful_attempts,   # Ai: jumlah attempt yang berhasil (0 atau 1 di prototipe)
    overall_attempts,      # A:  total attempt (1, 2, atau 3)
    correct_tests,         # Tc: unit tests yang lulus — dimapping ke binary sandbox result
    performed_tests,       # Tp: unit tests yang dilakukan — selalu 1 di prototipe
    time_used_ms,          # ti: waktu yang digunakan
    time_limit_ms = DEFAULT_TIME_LIMIT,
    discrimination = TIME_DISCRIMINATION
):
    IF overall_attempts == 0 OR performed_tests == 0:
        RETURN 0.0

    # Attempt ratio: Ai / A
    # Gradasi yang mungkin: {1.0, 0.5, 0.33, 0.0}
    attempt_ratio = successful_attempts / overall_attempts

    # Test ratio: Tc / Tp
    # Di prototipe: 1.0 jika benar, 0.0 jika salah
    # Catatan: ini adalah simplifikasi dari unit testing Vesin karena sandbox SQL
    # hanya menghasilkan binary pass/fail. Didokumentasikan sebagai prototype limitation.
    test_ratio = correct_tests / performed_tests

    # Time component: ai * (di - ti), clamped di 0
    time_component = discrimination * (time_limit_ms - time_used_ms)
    time_component = MAX(0.0, time_component)

    # Vesin Eq. 3: W = (Ai/A) * (Tc/Tp) * (1 + ai*di - ai*ti)
    W = attempt_ratio * test_ratio * (1.0 + time_component)

    RETURN CLAMP(W, 0.0, 2.0)
END FUNCTION
```

**Tabel distribusi W yang mungkin (contoh dengan time_limit=300000ms):**

| Ai/A | Tc/Tp | time_used_ms | Kalkulasi | W |
|------|-------|--------------|-----------|---|
| 1.0 (benar attempt 1) | 1.0 | 60000 (1 mnt) | 1.0 × 1.0 × (1 + 0.24) | **1.24** |
| 1.0 (benar attempt 1) | 1.0 | 150000 (2.5 mnt) | 1.0 × 1.0 × (1 + 0.15) | **1.15** |
| 1.0 (benar attempt 1) | 1.0 | 270000 (4.5 mnt) | 1.0 × 1.0 × (1 + 0.03) | **1.03** |
| 1.0 (benar attempt 1) | 1.0 | 300000 (tepat limit) | 1.0 × 1.0 × (1 + 0.00) | **1.00** |
| 0.5 (benar attempt 2) | 1.0 | 60000 | 0.5 × 1.0 × 1.24 | **0.62** |
| 0.5 (benar attempt 2) | 1.0 | 300000 | 0.5 × 1.0 × 1.00 | **0.50** |
| 0.33 (benar attempt 3) | 1.0 | 60000 | 0.33 × 1.0 × 1.24 | **0.41** |
| 0.33 (benar attempt 3) | 1.0 | 300000 | 0.33 × 1.0 × 1.00 | **0.33** |
| 0.0 (salah semua) | 0.0 | — | 0.0 × 0.0 × (...) | **0.0** |

**Catatan penting:** Dengan `ai = 1e-6` dan `di = 300000ms`, nilai `ai × di = 0.3` — mengikuti proporsi parameter Vesin et al. (2022) yang menggunakan satuan detik (`ai = 0.001`, `di = 300s`, sehingga `ai × di = 0.3`). Nilai `ai` di Equilibria dikalibrasi ulang dari `0.001` ke `1e-6` semata-mata karena perbedaan satuan waktu (milidetik vs detik), bukan perubahan desain. Dengan kalibrasi ini, time component memberikan gradasi yang meaningful: user yang menyelesaikan soal dalam 1 menit mendapat bonus ~24% dibanding user yang menyelesaikan tepat di batas waktu. Clamp ke 2.0 tetap dipertahankan sesuai Vesin, namun dalam praktik hanya tercapai jika `time_used_ms` bernilai negatif — yang tidak mungkin terjadi.

#### Elo Update Formula (Vesin et al. 2022, Eq. 1–2)

```python
FUNCTION calculate_expected_score(student_rating, question_difficulty):
    # Vesin Eq. 4: probabilitas student berhasil
    rating_diff = student_rating - question_difficulty
    RETURN 1.0 / (1.0 + 10 ^ (rating_diff / 400.0))

FUNCTION update_elo_ratings(student_rating, question_difficulty, success_rate, k_factor):
    expected = calculate_expected_score(student_rating, question_difficulty)

    # Vesin Eq. 1: update rating student
    new_student_rating = student_rating + k_factor * (success_rate - expected)

    # Vesin Eq. 2: update difficulty soal (zero-sum)
    new_question_difficulty = question_difficulty + k_factor * (expected - success_rate)

    new_student_rating      = CLAMP(new_student_rating, 0, 2000)
    new_question_difficulty = CLAMP(new_question_difficulty, 0, 2000)

    RETURN new_student_rating, new_question_difficulty
END FUNCTION
```

#### K-Factor Adaptation (Vesin et al. 2022, verbatim)

```python
FUNCTION get_k_factor(total_attempts):
    # Vesin et al. (2022): K ∈ {30, 20, 15, 10}
    IF total_attempts < 10:
        RETURN 30
    ELIF total_attempts < 25:
        RETURN 20
    ELIF total_attempts < 50:
        RETURN 15
    ELSE:
        RETURN 10
END FUNCTION
```

**Justifikasi threshold:** Menggunakan nilai Vesin et al. (2022) secara verbatim untuk reproducibility. Pada skala lab study (10–20 user), sebagian besar peserta tidak akan melebihi 25 attempt dalam satu sesi 90–120 menit, sehingga K=30 dan K=20 adalah yang paling relevan. Vesin membuktikan konvergensi dalam 7–10 soal (Vesin et al. 2022, Fig. 12), yang terjadi sepenuhnya dalam fase K=30.

---

### 6.3 Stagnation Detection sebagai Deteksi Konvergensi Prematur

**Landasan teoretis:** Vesin et al. (2022) secara empiris mengobservasi bahwa rating siswa
konvergen setelah 7–10 soal (Fig. 12) — kondisi di mana theta siswa dan difficulty soal
yang direkomendasikan saling terkunci pada level yang sama (*fixed point*), sehingga
`We ≈ W` dan `Δθ → 0`. Dalam sistem ProTuS, konvergensi ini adalah tujuan karena tidak
ada hierarki konten yang harus dilalui.

Equilibria berbeda secara fundamental: pembelajaran dimodelkan mengikuti kurikulum
universitas dengan hierarki chapter (CH01 → CH02 → CH03). Konvergensi yang terjadi
sebelum user mencapai chapter tertinggi (CH03) diinterpretasikan sebagai
**overpersonalization** — sistem terlalu mengoptimasi rekomendasi untuk level saat ini
sehingga menghambat progres ke chapter berikutnya. Oleh karena itu, *fixed point* yang
terdeteksi di CH01 atau CH02 memicu intervensi sosial untuk mendorong pertumbuhan
yang tidak bisa lagi dicapai melalui mekanisme adaptif individual.

Deteksi dilakukan dengan mengukur variance Δθ dari 5 soal final terakhir, **lintas sesi**
(karena konvergensi Elo bersifat global, tidak per-sesi). Stagnation hanya dipicu jika user
belum berada di chapter tertinggi (CH03).
```python
FUNCTION detect_stagnation(user_id, current_module_id):
    # Tidak ada stagnation jika user sudah di chapter tertinggi
    # Konvergensi di CH03 adalah tujuan, bukan masalah
    IF current_module_id == 'CH03':
        RETURN FALSE

    # Ambil 5 final attempt terakhir lintas sesi (konvergensi bersifat global)
    last_5_logs = QUERY assessment_logs
        WHERE user_id        = user_id
          AND is_final_attempt = TRUE
        ORDER BY timestamp DESC
        LIMIT 5

    IF COUNT(last_5_logs) < 5:
        RETURN FALSE   # Belum cukup data untuk deteksi

    deltas   = [log.theta_after - log.theta_before FOR log IN last_5_logs]
    variance = numpy.var(deltas)   # population variance

    RETURN variance < 165   # ε = 165 (lihat Section 13.1)
END FUNCTION
```

**Catatan:** Stagnation detection tidak menggunakan filter `session_id` karena konvergensi
Elo adalah properti akumulatif dari seluruh history user, bukan satu sesi. Ini konsisten
dengan K-factor decay yang juga berbasis `total_attempts` global.

**Post-stagnation action:**

```python
IF detect_stagnation(user_id, session_id):
    user.status = 'NEEDS_PEER_REVIEW'
    peer = find_heterogeneous_peer(user)
    IF peer IS NOT None:
        CREATE peer_session(
            requester_id   = user.user_id,
            reviewer_id    = peer.user_id,
            question_id    = session.current_question_id OR last_served_question,
            requester_query = last_user_query
        )
        LOG event_type = 'PEER_MATCH_SUCCESS'
        RETURN stagnation_detected = TRUE, peer_session_created = TRUE
    ELSE:
        LOG event_type = 'PEER_MATCH_FAIL'
        RETURN stagnation_detected = TRUE, peer_session_created = FALSE
        # User tetap lanjut individual mode
```

**Fallback Trigger (Safety Net untuk Lab Study):**

Selain variance-based detection, sistem mengimplementasikan fallback trigger berbasis
jumlah soal untuk memastikan intervensi terpicu dalam timeframe lab study yang terbatas:
```python
FUNCTION check_fallback_trigger(user, session):
    # Hanya aktif jika:
    # 1. User di Grup A
    # 2. User bukan di chapter tertinggi (CH03)
    # 3. Chapter berikutnya belum unlock
    IF user.group_assignment != 'A': RETURN FALSE
    IF session.module_id == 'CH03':  RETURN FALSE

    next_module    = GET module WITH order_index = current_module.order_index + 1
    next_unlocked  = (user.theta_individu >= next_module.unlock_theta_threshold)
    IF next_unlocked: RETURN FALSE

    soal_di_chapter = COUNT assessment_logs WHERE
        user_id          = user.user_id AND
        module_id        = session.module_id AND
        is_final_attempt = TRUE

    RETURN soal_di_chapter >= 8
END FUNCTION
```

**Justifikasi N=8:** Vesin et al. (2022) membuktikan konvergensi dalam 7–10 soal.
Jika setelah 8 soal user belum unlock chapter berikutnya, sistem dapat menyimpulkan
bahwa konvergensi prematur telah terjadi meski variance Δθ belum mencapai threshold.

**Prioritas trigger:** Variance-based detection (primary) → Fallback N=8 (secondary).
Kedua trigger menghasilkan efek yang sama: peer session dibuat dan `stagnation_detected = TRUE`
di-set di log. Event type berbeda untuk membedakan sumber trigger di analisis pasca-hoc:
- Variance trigger: `STAGNATION_DETECTED`
- Fallback trigger: `STAGNATION_FALLBACK_TRIGGER`

---

### 6.4 Constraint-Based Re-ranking (Heterogeneity Enforcement)

```python
FUNCTION find_heterogeneous_peer(requester):
    all_thetas     = QUERY SELECT theta_individu FROM users WHERE status = 'ACTIVE'
    population_std = numpy.std(all_thetas)

    IF population_std == 0:
        population_std = 100.0  # Fallback edge case

    min_difference = 0.5 * population_std  # Cohen's d = 0.5

    candidates = QUERY users WHERE
        user_id   != requester.user_id AND
        status    != 'NEEDS_PEER_REVIEW' AND
        ABS(theta_individu - requester.theta_individu) >= min_difference

    IF COUNT(candidates) == 0:
        RETURN None

    ORDER BY ABS(theta_individu - requester.theta_individu) DESCENDING
    LIMIT 5
    RETURN RANDOM_SELECT(candidates)
END FUNCTION
```

---

### 6.5 Social Elo (Reviewer-vs-Standar)

`theta_social` adalah dimensi Elo independen yang mengukur kualitas reviewer. Diupdate setelah requester memberikan rating (thumbs up/down), menggunakan mekanisme Elo dengan **expected score = 0.5** (standar netral — reviewer yang "rata-rata" diharapkan menghasilkan feedback berkualitas 0.5).

```python
FUNCTION update_theta_social(reviewer, peer_session):
    W_social  = peer_session.final_score   # 0.0 – 1.0
    We_social = 0.5                        # Expected baseline (reviewer rata-rata)
    K_social  = 30                         # Sama dengan K_individu fase novice
                                           # Justified: peer sessions di lab study
                                           # tidak akan melebihi 10 → tetap di K=30

    delta = K_social * (W_social - We_social)
    # delta range: [-15, +15] per interaksi

    new_theta_social = CLAMP(reviewer.theta_social + delta, 0, 2000)

    # Log ke peer_sessions untuk analisis
    peer_session.theta_social_before = reviewer.theta_social
    peer_session.theta_social_after  = new_theta_social
    peer_session.status              = 'COMPLETED'
    peer_session.completed_at        = NOW()

    reviewer.theta_social = new_theta_social
    reviewer.status       = 'ACTIVE'
    requester.status      = 'ACTIVE'

    SAVE reviewer, requester, peer_session
END FUNCTION
```

**`final_score` calculation:**

```python
final_score = (0.5 * system_score) + (0.5 * (1.0 IF is_helpful ELSE 0.0))
```

---

### 6.6 NLP Feedback Quality Scoring

```python
# Section 6.6: NLP Feedback Quality Scoring

# 1. Identification: Problem localization & error detection
# Source: Kerman et al. (2024) - Cognitive Identification Feature
IDENTIFICATION_KEYWORDS = [
    # Indonesian
    'error', 'salah', 'bug', 'masalah', 'issue', 'kurang', 'hilang', 
    'tidak muncul', 'tidak berjalan', 'kosong', 'null', 'gagal', 
    'exception', 'typo', 'keliru', 'cacat', 'anomali',
    # English
    'missing', 'wrong', 'incorrect', 'failed', 'issue', 'problem', 
    'undefined', 'empty', 'invalid'
]

# 2. Justification: Reasoning & Causal Explanation
# Source: Kerman et al. (2024) - Cognitive Justification Feature (NEW)
JUSTIFICATION_KEYWORDS = [
    # Indonesian
    'karena', 'sebab', 'akibat', 'sehingga', 'maka', 'akibatnya', 
    'alasan', 'penyebab', 'mengapa', 'due to', 'oleh karena',
    # English
    'because', 'therefore', 'thus', 'hence', 'due to', 'leads to', 
    'causes', 'reason', 'why', 'since', 'as a result'
]

# 3. Constructive: Actionable Recommendations & Plans
# Source: Kerman et al. (2024) - Constructive Feature
CONSTRUCTIVE_KEYWORDS = [
    # Indonesian
    'seharusnya', 'coba', 'gunakan', 'ubah', 'perbaiki', 'tambahkan', 
    'hapus', 'pindahkan', 'solusi', 'sarankan', 'usulkan', 'ganti',
    # English
    'should', 'try', 'use', 'change', 'fix', 'add', 'remove', 'move', 
    'consider', 'recommend', 'suggest', 'replace', 'update'
]

# 4. Bloom's Higher-Order Verbs (Quality Bonus)
# Source: ACM Bloom's for Computing (2023) - Evaluating & Analyzing Levels
BLOOMS_HIGH_ORDER_KEYWORDS = [
    # Indonesian
    'debug', 'optimize', 'validasi', 'trace', 'telusuri', 'analisis', 
    'evaluasi', 'refactor', 'struktur ulang', 'prioritas', 'bukti',
    # English
    'debug', 'optimize', 'validate', 'trace', 'analyze', 'evaluate', 
    'refactor', 'prioritize', 'prove', 'verify', 'test', 'secure'
]

FUNCTION calculate_system_score(feedback_text):
    # --- Pre-processing ---
    IF LENGTH(TRIM(feedback_text)) < 15:
        RETURN 0.1  # Too short to be meaningful

    text = LOWERCASE(feedback_text)
    
    # --- Tier 1: Structural Quality (Weighted Components) ---
    # Based on Kerman et al. (2024) findings on predictive features
    
    has_identification = ANY(kw IN text FOR kw IN IDENTIFICATION_KEYWORDS)
    has_justification  = ANY(kw IN text FOR kw IN JUSTIFICATION_KEYWORDS)
    has_constructive   = ANY(kw IN text FOR kw IN CONSTRUCTIVE_KEYWORDS)
    
    # Weighted Sum: Justification weighted highest as per Kerman's success predictors
    structural_score = 0.0
    IF has_identification: structural_score += 0.3
    IF has_justification:  structural_score += 0.4
    IF has_constructive:   structural_score += 0.3
    
    # --- Tier 2: Cognitive Depth Bonus (Bloom's Taxonomy) ---
    # Based on ACM Bloom's for Computing (2023) Higher-Order Verbs
    
    depth_bonus = 0.0
    high_order_count = COUNT(kw IN text FOR kw IN BLOOMS_HIGH_ORDER_KEYWORDS)
    
    IF high_order_count > 0:
        # Cap bonus at 0.2 to prevent overshadowing structural quality
        depth_bonus = MIN(0.2, high_order_count * 0.1)
    
    # --- Final Calculation ---
    final_score = structural_score + depth_bonus
    
    # Ensure score stays within [0.0, 1.0] range
    RETURN CLAMP(final_score, 0.0, 1.0)
END FUNCTION
```

---

### 6.7 Theta Display (Weighted Average)

```python
FUNCTION calculate_theta_display(theta_individu, theta_social):
    # Weighted average — output tetap di range [0, 2000]
    # theta_individu adalah komponen dominan (80%)
    # theta_social sebagai komplemen (20%)
    RETURN (0.8 * theta_individu) + (0.2 * theta_social)
END FUNCTION
```

Dihitung on-the-fly di endpoint `/profile/stats` dan `/leaderboard`. Tidak disimpan di database.

---

### 6.8 Module Unlock Check

```python
FUNCTION check_and_unlock_modules(user):
    all_modules = QUERY modules ORDER BY order_index
    FOR EACH module IN all_modules:
        progress = GET user_module_progress
            WHERE user_id = user.user_id AND module_id = module.module_id
        IF progress IS NULL:
            CREATE user_module_progress(user_id, module_id, is_unlocked=FALSE)

        IF NOT progress.is_unlocked AND user.theta_individu >= module.unlock_theta_threshold:
            progress.is_unlocked = TRUE
            SAVE progress
            LOG event_type = 'MODULE_UNLOCKED', module_id = module.module_id
END FUNCTION
```

---

## 7. BACKEND API SPECIFICATION

### 7.1 Authentication & Authorization

**JWT Flow:**
1. `POST /api/v1/auth/login` → JWT access token (30 mnt) + refresh token (7 hari)
2. Semua protected endpoint: `Authorization: Bearer <token>`
3. FastAPI dependency `get_current_user()` → validate JWT → return `UserResponse`

### 7.2 Response Convention (JSend)

```python
class JSendResponse[T](BaseModel, Generic[T]):
    status:  Literal["success", "fail", "error"]
    code:    int
    data:    Optional[T] = None
    message: Optional[str] = None
```

| `status` | HTTP Range | Kapan |
|----------|------------|-------|
| `success` | 2xx | Request berhasil |
| `fail` | 4xx | Kesalahan client (validasi, unauthorized, not found) |
| `error` | 5xx | Kesalahan server |

---

### 7.3 Complete API Endpoints Reference

#### A. Authentication Endpoints

| Method | Endpoint | Input Body | Output | Status Codes |
|--------|----------|-----------|--------|--------------|
| POST | `/api/v1/auth/register` | `{nim, full_name, password}` | `JSend[LoginResponse]` | 201, 409 |
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
    "theta_individu": 1300.0,
    "theta_social": 1300.0,
    "theta_display": 1240.0,
    "k_factor": 30,
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
| POST | `/api/v1/pretest/start` | — | `JSend[PretestSession]` | 201, 400, 403 |
| GET | `/api/v1/pretest/question/current` | — | `JSend[PretestQuestion]` | 200, 404 |
| POST | `/api/v1/pretest/submit` | `{question_id, question_number, user_query, execution_time_ms}` | `JSend[PretestSubmitResult]` | 200, 400 |

**Validation rules `/pretest/submit`:**
- `question_number` harus = `current_question_index + 1`. Jika tidak → 400 "Out of order submission"
- `question_id` harus sesuai soal yang sedang aktif di session

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

---

#### D. Assessment (Individual Mode) Endpoints

| Method | Endpoint | Input Body | Output | Status Codes |
|--------|----------|-----------|--------|--------------|
| POST | `/api/v1/session/start` | `{module_id}` | `JSend[SessionStartResult]` | 201, 400 (session aktif sudah ada), 403 (modul locked) |
| GET | `/api/v1/session/{session_id}` | — | `JSend[SessionStatus]` | 200, 404 |
| GET | `/api/v1/session/{session_id}/question` | — | `JSend[QuestionResponse]` | 200, 404 |
| POST | `/api/v1/session/{session_id}/submit` | `{question_id, user_query, execution_time_ms}` | `JSend[SubmitResult]` | 200, 400 |
| POST | `/api/v1/session/{session_id}/next` | — | `JSend[NextResult]` | 200, 400 (belum ada attempt), 404 |
| POST | `/api/v1/session/{session_id}/end` | — | `JSend[SessionSummary]` | 200, 404 |
| GET | `/api/v1/session/active` | — | `JSend[SessionStatus \| null]` | 200 |

**`GET /api/v1/session/active`** — mengembalikan session `ACTIVE` milik user saat ini jika ada, atau `data: null` jika tidak ada. Digunakan oleh dashboard dan module detail page untuk menampilkan tombol "Resume".

**Conflict resolution flow (`POST /api/v1/session/start`):**
- Jika tidak ada session `ACTIVE` → buat session baru, return 201
- Jika ada session `ACTIVE` di modul yang **sama** → return session yang ada (idempotent resume), return 200
- Jika ada session `ACTIVE` di modul yang **berbeda** → return 409 dengan payload session yang aktif:
```json
{
  "status": "fail",
  "code": 409,
  "data": {
    "active_session": {
      "session_id": "uuid",
      "module_id": "CH01",
      "started_at": "2026-03-16T07:00:00Z"
    }
  },
  "message": "Kamu masih memiliki sesi aktif di CH01. Akhiri sesi tersebut untuk memulai sesi baru."
}
```

Frontend menampilkan konfirmasi kepada user. Jika user konfirmasi, frontend memanggil `POST /session/{active_session_id}/end` terlebih dahulu, kemudian ulangi `POST /session/start`.

**`SubmitResult` schema** (belum ada Elo update, hanya sandbox result):
```json
{
  "is_correct": false,
  "attempt_number": 2,
  "can_retry": true,
  "is_final": false
}
```

**`NextResult` schema** (setelah Elo diupdate):
```json
{
  "theta_before": 1080.0,
  "theta_after": 1065.0,
  "w_success_rate": 0.0,
  "stagnation_detected": false,
  "peer_session_created": false,
  "session_completed": false,
  "next_question": { "question_id": "CH02-Q007", "content": "..." }
}
```

---

#### E. Collaborative Endpoints

| Method | Endpoint | Input Body | Output | Status Codes |
|--------|----------|-----------|--------|--------------|
| GET | `/api/v1/collaboration/inbox` | — | `JSend[PeerSessionInboxItem[]]` | 200 |
| GET | `/api/v1/collaboration/inbox/{session_id}` | — | `JSend[PeerSessionDetail]` | 200, 403, 404 |
| POST | `/api/v1/collaboration/inbox/{session_id}/submit` | `{review_content}` | `JSend[ReviewSubmitResult]` | 200, 400, 404 |
| GET | `/api/v1/collaboration/requests` | — | `JSend[PeerSessionRequest[]]` | 200 |
| POST | `/api/v1/collaboration/requests/{session_id}/rate` | `{is_helpful: bool}` | `JSend[RateResult]` | 200, 400, 403 |

**`PeerSessionDetail` schema (untuk reviewer — requester anonim):**
```json
{
  "session_id": "uuid",
  "question": { "content": "Tampilkan rata-rata IPK...", "topic_tags": ["AVG", "GROUP BY"] },
  "requester_query": "SELECT AVG(ipk) FROM mahasiswa",
  "status": "PENDING_REVIEW",
  "expires_at": "2026-03-17T07:00:00Z"
}
```

**`RateResult` schema** (setelah theta_social reviewer diupdate):
```json
{
  "final_score": 0.75,
  "reviewer_theta_social_before": 1300.0,
  "reviewer_theta_social_after": 1007.5
}
```

---

#### F. Leaderboard Endpoint

| Method | Endpoint | Input | Output | Status Codes |
|--------|----------|-------|--------|--------------|
| GET | `/api/v1/leaderboard` | `?limit=20&offset=0` | `JSend[LeaderboardEntry[]]` | 200 |

**`LeaderboardEntry` schema:**
```json
{
  "rank": 1,
  "user_id": "uuid",
  "display_name": "D***a",
  "theta_display": 1312.0,
  "is_self": false
}
```

`display_name` diobfuscate untuk semua user kecuali diri sendiri (`is_self = true`).

---

#### G. Profile & Statistics Endpoints

| Method | Endpoint | Output | Status Codes |
|--------|----------|--------|--------------|
| GET | `/api/v1/profile/stats` | `JSend[ProfileStats]` | 200 |
| GET | `/api/v1/profile/history` | `JSend[AssessmentLogPage]` | 200 |
| GET | `/api/v1/profile/social` | `JSend[SocialStats]` | 200 |

**`ProfileStats` schema:**
```json
{
  "theta_individu": 1150.0,
  "theta_social": 1007.5,
  "theta_display": 1121.5,
  "total_attempts": 18,
  "k_factor": 20,
  "module_progress": [
    { "module_id": "CH01", "is_unlocked": true, "is_completed": true },
    { "module_id": "CH02", "is_unlocked": true, "is_completed": false },
    { "module_id": "CH03", "is_unlocked": false, "is_completed": false }
  ],
  "accuracy_rate": 0.72
}
```

---

## 8. LOGGING SPECIFICATION

### 8.1 Dual Logging System

| Log Type | Location | Format | Rotation | Retention |
|----------|----------|--------|----------|-----------|
| System Logs | `/app/logs/syslogs/` | JSON | 10MB | 5 backup files |
| Assessment Logs | `/app/logs/asslogs/` | JSON | 10MB | 5 backup files |
| Assessment DB | PostgreSQL `assessment_logs` | Structured | Persistent | Indefinite |

### 8.2 Log Entry Format (System)

```json
{
  "timestamp": "2026-03-16T07:00:00.000Z",
  "level": "INFO",
  "logger": "equilibria.system",
  "message": "Login successful",
  "module": "auth",
  "function": "login",
  "line": 123,
  "user_id": "uuid",
  "event_type": "AUTH_LOGIN_SUCCESS"
}
```

### 8.3 Assessment Log Entry Format

```json
{
  "timestamp": "2026-03-16T07:05:00.000Z",
  "level": "INFO",
  "logger": "equilibria.assessment",
  "message": "Final attempt — Elo updated",
  "user_id": "uuid",
  "session_id": "uuid",
  "question_id": "CH02-Q004",
  "attempt_number": 2,
  "is_final_attempt": true,
  "is_correct": true,
  "w_success_rate": 0.5,
  "theta_before": 1080.0,
  "theta_after": 1096.2,
  "k_factor": 30,
  "execution_time_ms": 45000,
  "stagnation_detected": false,
  "event_type": "ASSESSMENT_NEXT"
}
```

### 8.4 Event Types

| event_type | Logger | Trigger |
|------------|--------|---------|
| `AUTH_LOGIN_SUCCESS` / `AUTH_LOGIN_FAIL` | system | Login |
| `PRETEST_START` / `PRETEST_SUBMIT` / `PRETEST_COMPLETE` | assessment | Pretest lifecycle |
| `ASSESSMENT_SUBMIT` | assessment | Setiap submit (intermediate dan final) |
| `ASSESSMENT_NEXT` | assessment | User klik Next — Elo diupdate di sini |
| `STAGNATION_DETECTED` | assessment | Stagnation terdeteksi |
| `PEER_MATCH_SUCCESS` / `PEER_MATCH_FAIL` | assessment | Peer matching attempt |
| `PEER_REVIEW_SUBMITTED` | assessment | Reviewer submit feedback |
| `PEER_RATED` | assessment | Requester rate feedback — theta_social diupdate |
| `MODULE_UNLOCKED` | assessment | Module baru terbuka |
| `SANDBOX_ERROR` | system | Query sandbox gagal |
| `STAGNATION_FALLBACK_TRIGGER` | assessment | Stagnation dipicu oleh fallback N=8 soal (bukan variance) — Grup A |
| `STAGNATION_DETECTED_NO_INTERVENTION` | assessment | Stagnation terdeteksi tapi tidak dipicu karena Grup B (ablation control) |

---

## 9. CONFIGURATION MANAGEMENT

### 9.1 Environment Variables (Backend)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ | — | `postgresql+asyncpg://...` |
| `JWT_SECRET_KEY` | ✅ | — | Min 32 karakter |
| `JWT_ALGORITHM` | ❌ | `HS256` | |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ❌ | `30` | |
| `REFRESH_TOKEN_EXPIRE_DAYS` | ❌ | `7` | |
| `LOG_LEVEL` | ❌ | `INFO` | |
| `SANDBOX_DB_ROLE` | ✅ | — | Nama role DB sandbox |
| `SANDBOX_QUERY_TIMEOUT_MS` | ❌ | `5000` | |

### 9.2 Environment Variables (Frontend)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_BASE_URL` | ✅ | Backend API endpoint |
| `VITE_APP_NAME` | ✅ | Application display name |
| `VITE_VERSION` | ✅ | Frontend version |

---

## 10. SECURITY & LIMITATIONS

### 10.1 Sandbox Security

| Feature | Status | Implementation |
|---------|--------|----------------|
| `SELECT`-only access | ✅ | Role `sandbox_executor` dengan GRANT SELECT only |
| No `public` schema access | ✅ | `REVOKE ALL ON SCHEMA public FROM sandbox_executor` |
| Query timeout | ✅ | `SET LOCAL statement_timeout = 5000` sebelum query |
| Dangerous keyword blocklist | ✅ | Case-insensitive: `DROP`, `DELETE`, `INSERT`, `UPDATE`, `ALTER`, `CREATE`, `TRUNCATE`, `GRANT`, `REVOKE`, `PG_`, `--` |
| Dedicated engine isolation | ✅ | Engine terpisah, tidak share session dengan main app |
| Transaction isolation | ✅ | Sandbox error → `SandboxExecutionError` → `is_correct = False`, main session tidak abort |
| Schema routing | ✅ | `SET ROLE sandbox_executor` + `SET search_path = sandbox` |
| Container isolation | ⚠️ | Not implemented (prototype scale) |

### 10.2 Edge Cases

| Edge Case | Risk | Mitigation |
|-----------|------|------------|
| Bank soal habis | Rendah | 40C16 ≈ 4.8 juta kombinasi |
| Tidak ada peer tersedia | Sedang | Lanjut individual mode, log `PEER_MATCH_FAIL` |
| Peer session timeout | Sedang | Auto-expire 24h via background task |
| Session conflict | Rendah | Tolak `POST /session/start` jika ada session `ACTIVE` |
| W selalu clamp ke 2.0 | Rendah | Lihat catatan Section 6.2 — acceptable untuk prototipe |
| theta_social belum converge | Sedang | Lab study kecil → stated as limitation di laporan |
| Session ditinggal tanpa di-end | Sedang | Auto-ABANDONED setelah 24 jam dari `started_at` via background task |
| User mulai session baru saat ada session ACTIVE | Rendah | Return 409 + conflict payload → frontend tampilkan konfirmasi terminasi |

### 10.3 Security

- **Password:** Argon2id, `m=2^16, t=3, p=4` (RFC 9106)
- **JWT:** HS256, access token 30 mnt, refresh token 7 hari
- **Storage:** Hash only, HTTPS di production

---

## 11. DEPLOYMENT SPECIFICATION

### 11.1 Infrastructure

| Service | Platform | Configuration |
|---------|----------|---------------|
| Frontend | Vercel | Hobby Tier |
| Backend | Render/Railway | Free Tier, Docker |
| Database | Supabase | Free Tier (500MB) |

### 11.2 Docker Configuration

- Health check untuk memastikan PostgreSQL ready sebelum FastAPI start
- `init_sandbox.sql` di-mount ke `/docker-entrypoint-initdb.d/`
- Log directory di-mount sebagai volume

### 11.3 Deployment Pipeline

| Stage | Trigger | Approval |
|-------|---------|----------|
| Development | Local Docker Compose | None |
| Staging | Auto-deploy on push ke `staging` | None |
| Production | Manual trigger | Required |

---

## 12. TESTING & EVALUATION

### 12.1 Controlled Lab Study Design

- **Method:** Two-Group Pretest-Posttest dengan Stratified Assignment (Ablation Study)
- **Participants:** 20 mahasiswa STEI-K ITB yang telah menyelesaikan mata kuliah
  Pemodelan Basis Data. Dipilih karena familiar dengan konsep SQL, namun diasumsikan
  mengalami sebagian forgetting sehingga sistem adaptif tetap relevan.
- **Group Assignment:** Stratified berdasarkan nilai mata kuliah (A/AB/B/BC/C) untuk
  memastikan distribusi kemampuan yang seimbang antar grup. Keseimbangan diverifikasi
  menggunakan theta_initial dari pretest (Mann-Whitney U test, target p > 0.05).
  Assignment dilakukan manual oleh instruktur sebelum lab study dimulai via field
  `group_assignment` di tabel `users`.
- **Grup A (with intervention):** variance-based stagnation detection + fallback trigger
  N=8 soal aktif → peer review dipicu saat stagnation terdeteksi
- **Grup B (without intervention / ablation):** stagnation detection berjalan dan di-log
  (`stagnation_detected = TRUE`) tapi peer review **tidak** dipicu → user lanjut
  individual mode
- **Study framing:** Proof-of-concept ablation study untuk mengisolasi kontribusi
  komponen kolaboratif dalam memitigasi overpersonalization

### 12.2 Testing Phases

| Phase | Duration | Activity |
|-------|----------|----------|
| Pre-test | 15 menit | 5 soal adaptive → θ_initial sebagai baseline pengukuran NLG |
| Interaksi Sistem | 75 menit | Individual mode + peer review (Grup A) secara rolling — peer review tidak diblok ke slot waktu tersendiri, terjadi seiring berjalannya sesi saat stagnation terdeteksi |
| Post-test | 15 menit | 5 soal dari bank reserved → θ_final untuk NLG |
| **Total** | **105 menit** | |

**Catatan Grup B:** Selama fase Interaksi Sistem, Grup B tetap mengerjakan individual
mode sepanjang 75 menit tanpa intervensi peer review, meskipun stagnation terdeteksi.

### 12.3 Success Metrics

| Metric | Formula / Pengukuran | Target |
|--------|----------------------|--------|
| **Normalized Learning Gain** | `g = (post_score - pre_score) / (100 - pre_score)` — dibandingkan antara Grup A dan Grup B | g_A ≥ 0.3 dan g_A > g_B |
| **Efektivitas Mitigasi Overpersonalization** | Perbandingan slope Δθ pre-intervention vs post-intervention untuk Grup A. Slope dihitung dari 5 log terakhir sebelum dan sesudah titik `stagnation_detected = TRUE` | Slope post > Slope pre (Δθ meningkat setelah intervensi) |
| **Kontrol Grup B** | Slope Δθ pada titik yang ekuivalen dengan stagnation detection di Grup B — diharapkan tetap datar | Slope tidak meningkat secara signifikan |
| **Matching Validity** | % peer pairs dengan `\|θ_individu_reviewer - θ_individu_requester\| ≥ 0.5σ` | 100% |
| **Stagnation Trigger Rate** | % user yang mengalami `stagnation_detected = TRUE` per grup | ≥ 50% per grup (minimal 5 dari 10 user) |
| **Peer Feedback Quality** | Rata-rata `system_score` dari semua peer_sessions (Grup A) | ≥ 0.6 (validasi operasional theta_social) |
| **Response Time** | API latency p95 | ≤ 500ms |

**Catatan Peer Feedback Quality:** Metrik ini bersifat operasional — memvalidasi bahwa
`theta_social` mendapat sinyal yang bermakna, bukan bukti efektivitas sistem secara
keseluruhan.

### 12.4 Risk Mitigation

| Risk | P | I | Mitigation |
|------|---|---|------------|
| Stagnation tidak terpicu (variance only) | Rendah | Tinggi | Fallback trigger N=8 soal sebagai safety net |
| Grup tidak seimbang kemampuan awal | Rendah | Tinggi | Stratified assignment + verifikasi Mann-Whitney pada theta_initial |
| Reviewer tidak tersedia saat stagnation terpicu | Sedang | Sedang | Peer review rolling (tidak semua user stuck bersamaan); Grup B bisa jadi reviewer cadangan jika perlu |
| Tidak cukup data post-intervention untuk slope analysis | Sedang | Tinggi | Pastikan minimal 5 soal dikerjakan setelah intervensi; extend sesi ke 90 menit jika diperlukan |
| theta_social tidak converge | Tinggi | Rendah | Stated as limitation; log tersedia untuk analisis pasca-hoc |
## 13. APPENDIX: PARAMETER CALIBRATION LOG

### 13.1 ε Stagnation Threshold (Recalibrated)

Nilai ε dikalibrasi ulang dari 0.05 (dirancang untuk skala Δθ ternormalisasi) ke **165**
untuk menyesuaikan skala Elo [0, 2000] dengan K-factor K=30.

**Distribusi Δθ expected pada skala [0, 2000] dengan K=30:**

Δθ = K × (W − We)

| Skenario | W | We | Δθ |
|---|---|---|---|
| Benar attempt 1, cepat | ~1.3 | ~0.4 | +27 |
| Benar attempt 2, lambat | ~0.5 | ~0.5 | 0 |
| Salah semua | 0.0 | ~0.6 | -18 |
| Fixed point (W ≈ We) | ~0.5 | ~0.5 | ±6 |

**Kalibrasi empiris:**

| Simulation Pattern | Δθ Sequence | Variance | Decision |
|--------------------|-------------|----------|----------|
| Fixed point / konvergensi prematur | [-6, +6, -4, +5, -3] | ~25 | Harus trigger |
| Fluktuasi normal (user berkembang) | [+27, -18, +15, -12, +20] | ~310 | Tidak boleh trigger |
| **Threshold ε = 165** | — | **165** | **Midpoint [25, 310]** |

**Justifikasi:** Nilai 165 dipilih sebagai titik tengah antara batas atas variance konvergensi
prematur (~25) dan batas bawah variance fluktuasi normal (~310). Threshold ini hanya
relevan untuk chapter CH01 dan CH02 — konvergensi di CH03 tidak memicu intervensi
karena merupakan tujuan pembelajaran (lihat Section 6.3).

Dalam konteks lab study dengan K=30, ε=165 setara dengan kondisi di mana standar
deviasi Δθ secara konsisten di bawah √165 ≈ 12.8 poin selama 5 soal berturutan.

### 13.2 K-Factor (Vesin et al. 2022, verbatim)

| total_attempts | K | Fase |
|----------------|---|------|
| < 10 | 30 | Novice — responsive, cold-start |
| 10–24 | 20 | Intermediate — transisi |
| 25–49 | 15 | Advanced — mendekati konvergensi |
| ≥ 50 | 10 | Expert — stabil |

K_pretest = K_social = **30** (justified: attempts tidak akan melebihi 10 di lab study).

### 13.3 Cohen's d Threshold

d = **0.5** (medium effect size, Cohen 1988). Balance antara meaningful heterogeneity dan ketersediaan peer dalam populasi kecil.

### 13.4 Rating Scale

| Parameter | Nilai | Justifikasi |
|-----------|-------|-------------|
| Scale | [0, 2000] | Buffer di luar range empiris [500, 1500] untuk safety |
| θ_individu baseline | 1300 | Vesin et al. (2022) initial rating ProTuS |
| θ_social baseline | 1300 | Mengikuti baseline individu — tidak ada cold-start pretest untuk sosial |
| θ_display formula | `(0.8 × θ_ind) + (0.2 × θ_soc)` | Individu dominan; sosial sebagai komplemen |
| Range empiris Vesin | [1100, 1500] | n=87 active users, one semester |

**catatan:** difficulty range Equilibria diperluas ke [1000, 1800] untuk mengakomodasi theta_initial minimum dan headroom untuk CH03.

### 13.5 Success Rate — Mapping Vesin ke SQL Sandbox

| Parameter Vesin | Mapping di Equilibria | Justifikasi |
|-----------------|----------------------|-------------|
| `Ai` (successful attempts) | Jumlah attempt yang `is_correct = TRUE` di soal ini | Langsung |
| `A` (total attempts) | Total attempt di soal ini (1–3) | Langsung |
| `Tc` (correct unit tests) | 1 jika ada attempt benar, 0 jika tidak | Binary sandbox result — simplifikasi dari unit testing |
| `Tp` (performed unit tests) | Selalu 1 | Sandbox sebagai satu "unit test" per soal |
| `ai` | 0.001 | Nilai default Vesin |
| `di` | 300000ms (5 mnt) | Time limit per soal |

**Prototype limitation:** `Tc/Tp` selalu 0 atau 1 karena sandbox SQL menghasilkan binary pass/fail, bukan partial unit test results. Ini menyebabkan W praktis tereduksi menjadi `(Ai/A) × (1 + time_component)` untuk jawaban benar dan 0.0 untuk jawaban salah.

---

## 14. REFERENCES

1. Vesin, B., Mangaroska, K., Akhuseyinoglu, K., & Giannakos, M. (2022). Adaptive Assessment and Content Recommendation in Online Programming Courses: On the Use of Elo-rating. *ACM Transactions on Computing Education*, 22(3), Article 33.
2. Kerman, N. T., et al. (2024). Online peer feedback patterns of success and failure in argumentative essay writing. *Interactive Learning Environments*.
3. ACM CCECC (2023). Bloom's for Computing: Enhancing Bloom's Revised Taxonomy with Verbs for Computing Disciplines.
4. Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences* (2nd ed.).
5. Biasio, A. D., et al. (2023). On the problem of recommendation for sensitive users and influential items. *Knowledge-Based Systems*.
6. Hake, R. R. (1999). Analyzing change/gain scores. AERA/NCME.
7. Minn, S. (2022). AI-assisted knowledge assessment techniques for adaptive learning environments. *Computers and Education: Artificial Intelligence*.
8. Brusilovsky, P., et al. (2016). Open Social Student Modeling for Personalized Learning. *IEEE Transactions on Emerging Topics in Computing*.

---

**Document Version:** 4.2  
**Last Updated:** March 16, 2026  
**Author:** Dama Dhananjaya Daliman (18222047)  
**Status:** Implementation Ready