-- =====================================================
-- EQUILIBRIA SANDBOX INITIALIZATION SCRIPT
-- This script runs ONLY on first database initialization
-- =====================================================

-- 1. Create Sandbox Schema
CREATE SCHEMA IF NOT EXISTS sandbox;

-- 2. Create Sandbox Executor Role (NO LOGIN)
CREATE ROLE sandbox_executor NOLOGIN;

-- 3. Grant SELECT Only on Sandbox Schema
GRANT USAGE ON SCHEMA sandbox TO sandbox_executor;
GRANT SELECT ON ALL TABLES IN SCHEMA sandbox TO sandbox_executor;

-- 4. Auto-grant for Future Tables
ALTER DEFAULT PRIVILEGES IN SCHEMA sandbox GRANT SELECT ON TABLES TO sandbox_executor;

-- 5. REVOKE Access to Public Schema (Security)
REVOKE ALL ON SCHEMA public FROM sandbox_executor;

-- 6. Create Dummy Tables for Sandbox
CREATE TABLE IF NOT EXISTS sandbox.mahasiswa (
    nim VARCHAR(20) PRIMARY KEY,
    nama VARCHAR(100),
    ipk FLOAT
);

CREATE TABLE IF NOT EXISTS sandbox.matakuliah (
    kode_mk VARCHAR(10) PRIMARY KEY,
    nama_mk VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS sandbox.dosen (
    nip VARCHAR(20) PRIMARY KEY,
    nama VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS sandbox.frs (
    nim VARCHAR(20),
    kode_mk VARCHAR(10),
    semester INTEGER,
    PRIMARY KEY (nim, kode_mk, semester)
);

-- 7. Insert Dummy Data
INSERT INTO sandbox.mahasiswa (nim, nama, ipk) VALUES 
('18222047', 'Dama Dhananjaya', 3.75),
('18222048', 'John Doe', 3.80),
('18222049', 'Jane Smith', 3.50),
('18222050', 'Bob Wilson', 3.25),
('18222051', 'Alice Brown', 3.90)
ON CONFLICT (nim) DO NOTHING;

INSERT INTO sandbox.matakuliah (kode_mk, nama_mk) VALUES 
('IF1210', 'Algoritma dan Pemrograman'),
('IF2110', 'Basis Data'),
('IF2111', 'Basis Data Lanjut'),
('IF3110', 'Sistem Basis Data')
ON CONFLICT (kode_mk) DO NOTHING;

INSERT INTO sandbox.dosen (nip, nama) VALUES 
('196404301989031005', 'Windy Gambetta'),
('198001012005011001', 'Dosen Basis Data')
ON CONFLICT (nip) DO NOTHING;

-- 8. Grant SELECT to equilibria_user on sandbox (for testing)
GRANT SELECT ON ALL TABLES IN SCHEMA sandbox TO equilibria_user;