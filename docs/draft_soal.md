### 🔍 Logical Mapping & Difficulty Calibration
1. **Curriculum Alignment**
   - **CH01 (Basic Selection)** maps to `Praktikum 0` & early `Praktikum 1` (Weeks 5–6: Basic SQL, String Ops, ORDER BY, Set Operations intro, Null Values).
   - **CH02 (Aggregation & Grouping)** maps to late `Praktikum 1` & early `Praktikum 2` (Weeks 5–6: Aggregate Functions, Nested Subqueries intro, CASE WHEN).
   - **CH03 (Advanced Querying & Modification)** maps to `Praktikum 2` & `Praktikum 3` (Weeks 6–7: Explicit JOINs, Views/Materialized Views, DML/DDL, CTEs, complex subqueries).
2. **Theta Initialization Strategy**
   - Based on Spec v4.3: Scale `[0, 2000]`, baseline `1300`.
   - `initial_difficulty` is manually seeded but will be dynamically recalibrated by the Elo engine after each `is_final_attempt`.
   - Theta distributed linearly with complexity steps:
     - `CH01`: `1000 → 1380` (Basic syntax → multi-condition filtering)
     - `CH02`: `1200 → 1580` (Single aggregates → GROUP BY + HAVING + CASE + multi-table)
     - `CH03`: `1400 → 1780` (Explicit JOINs → correlated subqueries, set ops, DDL/DML with subqueries)

---

## 📘 CH01: Basic Selection & Filtering
**Target Theta:** 1000–1380 | **Jumlah Soal:** 25 | **Tabel:** `student`, `course`, `instructor`, `department`, `classroom`, `section`

