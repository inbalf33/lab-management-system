-- 1. Insert Colleges
INSERT INTO Colleges (college_name) VALUES 
('עזריאלי'),
('מכון לב'),
('מכון טל');

-- 2. Insert Courses (CIM for Azrieli with standard weights: 70% lab, 7% prep, 3% summary, 20% final lab)
INSERT INTO Courses (college_id, course_name, course_code, lab_work_weight, prep_report_weight, summary_report_weight, final_lab_weight, quiz_weight, is_active)
VALUES (1, 'CIM', 'CIM-2026-A', 70, 7, 3, 20, 0, true);

-- 3. Insert Users (Admin initialized, others pending registration with NULL email/password)
INSERT INTO Users (id_number, first_name, last_name, email, password, role, is_miluim, is_active) VALUES
-- Admin (Active with pre-configured password)
('307861781', 'ענבל', 'פיש', 'inbalf33@gmail.com', 'hashed_password_123', 'admin', false, true),

-- Lecturer (Pending registration)
('307471201', 'דוד', 'אבישי', NULL, NULL, 'lecturer', false, true),

-- Instructors (Pending registration)
('201632346', 'גארו', 'קבושיאן', NULL, NULL, 'instructor', false, true),
('322974866', 'יאנה', 'שפירא', NULL, NULL, 'instructor', false, true),

-- Students Group 1 (Pending registration)
('311111111', 'סטודנט בדיקה1', 'ישראלי', NULL, NULL, 'student', false, true),
('322222222', 'דניאל', 'כהן', NULL, NULL, 'student', true, true), -- מילואים
('333333333', 'דניאל', 'לוי', NULL, NULL, 'student', false, true),
('344444444', 'יוסי', 'כהן', NULL, NULL, 'student', false, true),
('355555555', 'מיכל', 'אברהם', NULL, NULL, 'student', false, true),

-- Students Group 2 (Pending registration)
('366666666', 'נועה', 'שפירא', NULL, NULL, 'student', false, true),
('377777777', 'עומר', 'פרץ', NULL, NULL, 'student', true, true), -- מילואים
('388888888', 'רועי', 'אזולאי', NULL, NULL, 'student', false, true),
('399999999', 'מאיה', 'לוי', NULL, NULL, 'student', false, true),
('310101010', 'איתי', 'גולן', NULL, NULL, 'student', true, true), -- מילואים
('312121212', 'שירה', 'חדד', NULL, NULL, 'student', false, true);

-- 4. Insert Lab Groups (Time Slots)
INSERT INTO Lab_Groups (course_id, group_code, day, time, instructor_id, lecturer_id) VALUES
(1, 'Group 1', 'שני', '10:00 - 12:45', 3, 2), -- קבוצת זמן 1 (שני בבוקר)
(1, 'Group 2', 'רביעי', '09:00 - 11:45', 4, 2); -- קבוצת זמן 2 (רביעי בבוקר)

-- 5. Assign Students to Lab Groups & Teams
-- Group 1 (5 Students, Split into Pairs + 1 Solo)
INSERT INTO Group_Students (group_id, student_id, team_code) VALUES
(1, 5, 'A1'),
(1, 6, 'A1'),
(1, 7, 'A2'),
(1, 8, 'A2'),
(1, 9, 'A3');

-- Group 2 (6 Students, Split into Pairs)
INSERT INTO Group_Students (group_id, student_id, team_code) VALUES
(2, 10, 'B1'),
(2, 11, 'B1'),
(2, 12, 'B2'),
(2, 13, 'B2'),
(2, 14, 'B3'),
(2, 15, 'B3');

-- 6. Insert Lab Topics for CIM (Order of execution)
INSERT INTO Lab_Topics (course_id, topic_name) VALUES
(1, 'מבוא והדגמה'),
(1, 'רובוטיקה 1'),
(1, 'רובוטיקה 2'),
(1, 'רובוטיקה 3'),
(1, 'רובוטיקה 4'),
(1, 'PLC'),
(1, 'CNC כרסומת'),
(1, 'CNC מחרטה'),
(1, 'CIM'),
(1, 'מעבדה מסכמת');

