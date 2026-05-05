# server/scripts/seed_sql_questions.py
"""
SQL Questions Seeding Script
Creates modules and SQL questions for adaptive assessment system.
Usage: python -m scripts.seed_sql_questions
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.db.base import Base
from app.db.models.module import Module
from app.db.models.question import Question
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


MODULES_DATA = [
    {
        "module_id": "CH01",
        "title": "Basic Selection",
        "description": "SELECT, WHERE, and basic filtering operations",
        "difficulty_min": 1000.0,
        "difficulty_max": 1400.0,
        "unlock_theta_threshold": 0.0,  # Always open
        "order_index": 1,
        "content_html": "<h1>Basic Selection</h1><p>Learn SELECT and WHERE clauses...</p>",
    },
    {
        "module_id": "CH02",
        "title": "Aggregation",
        "description": "GROUP BY, HAVING, and aggregate functions",
        "difficulty_min": 1200.0,
        "difficulty_max": 1600.0,
        "unlock_theta_threshold": 1300.0,
        "order_index": 2,
        "content_html": "<h1>Aggregation</h1><p>Learn GROUP BY and aggregate functions...</p>",
    },
    {
        "module_id": "CH03",
        "title": "Advanced Querying",
        "description": "JOINs, Subqueries, and CTEs",
        "difficulty_min": 1400.0,
        "difficulty_max": 1800.0,
        "unlock_theta_threshold": 1500.0,
        "order_index": 3,
        "content_html": "<h1>Advanced Querying</h1><p>Learn JOINs and subqueries...</p>",
    },
]


QUESTIONS_DATA = [
    # ========== CH01: Basic Selection & Filtering (25 questions, Theta 1000-1380) ==========
    {
        "question_id": "CH01-Q001",
        "module_id": "CH01",
        "content": "Tampilkan seluruh data yang ada pada tabel `student`. Gampang sih, tinggal SELECT aja!",
        "target_query": "SELECT * FROM student;",
        "initial_difficulty": 1000.0,
        "current_difficulty": 1000.0,
        "topic_tags": ["SELECT", "ALL"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q002",
        "module_id": "CH01",
        "content": "Kita butuh daftar nama semua mahasiswa dan total SKS (SKS) mereka buat laporan akademik.",
        "target_query": "SELECT name, tot_cred FROM student;",
        "initial_difficulty": 1015.0,
        "current_difficulty": 1015.0,
        "topic_tags": ["SELECT", "COLUMN"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q003",
        "module_id": "CH01",
        "content": "Nona Angelin pengen liat siapa saja mahasiswa yang total SKSnya nggak nol alias udah punya SKS terakumulasi. Bantuin dong!",
        "target_query": "SELECT * FROM student WHERE tot_cred <> 0;",
        "initial_difficulty": 1030.0,
        "current_difficulty": 1030.0,
        "topic_tags": ["SELECT", "WHERE", "COMPARISON"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q004",
        "module_id": "CH01",
        "content": "TU katanya mau liat data mahasiswa dari departemen 'Comp. Sci.'. Bantu filter dong biar lebih rapih.",
        "target_query": "SELECT * FROM student WHERE dept_name = 'Comp. Sci.';",
        "initial_difficulty": 1045.0,
        "current_difficulty": 1045.0,
        "topic_tags": ["SELECT", "WHERE", "EQUALITY"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q005",
        "module_id": "CH01",
        "content": "Dosen-dosen yang departemennya 'Comp. Sci.' lagi dikumpulin buat rapat. Tampilkan siapa saja nama mereka dan departemennya.",
        "target_query": "SELECT name, dept_name FROM instructor WHERE dept_name = 'Comp. Sci.';",
        "initial_difficulty": 1060.0,
        "current_difficulty": 1060.0,
        "topic_tags": ["SELECT", "WHERE", "COLUMN"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q006",
        "module_id": "CH01",
        "content": "Kampus kita lagi ngadain survei nih. Kita mau tau judul mata kuliah apa aja yang ditawarkan. Bantuin buat daftarnya dong!",
        "target_query": "SELECT DISTINCT title FROM course;",
        "initial_difficulty": 1075.0,
        "current_difficulty": 1075.0,
        "topic_tags": ["SELECT", "DISTINCT"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q007",
        "module_id": "CH01",
        "content": "Mahasiswa yang namanya mulai dari huruf 'Z' doang yang ikut acara hari ini. Cari yang namanya AWAL dengan 'Z' ya!",
        "target_query": "SELECT * FROM student WHERE name LIKE 'Z%';",
        "initial_difficulty": 1090.0,
        "current_difficulty": 1090.0,
        "topic_tags": ["SELECT", "WHERE", "LIKE"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q008",
        "module_id": "CH01",
        "content": "Kita mau ngasih kado ke mahasiswa yang nama belakangnya 'ez'. Bantuin cari yang namanya BERAKHIRAN 'ez' dong.",
        "target_query": "SELECT * FROM student WHERE name LIKE '%ez';",
        "initial_difficulty": 1105.0,
        "current_difficulty": 1105.0,
        "topic_tags": ["SELECT", "WHERE", "LIKE"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q009",
        "module_id": "CH01",
        "content": "Mahasiswa dari departemen 'Comp. Sci.' atau 'Physics' aja yang mau kita ajak survei. Kedua departemen itu penting banget buat proyek ini. Coba bantu buatin querynya.",
        "target_query": "SELECT * FROM student WHERE dept_name IN ('Comp. Sci.', 'Physics');",
        "initial_difficulty": 1120.0,
        "current_difficulty": 1120.0,
        "topic_tags": ["SELECT", "WHERE", "IN"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q010",
        "module_id": "CH01",
        "content": "Total SKS antara 50 sampai 100 itu range yang cukup bagus. Tunjukkan mahasiswa di range itu aja.",
        "target_query": "SELECT * FROM student WHERE tot_cred BETWEEN 50 AND 100;",
        "initial_difficulty": 1135.0,
        "current_difficulty": 1135.0,
        "topic_tags": ["SELECT", "WHERE", "BETWEEN"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q011",
        "module_id": "CH01",
        "content": "Kita perlu tahu siapa saja mahasiswa yang belum punya total SKS alias 0 (treat as NULL concept) nih. Bantuin filter dong.",
        "target_query": "SELECT * FROM student WHERE tot_cred = 0;",
        "initial_difficulty": 1150.0,
        "current_difficulty": 1150.0,
        "topic_tags": ["SELECT", "WHERE", "NULL"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q012",
        "module_id": "CH01",
        "content": "Kita juga perlu tahu siapa saja mahasiswa yang total SKSnya SUDAH ADA dan nggak 0.",
        "target_query": "SELECT * FROM student WHERE tot_cred > 0;",
        "initial_difficulty": 1165.0,
        "current_difficulty": 1165.0,
        "topic_tags": ["SELECT", "WHERE", "NOT NULL"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q013",
        "module_id": "CH01",
        "content": "Urutkan mahasiswa berdasarkan total SKS tertinggi. Kita mau buat dean's list!",
        "target_query": "SELECT * FROM student ORDER BY tot_cred DESC;",
        "initial_difficulty": 1180.0,
        "current_difficulty": 1180.0,
        "topic_tags": ["SELECT", "ORDER BY", "DESC"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q014",
        "module_id": "CH01",
        "content": "Bisa tolong tunjukin mata kuliah yang punya SKS lebih dari 3? Terus dibuat terurut berdasarkan JUDUL secara ascending... A-Z gitu lohh.",
        "target_query": "SELECT * FROM course WHERE credits > 3 ORDER BY title ASC;",
        "initial_difficulty": 1195.0,
        "current_difficulty": 1195.0,
        "topic_tags": ["SELECT", "WHERE", "ORDER BY", "ASC"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q015",
        "module_id": "CH01",
        "content": "Kapasitas ruangan kampus lagi disurvei nih. Cari bangunan dengan kapasitas > 150, urutin dari yang paling gede.",
        "target_query": "SELECT building, room_no, capacity FROM classroom WHERE capacity > 150 ORDER BY capacity DESC;",
        "initial_difficulty": 1210.0,
        "current_difficulty": 1210.0,
        "topic_tags": ["SELECT", "WHERE", "ORDER BY", "COMPARISON"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q016",
        "module_id": "CH01",
        "content": "Fakultas sedang mempertimbangkan untuk menggandakan SKS mata kuliah tertentu. Coba tampilin kode matkul, SKS lama, dan SKS baru kalau SKS mata kuliah yang ada dikali 2. Kasih alias `double_credits` biar jelas!",
        "target_query": "SELECT course_id, credits, (credits * 2) AS double_credits FROM course;",
        "initial_difficulty": 1225.0,
        "current_difficulty": 1225.0,
        "topic_tags": ["SELECT", "ARITHMETIC", "ALIAS"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q017",
        "module_id": "CH01",
        "content": "Mahasiswa departemen 'Comp. Sci.' ATAU yang total SKSnya < 50 bisa ikut program beasiswa ini. Tolong cariin dong siapa aja itu",
        "target_query": "SELECT * FROM student WHERE dept_name = 'Comp. Sci.' OR tot_cred < 50;",
        "initial_difficulty": 1240.0,
        "current_difficulty": 1240.0,
        "topic_tags": ["SELECT", "WHERE", "OR"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q018",
        "module_id": "CH01",
        "content": "Panitia hackathon mau melakukan pre-filter calon perwakilan. Syaratnya mahasiswa 'Comp. Sci.' dengan total SKS > 80, dua-duanya harus terpenuhi buat masuk tim utama.",
        "target_query": "SELECT * FROM student WHERE dept_name = 'Comp. Sci.' AND tot_cred > 80;",
        "initial_difficulty": 1255.0,
        "current_difficulty": 1255.0,
        "topic_tags": ["SELECT", "WHERE", "AND"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q019",
        "module_id": "CH01",
        "content": "Coba tunjukin ada gak sih dosen dengan gaji antara 60rb dan 90rb? jangan lupa cek yang salary-nya nggak NULL ya!",
        "target_query": "SELECT * FROM instructor WHERE salary BETWEEN 60000 AND 90000 AND salary IS NOT NULL;",
        "initial_difficulty": 1270.0,
        "current_difficulty": 1270.0,
        "topic_tags": ["SELECT", "WHERE", "BETWEEN", "IS NOT NULL"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q020",
        "module_id": "CH01",
        "content": "Kombinasi building dan room_no yang unik aja dong.",
        "target_query": "SELECT DISTINCT building, room_no FROM classroom;",
        "initial_difficulty": 1285.0,
        "current_difficulty": 1285.0,
        "topic_tags": ["SELECT", "DISTINCT", "MULTI-COLUMN"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q021",
        "module_id": "CH01",
        "content": "Rudi penasaran siapa saja mahasiswa yang namanya setidaknya mengandung 2 kata (berarti ada spasi) dan berakhiran huruf 'n'",
        "target_query": "SELECT * FROM student WHERE name LIKE '% %' AND name LIKE '%n';",
        "initial_difficulty": 1300.0,
        "current_difficulty": 1300.0,
        "topic_tags": ["SELECT", "WHERE", "LIKE", "AND"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q022",
        "module_id": "CH01",
        "content": "Coba cari mata kuliah yang TIDAK mengandung kata 'Intro' di judulnya dan SKS-nya <= 3.",
        "target_query": "SELECT * FROM course WHERE title NOT LIKE '%Intro%' AND credits <= 3;",
        "initial_difficulty": 1315.0,
        "current_difficulty": 1315.0,
        "topic_tags": ["SELECT", "WHERE", "NOT LIKE", "COMPARISON"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q023",
        "module_id": "CH01",
        "content": "Kampus sedang mau liat daftar dosen dan mata kuliah yang mereka ajar. Bisa bantu cariin? Tolong diurutkan berdasarkan nama dosen ASC dan course_id ASC",
        "target_query": "SELECT i.name, t.course_id FROM instructor i, teaches t WHERE i.ID = t.ID ORDER BY i.name ASC, t.course_id ASC;",
        "initial_difficulty": 1330.0,
        "current_difficulty": 1330.0,
        "topic_tags": ["SELECT", "IMPLICIT JOIN", "ORDER BY"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q024",
        "module_id": "CH01",
        "content": "Coba ada fakultas apa aja sih yang name nya mengandung kata subkata 'tech' dan budgetnya > 10jt!",
        "target_query": "SELECT * FROM department WHERE dept_name LIKE '%tech%' AND budget > 10000000;",
        "initial_difficulty": 1345.0,
        "current_difficulty": 1345.0,
        "topic_tags": ["SELECT", "WHERE", "LIKE", "COMPARISON"],
        "is_active": True,
    },
    {
        "question_id": "CH01-Q025",
        "module_id": "CH01",
        "content": "Coba tampilkan semua mata kuliah (course), semester, serta tahun kelasnya (section). Semua atribut dari course harus ditampilkan",
        "target_query": "SELECT c.*, s.semester, s.year FROM course c, section s WHERE c.course_id = s.course_id;",
        "initial_difficulty": 1380.0,
        "current_difficulty": 1380.0,
        "topic_tags": ["SELECT", "IMPLICIT JOIN", "MULTI-TABLE"],
        "is_active": True,
    },

    # ========== CH02: Aggregation & Grouping (25 questions, Theta 1200-1580) ==========
    {
        "question_id": "CH02-Q001",
        "module_id": "CH02",
        "content": "Tolong hitung dong total semua mahasiswa yang terdaftar di sistem kita. Cukup tampilkan kolom count-nya saja ya!",
        "target_query": "SELECT COUNT(*) FROM student;",
        "initial_difficulty": 1200.0,
        "current_difficulty": 1200.0,
        "topic_tags": ["COUNT", "AGGREGATE"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q002",
        "module_id": "CH02",
        "content": "Tolong tampilin nama departemen dan jumlah mahasiswa (alias jumlah_mhs) di setiap departemen tersebut. Kita pengen tau departemen mana yang favorit.",
        "target_query": "SELECT dept_name, COUNT(*) AS jumlah_mhs FROM student GROUP BY dept_name;",
        "initial_difficulty": 1215.0,
        "current_difficulty": 1215.0,
        "topic_tags": ["COUNT", "GROUP BY"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q003",
        "module_id": "CH02",
        "content": "Dosen-dosen penasaran nih, tolong tampilkan nama departemen dan berapa rata-rata total SKS mahasiswa di tiap departemen tersebut.",
        "target_query": "SELECT dept_name, AVG(tot_cred) FROM student GROUP BY dept_name;",
        "initial_difficulty": 1230.0,
        "current_difficulty": 1230.0,
        "topic_tags": ["AVG", "GROUP BY"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q004",
        "module_id": "CH02",
        "content": "Kita mau cari bintang kampus! Coba tampilkan nama departemen dan total SKS tertinggi (alias max_sks) di masing-masing departemen.",
        "target_query": "SELECT dept_name, MAX(tot_cred) AS max_sks FROM student GROUP BY dept_name;",
        "initial_difficulty": 1245.0,
        "current_difficulty": 1245.0,
        "topic_tags": ["MAX", "GROUP BY"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q005",
        "module_id": "CH02",
        "content": "Biasanya semester berapa sih yang beban matakuliahnya paling enteng? Coba tampilkan nama semester dan SKS paling kecil di tiap semester tersebut.",
        "target_query": "SELECT semester, MIN(credits) FROM course JOIN section ON course.course_id = section.course_id GROUP BY semester;",
        "initial_difficulty": 1260.0,
        "current_difficulty": 1260.0,
        "topic_tags": ["MIN", "GROUP BY"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q006",
        "module_id": "CH02",
        "content": "Tolong rekap nama departemen dan total SKS yang ditawarkan di masing-masing departemen tersebut.",
        "target_query": "SELECT dept_name, SUM(credits) FROM course GROUP BY dept_name;",
        "initial_difficulty": 1275.0,
        "current_difficulty": 1275.0,
        "topic_tags": ["SUM", "GROUP BY"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q007",
        "module_id": "CH02",
        "content": "Tampilkan nama semester, tahun, dan jumlah mata kuliah (alias jumlah_course) yang dibuka pada periode tersebut.",
        "target_query": "SELECT semester, year, COUNT(*) AS jumlah_course FROM section GROUP BY semester, year;",
        "initial_difficulty": 1290.0,
        "current_difficulty": 1290.0,
        "topic_tags": ["COUNT", "GROUP BY", "MULTI-COLUMN"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q008",
        "module_id": "CH02",
        "content": "Coba hitung rata-rata budget untuk departemen-departemen yang ada di gedung 'Taylor'. Tampilkan kolom rata-ratanya saja.",
        "target_query": "SELECT AVG(budget) FROM department WHERE building = 'Taylor';",
        "initial_difficulty": 1305.0,
        "current_difficulty": 1305.0,
        "topic_tags": ["AVG", "WHERE"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q009",
        "module_id": "CH02",
        "content": "Tampilkan nama departemen dan total SKS mata kuliahnya untuk departemen yang total SKS-nya sudah lebih dari 10.",
        "target_query": "SELECT dept_name, SUM(credits) FROM course GROUP BY dept_name HAVING SUM(credits) > 10;",
        "initial_difficulty": 1320.0,
        "current_difficulty": 1320.0,
        "topic_tags": ["SUM", "GROUP BY", "HAVING"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q010",
        "module_id": "CH02",
        "content": "Tunjukkan nama gedung dan rata-rata kapasitasnya, khusus untuk gedung yang punya rata-rata kapasitas di atas 80 orang.",
        "target_query": "SELECT building, AVG(capacity) FROM classroom GROUP BY building HAVING AVG(capacity) > 80;",
        "initial_difficulty": 1335.0,
        "current_difficulty": 1335.0,
        "topic_tags": ["AVG", "GROUP BY", "HAVING"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q011",
        "module_id": "CH02",
        "content": "Tampilkan nama departemen dan jumlah dosen di tiap departemen tersebut, lalu urutkan dari yang paling banyak personilnya.",
        "target_query": "SELECT dept_name, COUNT(ID) FROM instructor GROUP BY dept_name ORDER BY COUNT(ID) DESC;",
        "initial_difficulty": 1350.0,
        "current_difficulty": 1350.0,
        "topic_tags": ["COUNT", "GROUP BY", "ORDER BY"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q012",
        "module_id": "CH02",
        "content": "Tampilkan nama departemen yang berani ngasih gaji dosen paling tinggi (di atas 90 ribu).",
        "target_query": "SELECT dept_name FROM instructor GROUP BY dept_name HAVING MAX(salary) > 90000;",
        "initial_difficulty": 1365.0,
        "current_difficulty": 1365.0,
        "topic_tags": ["MAX", "GROUP BY", "HAVING"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q013",
        "module_id": "CH02",
        "content": "Ada berapa banyak sih mahasiswa unik yang ngambil mata kuliah di tahun 2009? Tampilkan kolom count-nya saja.",
        "target_query": "SELECT COUNT(DISTINCT ID) FROM takes WHERE year = 2009;",
        "initial_difficulty": 1380.0,
        "current_difficulty": 1380.0,
        "topic_tags": ["COUNT", "DISTINCT", "WHERE"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q014",
        "module_id": "CH02",
        "content": "Coba hitung rata-rata total SKS untuk mahasiswa yang sudah punya lebih dari 50 SKS. Tampilkan kolom rata-ratanya saja.",
        "target_query": "SELECT AVG(tot_cred) FROM student WHERE tot_cred > 50;",
        "initial_difficulty": 1395.0,
        "current_difficulty": 1395.0,
        "topic_tags": ["AVG", "WHERE"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q015",
        "module_id": "CH02",
        "content": "Tolong tampilkan ID dosen dan berapa banyak mata kuliah yang mereka ajar masing-masing.",
        "target_query": "SELECT t.ID, COUNT(c.course_id) FROM teaches t JOIN course c ON t.course_id = c.course_id GROUP BY t.ID;",
        "initial_difficulty": 1410.0,
        "current_difficulty": 1410.0,
        "topic_tags": ["COUNT", "JOIN", "GROUP BY"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q016",
        "module_id": "CH02",
        "content": "Tampilkan judul mata kuliah beserta total mahasiswa yang terdaftar di setiap mata kuliah tersebut.",
        "target_query": "SELECT c.title, COUNT(t.ID) FROM takes t JOIN course c ON t.course_id = c.course_id GROUP BY c.title;",
        "initial_difficulty": 1425.0,
        "current_difficulty": 1425.0,
        "topic_tags": ["COUNT", "JOIN", "GROUP BY"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q017",
        "module_id": "CH02",
        "content": "Tampilkan nama departemen yang punya dosen lebih dari 2 orang.",
        "target_query": "SELECT dept_name FROM instructor GROUP BY dept_name HAVING COUNT(ID) > 2;",
        "initial_difficulty": 1440.0,
        "current_difficulty": 1440.0,
        "topic_tags": ["COUNT", "GROUP BY", "HAVING"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q018",
        "module_id": "CH02",
        "content": "Tampilkan nama departemen dan rata-rata gaji dosennya, khusus untuk departemen yang berada di bawah naungan fakultas dengan budget di atas 150 ribu.",
        "target_query": "SELECT dept_name, AVG(salary) FROM instructor WHERE dept_name IN (SELECT dept_name FROM department WHERE budget > 150000) GROUP BY dept_name;",
        "initial_difficulty": 1455.0,
        "current_difficulty": 1455.0,
        "topic_tags": ["AVG", "WHERE", "SUBQUERY", "GROUP BY"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q019",
        "module_id": "CH02",
        "content": "Daftarkan nama departemen, jumlah mata kuliah, dan rata-rata SKS-nya untuk departemen yang rata-rata SKS mata kuliahnya 3 ke atas.",
        "target_query": "SELECT dept_name, COUNT(*), AVG(credits) FROM course GROUP BY dept_name HAVING AVG(credits) >= 3;",
        "initial_difficulty": 1470.0,
        "current_difficulty": 1470.0,
        "topic_tags": ["AVG", "COUNT", "GROUP BY", "HAVING"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q020",
        "module_id": "CH02",
        "content": "Tampilkan nama mahasiswa, total SKS, and klasifikasinya (alias classification) berdasarkan aturan: <30 'Freshman', 30-59 'Sophomore', 60-89 'Junior', sisanya 'Final Year'.",
        "target_query": "SELECT name, tot_cred, CASE WHEN tot_cred < 30 THEN 'Freshman' WHEN tot_cred BETWEEN 30 AND 59 THEN 'Sophomore' WHEN tot_cred BETWEEN 60 AND 89 THEN 'Junior' ELSE 'Final Year' END AS classification FROM student;",
        "initial_difficulty": 1485.0,
        "current_difficulty": 1485.0,
        "topic_tags": ["CASE", "SELECT"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q021",
        "module_id": "CH02",
        "content": "Tampilkan ID jadwal (time slot) and berapa banyak kelas yang menggunakan jadwal tersebut, untuk jadwal yang setidaknya digunakan oleh satu kelas.",
        "target_query": "SELECT ts.time_slot_id, COUNT(*) FROM time_slot ts LEFT JOIN section s ON ts.time_slot_id = s.time_slot_id GROUP BY ts.time_slot_id HAVING COUNT(*) > 0;",
        "initial_difficulty": 1500.0,
        "current_difficulty": 1500.0,
        "topic_tags": ["COUNT", "LEFT JOIN", "GROUP BY", "HAVING"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q022",
        "module_id": "CH02",
        "content": "Tampilkan nama departemen and rata-rata total SKS (alias avg_cred) mahasiswa untuk 3 departemen dengan rata-rata tertinggi.",
        "target_query": "SELECT dept_name, AVG(tot_cred) AS avg_cred FROM student GROUP BY dept_name ORDER BY avg_cred DESC LIMIT 3;",
        "initial_difficulty": 1515.0,
        "current_difficulty": 1515.0,
        "topic_tags": ["AVG", "GROUP BY", "ORDER BY", "LIMIT"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q023",
        "module_id": "CH02",
        "content": "Tolong tampilkan nama gedung and total budget departemen di gedung tersebut, khusus untuk gedung yang total budget-nya di atas 50 ribu.",
        "target_query": "SELECT building, SUM(budget) FROM department GROUP BY building HAVING SUM(budget) > 50000;",
        "initial_difficulty": 1530.0,
        "current_difficulty": 1530.0,
        "topic_tags": ["SUM", "GROUP BY", "HAVING"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q024",
        "module_id": "CH02",
        "content": "Tampilkan kode mata kuliah, ID kelas, semester, tahun, and jumlah mahasiswa unik di setiap kelas tersebut.",
        "target_query": "SELECT course_id, sec_id, semester, year, COUNT(DISTINCT ID) FROM takes GROUP BY course_id, sec_id, semester, year;",
        "initial_difficulty": 1545.0,
        "current_difficulty": 1545.0,
        "topic_tags": ["COUNT", "DISTINCT", "GROUP BY"],
        "is_active": True,
    },
    {
        "question_id": "CH02-Q025",
        "module_id": "CH02",
        "content": "Tolong tampilkan klasifikasi angkatan (alias classification) and jumlah mahasiswa di setiap kategori tersebut.",
        "target_query": "SELECT CASE WHEN tot_cred < 30 THEN 'Freshman' WHEN tot_cred BETWEEN 30 AND 59 THEN 'Sophomore' WHEN tot_cred BETWEEN 60 AND 89 THEN 'Junior' ELSE 'Final Year' END AS classification, COUNT(*) AS jumlah FROM student GROUP BY classification;",
        "initial_difficulty": 1580.0,
        "current_difficulty": 1580.0,
        "topic_tags": ["CASE", "COUNT", "GROUP BY"],
        "is_active": True,
    },

    # ========== CH03: Advanced Querying & Modification (25 questions, Theta 1400-1780) ==========
    {
        "question_id": "CH03-Q001",
        "module_id": "CH03",
        "content": "Tolong gabungin tabel student sama takes-nya, kita mau liat nama mahasiswa barengan sama kode mata kuliah yang dia ambil.",
        "target_query": "SELECT s.name, t.course_id FROM student s INNER JOIN takes t ON s.ID = t.ID;",
        "initial_difficulty": 1400.0,
        "current_difficulty": 1400.0,
        "topic_tags": ["INNER JOIN", "SELECT"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q002",
        "module_id": "CH03",
        "content": "Coba cari tahu departemen mana aja yang ternyata belum punya dosen sama sekali. Pakai filter NULL ya! Ga perlu pake alias ya! :D",
        "target_query": "SELECT d.dept_name, COUNT(i.ID) FROM department d LEFT JOIN instructor i ON d.dept_name = i.dept_name GROUP BY d.dept_name HAVING COUNT(i.ID) = 0;",
        "initial_difficulty": 1420.0,
        "current_difficulty": 1420.0,
        "topic_tags": ["LEFT JOIN", "HAVING", "COUNT"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q003",
        "module_id": "CH03",
        "content": "Bisa tunjukin judul mata kuliah, hari, sama jam mulai dan berakhirnya nggak? Gabungin tiga tabel sekalian ya.",
        "target_query": "SELECT c.title, t.day, t.start_time, t.end_time FROM course c JOIN section s ON c.course_id = s.course_id JOIN time_slot t ON s.time_slot_id = t.time_slot_id;",
        "initial_difficulty": 1440.0,
        "current_difficulty": 1440.0,
        "topic_tags": ["JOIN", "MULTI-TABLE"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q004",
        "module_id": "CH03",
        "content": "Cari mahasiswa yang ngambil 'Intro. to Computer Science' tapi total SKSnya masih di bawah 60. Mau kita kasih bimbingan tambahan. Ga perlu pake alias ya! :D",
        "target_query": "SELECT s.ID, s.name, s.tot_cred, s.dept_name FROM student s JOIN takes t ON s.ID = t.ID JOIN course c ON t.course_id = c.course_id WHERE c.title = 'Intro. to Computer Science' AND s.tot_cred < 60;",
        "initial_difficulty": 1460.0,
        "current_difficulty": 1460.0,
        "topic_tags": ["JOIN", "WHERE", "MULTI-TABLE"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q005",
        "module_id": "CH03",
        "content": "Tampilkan daftar mata kuliah beserta nama mata kuliah prasyaratnya. Biar mahasiswa nggak bingung pas mau ngambil.",
        "target_query": "SELECT c.course_id, c.title, p.prereq_id, pr.title AS prereq_title FROM course c JOIN prereq p ON c.course_id = p.course_id JOIN course pr ON p.prereq_id = pr.course_id;",
        "initial_difficulty": 1480.0,
        "current_difficulty": 1480.0,
        "topic_tags": ["JOIN", "SELF-JOIN"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q006",
        "module_id": "CH03",
        "content": "Tolong cari mata kuliah yang SKS-nya di atas rata-rata SKS semua mata kuliah yang ada.",
        "target_query": "SELECT * FROM course WHERE credits > (SELECT AVG(credits) FROM course);",
        "initial_difficulty": 1500.0,
        "current_difficulty": 1500.0,
        "topic_tags": ["SUBQUERY", "SCALAR"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q007",
        "module_id": "CH03",
        "content": "Siapa aja mahasiswa yang dosen pembimbingnya berasal dari departemen 'Comp. Sci.'? Ga perlu pake alias ya! :D",
        "target_query": "SELECT DISTINCT s.ID, s.name FROM student s JOIN advisor a ON s.ID = a.s_ID WHERE a.i_ID IN (SELECT ID FROM instructor WHERE dept_name = 'Comp. Sci.');",
        "initial_difficulty": 1520.0,
        "current_difficulty": 1520.0,
        "topic_tags": ["IN", "SUBQUERY", "JOIN"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q008",
        "module_id": "CH03",
        "content": "Mata kuliah apa aja sih yang sama sekali nggak ada peminatnya (nggak diambil siapapun) di tahun 2009?",
        "target_query": "SELECT * FROM course WHERE course_id NOT IN (SELECT DISTINCT course_id FROM takes WHERE year = 2009);",
        "initial_difficulty": 1540.0,
        "current_difficulty": 1540.0,
        "topic_tags": ["NOT IN", "SUBQUERY"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q009",
        "module_id": "CH03",
        "content": "Cari dosen yang gajinya lebih tinggi dibandingkan rata-rata gaji di departemennya sendiri. Sultan nih! Ga perlu pake alias ya! :D",
        "target_query": "SELECT * FROM instructor i WHERE salary > (SELECT AVG(salary) FROM instructor WHERE dept_name = i.dept_name);",
        "initial_difficulty": 1560.0,
        "current_difficulty": 1560.0,
        "topic_tags": ["CORRELATED SUBQUERY"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q010",
        "module_id": "CH03",
        "content": "Tampilkan departemen yang nawarin setidaknya satu mata kuliah dengan SKS lebih dari 4.",
        "target_query": "SELECT * FROM department d WHERE EXISTS (SELECT * FROM course c WHERE c.dept_name = d.dept_name AND c.credits > 4);",
        "initial_difficulty": 1580.0,
        "current_difficulty": 1580.0,
        "topic_tags": ["EXISTS", "SUBQUERY"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q011",
        "module_id": "CH03",
        "content": "Tolong gabungin daftar nama mahasiswa dari jurusan 'Physics' sama jurusan 'Elec. Eng.' jadi satu list. Ga perlu pake alias ya! :D",
        "target_query": "(SELECT name FROM student WHERE dept_name = 'Physics') UNION (SELECT name FROM student WHERE dept_name = 'Elec. Eng.');",
        "initial_difficulty": 1600.0,
        "current_difficulty": 1600.0,
        "topic_tags": ["UNION", "SET-OP"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q012",
        "module_id": "CH03",
        "content": "Tampilkan ruangan yang kapasitasnya di atas 100, tapi jangan masukin ruangan yang ada di gedung Watson.",
        "target_query": "(SELECT building, room_no, capacity FROM classroom WHERE capacity > 100) EXCEPT (SELECT building, room_no, capacity FROM classroom WHERE building = 'Watson');",
        "initial_difficulty": 1620.0,
        "current_difficulty": 1620.0,
        "topic_tags": ["EXCEPT", "SET-OP"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q013",
        "module_id": "CH03",
        "content": "Siapa sih mahasiswa rajin yang ngambil mata kuliah 'CS-101' sekaligus 'CS-201'? Ga perlu pake alias ya! :D",
        "target_query": "(SELECT ID FROM takes WHERE course_id = 'CS-101') INTERSECT (SELECT ID FROM takes WHERE course_id = 'CS-201');",
        "initial_difficulty": 1640.0,
        "current_difficulty": 1640.0,
        "topic_tags": ["INTERSECT", "SET-OP"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q014",
        "module_id": "CH03",
        "content": "Coba hitung dulu rata-rata budget (alias avg_budget) per gedung, terus tampilin gedung mana yang rata-ratanya di atas rata-rata budget kampus secara keseluruhan.",
        "target_query": "WITH building_avg AS (SELECT building, AVG(budget) AS avg_budget FROM department GROUP BY building) SELECT * FROM building_avg WHERE avg_budget > (SELECT AVG(budget) FROM department);",
        "initial_difficulty": 1660.0,
        "current_difficulty": 1660.0,
        "topic_tags": ["CTE", "WITH", "SUBQUERY"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q015",
        "module_id": "CH03",
        "content": "Tolong buatin ranking mahasiswa berdasarkan total SKS di masing-masing departemennya, dan kolom rankingnya alias 'rank' ya!",
        "target_query": "SELECT name, dept_name, tot_cred, RANK() OVER(PARTITION BY dept_name ORDER BY tot_cred DESC) AS rank FROM student;",
        "initial_difficulty": 1680.0,
        "current_difficulty": 1680.0,
        "topic_tags": ["RANK", "WINDOW", "PARTITION"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q016",
        "module_id": "CH03",
        "content": "Ada kabar gembira! Fakultas (departemen) yang rata-rata SKS (tot_cred) mahasiswanya lebih dari 50 akan mendapatkan peningkatkan APB dari pusat DITKEU. Coba tampilkan nama fakultas, budget saat ini, dan kolom 'proyeksi_budget' (budget + 10%) untuk departemen-departemen tersebut",
        "target_query": "SELECT dept_name, budget, (budget * 1.1) AS proyeksi_budget FROM department WHERE dept_name IN (SELECT dept_name FROM student GROUP BY dept_name HAVING AVG(tot_cred) > 50);",
        "initial_difficulty": 1700.0,
        "current_difficulty": 1700.0,
        "topic_tags": ["SUBQUERY", "ARITHMETIC"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q017",
        "module_id": "CH03",
        "content": "TU Akademik sedang mensurvei kelas apa saja yang perlu ditutup pada masa PRS. Coba cari data kelas di tahun 2008 yang memiliki kurang dari 5 mahasiswa. Tampilkan course_id, sec_id, dan kolom jumlah mahasiswanya alias 'jumlah_mhs' ya!",
        "target_query": "SELECT course_id, sec_id, COUNT(ID) AS jumlah_mhs FROM takes WHERE year = 2008 GROUP BY course_id, sec_id HAVING COUNT(ID) < 5;",
        "initial_difficulty": 1715.0,
        "current_difficulty": 1715.0,
        "topic_tags": ["COUNT", "GROUP BY", "HAVING"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q018",
        "module_id": "CH03",
        "content": "Kita ingin merancang mata kuliah baru. Tampilkan sebuah baris tunggal dengan ID 'NEW-001', judulnya 'NEW COURSE', departemennya sama dengan 'CS-101', dan SKS-nya juga sama",
        "target_query": "SELECT 'NEW-001' AS course_id, 'New Course' AS title, dept_name, credits FROM course WHERE course_id = 'CS-101';",
        "initial_difficulty": 1730.0,
        "current_difficulty": 1730.0,
        "topic_tags": ["LITERAL", "SELECT"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q019",
        "module_id": "CH03",
        "content": "Gunakan CTE (Common Table Expression) dengan alias 'jml' untuk menghitung jumlah mahasiswa per departemen, lalu tampilkan departemen yang populasinya di atas rata-rata populasi departemen lain",
        "target_query": "WITH dept_counts AS (SELECT dept_name, COUNT(*) AS jml FROM student GROUP BY dept_name) SELECT * FROM dept_counts WHERE jml > (SELECT AVG(jml) FROM dept_counts);",
        "initial_difficulty": 1745.0,
        "current_difficulty": 1745.0,
        "topic_tags": ["CTE", "WITH", "SUBQUERY"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q020",
        "module_id": "CH03",
        "content": "Gunakan CTE dengan alias 'jml' untuk menghitung jumlah mahasiswa per departemen, lalu tampilkan departemen yang mahasiswanya lebih dari 20 orang.",
        "target_query": "WITH dept_counts AS (SELECT dept_name, COUNT(*) AS jml FROM student GROUP BY dept_name) SELECT * FROM dept_counts WHERE jml > 20;",
        "initial_difficulty": 1760.0,
        "current_difficulty": 1760.0,
        "topic_tags": ["CTE", "WITH"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q021",
        "module_id": "CH03",
        "content": "Coba klasifikasi mata kuliah berdasarkan nilai rata-rata mahasiswanya dengan alias kolom: avg_grade (rata-rata nilai) dan difficulty ('Easy' kalau >= 'B', 'Medium' antara 'C' dan 'B', 'Hard' sisanya).",
        "target_query": "SELECT c.title, AVG(t.grade) AS avg_grade, CASE WHEN AVG(t.grade) >= 'B' THEN 'Easy' WHEN AVG(t.grade) BETWEEN 'C' AND 'B' THEN 'Medium' ELSE 'Hard' END AS difficulty FROM course c JOIN takes t ON c.course_id = t.course_id GROUP BY c.title;",
        "initial_difficulty": 1770.0,
        "current_difficulty": 1770.0,
        "topic_tags": ["CASE", "JOIN", "GROUP BY"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q022",
        "module_id": "CH03",
        "content": "Tampilkan judul mata kuliah, terus di kolom sebelahnya alias 'enrolled' hitung berapa banyak mahasiswa yang daftar di tiap mata kuliah itu.",
        "target_query": "SELECT c.title, (SELECT COUNT(*) FROM takes t WHERE t.course_id = c.course_id) AS enrolled FROM course c;",
        "initial_difficulty": 1775.0,
        "current_difficulty": 1775.0,
        "topic_tags": ["CORRELATED SUBQUERY", "SELECT"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q023",
        "module_id": "CH03",
        "content": "Amad ingin melihat mata kuliah-mata kuliah yang 'berat' dan 'ringan' yang ada di kampusnya. Bantu Amad untuk menampilkan judul mata kuliah dan kolom 'level' berisi 'berat' jka SKS >=4 dan 'ringan' jika SKS < 4. Urutkan berdasarkan 'level' tersebut.",
        "target_query": "SELECT title, credits, CASE WHEN credits >= 4 THEN 'berat' ELSE 'ringan' END AS level FROM course ORDER BY level;",
        "initial_difficulty": 1780.0,
        "current_difficulty": 1780.0,
        "topic_tags": ["CASE", "ORDER BY"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q024",
        "module_id": "CH03",
        "content": "Tampilkan nama gedung, total budget fakultas (alias total_bud), dan banyaknya dosen unik (alias jml_dosen) yang berkantor di gedung tersebut. Tapi hanya untuk fakultas dengan total budget > 50 ribu",
        "target_query": "SELECT d.building, SUM(d.budget) AS total_bud, COUNT(DISTINCT i.ID) AS jml_dosen FROM department d LEFT JOIN instructor i ON d.dept_name = i.dept_name GROUP BY d.building HAVING SUM(d.budget) > 50000;",
        "initial_difficulty": 1785.0,
        "current_difficulty": 1785.0,
        "topic_tags": ["LEFT JOIN", "SUM", "COUNT", "HAVING"],
        "is_active": True,
    },
    {
        "question_id": "CH03-Q025",
        "module_id": "CH03",
        "content": "Tolong list 10 mahasiswa 'Senior' (SKS >= 90) dengan SKS tertinggi, dan kasih kolom status 'Excellent' kalau SKSnya sudah 120 ke atas, atau 'Good' kalau belum.",
        "target_query": "WITH high_cred_students AS (SELECT * FROM student WHERE tot_cred >= 90) SELECT h.name, h.dept_name, h.tot_cred, CASE WHEN h.tot_cred >= 120 THEN 'Excellent' ELSE 'Good' END AS status FROM high_cred_students h ORDER BY h.tot_cred DESC LIMIT 10;",
        "initial_difficulty": 1780.0,
        "current_difficulty": 1780.0,
        "topic_tags": ["CTE", "WITH", "CASE", "LIMIT"],
        "is_active": True,
    },
]


async def seed_database():
    async with AsyncSessionLocal() as session:
        try:
            print("Starting SQL questions database seeding...")
            
            # Seed Modules
            print("Processing modules...")
            for module_data in MODULES_DATA:
                module = await session.get(Module, module_data["module_id"])
                if module:
                    # Update existing module fields
                    for key, value in module_data.items():
                        setattr(module, key, value)
                    print(f"  Updated module {module_data['module_id']}")
                else:
                    module = Module(**module_data)
                    session.add(module)
                    print(f"  Created module {module_data['module_id']}")
            
            await session.commit()
            
            # Seed Questions
            print("Processing questions...")
            for question_data in QUESTIONS_DATA:
                question = await session.get(Question, question_data["question_id"])
                if question:
                    # Update content-related fields, but keep current difficulty
                    question.content = question_data["content"]
                    question.target_query = question_data["target_query"]
                    question.topic_tags = question_data["topic_tags"]
                    question.is_active = question_data.get("is_active", True)
                    print(f"  Updated question {question_data['question_id']}")
                else:
                    question = Question(**question_data)
                    session.add(question)
                    print(f"  Created question {question_data['question_id']} (D={question_data['current_difficulty']})")
            
            await session.commit()
            
            # Summary
            print("\n" + "=" * 50)
            print("SQL QUESTIONS SEEDING COMPLETED")
            print("=" * 50)
            print(f"Modules: {len(MODULES_DATA)}")
            print(f"Questions: {len(QUESTIONS_DATA)}")
            print(f"CH01 Questions: {len([q for q in QUESTIONS_DATA if q['module_id'] == 'CH01'])}")
            print(f"CH02 Questions: {len([q for q in QUESTIONS_DATA if q['module_id'] == 'CH02'])}")
            print(f"CH03 Questions: {len([q for q in QUESTIONS_DATA if q['module_id'] == 'CH03'])}")
            print(f"Difficulty Range: 1000 - 1800 (Elo Scale)")
            print("=" * 50)
            
        except Exception as e:
            await session.rollback()
            print(f"\nSeeding failed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_database())
