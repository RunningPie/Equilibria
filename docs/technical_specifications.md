# TECHNICAL SPECIFICATION DOCUMENT: EQUILIBRIA

Project: Prototype of Collaborative Adaptive Assessment System with Overpersonalization Mitigation  
Student: Dama Dhananjaya Daliman (18222047)  
Version: 1.0 (Final Draft)

## 0. EXECUTIVE SUMMARY

Equilibria adalah inisiatif pengembangan purwarupa sistem asesmen adaptif (Computerized Adaptive Testing) yang dirancang khusus untuk domain pendidikan Ilmu Komputer, dengan studi kasus pada materi SQL Querying. Proyek ini bertujuan untuk mengatasi keterbatasan asesmen linear tradisional yang sering kali gagal mengukur kemampuan siswa secara presisi, serta menjawab tantangan overpersonalization (isolasi konten) yang kerap muncul pada sistem adaptif modern.

Sistem ini mengimplementasikan algoritma Elo Rating System untuk kalibrasi dinamis tingkat kesulitan soal terhadap kemampuan siswa secara real-time. Sebagai fitur novelty, Equilibria memperkenalkan Mekanisme Kolaboratif Mitigasi Overpersonalization, di mana sistem secara cerdas mendeteksi stagnasi kemampuan siswa dan memicu interaksi sosial (seperti Peer Review atau Code Clash) untuk membuka wawasan siswa terhadap pendekatan penyelesaian masalah yang lebih beragam.

Secara teknis, Equilibria dibangun dengan arsitektur Client-Server yang modern dan scalable. Sisi klien (Frontend) dikembangkan menggunakan React.js untuk menjamin interaktivitas tinggi, sementara sisi peladen (Backend) ditenagai oleh Python FastAPI untuk menangani komputasi algoritma adaptif dan eksekusi query basis data yang aman. Data disimpan menggunakan PostgreSQL dengan pemisahan skema antara data operasional sistem dan lingkungan sandbox eksekusi siswa.

Dokumen ini memuat spesifikasi teknis menyeluruh mulai dari arsitektur sistem, skema basis data, logika algoritma adaptif dan kolaboratif.

## 1. System Architecture

Sistem menggunakan pola arsitektur Client-Server dalam satu repositori terpusat (Monolithic Codebase), memisahkan concern antara antarmuka pengguna dan logika bisnis.

- **Repository Pattern**: Monorepo (`/root`)
  - **Client (Frontend)**: Single Page Application (SPA) yang menangani interaksi user.
  - **Server (Backend)**: RESTful API yang menangani logika adaptif, eksekusi query aman, dan manajemen data.
- **Communication**: JSON via HTTP/HTTPS.

## 2. Technology Stack

- **Frontend**:
  - Framework: React.js (Vite build tool).
  - Styling: Tailwind CSS (untuk UI cepat dan konsisten).
  - State Management: React Context API / Zustand.
  - Code Editor: CodeMirror / Monaco Editor (untuk syntax highlighting SQL).
- **Backend**:
  - Language: Python 3.10+.
  - Framework: FastAPI (High performance, async support untuk eksekusi query).
  - ORM: SQLAlchemy (Async).
  - Data Validation: Pydantic.
- **Database**:
  - RDBMS: PostgreSQL 15+.

## 3. Database Specification

Sistem menggunakan satu instance PostgreSQL yang menampung dua skema logis terpisah untuk keamanan.

### A. Core Database (Schema: `public`)

Menyimpan data operasional sistem.

1. **Table `users`**
   - `user_id` (PK): UUID (v4)
   - `nim`: VARCHAR(20) [UNIQUE]
   - `full_name`: VARCHAR(100)
   - `password_hash`: VARCHAR
   - `current_theta`: FLOAT (Default: 0.0, Range: -3.0 s.d +3.0)
   - `k_factor`: INTEGER (Default: 32)
   - `learning_style`: VARCHAR (Opsional, jika ada kuesioner awal)

2. **Table `modules` (Submodul)**
   - `module_id`: VARCHAR(5) (PK) (e.g., `'CH01'`)
   - `title`: VARCHAR
   - `difficulty_range_min`: FLOAT
   - `difficulty_range_max`: FLOAT

3. **Table `questions` (Bank Soal)**
   - `question_id`: VARCHAR(10) (PK) (Format: CHXX-QYYY, e.g., CH01-Q005)
   - `module_id`: VARCHAR(5) (FK)
   - `content`: TEXT (Narasi soal HTML/Markdown)
   - `target_query`: TEXT (Kunci jawaban)
   - `initial_difficulty`: FLOAT ($b$ awal)
   - `current_difficulty`: FLOAT ($b$ dinamis)
   - `topic_tags`: ARRAY[VARCHAR]