| ID | Question Text | Initial Theta | Target Query |
|----|--------------|---------------|--------------|
| CH01-Q001 | Tampilkan seluruh data yang ada pada tabel `student`. Gampang sih, tinggal SELECT aja! | 1000 | `SELECT * FROM student;` |
| CH01-Q002 | Kita butuh daftar nama semua mahasiswa dan total SKS (SKS) mereka buat laporan akademik. | 1015 | `SELECT name, tot_cred FROM student;` |
| CH01-Q003 | Nona Angelin pengen liat siapa saja mahasiswa yang total SKSnya nggak nol alias udah punya SKS terakumulasi. Bantuin dong! | 1030 | `SELECT * FROM student WHERE tot_cred <> 0;` |
| CH01-Q004 | TU katanya mau liat data mahasiswa dari departemen 'Comp. Sci.'. Bantu filter dong biar lebih rapih. | 1045 | `SELECT * FROM student WHERE dept_name = 'Comp. Sci.';` |
| CH01-Q005 | Dosen-dosen yang departemennya 'Comp. Sci.' lagi dikumpulin buat rapat. Tampilkan siapa saja nama mereka dan departemennya. | 1060 | `SELECT name, dept_name FROM instructor WHERE dept_name = 'Comp. Sci.';` |
| CH01-Q006 | Kampus kita lagi ngadain survei nih. Kita mau tau judul mata kuliah apa aja yang ditawarkan. Bantuin buat daftarnya dong! | 1075 | `SELECT DISTINCT title FROM course;` |
| CH01-Q007 | Mahasiswa yang namanya mulai dari huruf 'Z' doang yang ikut acara hari ini. Cari yang namanya AWAL dengan 'Z' ya! | 1090 | `SELECT * FROM student WHERE name LIKE 'Z%';` |
| CH01-Q008 | Kita mau ngasih kado ke mahasiswa yang nama belakangnya 'ez'. Bantuin cari yang namanya BERAKHIRAN 'ez' dong. | 1105 | `SELECT * FROM student WHERE name LIKE '%ez';` |
| CH01-Q009 | Mahasiswa dari departemen 'Comp. Sci.' atau 'Physics' aja yang mau kita ajak survei. Kedua departemen itu penting banget buat proyek ini. Coba bantu buatin querynya. | 1120 | `SELECT * FROM student WHERE dept_name IN ('Comp. Sci.', 'Physics');` |
| CH01-Q010 | Total SKS antara 50 sampai 100 itu range yang cukup bagus. Tunjukkan mahasiswa di range itu aja. | 1135 | `SELECT * FROM student WHERE tot_cred BETWEEN 50 AND 100;` |
| CH01-Q011 | Kita perlu tahu siapa saja mahasiswa yang belum punya total SKS alias 0 (treat as NULL concept) nih. Bantuin filter dong. | 1150 | `SELECT * FROM student WHERE tot_cred = 0;` |
| CH01-Q012 | Kita juga perlu tahu siapa saja mahasiswa yang total SKSnya SUDAH ADA dan nggak 0. | 1165 | `SELECT * FROM student WHERE tot_cred > 0;` |
| CH01-Q013 | Urutkan mahasiswa berdasarkan total SKS tertinggi. Kita mau buat dean's list! | 1180 | `SELECT * FROM student ORDER BY tot_cred DESC;` |
| CH01-Q014 | Bisa tolong tunjukin mata kuliah yang punya SKS lebih dari 3? Terus dibuat terurut berdasarkan JUDUL secara ascending... A-Z gitu lohh. | 1195 | `SELECT * FROM course WHERE credits > 3 ORDER BY title ASC;` |
| CH01-Q015 | Kapasitas ruangan kampus lagi disurvei nih. Cari bangunan dengan kapasitas > 150, urutin dari yang paling gede. | 1210 | `SELECT building, room_no, capacity FROM classroom WHERE capacity > 150 ORDER BY capacity DESC;` |
| CH01-Q016 | Fakultas sedang mempertimbangkan untuk menggandakan SKS mata kuliah tertentu. Coba tampilin SKS baru kalau SKS mata kuliah yang ada dikali 2. Kasih alias biar jelas! | 1225 | `SELECT course_id, credits, (credits * 2) AS double_credits FROM course;` |
| CH01-Q017 | Mahasiswa departemen 'Comp. Sci.' ATAU yang total SKSnya < 50 bisa ikut program beasiswa ini. Tolong cariin dong siapa aja itu | 1240 | `SELECT * FROM student WHERE dept_name = 'Comp. Sci.' OR tot_cred < 50;` |
| CH01-Q018 | Panitia hackathon mau melakukan pre-filter calon perwakilan. Syaratnya mahasiswa 'Comp. Sci.' dengan total SKS > 80, dua-duanya harus terpenuhi buat masuk tim utama. | 1255 | `SELECT * FROM student WHERE dept_name = 'Comp. Sci.' AND tot_cred > 80;` |
| CH01-Q019 | Coba tunjukin ada gak sih dosen dengan gaji antara 60rb dan 90rb? jangan lupa cek yang salary-nya nggak NULL ya! | 1270 | `SELECT * FROM instructor WHERE salary BETWEEN 60000 AND 90000 AND salary IS NOT NULL;` |
| CH01-Q020 | Kombinasi building dan room_no yang unik aja dong. | 1285 | `SELECT DISTINCT building, room_no FROM classroom;` |
| CH01-Q021 | Rudi penasaran siapa saja mahasiswa yang namanya setidaknya mengandung 2 kata (berarti ada spasi) dan berakhiran huruf 'n' | 1300 | `SELECT * FROM student WHERE name LIKE '% %' AND name LIKE '%n';` |
| CH01-Q022 | Coba cari mata kuliah yang TIDAK mengandung kata "Intro" di judulnya dan SKS-nya <= 3. | 1315 | `SELECT * FROM course WHERE title NOT LIKE '%Intro%' AND credits <= 3;` |
| CH01-Q023 | Kampus sedang mau liat daftar dosen dan mata kuliah yang mereka ajar. Bisa bantu cariin? Tolong diurutkan berdasarkan nama dosen ASC dan course_id ASC | 1330 | `SELECT i.name, t.course_id FROM instructor i, teaches t WHERE i.ID = t.ID ORDER BY i.name ASC, t.course_id ASC;` |
| CH01-Q024 | Coba ada fakultas apa aja sih yang name nya mengandung kata subkata 'tech' dan budgetnya > 10jt! | 1345 | `SELECT * FROM department WHERE dept_name LIKE '%tech%' AND budget > 10000000;` |
| CH01-Q025 | Coba cari semua mata kuliah (course) dan kelasnya (section). Semua atribut dari course harus ditampilkan | 1380 | `SELECT c.*, s.semester, s.year FROM course c, section s WHERE c.course_id = s.course_id;` |

---

## 📗 CH02: Aggregation & Grouping
**Target Theta:** 1200–1580 | **Jumlah Soal:** 25 | **Tabel:** `student`, `course`, `instructor`, `takes`, `department`, `classroom`, `time_slot`

