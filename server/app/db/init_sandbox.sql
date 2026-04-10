-- =====================================================
-- EQUILIBRIA SANDBOX INITIALIZATION SCRIPT
-- Classic University Schema (Silberschatz-style)
-- This script runs ONLY on first database initialization
-- =====================================================

-- 1. Create Sandbox Schema
CREATE SCHEMA IF NOT EXISTS sandbox;

-- 2. Create Sandbox Executor Role (LOGIN with password)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'sandbox_executor') THEN
        CREATE ROLE sandbox_executor LOGIN PASSWORD 'sandbox_pass_123';
    END IF;
END
$$;

-- 3. Grant SELECT Only on Sandbox Schema
GRANT USAGE ON SCHEMA sandbox TO sandbox_executor;
GRANT SELECT ON ALL TABLES IN SCHEMA sandbox TO sandbox_executor;

-- 4. Auto-grant for Future Tables
ALTER DEFAULT PRIVILEGES IN SCHEMA sandbox GRANT SELECT ON TABLES TO sandbox_executor;

-- 5. REVOKE Access to Public Schema (Security)
REVOKE ALL ON SCHEMA public FROM sandbox_executor;

-- 6. Create Sandbox Tables (Complete University Schema per Tech Specs v4)

CREATE TABLE IF NOT EXISTS sandbox.department (
    dept_name   VARCHAR(50)     PRIMARY KEY,
    building    VARCHAR(50)     NOT NULL,
    budget      DECIMAL(12,2)   NOT NULL CHECK (budget > 0)
);

CREATE TABLE IF NOT EXISTS sandbox.classroom (
    building    VARCHAR(50),
    room_no     VARCHAR(10),
    capacity    INTEGER         NOT NULL CHECK (capacity > 0),
    PRIMARY KEY (building, room_no)
);

CREATE TABLE IF NOT EXISTS sandbox.course (
    course_id   VARCHAR(10)     PRIMARY KEY,
    title       VARCHAR(100)    NOT NULL,
    dept_name   VARCHAR(50)     NOT NULL REFERENCES sandbox.department(dept_name),
    credits     INTEGER         NOT NULL CHECK (credits > 0)
);

CREATE TABLE IF NOT EXISTS sandbox.instructor (
    ID          VARCHAR(10)     PRIMARY KEY,
    name        VARCHAR(100)    NOT NULL,
    dept_name   VARCHAR(50)     NOT NULL REFERENCES sandbox.department(dept_name),
    salary      DECIMAL(10,2)   CHECK (salary > 0)
);

CREATE TABLE IF NOT EXISTS sandbox.student (
    ID          VARCHAR(10)     PRIMARY KEY,
    name        VARCHAR(100)    NOT NULL,
    dept_name   VARCHAR(50)     NOT NULL REFERENCES sandbox.department(dept_name),
    tot_cred    INTEGER         NOT NULL DEFAULT 0 CHECK (tot_cred >= 0)
);

CREATE TABLE IF NOT EXISTS sandbox.time_slot (
    time_slot_id    VARCHAR(10)     PRIMARY KEY,
    day             VARCHAR(10)     NOT NULL,
    start_time      TIME            NOT NULL,
    end_time        TIME            NOT NULL
);

CREATE TABLE IF NOT EXISTS sandbox.section (
    course_id       VARCHAR(10)     REFERENCES sandbox.course(course_id),
    sec_id          VARCHAR(5),
    semester        VARCHAR(10),
    year            INTEGER,
    building        VARCHAR(50),
    room_no         VARCHAR(10),
    time_slot_id    VARCHAR(10)     REFERENCES sandbox.time_slot(time_slot_id),
    PRIMARY KEY (course_id, sec_id, semester, year),
    FOREIGN KEY (building, room_no) REFERENCES sandbox.classroom(building, room_no)
);