4. **Table `assessment_logs` (Jejak Pengerjaan)**
   - `log_id`: SERIAL (PK)
   - `session_id`: UUID
   - `user_id`: UUID (FK)
   - `question_id`: VARCHAR(10) (FK)
   - `user_query`: TEXT
   - `is_correct`: BOOLEAN
   - `theta_before`: FLOAT
   - `difficulty_before`: FLOAT
   - `execution_time_ms`: INTEGER
   - `timestamp`: TIMESTAMP

5. **Table `peer_sessions` (Kolaboratif)**
   - `session_id`: UUID (PK)
   - `requester_id`: UUID (FK)
   - `reviewer_id`: UUID (FK)
   - `question_id`: VARCHAR(10) (FK)
   - `review_content`: TEXT
   - `submitted_at`: TIMESTAMP
   - `system_score`: FLOAT
   - `is_helpful`: boolean
   - `requester_feedback_at`: TIMESTAMP
   - `final_score`: FLOAT (gabungan system + requester)
   - `elo_change_reviewer`: FLOAT
   - `status`: ENUM (`'PENDING_REVIEW'`, `'WAITING_CONFIRMATION'`, `'COMPLETED'`)

### B. Sandbox Database (Schema: `sandbox`)

Skema read-only untuk user, berisi data dummy.

- **Tables**: `mahasiswa`, `matakuliah`, `dosen`, `frs`.
- **Security**: User koneksi database untuk eksekusi query siswa hanya memiliki hak akses `SELECT` pada skema ini.

## 4. Struktur Materi (Hierarchical Domain)

Materi SQL dibagi menjadi 3 submodul dengan rentang kesulitan ($D$) bertingkat:

1. **CH01: Basic Selection (`SELECT..WHERE`)**
   - Rentang $D$: -3.0 s.d -1.0
   - Fokus: Proyeksi kolom, filtering dasar, operator logika.

2. **CH02: Aggregation (`GROUP BY..HAVING`)**
   - Rentang $D$: -1.0 s.d +1.0
   - Fokus: Fungsi agregat (COUNT, SUM), pengelompokan, filtering hasil agregasi.

3. **CH03: Advanced Querying (CTE & JOIN)**
   - Rentang $D$: +1.0 s.d +3.0
   - Fokus: WITH clause (CTE), Subquery, Multiple Joins.

## 5. Frontend Specification (Menu Structure)

Aplikasi menggunakan Sidebar Navigation persisten.

1. **Dashboard**
   - Progress Radar: Visualisasi kompetensi di 3 submodul.
   - Elo Stats: Menampilkan $\theta$ saat ini dan peringkat (tier).
   - Quick Resume: Tombol lanjut ke modul terakhir.

2. **Coursework (Materi & Latihan)**
   - Module Tree: List CH01, CH02, CH03.
   - Content View: Tab untuk membaca materi (PDF/Text) dan Tab "Practice" (Latihan Adaptif).
   - Status Indicator: Locked/Unlocked berdasarkan mastery modul sebelumnya.

3. **Collaborative Space (Fitur Novelty)**
   - Peer Review Inbox: Daftar permintaan review dari teman yang ditugaskan sistem kepada user (sebagai Reviewer).
   - My Requests Status: Status permintaan review yang dikirim user (sebagai Requester) saat user mengalami stagnasi. Berisi balasan/komentar dari teman.

4. **Profile**
   - Info user, NIM, dan History Log pengerjaan.

5. **Settings**
   - Tema (Dark/Light), Konfigurasi Editor.

## 6. Logika Algoritma (Backend Core)

### A. Algoritma Adaptif (Adaptive Engine)

1. **Inisialisasi Sesi**:
   - User memilih Submodul.
   - Sistem set `current_theta` user (dari DB).
   - Set limit soal per sesi (e.g., 20).

2. **Seleksi Soal (Item Selection Strategy)**:
   - Candidate Pool = Ambil semua soal di Submodul aktif KECUALI yang sudah ada di `assessment_logs` user tersebut.
   - Hitung jarak: $\|D_j - \theta_{user}\|$.
   - Ambil 5 soal dengan jarak terkecil.
   - Pilih 1 secara acak (Proportional Random) untuk menghindari repetisi pola.