| ID | Question Text | Initial Theta | Target Query |
|----|--------------|---------------|--------------|
| CH02-Q001 | Eh, coba hitung dong total semua mahasiswa yang kedaftar di sistem kita. Tinggal pake COUNT kan? | 1200 | `SELECT COUNT(*) FROM student;` |
| CH02-Q002 | Bisa gak bikinin daftar jumlah mahasiswa per departemen? Biar kita tau mana departemen yang paling rame. | 1215 | `SELECT dept_name, COUNT(*) AS jumlah_mhs FROM student GROUP BY dept_name;` |
| CH02-Q003 | Dosen-dosen penasaran nih, berapa sih rata-rata total SKS mahasiswa di tiap departemen? Coba liatin dong. | 1230 | `SELECT dept_name, AVG(tot_cred) AS rata_sks FROM student GROUP BY dept_name;` |
| CH02-Q004 | Kita mau cari bintang kampus! Coba cari tahu berapa total SKS tertinggi di tiap-tiap departemen. | 1245 | `SELECT dept_name, MAX(tot_cred) AS max_sks FROM student GROUP BY dept_name;` |
| CH02-Q005 | Biasanya semester berapa sih yang beban matakuliahnya paling enteng? Coba cari SKS paling kecil di tiap semester. | 1260 | `SELECT semester, MIN(credits) AS min_credits FROM course GROUP BY semester;` |
| CH02-Q006 | Tolong rekap dong total SKS yang ditawarkan di masing-masing departemen. | 1275 | `SELECT dept_name, SUM(credits) AS total_sks FROM course GROUP BY dept_name;` |
| CH02-Q007 | Berapa banyak sih mata kuliah yang dibuka tiap semester per tahunnya? Biar kita bisa liat trennya. | 1290 | `SELECT semester, year, COUNT(*) AS jumlah_course FROM section GROUP BY semester, year;` |
| CH02-Q008 | Coba hitung rata-rata budget buat departemen-departemen yang ada di gedung Taylor. | 1305 | `SELECT AVG(budget) FROM department WHERE building = 'Taylor';` |
| CH02-Q009 | Mana aja nih departemen yang total SKS mata kuliahnya udah lebih dari 10? Kasih tau ya. | 1320 | `SELECT dept_name, SUM(credits) FROM course GROUP BY dept_name HAVING SUM(credits) > 10;` |
| CH02-Q010 | Gedung mana aja yang punya rata-rata kapasitas ruangan di atas 80 orang? | 1335 | `SELECT building, AVG(capacity) FROM classroom GROUP BY building HAVING AVG(capacity) > 80;` |
| CH02-Q011 | Cariin jumlah dosen di tiap departemen, terus urutin dari yang paling banyak personilnya. | 1350 | `SELECT dept_name, COUNT(ID) AS jumlah_dosen FROM instructor GROUP BY dept_name ORDER BY COUNT(ID) DESC;` |
| CH02-Q012 | Departemen mana nih yang berani ngasih gaji dosen paling tinggi (di atas 90 ribu)? | 1365 | `SELECT dept_name FROM instructor GROUP BY dept_name HAVING MAX(salary) > 90000;` |
| CH02-Q013 | Ada berapa banyak sih mahasiswa (unik) yang ngambil mata kuliah di tahun 2009? | 1380 | `SELECT COUNT(DISTINCT ID) FROM takes WHERE year = 2009;` |
| CH02-Q014 | Coba hitung rata-rata total SKS, tapi buat mahasiswa yang udah punya lebih dari 50 SKS aja. | 1395 | `SELECT AVG(tot_cred) FROM student WHERE tot_cred > 50;` |
| CH02-Q015 | Tolong tampilin ID dosen sama berapa banyak mata kuliah yang mereka ajar masing-masing. | 1410 | `SELECT t.ID, COUNT(c.course_id) FROM teaches t JOIN course c ON t.course_id = c.course_id GROUP BY t.ID;` |
| CH02-Q016 | Tampilkan nama mata kuliah beserta total mahasiswa yang ikutan di kelas itu. | 1425 | `SELECT c.title, COUNT(t.ID) FROM takes t JOIN course c ON t.course_id = c.course_id GROUP BY c.title;` |
| CH02-Q017 | Departemen mana aja yang punya dosen lebih dari 2 orang? Kayaknya yang sedikit perlu ditambah nih. | 1440 | `SELECT dept_name FROM instructor GROUP BY dept_name HAVING COUNT(ID) > 2;` |
| CH02-Q018 | Coba hitung rata-rata gaji dosen di departemen yang budget-nya gede banget, di atas 150 ribu. | 1455 | `SELECT dept_name, AVG(salary) FROM instructor WHERE dept_name IN (SELECT dept_name FROM department WHERE budget > 150000) GROUP BY dept_name;` |
| CH02-Q019 | Daftarin departemen yang rata-rata SKS mata kuliahnya 3 ke atas, tunjukin juga berapa jumlah mata kuliahnya. | 1470 | `SELECT dept_name, COUNT(*), AVG(credits) FROM course GROUP BY dept_name HAVING AVG(credits) >= 3;` |
| CH02-Q020 | Biar rapi, tolong kumpulin mahasiswa berdasarkan jumlah SKSnya: <30 itu Freshman, 30-59 Sophomore, 60-89 Junior, sisanya Final Year. | 1485 | `SELECT name, tot_cred, CASE WHEN tot_cred < 30 THEN 'Freshman' WHEN tot_cred BETWEEN 30 AND 59 THEN 'Sophomore' WHEN tot_cred BETWEEN 60 AND 89 THEN 'Junior' ELSE 'Final Year' END AS classification FROM student;` |
| CH02-Q021 | Cek tiap jadwal (time slot), ada berapa banyak kelas yang pake jadwal itu? Yang nggak kepake gak usah dimunculin. | 1500 | `SELECT ts.time_slot_id, COUNT(*) FROM time_slot ts LEFT JOIN section s ON ts.time_slot_id = s.time_slot_id GROUP BY ts.time_slot_id HAVING COUNT(*) > 0;` |
| CH02-Q022 | Siapa 3 departemen teratas yang punya rata-rata total SKS mahasiswa paling tinggi? | 1515 | `SELECT dept_name, AVG(tot_cred) AS avg_cred FROM student GROUP BY dept_name ORDER BY avg_cred DESC LIMIT 3;` |
| CH02-Q023 | Tolong jumlahin budget departemen berdasarkan gedungnya, terus tampilin yang totalnya di atas 50 ribu. | 1530 | `SELECT building, SUM(budget) FROM department GROUP BY building HAVING SUM(budget) > 50000;` |
| CH02-Q024 | Hitung berapa banyak mahasiswa yang beda-beda di setiap kelas (kode mk, seksi, semester, dan tahun). | 1545 | `SELECT course_id, sec_id, semester, year, COUNT(DISTINCT ID) FROM takes GROUP BY course_id, sec_id, semester, year;` |
| CH02-Q025 | Tolong rekap jumlah mahasiswa untuk setiap kategori angkatan (Freshman, Sophomore, Junior, Final Year) biar gampang dipantau. | 1580 | `SELECT CASE WHEN tot_cred < 30 THEN 'Freshman' WHEN tot_cred BETWEEN 30 AND 59 THEN 'Sophomore' WHEN tot_cred BETWEEN 60 AND 89 THEN 'Junior' ELSE 'Final Year' END AS classification, COUNT(*) AS jumlah FROM student GROUP BY classification;` |