CREATE TABLE IF NOT EXISTS sandbox.takes (
    ID          VARCHAR(10)     REFERENCES sandbox.student(ID),
    course_id   VARCHAR(10),
    sec_id      VARCHAR(5),
    semester    VARCHAR(10),
    year        INTEGER,
    grade       VARCHAR(2),
    PRIMARY KEY (ID, course_id, sec_id, semester, year),
    FOREIGN KEY (course_id, sec_id, semester, year) 
        REFERENCES sandbox.section(course_id, sec_id, semester, year)
);

CREATE TABLE IF NOT EXISTS sandbox.teaches (
    ID          VARCHAR(10)     REFERENCES sandbox.instructor(ID),
    course_id   VARCHAR(10),
    sec_id      VARCHAR(5),
    semester    VARCHAR(10),
    year        INTEGER,
    PRIMARY KEY (ID, course_id, sec_id, semester, year),
    FOREIGN KEY (course_id, sec_id, semester, year)
        REFERENCES sandbox.section(course_id, sec_id, semester, year)
);

CREATE TABLE IF NOT EXISTS sandbox.prereq (
    course_id   VARCHAR(10)     REFERENCES sandbox.course(course_id),
    prereq_id   VARCHAR(10)     REFERENCES sandbox.course(course_id),
    PRIMARY KEY (course_id, prereq_id)
);

CREATE TABLE IF NOT EXISTS sandbox.advisor (
    s_ID        VARCHAR(10)     REFERENCES sandbox.student(ID),
    i_ID        VARCHAR(10)     REFERENCES sandbox.instructor(ID),
    PRIMARY KEY (s_ID)
);

-- 7. Insert Comprehensive Sample Data (per Tech Specs v4)

INSERT INTO sandbox.department VALUES
('Comp. Sci.', 'Taylor', 100000),
('Physics', 'Watson', 70000),
('Elec. Eng.', 'Taylor', 85000),
('Music', 'Packard', 120000),
('Finance', 'Painter', 120000),
('History', 'Painter', 50000),
('Biology', 'Watson', 90000),
('Math', 'Taylor', 75000)
ON CONFLICT (dept_name) DO NOTHING;

INSERT INTO sandbox.classroom VALUES
('Packard', '101', 500),
('Painter', '514', 50),
('Taylor', '3128', 100),
('Watson', '100', 30),
('Watson', '120', 50),
('Taylor', '3108', 150),
('Taylor', '3126', 80)
ON CONFLICT (building, room_no) DO NOTHING;

INSERT INTO sandbox.course VALUES
('CS-101', 'Intro. to Computer Science', 'Comp. Sci.', 4),
('CS-201', 'Data Structures', 'Comp. Sci.', 4),
('CS-315', 'Database Systems', 'Comp. Sci.', 3),
('CS-319', 'Computer Networks', 'Comp. Sci.', 3),
('CS-347', 'Operating Systems', 'Comp. Sci.', 3),
('EE-181', 'Intro. to Digital Systems', 'Elec. Eng.', 3),
('PHY-101', 'Physical Principles', 'Physics', 4),
('BIO-301', 'Genetics', 'Biology', 4),
('BIO-399', 'Computational Biology', 'Biology', 3),
('HIS-351', 'World History', 'History', 3),
('FIN-201', 'Investment Banking', 'Finance', 3),
('MU-199', 'Music Video Production', 'Music', 3),
('MAT-101', 'Calculus I', 'Math', 4),
('MAT-201', 'Linear Algebra', 'Math', 3)
ON CONFLICT (course_id) DO NOTHING;