-- 7. Insert Lab Schedules (13 Weeks starting October 11, 2026)
-- Group 1 (Mondays starting Oct 12, 2026)
INSERT INTO Lab_Schedules (group_id, topic_id, lab_date, week_number, session_type) VALUES
(1, 1, '2026-10-12 10:00:00', 1, 'INTRO'), 
(1, 2, '2026-10-19 10:00:00', 2, 'REGULAR'),     
(1, 3, '2026-10-26 10:00:00', 3, 'REGULAR'),
(1, 4, '2026-11-02 10:00:00', 4, 'REGULAR'),
(1, 5, '2026-11-09 10:00:00', 5, 'REGULAR'),
(1, 6, '2026-11-16 10:00:00', 6, 'REGULAR'),
(1, 7, '2026-11-23 10:00:00', 7, 'REGULAR'),
(1, 8, '2026-11-30 10:00:00', 8, 'REGULAR'),
(1, 9, '2026-12-07 10:00:00', 9, 'REGULAR'),
(1, 10, '2026-12-14 10:00:00', 10, 'FINAL_LAB'),
(1, 11, '2026-12-21 10:00:00', 11, 'COMPLETION'),
(1, 12, '2026-12-28 10:00:00', 12, 'COMPLETION'),
(1, 13, '2027-01-04 10:00:00', 13, 'COMPLETION');

-- Group 2 (Wednesdays starting Oct 14, 2026)
INSERT INTO Lab_Schedules (group_id, topic_id, lab_date, week_number, session_type) VALUES
(2, 1, '2026-10-14 09:00:00', 1, 'INTRO'),
(2, 2, '2026-10-21 09:00:00', 2, 'REGULAR'),
(2, 3, '2026-10-28 09:00:00', 3, 'REGULAR'),
(2, 4, '2026-11-04 09:00:00', 4, 'REGULAR'),
(2, 5, '2026-11-11 09:00:00', 5, 'REGULAR'),
(2, 6, '2026-11-18 09:00:00', 6, 'REGULAR'),
(2, 7, '2026-11-25 09:00:00', 7, 'REGULAR'),
(2, 8, '2026-12-02 09:00:00', 8, 'REGULAR'),
(2, 9, '2026-12-09 09:00:00', 9, 'REGULAR'),
(2, 10, '2026-12-16 09:00:00', 10, 'FINAL_LAB'),
(2, 11, '2026-12-23 09:00:00', 11, 'COMPLETION'),
(2, 12, '2027-01-06 09:00:00', 12, 'COMPLETION'),
(2, 13, '2027-01-13 09:00:00', 13, 'COMPLETION');

-- 8. Insert Sample Grades
-- GROUP 1 (Schedule IDs: 1, 2, 3...)
INSERT INTO Grades (schedule_id, student_id, attendance_status, lab_work_grade, prep_report_grade, summary_report_grade, final_calculated_grade, internal_notes, student_feedback) VALUES
(1, 5, 'present', NULL, NULL, NULL, NULL, 'מפגש מבוא - נוכח', 'מפגש מבוא והדגמה'),
(1, 6, 'present', NULL, NULL, NULL, NULL, 'מפגש מבוא - נוכח', 'מפגש מבוא והדגמה'),
(1, 7, 'present', NULL, NULL, NULL, NULL, 'מפגש מבוא - נוכח', 'מפגש מבוא והדגמה'),
(1, 8, 'present', NULL, NULL, NULL, NULL, 'מפגש מבוא - נוכח', 'מפגש מבוא והדגמה'),
(1, 9, 'present', NULL, NULL, NULL, NULL, 'מפגש מבוא - נוכח', 'מפגש מבוא והדגמה');