---

## 📙 CH03: Advanced Querying & Modification
**Target Theta:** 1400–1780 | **Jumlah Soal:** 25 | **Tabel:** `student`, `course`, `instructor`, `takes`, `department`, `section`, `time_slot`, `prereq`, `advisor`

| ID | Question Text | Initial Theta | Target Query |
|----|--------------|---------------|--------------|
| CH03-Q001 | Tolong gabungin tabel student sama takes-nya, kita mau liat nama mahasiswa barengan sama kode mata kuliah yang dia ambil. | 1400 | `SELECT s.name, t.course_id FROM student s INNER JOIN takes t ON s.ID = t.ID;` |
| CH03-Q002 | Coba cari tahu departemen mana aja yang ternyata belum punya dosen sama sekali. Pakai filter NULL ya! | 1420 | `SELECT d.dept_name, COUNT(i.ID) FROM department d LEFT JOIN instructor i ON d.dept_name = i.dept_name GROUP BY d.dept_name HAVING COUNT(i.ID) = 0;` |
| CH03-Q003 | Bisa tunjukin judul mata kuliah, hari, sama jam mulai dan berakhirnya nggak? Gabungin tiga tabel sekalian ya. | 1440 | `SELECT c.title, t.day, t.start_time, t.end_time FROM course c JOIN section s ON c.course_id = s.course_id JOIN time_slot t ON s.time_slot_id = t.time_slot_id;` |
| CH03-Q004 | Cari mahasiswa yang ngambil 'Intro. to Computer Science' tapi total SKSnya masih di bawah 60. Mau kita kasih bimbingan tambahan. | 1460 | `SELECT s.ID, s.name, s.tot_cred, s.dept_name FROM student s JOIN takes t ON s.ID = t.ID JOIN course c ON t.course_id = c.course_id WHERE c.title = 'Intro. to Computer Science' AND s.tot_cred < 60;` |
| CH03-Q005 | Tampilkan daftar mata kuliah beserta nama mata kuliah prasyaratnya. Biar mahasiswa nggak bingung pas mau ngambil. | 1480 | `SELECT c.course_id, c.title, p.prereq_id, pr.title AS prereq_title FROM course c JOIN prereq p ON c.course_id = p.course_id JOIN course pr ON p.prereq_id = pr.course_id;` |
| CH03-Q006 | Tolong cari mata kuliah yang SKS-nya di atas rata-rata SKS semua mata kuliah yang ada. | 1500 | `SELECT * FROM course WHERE credits > (SELECT AVG(credits) FROM course);` |
| CH03-Q007 | Siapa aja mahasiswa yang dosen pembimbingnya berasal dari departemen 'Comp. Sci.'? | 1520 | `SELECT DISTINCT s.ID, s.name FROM student s JOIN advisor a ON s.ID = a.s_ID WHERE a.i_ID IN (SELECT ID FROM instructor WHERE dept_name = 'Comp. Sci.');` |
| CH03-Q008 | Mata kuliah apa aja sih yang sama sekali nggak ada peminatnya (nggak diambil siapapun) di tahun 2009? | 1540 | `SELECT * FROM course WHERE course_id NOT IN (SELECT DISTINCT course_id FROM takes WHERE year = 2009);` |
| CH03-Q009 | Cari dosen yang gajinya lebih tinggi dibandingkan rata-rata gaji di departemennya sendiri. Sultan nih! | 1560 | `SELECT * FROM instructor i WHERE salary > (SELECT AVG(salary) FROM instructor WHERE dept_name = i.dept_name);` |
| CH03-Q010 | Tampilkan departemen yang nawarin setidaknya satu mata kuliah dengan SKS lebih dari 4. | 1580 | `SELECT * FROM department d WHERE EXISTS (SELECT * FROM course c WHERE c.dept_name = d.dept_name AND c.credits > 4);` |
| CH03-Q011 | Tolong gabungin daftar nama mahasiswa dari jurusan 'Physics' sama jurusan 'Elec. Eng.' jadi satu list. | 1600 | `(SELECT name FROM student WHERE dept_name = 'Physics') UNION (SELECT name FROM student WHERE dept_name = 'Elec. Eng.');` |
| CH03-Q012 | Tampilkan ruangan yang kapasitasnya di atas 100, tapi jangan masukin ruangan yang ada di gedung Watson. | 1620 | `(SELECT building, room_no, capacity FROM classroom WHERE capacity > 100) EXCEPT (SELECT building, room_no, capacity FROM classroom WHERE building = 'Watson');` |
| CH03-Q013 | Siapa sih mahasiswa rajin yang ngambil mata kuliah 'CS-101' sekaligus 'CS-201'? | 1640 | `(SELECT ID FROM takes WHERE course_id = 'CS-101') INTERSECT (SELECT ID FROM takes WHERE course_id = 'CS-201');` |
| CH03-Q014 | Coba hitung dulu rata-rata budget per gedung, terus tampilin gedung mana yang rata-ratanya di atas rata-rata budget kampus secara keseluruhan. | 1660 | `WITH building_avg AS (SELECT building, AVG(budget) AS avg_budget FROM department GROUP BY building) SELECT * FROM building_avg WHERE avg_budget > (SELECT AVG(budget) FROM department);` |
| CH03-Q015 | Tolong buatin ranking mahasiswa berdasarkan total SKS di masing-masing departemennya. | 1680 | `SELECT name, dept_name, tot_cred, RANK() OVER(PARTITION BY dept_name ORDER BY tot_cred DESC) AS rank FROM student;` |
| CH03-Q016 | Ada kabar gembira! Fakultas (departemen) yang rata-rata SKS (tot_cred) mahasiswanya lebih dari 50 akan mendapatkan peningkatkan APB dari pusat DITKEU. Coba tampilkan nama fakultas, budget saat ini, dan kolom "proyeksi_budget" (budget + 10%) untuk departemen-departemen tersebut | 1700 | `SELECT dept_name, budget, (budget * 1.1) AS proyeksi_budget FROM department WHERE dept_name IN (SELECT dept_name FROM student GROUP BY dept_name HAVING AVG(tot_cred) > 50);` |
| CH03-Q017 | TU Akademik sedang mensurvei kelas apa saja yang perlu ditutup pada masa PRS. Coba cari data kelas di tahun 2008 yang memiliki kurang dari 5 mahasiswa. Tampilkan course_id, sec_id, dan jumlah mahasiswanya. | 1715 | `SELECT course_id, sec_id, COUNT(ID) AS jumlah_mhs FROM takes WHERE year = 2008 GROUP BY course_id, sec_id HAVING COUNT(ID) < 5;` |
| CH03-Q018 | Kita ingin merancang mata kuliah baru. Tampilkan sebuah baris tunggal dengan ID 'NEW-001', judulnya 'NEW COURSE', departemennya sama dengan 'CS-101', dan SKS-nya juga sama | 1730 | `SELECT 'NEW-001' AS course_id, 'New Course' AS title, dept_name, credits FROM course WHERE course_id = 'CS-101';` |
| CH03-Q019 | Gunakan CTE (Common Table Expression) untuk menghitung jumlah mahasiswa per departemen, lalu tampilkan departemen yang populasinya di atas rata-rata populasi departemen lain | 1745 | `WITH dept_counts AS (SELECT dept_name, COUNT(*) AS jml FROM student GROUP BY dept_name) SELECT * FROM dept_counts WHERE jml > (SELECT AVG(jml) FROM dept_counts);` |
| CH03-Q020 | Gunakan CTE (Common Table Expression) untuk menghitung jumlah mahasiswa per departemen, lalu tampilkan departemen yang mahasiswanya lebih dari 20 orang. | 1760 | `WITH dept_counts AS (SELECT dept_name, COUNT(*) AS jml FROM student GROUP BY dept_name) SELECT * FROM dept_counts WHERE jml > 20;` |
| CH03-Q021 | Coba klasifikasi mata kuliah berdasarkan nilai rata-rata mahasiswanya: >= 'B' itu Gampang, antara 'C' dan 'B' itu Sedang, sisanya Susah. | 1770 | `SELECT c.title, AVG(t.grade) AS avg_grade, CASE WHEN AVG(t.grade) >= 'B' THEN 'Easy' WHEN AVG(t.grade) BETWEEN 'C' AND 'B' THEN 'Medium' ELSE 'Hard' END AS difficulty FROM course c JOIN takes t ON c.course_id = t.course_id GROUP BY c.title;` |
| CH03-Q022 | Tampilkan judul mata kuliah, terus di kolom sebelahnya hitung berapa banyak mahasiswa yang daftar di tiap mata kuliah itu. | 1775 | `SELECT c.title, (SELECT COUNT(*) FROM takes t WHERE t.course_id = c.course_id) AS enrolled FROM course c;` |
| CH03-Q023 | Amad ingin melihat mata kuliah-mata kuliah yang "berat" dan "ringan" yang ada di kampusnya. Bantu Amad untuk menampilkan judul mata kuliah dan kolom "level" berisi "berat" jka SKS >=4 dan "ringan" jika SKS < 4. Urutkan berdasarkan "level" tersebut. | 1780 | `SELECT title, credits, CASE WHEN credits >= 4 THEN 'berat' ELSE 'ringan' END AS level FROM course ORDER BY level;` |
| CH03-Q024 | Tampilkan nama gedung, total budget fakultas yang menggunakan gedung tersebut, dan banyaknya dosen (unik) yang berkantor di gedung tersebut. Tapi hanya untuk fakultas dengan total budget > 50 ribu | 1785 | `SELECT d.building, SUM(d.budget) AS total_bud, COUNT(DISTINCT i.ID) AS jml_dosen FROM department d LEFT JOIN instructor i ON d.dept_name = i.dept_name GROUP BY d.building HAVING SUM(d.budget) > 50000;` |
| CH03-Q025 | Tolong list 10 mahasiswa 'Senior' (SKS >= 90) dengan SKS tertinggi, dan kasih status 'Excellent' kalau SKSnya sudah 120 ke atas. | 1780 | `WITH high_cred_students AS (SELECT * FROM student WHERE tot_cred >= 90) SELECT h.name, h.dept_name, h.tot_cred, CASE WHEN h.tot_cred >= 120 THEN 'Excellent' ELSE 'Good' END AS status FROM high_cred_students h ORDER BY h.tot_cred DESC LIMIT 10;` |