INSERT INTO sandbox.instructor VALUES
('10101', 'Srinivasan', 'Comp. Sci.', 65000),
('12121', 'Wu', 'Finance', 90000),
('15151', 'Mozart', 'Music', 40000),
('22222', 'Einstein', 'Physics', 95000),
('32343', 'El Said', 'History', 60000),
('33456', 'Gold', 'Physics', 87000),
('45565', 'Katz', 'Comp. Sci.', 75000),
('58583', 'Califieri', 'History', 62000),
('76543', 'Singh', 'Finance', 80000),
('76766', 'Crick', 'Biology', 72000),
('83821', 'Brandt', 'Comp. Sci.', 92000),
('98345', 'Kim', 'Elec. Eng.', 80000)
ON CONFLICT (ID) DO NOTHING;

INSERT INTO sandbox.student VALUES
('00128', 'Zhang', 'Comp. Sci.', 102),
('12345', 'Shankar', 'Comp. Sci.', 32),
('19991', 'Brandt', 'History', 80),
('23121', 'Chavez', 'Finance', 110),
('44553', 'Peltier', 'Physics', 56),
('45678', 'Levy', 'Physics', 46),
('54321', 'Williams', 'Comp. Sci.', 54),
('55739', 'Sanchez', 'Music', 38),
('70557', 'Snow', 'Physics', 0),
('76543', 'Brown', 'Comp. Sci.', 58),
('76653', 'Aoi', 'Elec. Eng.', 60),
('98765', 'Bourikas', 'Elec. Eng.', 98),
('98988', 'Tanaka', 'Biology', 120),
('11111', 'Adams', 'Comp. Sci.', 85),
('22222', 'Baker', 'Physics', 72),
('33333', 'Cooper', 'Finance', 95)
ON CONFLICT (ID) DO NOTHING;

INSERT INTO sandbox.time_slot VALUES
('A', 'M', '08:00', '08:50'),
('A', 'W', '08:00', '08:50'),
('A', 'F', '08:00', '08:50'),
('B', 'M', '09:00', '09:50'),
('B', 'W', '09:00', '09:50'),
('B', 'F', '09:00', '09:50'),
('C', 'M', '11:00', '12:30'),
('C', 'W', '11:00', '12:30'),
('D', 'M', '13:00', '14:30'),
('D', 'W', '13:00', '14:30'),
('E', 'T', '10:30', '11:45'),
('E', 'Th', '10:30', '11:45'),
('F', 'T', '14:30', '15:45'),
('F', 'Th', '14:30', '15:45'),
('G', 'F', '14:00', '16:00'),
('H', 'W', '10:00', '12:30')
ON CONFLICT (time_slot_id) DO NOTHING;

INSERT INTO sandbox.section VALUES
('CS-101', '1', 'Fall', 2009, 'Packard', '101', 'H'),
('CS-101', '2', 'Fall', 2009, 'Painter', '514', 'F'),
('CS-201', '1', 'Spring', 2010, 'Taylor', '3128', 'E'),
('CS-315', '1', 'Spring', 2010, 'Taylor', '3128', 'B'),
('CS-319', '1', 'Spring', 2010, 'Taylor', '3126', 'C'),
('CS-319', '2', 'Spring', 2010, 'Taylor', '3126', 'D'),
('CS-347', '1', 'Fall', 2009, 'Taylor', '3128', 'A'),
('EE-181', '1', 'Spring', 2009, 'Taylor', '3128', 'C'),
('FIN-201', '1', 'Spring', 2010, 'Packard', '101', 'B'),
('HIS-351', '1', 'Spring', 2010, 'Painter', '514', 'C'),
('MU-199', '1', 'Spring', 2010, 'Packard', '101', 'D'),
('PHY-101', '1', 'Fall', 2009, 'Watson', '100', 'A'),
('BIO-301', '1', 'Summer', 2009, 'Watson', '120', 'E'),
('BIO-399', '1', 'Summer', 2010, 'Taylor', '3108', 'G'),
('CS-101', '2', 'Spring', 2010, 'Painter', '514', 'F')
ON CONFLICT (course_id, sec_id, semester, year) DO NOTHING;