3. **Evaluasi Jawaban (Auto-Grader)**:
   - Run `target_query` di Sandbox DB $\rightarrow$ ExpectedResult.
   - Run `user_query` di Sandbox DB $\rightarrow$ ActualResult.
   - Logic: `is_correct` = (ExpectedResult == ActualResult). (Tangani Unordered result jika tidak ada ORDER BY).

4. **Update Elo Rating**:
   - Hitung Probabilitas: $P = \frac{1}{1 + 10^{(D - \theta)/400}}$ (Skala 400) atau logistik standar.
   - Update Siswa: $\theta_{new} = \theta_{old} + K \cdot (Score - P)$.
   - Update Soal: $D_{new} = D_{old} + K \cdot (P - Score)$.
   - Simpan ke DB.

### B. Algoritma Kolaboratif (Mitigasi Overpersonalization)

1. **Detection (Triggering)**
   - Logic: Setiap kali user menyelesaikan soal, sistem menghitung variansi perubahan estimasi kemampuan ($\Delta\theta$) dalam 5 log terakhir.
   - Condition: Jika Variansi $< \epsilon$ (User mengalami stagnasi/plateau), set status User menjadi NEEDS_PEER_REVIEW.
   - Action: Tampilkan intervensi "Sistem mendeteksi pola stagnan. Selesaikan misi review untuk membuka materi selanjutnya."

2. **Matchmaking (Constraint-Based Re-ranking)**
   - Logic: Query tabel User untuk mencari kandidat reviewer yang berstatus Idle.
   - Filtering:
     - Hapus kandidat yang sudah pernah berpasangan dengan user di soal yang sama.
     - Prioritaskan kandidat yang memiliki Disparitas Kemampuan (heterogenitas) untuk memaksimalkan pertukaran perspektif (misal: $\theta_{reviewer} > \theta_{user}$ atau sebaliknya, yang penting tidak identik).
   - Execution: Insert data ke tabel `peer_sessions` dengan status `PENDING_REVIEW`.

3. **Assessment & Reward Process (Hybrid Evaluation & Delayed Update)**

   Proses ini terjadi dalam dua tahap terpisah (Two-phase commit):

   **Tahap A: Submission & System Evaluation (Immediate)**

   1. Submission: Reviewer mengirimkan teks umpan balik (feedback) terhadap kode Requester.
   2. System Grading (NLP Sederhana): Backend melakukan analisis otomatis terhadap teks review:
      - Length Check: Apakah panjang karakter memenuhi batas minimum?
      - Keyword Matching: Apakah mengandung kata kunci konstruktif (misal: "coba", "karena", "seharusnya", "ganti")?
      - Output: Skor Sistem ($S_{sys}$) dalam skala 0.0–1.0.
   3. State Update: Status sesi berubah menjadi `WAITING_CONFIRMATION`. Requester mendapat notifikasi.

   **Tahap B: Requester Confirmation & Elo Calculation (Delayed)**

   1. Requester Feedback: Requester membaca review dan memberikan respons biner:
      - Thumbs Up (Helpful): Nilai $S_{peer} = 1.0$.
      - Thumbs Down (Not Helpful): Nilai $S_{peer} = 0.0$.
   2. Final Score Calculation ($S_{final}$):
      Sistem menggabungkan kedua nilai dengan bobot (50-50):
      $$
      S_{final} = (0.5 \times S_{sys}) + (0.5 \times S_{peer})
      $$
      (Jika Peer memberikan Thumbs Down, $S_{final}$ dapat dipenalti lebih berat).
   3. Reviewer Elo Update:
      Sistem baru memperbarui Elo Rating Reviewer menggunakan formula Two-Source:
      $$
      \theta_{new} = \theta_{old} + K_{social} \times (S_{final} - P_{expected})
      $$
      - Keterangan: Reviewer yang memberikan review bagus tapi dinilai tidak membantu oleh teman tidak akan mendapat poin maksimal.

## 7. Backend API Specification

Base URL: `/api/v1`

| Method | Endpoint                   | Input (Body/Query)       | Output (JSON)            | Deskripsi                              |
|--------|----------------------------|--------------------------|--------------------------|----------------------------------------|
| POST   | `/auth/login`              | nim, password            | token, user_detail       | Autentikasi                            |
| GET    | `/dashboard/stats`         | -                        | theta, radar_data, history | Data untuk grafik dashboard          |
| POST   | `/session/start`           | module_id                | session_token, question  | Mulai sesi, return soal pertama        |
| POST   | `/session/submit`          | session_token, q_id, query | is_correct, result_table, next_q | Submit jawaban, return soal berikutnya |
| GET    | `/collab/pending`          | -                        | list_of_requests         | Cek apakah ada tugas peer review       |
| POST   | `/collab/submit-review`    | session_id, content      | -                        | Simpan konten, jalankan NLP, update system_score, set status `WAITING_CONFIRMATION` |
| POST   | `/collab/rate-review`      | session_id, is_helpful   | -                        | Hitung final_score, jalankan Elo update untuk reviewer, set status 'COMPLETED' |
| POST   | `/auth/token`              | LoginRequest             | Token                    | Login & dapatkan JWT                   |
| GET    | `/users/me`                | Header: Bearer Token     | UserResponse             | Ambil data profile sendiri             |
| PUT    | `/users/me`                | UserUpdate               | UserResponse             | Update nama/password                   |