INSERT INTO Grades (schedule_id, student_id, attendance_status, lab_work_grade, prep_report_grade, summary_report_grade, final_calculated_grade, internal_notes, student_feedback) VALUES
(2, 5, 'present', 92, 100, 88, 93, 'תפקוד מעולה בזוג A1', 'עבודה מצוינת'),
(2, 6, 'miluim', NULL, NULL, NULL, NULL, 'זימון מילואים פקודתי - אושר', 'מאושר מילואים'),
(2, 7, 'present', 85, 90, 82, 86, 'עבודה טובה, הציג יפה', 'כל הכבוד'),
(2, 8, 'present', 85, 90, 82, 86, 'עבד בזוג A2 עם דניאל לוי', 'כל הכבוד'),
(2, 9, 'present', 78, 100, 75, 82, 'עבד לבד בצוות A3', 'התמודדות טובה בעבודה יחידנית');

INSERT INTO Grades (schedule_id, student_id, attendance_status, lab_work_grade, prep_report_grade, summary_report_grade, final_calculated_grade, internal_notes, student_feedback) VALUES
(3, 5, 'present', 95, 95, 90, 93, 'שליטה מצוינת בחומר', 'עבודה מעולה'),
(3, 6, 'present', 88, 90, 85, 87, 'חזר ממילואים, ביצוע יפה', 'חזרה טובה לשגרה'),
(3, 7, 'present', 90, 85, 88, 88, 'עבודה זוגית טובה', 'שיפור ניכר'),
(3, 8, 'present', 90, 85, 88, 88, 'עבודה זוגית טובה', 'שיפור ניכר'),
(3, 9, 'absent', NULL, NULL, NULL, NULL, 'נעדר ללא הצדקה', 'חיסור לא מוצדק');

-- GROUP 2 (Schedule IDs: 14, 15...)
INSERT INTO Grades (schedule_id, student_id, attendance_status, lab_work_grade, prep_report_grade, summary_report_grade, final_calculated_grade, internal_notes, student_feedback) VALUES
(14, 10, 'present', NULL, NULL, NULL, NULL, 'מפגש מבוא - נוכחת', 'מפגש מבוא והדגמה'),
(14, 11, 'present', NULL, NULL, NULL, NULL, 'מפגש מבוא - נוכח', 'מפגש מבוא והדגמה'),
(14, 12, 'present', NULL, NULL, NULL, NULL, 'מפגש מבוא - נוכח', 'מפגש מבוא והדגמה'),
(14, 13, 'present', NULL, NULL, NULL, NULL, 'מפגש מבוא - נוכח', 'מפגש מבוא והדגמה'),
(14, 14, 'present', NULL, NULL, NULL, NULL, 'מפגש מבוא - נוכח', 'מפגש מבוא והדגמה'),
(14, 15, 'present', NULL, NULL, NULL, NULL, 'מפגש מבוא - נוכחת', 'מפגש מבוא והדגמה');

INSERT INTO Grades (schedule_id, student_id, attendance_status, lab_work_grade, prep_report_grade, summary_report_grade, final_calculated_grade, internal_notes, student_feedback) VALUES
(15, 10, 'present', 90, 95, 92, 92, 'עבודה יפה מאוד', 'תפקוד מצוין'),
(15, 11, 'present', 90, 95, 92, 92, 'עבודה יפה מאוד', 'תפקוד מצוין'),
(15, 12, 'present', 82, 80, 85, 83, 'הבנה טובה של החומר', 'עבודה טובה'),
(15, 13, 'present', 82, 80, 85, 83, 'הבנה טובה של החומר', 'עבודה טובה'),
(15, 14, 'present', 88, 90, 85, 87, 'ביצוע חלק של התרגיל', 'כל הכבוד'),
(15, 15, 'present', 88, 90, 85, 87, 'ביצוע חלק של התרגיל', 'כל הכבוד');