INSERT INTO sandbox.takes VALUES
('00128', 'CS-101', '1', 'Fall', 2009, 'A'),
('00128', 'CS-347', '1', 'Fall', 2009, 'A-'),
('12345', 'CS-101', '1', 'Fall', 2009, 'C'),
('12345', 'CS-315', '1', 'Spring', 2010, 'A'),
('12345', 'CS-347', '1', 'Fall', 2009, 'A'),
('19991', 'HIS-351', '1', 'Spring', 2010, 'B'),
('23121', 'FIN-201', '1', 'Spring', 2010, 'C+'),
('44553', 'PHY-101', '1', 'Fall', 2009, 'B-'),
('45678', 'CS-101', '1', 'Fall', 2009, 'F'),
('45678', 'CS-101', '2', 'Spring', 2010, 'B+'),
('45678', 'CS-319', '1', 'Spring', 2010, 'B'),
('54321', 'CS-101', '1', 'Fall', 2009, 'A-'),
('55739', 'MU-199', '1', 'Spring', 2010, 'A-'),
('76543', 'CS-101', '2', 'Spring', 2010, 'A'),
('76543', 'CS-319', '2', 'Spring', 2010, 'A'),
('76653', 'EE-181', '1', 'Spring', 2009, 'C'),
('98765', 'CS-101', '1', 'Fall', 2009, 'C-'),
('98765', 'CS-315', '1', 'Spring', 2010, 'B'),
('98988', 'BIO-301', '1', 'Summer', 2009, 'A'),
('98988', 'BIO-399', '1', 'Summer', 2010, 'A'),
('11111', 'CS-101', '1', 'Fall', 2009, 'B+'),
('22222', 'PHY-101', '1', 'Fall', 2009, 'A'),
('33333', 'FIN-201', '1', 'Spring', 2010, 'A-')
ON CONFLICT (ID, course_id, sec_id, semester, year) DO NOTHING;

INSERT INTO sandbox.teaches VALUES
('10101', 'CS-101', '1', 'Fall', 2009),
('10101', 'CS-315', '1', 'Spring', 2010),
('10101', 'CS-347', '1', 'Fall', 2009),
('12121', 'FIN-201', '1', 'Spring', 2010),
('15151', 'MU-199', '1', 'Spring', 2010),
('22222', 'PHY-101', '1', 'Fall', 2009),
('32343', 'HIS-351', '1', 'Spring', 2010),
('45565', 'CS-101', '1', 'Fall', 2009),
('45565', 'CS-319', '1', 'Spring', 2010),
('76766', 'BIO-301', '1', 'Summer', 2009),
('76766', 'BIO-399', '1', 'Summer', 2010),
('83821', 'CS-101', '2', 'Spring', 2010),
('83821', 'CS-319', '2', 'Spring', 2010),
('98345', 'EE-181', '1', 'Spring', 2009)
ON CONFLICT (ID, course_id, sec_id, semester, year) DO NOTHING;

INSERT INTO sandbox.prereq VALUES
('CS-201', 'CS-101'),
('CS-315', 'CS-201'),
('CS-319', 'CS-101'),
('CS-347', 'CS-201'),
('BIO-399', 'BIO-301'),
('MAT-201', 'MAT-101')
ON CONFLICT (course_id, prereq_id) DO NOTHING;

INSERT INTO sandbox.advisor VALUES
('00128', '10101'),
('12345', '10101'),
('19991', '32343'),
('23121', '12121'),
('44553', '22222'),
('45678', '22222'),
('54321', '45565'),
('55739', '15151'),
('76543', '45565'),
('76653', '98345'),
('98765', '10101'),
('98988', '76766'),
('11111', '10101'),
('22222', '22222'),
('33333', '12121')
ON CONFLICT (s_ID) DO NOTHING;

-- 8. Grant SELECT to equilibria_user on sandbox (for testing)
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'equilibria_user') THEN
        GRANT SELECT ON ALL TABLES IN SCHEMA sandbox TO equilibria_user;
    END IF;
END
$$;