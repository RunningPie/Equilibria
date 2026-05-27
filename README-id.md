# Equilibria

[![Thesis Project](https://img.shields.io/badge/Academic-Thesis%20Project-blue?style=flat-square)](#)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688?style=flat-square&logo=fastapi&logoColor=white)](#)
[![React 19](https://img.shields.io/badge/React-19.0-61DAFB?style=flat-square&logo=react&logoColor=black)](#)
[![PostgreSQL 15](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat-square&logo=postgresql&logoColor=white)](#)

> **Prototipe Sistem Penilaian Adaptif Kolaboratif dengan Mitigasi Overpersonalisasi**  
> Platform e-learning buat belajar SQL tingkat kuliah. Di dalamnya ada engine rating berbasis Elo (Vesin-aligned), deteksi stagnasi belajar secara real-time, dan pencocokan peer review secara anonim (constraint-based).

---

## 1. Tentang Proyek Ini

Sistem pembelajaran adaptif biasa (yang cuma nyesuaiin soal sama kemampuan kita) sering kali bikin kita terjebak di zona nyaman. Ini namanya **overpersonalization** atau filter bubble, kita jadi gak pernah dapet soal yang lebih bervariasi atau menantang, dan ngerasa udah jago padahal konsepnya gitu-gitu aja.

**Equilibria** hadir buat memecah gelembung itu dengan **diversifikasi kognitif**. Selain ngasih soal adaptif pakai sistem rating Elo, aplikasi ini bakal ngedeteksi kalau cara belajar kamu mulai "stagnan" (jalan di tempat). Begitu stagnasi terdeteksi, sistem bakal otomatis mencocokkan kamu secara anonim dengan temen sekelas (peer) untuk melakukan review query SQL. Jadinya, kamu gak cuma belajar sendiri tapi juga bisa dapet perspektif baru dari temenmu.

---

## 2. Arsitektur Sistem

Aplikasi ini menggunakan arsitektur terpisah (decoupled) antara Frontend (Single Page Application) dan Backend (REST API) yang terhubung dengan database PostgreSQL.

![Diagram Komunikasi Sistem](docs/communication_diagram.png)

---

## 3. Algoritma Utama

### 3.1 Perhitungan Rating Elo (Vesin-Aligned)
Sistem bakal selalu update rating kemampuanmu ($\theta$) dan tingkat kesulitan soal ($D$) setelah kamu selesai ngerjain satu soal. Rating-nya berkisar antara `1000` sampai `1800` dengan nilai awal `1300`.

*   **Success Rate ($W$):** Nilai pengerjaan soalmu ($0.0$ sampai $2.0$). Nilai ini dinilai dari jumlah attempt (maksimal 3 kali), kebenaran query di sandbox, dan bonus kalau kamu ngerjainnya cepet.
*   **Expected Score ($W_e$):** Peluang kamu bisa ngejawab soal itu dengan benar berdasarkan selisih rating-mu dan kesulitan soal.
*   **K-Factor Decay:** Nilai pengali update rating yang makin lama makin kecil seiring bertambahnya jumlah soal yang kamu kerjain `{<10 soal: 30, 10-24 soal: 20, 25-49 soal: 15, ≥50 soal: 10}` biar rating-mu makin stabil.

### 3.2 Deteksi Stagnasi
Ada dua cara sistem tahu kalau kamu lagi stagnan:
1.  **Trigger Utama (Variansi Rating):** Dihitung dari 5 pengerjaan soal terakhir secara global. Kalau variansi perubahan rating-mu ($\Delta\theta$) di bawah `165.0` (artinya grafik kemampuanmu datar), kamu dianggap stagnan.
2.  **Trigger Fallback (Safety Net):** Kalau kamu salah terus di lebih dari 4 soal dalam 8 kali pengerjaan terakhir di chapter yang sama, sistem bakal otomatis nge-trigger stagnasi biar kamu dapet bantuan review.

### 3.3 Pencarian Teman Review (Peer Matching)
Begitu statusmu berubah jadi `NEEDS_PEER_REVIEW`, sistem bakal nyari temen di grup yang sama buat ngebantu kamu:
*   **Syarat Perbedaan Rating:** Temen yang dipilih harus punya selisih rating minimal $0.5$ standard deviasi dari rating kamu (biar tingkat pemahamannya beda cukup jauh dan review-nya lebih bermakna).
*   **Pemilihan:** Dari daftar temen yang memenuhi syarat, sistem bakal milih acak dari top 5 yang punya selisih paling jauh.

### 3.4 Social Elo & Penilaian NLP
Rating sosialmu ($\theta_{\text{social}}$) dihitung secara terpisah dari rating individu:
*   **Review Anonim:** Temenmu bakal ngereview query SQL kamu secara anonim pake rubrik penilaian yang udah disediain.
*   **Sistem Penilaian Dual-Track:** Nilai review digabung antara rating dari temen yang direview ($50\%$) dan penilaian otomatis dari sistem NLP ($50\%$).
    *   *Sistem NLP:* Memakai library `fastembed` dengan model `MiniLM` buat ngecek kualitas feedback temenmu (apakah jelas, konstruktif, dan sesuai dengan kata kunci query SQL).
*   **Rating Akhir:** Rating yang ditampilin di profil dan leaderboard adalah gabungan keduanya:
    $$\theta_{\text{display}} = (0.8 \times \theta_{\text{individual}}) + (0.2 \times \theta_{\text{social}})$$

---

## 4. Teknologi yang Digunakan

### Backend (FastAPI)
*   **Framework:** FastAPI (Python 3.12) dengan fungsi-fungsi asynchronous biar responsif.
*   **Database & Migrasi:** SQLAlchemy 2.0 (async via `asyncpg`) & Alembic buat migrasi skema database.
*   **Keamanan:** JWT token buat login, hashing password memakai Argon2id.
*   **NLP Engine:** `fastembed` untuk proses embedding teks feedback peer review secara lokal di CPU server.

### Frontend (React 19)
*   **Build Tool:** Vite (TypeScript).
*   **Styling:** Tailwind CSS 4.x untuk desain antarmuka modern dan responsif.
*   **State Management:** Zustand + Zukeeper buat nge-track state aplikasi di browser.
*   **Code Editor:** CodeMirror 6 dengan syntax highlighting SQL.
*   **Avatar:** DiceBear API untuk nge-generate avatar unik secara otomatis berdasarkan NIM mahasiswa.

### Database (PostgreSQL 15)
*   **Skema Public:** Menyimpan data akun user, rating, riwayat pengerjaan soal, dan data kolaborasi.
*   **Skema Sandbox:** Terisolasi khusus untuk nyimpen tabel-tabel data perkuliahan (klasik Silberschatz) tempat mahasiswa mengeksekusi query SQL mereka secara aman.

---

## 5. Struktur Direktori Projek

```text
Equilibria/
├── client/                     # Kode Frontend React 19
│   ├── src/
│   │   ├── assets/             # Gambar & aset statis
│   │   ├── components/         # Komponen UI: Auth Guards, query display, modal, toast
│   │   ├── data/               # Bahan bacaan modul (format Markdown)
│   │   ├── hooks/              # State managemen toast
│   │   ├── pages/              # Halaman Dashboard, pengerjaan soal, peer review hub, pretest, dll.
│   │   ├── routes/             # Setup routing halaman
│   │   ├── services/           # API Client (Axios wrapper)
│   │   ├── store/              # Global state (auth & session)
│   │   └── types/              # Deklarasi Type/Interface TypeScript
│   ├── package.json
│   └── vite.config.ts
├── server/                     # Kode Backend FastAPI
│   ├── app/
│   │   ├── api/                # Router endpoint API (auth, modul, kolaborasi, admin)
│   │   ├── core/               # Konfigurasi aplikasi, keamanan, engine Elo, & NLP
│   │   ├── db/                 # Model database, session builder, dan script seeder data
│   │   ├── schemas/            # Skema validasi Pydantic (request & response)
│   │   └── tests/              # File unit test server
│   ├── alembic/                # File migrasi database
│   ├── logs/                   # Log pengerjaan mahasiswa & sistem (format JSON)
│   ├── docker-compose.yml      # Setup Docker container lokal
│   ├── Dockerfile
│   └── requirements.txt
├── docs/                       # Dokumen Tugas Akhir, PRD, dan spesifikasi teknis
├── LICENSE                     # Lisensi Projek
└── README.md
```

---

## 6. Cara Menjalankan Aplikasi di Lokal

### 6.1 Persyaratan Sistem
Pastikan laptop/komputer kamu sudah terinstall:
*   [Docker Desktop](https://www.docker.com/products/docker-desktop/)
*   [Node.js (v18+)](https://nodejs.org/) & `npm`
*   [Python 3.12+](https://www.python.org/downloads/) (opsional, jika ingin running backend tanpa Docker)

### 6.2 Menjalankan Backend (Docker)
1. Masuk ke direktori `server/`:
   ```bash
   cd server
   ```
2. Copy template environment variables:
   ```bash
   cp .env.example .env
   cp .env.db.example .env.db
   ```
3. Nyalakan database PostgreSQL dan server FastAPI:
   ```bash
   docker compose up --build -d
   ```
4. Jalankan migrasi database biar tabelnya terbuat otomatis:
   ```bash
   docker compose exec backend alembic upgrade head
   ```
5. Isi database dengan soal-soal adaptif dan data pretest:
   ```bash
   docker compose exec backend python -m app.db.seed_sql_questions
   ```
   *Catatan: Script ini bakal membuat skema public dan sekaligus mengisi tabel perkuliahan (Silberschatz) di skema sandbox secara otomatis.*

### 6.3 Menjalankan Frontend
1. Masuk ke direktori `client/`:
   ```bash
   cd ../client
   ```
2. Install semua library pendukung:
   ```bash
   npm install
   ```
3. Jalankan server lokal:
   ```bash
   npm run dev
   ```
4. Buka browser dan akses [http://localhost:5173](http://localhost:5173).

---

## 7. Keamanan Sandbox SQL

Biar mahasiswa gak bisa nge-drop tabel, ngintip jawaban, atau merusak data mahasiswa lain saat ngerjain query SQL, Equilibria menerapkan beberapa mekanisme keamanan:

> **1. Isolasi Akun & Skema**
> Eksekusi query mahasiswa menggunakan user database khusus bernama `sandbox_executor`. Akun ini cuma punya hak akses `SELECT` di skema `sandbox`. Akun ini sama sekali tidak bisa membaca atau memodifikasi tabel di skema `public` yang berisi data akun, password, dan rating mahasiswa.

> **2. Pemblokiran Keyword Berbahaya**
> Sebelum query SQL mahasiswa dikirim ke database, sistem backend bakal nge-cek query tersebut memakai regex. Kalau ada kata kunci berbahaya seperti:
> `DROP`, `DELETE`, `INSERT`, `UPDATE`, `ALTER`, `CREATE`, `TRUNCATE`, `GRANT`, `REVOKE`, `PG_`, `--`
> pengerjaan bakal langsung ditolak tanpa dieksekusi di database.

> **3. Timeout Eksekusi**
> Untuk mencegah mahasiswa menulis query yang gak beres (misalnya cross join tanpa limit yang bikin server hang), backend membatasi durasi eksekusi query maksimal 5 detik saja:
> ```sql
> SET LOCAL statement_timeout = 5000; -- Putus koneksi jika query berjalan > 5 detik
> ```

---

## 8. Desain Eksperimen Lab Study

Aplikasi ini dibuat untuk skenario pengujian Tugas Akhir dengan desain eksperimen:
*   **Format Pengujian:** Eksperimen 105 menit (15m pretest adaptif → 75m pengerjaan soal di sistem → 15m posttest).
*   **Grup A (Kelompok Uji):** Dapet sistem penuh. Kalau belajarnya stagnan, bakal masuk ke mode kolaboratif (peer review) dan dihitung Social Elo-nya.
*   **Grup B (Kelompok Kontrol):** Stagnasinya cuma dicatat di database secara diam-diam. Mereka tetep lanjut ngerjain soal adaptif biasa tanpa ada intervensi peer review.
*   **Metrik Penilaian:** Normalized Learning Gain (NLG) ($g \geq 0.3$), analisis slope/kemiringan peningkatan rating sebelum vs sesudah intervensi, Cohen's $d$ untuk validasi pencocokan peer, dan skor NLP dari feedback review.

---

## 9. Referensi Akademik

*   **Vesin, B., dkk. (2022).** *Adaptive Assessment and Content Recommendation in Online Programming Courses.* Acuan utama untuk engine penilaian adaptif Elo, perhitungan success rate ($W$), dan adaptasi $K$-factor decay.
*   **Biasio, M., dkk. (2023).** *Algorithmic Filter Bubble Mitigation.* Dasar pencocokan peer review untuk memitigasi echo chamber berdasarkan Cohen’s $d \geq 0.5$.
*   **Kerman, J., dkk. (2024).** *Peer Feedback Assessment Rubric.* Acuan rubrik feedback (Identification, Justification, Constructive, Bloom’s Verbs) yang divalidasi memakai sentence embeddings.
*   **Silberschatz, A., Korth, H. F., & Sudarshan, S. (2019).** *Database System Concepts.* Sumber skema database universitas klasik yang dipakai sebagai basis soal di skema sandbox SQL.

---
