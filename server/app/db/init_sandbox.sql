-- =====================================================
-- EQUILIBRIA SANDBOX INITIALIZATION SCRIPT
-- This script runs ONLY on first database initialization
-- =====================================================

-- 1. Create Sandbox Schema
CREATE SCHEMA IF NOT EXISTS sandbox;

-- 2. Create Sandbox Executor Role (LOGIN with password)
CREATE ROLE sandbox_executor LOGIN PASSWORD 'sandbox_pass_123';

-- 3. Grant SELECT Only on Sandbox Schema
GRANT USAGE ON SCHEMA sandbox TO sandbox_executor;
GRANT SELECT ON ALL TABLES IN SCHEMA sandbox TO sandbox_executor;

-- 4. Auto-grant for Future Tables
ALTER DEFAULT PRIVILEGES IN SCHEMA sandbox GRANT SELECT ON TABLES TO sandbox_executor;

-- 5. REVOKE Access to Public Schema (Security)
REVOKE ALL ON SCHEMA public FROM sandbox_executor;

-- 6. Create Sandbox Tables (Complete Structure per Tech Specs)
CREATE TABLE IF NOT EXISTS sandbox.mahasiswa (
    nim        VARCHAR(15)    PRIMARY KEY,
    nama       VARCHAR(100)   NOT NULL,
    jurusan    VARCHAR(10)    NOT NULL,
    angkatan   INTEGER        NOT NULL,
    ipk        DECIMAL(3,2)   CHECK (ipk BETWEEN 0.0 AND 4.0)
);

CREATE TABLE IF NOT EXISTS sandbox.matakuliah (
    kode_mk    VARCHAR(10)    PRIMARY KEY,
    nama_mk    VARCHAR(100)   NOT NULL,
    sks        INTEGER        NOT NULL,
    semester   INTEGER        NOT NULL
);

CREATE TABLE IF NOT EXISTS sandbox.dosen (
    nip        VARCHAR(20)    PRIMARY KEY,
    nama       VARCHAR(100)   NOT NULL,
    bidang     VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS sandbox.frs (
    nim        VARCHAR(15)    REFERENCES sandbox.mahasiswa(nim),
    kode_mk    VARCHAR(10)    REFERENCES sandbox.matakuliah(kode_mk),
    nip_dosen  VARCHAR(20)    REFERENCES sandbox.dosen(nip),
    semester   INTEGER        NOT NULL,
    nilai      CHAR(2)        CHECK (nilai IN ('A','AB','B','BC','C','D','E')),
    PRIMARY KEY (nim, kode_mk)
);

-- 7. Insert Comprehensive Sample Data (per Tech Specs)
INSERT INTO sandbox.dosen VALUES
('D001', 'Budi Santoso', 'Basis Data'),
('D002', 'Siti Rahayu', 'Algoritma'),
('D003', 'Ahmad Fauzi', 'Jaringan Komputer'),
('D004', 'Dewi Lestari', 'Rekayasa Perangkat Lunak'),
('D005', 'Riko Pratama', 'Kecerdasan Buatan')
ON CONFLICT (nip) DO NOTHING;

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
('IF4091', 'Tugas Akhir I', 3, 7)
ON CONFLICT (kode_mk) DO NOTHING;

INSERT INTO sandbox.mahasiswa VALUES
('18222001', 'Adi Nugroho',      'IF', 2022, 3.75),
('18222002', 'Bela Kusuma',      'IF', 2022, 2.90),
('18222003', 'Candra Wijaya',    'IF', 2022, 3.20),
('18222004', 'Diana Putri',      'IF', 2022, 3.85),
('18222005', 'Eka Saputra',      'IF', 2022, 2.45),
('18222006', 'Farhan Malik',     'IF', 2021, 3.60),
('18222007', 'Gita Ananda',      'IF', 2021, 3.10),
('18222008', 'Hendra Yusuf',     'IF', 2021, 2.75),
('18222009', 'Ira Salsabila',    'IF', 2021, 3.95),
('18222010', 'Joko Purnomo',     'IF', 2021, 3.30),
('18222011', 'Kartika Dewi',     'EL', 2022, 3.50),
('18222012', 'Lukman Hakim',     'EL', 2022, 2.60),
('18222013', 'Maya Sari',        'EL', 2022, 3.15),
('18222014', 'Naufal Rizki',     'MK', 2022, 3.70),
('18222015', 'Olivia Tanjung',   'MK', 2022, 3.40),
('18222016', 'Pandu Arifin',     'IF', 2020, 3.80),
('18222017', 'Qoriah Nisa',      'IF', 2020, 2.95),
('18222018', 'Rendi Firmansyah', 'IF', 2020, 3.25),
('18222019', 'Sari Oktaviani',   'IF', 2020, 3.65),
('18222020', 'Taufik Rahman',    'IF', 2020, 2.80),
('18222021', 'Umar Hamdani',     'IF', 2023, 3.10),
('18222022', 'Vina Melati',      'IF', 2023, 3.55),
('18222023', 'Wahyu Santoso',    'IF', 2023, 2.70),
('18222024', 'Xena Pratiwi',     'IF', 2023, 3.90),
('18222025', 'Yoga Wibisono',    'IF', 2023, 3.35),
('18222026', 'Zara Halimah',     'EL', 2021, 3.45),
('18222027', 'Aldi Firmandi',    'EL', 2021, 2.85),
('18222028', 'Bella Tristanti',  'MK', 2021, 3.20),
('18222029', 'Ciko Satria',      'MK', 2021, 3.75),
('18222030', 'Dinda Permata',    'IF', 2022, 3.00)
ON CONFLICT (nim) DO NOTHING;

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
('18222019', 'IF4091', 'D004', 7, 'AB')
ON CONFLICT (nim, kode_mk) DO NOTHING;

-- 8. Grant SELECT to equilibria_user on sandbox (for testing)
GRANT SELECT ON ALL TABLES IN SCHEMA sandbox TO equilibria_user;