### 7.1. Mekanisme Retain Session (JWT)

1. Login: Frontend kirim NIM (or username) & password → Backend verify → Backend generate JWT (isinya user_id, expiration, dan version untuk token versioning) → Kirim JWT ke frontend
2. Storage: React menyimpan token (idealnya HttpOnly cookie)
3. Request: Setiap request ke API menyisipkan header: `Authorization: Bearer <token_jwt>`
4. Backend: FastAPI menggunakan dependency injection untuk mendekode token. Jika valid dan belum expired request diproses. Jika tidak return 401 Unauthorized.

### 7.2. API Response Convention

Menggunakan Generic[T] dari Python, jadi buat satu "template" di `schemas/response.py`

```python
from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel
from enum import Enum

# Definisikan Generic Type Variable
T = TypeVar('T')

class StatusEnum(str, Enum):
    SUCCESS = "success"
    FAIL = "fail"
    ERROR = "error"

# Ini Wrapper Ajaibnya
class JSendResponse(BaseModel, Generic[T]):
    status: StatusEnum
    code: int  # HTTP Status Code (200, 400, 500)
    data: Optional[T] = None  # Data spesifik (User, Question, dll)
    message: Optional[str] = None  # Untuk error message
```

Cara menggunakan di Endpoint

```python
from fastapi import APIRouter
from app.schemas.response import JSendResponse, StatusEnum
from app.schemas.users import UserResponse  # Schema user biasa

router = APIRouter()

# Perhatikan response_model ini!
@router.get("/users/me", response_model=JSendResponse[UserResponse])
async def get_current_user(current_user: UserResponse):
    # Return tetap object Pydantic, tapi dibungkus
    return JSendResponse(
        status=StatusEnum.SUCCESS,
        code=200,
        data=current_user  # Ini otomatis divalidasi sbg UserResponse
    )
```

Hasil JSON

```json
{
  "status": "success",
  "code": 200,
  "data": {
    "user_id": "uuid-1234",
    "nim": "18222047",
    "full_name": "Dama Daliman",
    "current_theta": 1.5
  },
  "message": null
}
```

Dampak pada Swagger UI  
Karena kita menggunakan `JSendResponse[UserResponse]`, Swagger UI akan Sangat Cerdas. Dia akan menampilkan dokumentasi:

- Response 200:
  - `status`: string
  - `code`: integer
  - `data`: Object (UserResponse) ← Swagger tetap bisa "membaca" isi dalamnya!

## 8. File & Repository Structure

Struktur folder untuk Backend (Python/FastAPI) dirancang modular agar mudah di-maintain.

```
equilibria-monorepo/
├── client/                 # React Frontend
│   └── src/
│       ├── components/
│       ├── pages/
│       └── services/       # Axios calls to Backend
│       └── ...
├── server/                 # Python Backend
│   └── app/
│       ├── api/            # API Routers
│       │   ├── auth.py
│       │   ├── assessment.py   # Endpoint latihan soal
│       │   └── collab.py       # Endpoint fitur sosial
│       ├── core/           # Business Logic Utama
│       │   ├── config.py
│       │   ├── elo_engine.py   # Algoritma Elo & Selection
│       │   └── security.py
│       ├── db/             # Database Interface
│       │   ├── session.py
│       │   └── models.py       # SQLAlchemy Models
│       ├── sandbox/        # Modul Eksekusi SQL Aman
│       │   ├── executor.py     # Logic run query di Sandbox schema
│       │   └── validator.py    # Cek forbidden keywords (DROP, DELETE)
│       ├── schemas/        # Pydantic Models (Request/Response)
│       │   ├── auth.py
│       │   ├── user.py
│       │   ├── response.py
│       │   ├── question.py
│       │   └── answer.py
│       └── main.py         # App Entry Point
├── requirements.txt
├── docker-compose.yml      # Container orchestration
└── README.md
```