-- Drop tables in reverse order of creation to avoid foreign key conflicts
DROP TABLE IF EXISTS Swap_Requests;
DROP TABLE IF EXISTS Cms_Content;
DROP TABLE IF EXISTS Course_Final_Grades;
DROP TABLE IF EXISTS Grades;
DROP TABLE IF EXISTS Lab_Schedules;
DROP TABLE IF EXISTS Lab_Topics;
DROP TABLE IF EXISTS Group_Students;
DROP TABLE IF EXISTS Lab_Groups;
DROP TABLE IF EXISTS Users;
DROP TABLE IF EXISTS Courses;
DROP TABLE IF EXISTS Colleges;

-- 1. Colleges
CREATE TABLE Colleges (
  college_id INT PRIMARY KEY AUTO_INCREMENT,
  college_name VARCHAR(255) NOT NULL
);

-- 2. Courses
CREATE TABLE Courses (
  course_id INT PRIMARY KEY AUTO_INCREMENT,
  college_id INT NOT NULL,
  course_name VARCHAR(255) NOT NULL,
  course_code VARCHAR(255) NOT NULL,
  lab_work_weight INT DEFAULT 100,
  prep_report_weight INT DEFAULT 0,
  summary_report_weight INT DEFAULT 0,
  final_lab_weight INT DEFAULT 0,
  quiz_weight INT DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  FOREIGN KEY (college_id) REFERENCES Colleges(college_id) ON DELETE CASCADE
);

-- 3. Users
CREATE TABLE Users (
  user_id INT PRIMARY KEY AUTO_INCREMENT,
  id_number VARCHAR(255) UNIQUE NOT NULL,
  first_name VARCHAR(255) NOT NULL,
  last_name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NULL,
  password VARCHAR(255) NULL,
  role VARCHAR(255) NOT NULL,
  is_miluim BOOLEAN DEFAULT FALSE,
  is_active BOOLEAN DEFAULT TRUE
);

-- 4. Lab Groups
CREATE TABLE Lab_Groups (
  group_id INT PRIMARY KEY AUTO_INCREMENT,
  course_id INT NOT NULL,
  group_code VARCHAR(255) NOT NULL,
  day VARCHAR(255) NOT NULL,
  time VARCHAR(255) NOT NULL,
  instructor_id INT,
  lecturer_id INT,
  FOREIGN KEY (course_id) REFERENCES Courses(course_id) ON DELETE CASCADE,
  FOREIGN KEY (instructor_id) REFERENCES Users(user_id) ON DELETE SET NULL,
  FOREIGN KEY (lecturer_id) REFERENCES Users(user_id) ON DELETE SET NULL
);

-- 5. Group Students (Junction Table)
CREATE TABLE Group_Students (
  group_id INT NOT NULL,
  student_id INT NOT NULL,
  team_code VARCHAR(255) NULL,
  PRIMARY KEY (group_id, student_id),
  FOREIGN KEY (group_id) REFERENCES Lab_Groups(group_id) ON DELETE CASCADE,
  FOREIGN KEY (student_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

-- 6. Lab Topics
CREATE TABLE Lab_Topics (
  topic_id INT PRIMARY KEY AUTO_INCREMENT,
  course_id INT NOT NULL,
  topic_name VARCHAR(255) NOT NULL,
  FOREIGN KEY (course_id) REFERENCES Courses(course_id) ON DELETE CASCADE
);

-- 7. Lab Schedules
CREATE TABLE Lab_Schedules (
  schedule_id INT PRIMARY KEY AUTO_INCREMENT,
  group_id INT NOT NULL,
  topic_id INT NOT NULL,
  lab_date DATETIME NOT NULL,
  week_number INT NOT NULL,
  session_type VARCHAR(255) DEFAULT 'REGULAR',
  FOREIGN KEY (group_id) REFERENCES Lab_Groups(group_id) ON DELETE CASCADE,
  FOREIGN KEY (topic_id) REFERENCES Lab_Topics(topic_id) ON DELETE CASCADE
);

-- 8. Grades
CREATE TABLE Grades (
  grade_id INT PRIMARY KEY AUTO_INCREMENT,
  schedule_id INT NOT NULL,
  student_id INT NOT NULL,
  attendance_status VARCHAR(255) NOT NULL,
  lab_work_grade INT,
  prep_report_grade INT,
  summary_report_grade INT,
  final_calculated_grade INT,
  internal_notes TEXT NOT NULL,
  student_feedback TEXT,
  FOREIGN KEY (schedule_id) REFERENCES Lab_Schedules(schedule_id) ON DELETE CASCADE,
  FOREIGN KEY (student_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

-- 9. Course Final Grades
CREATE TABLE Course_Final_Grades (
  enrollment_id INT PRIMARY KEY AUTO_INCREMENT,
  course_id INT NOT NULL,
  student_id INT NOT NULL,
  final_score INT,
  is_approved BOOLEAN DEFAULT FALSE,
  updated_at DATETIME,
  FOREIGN KEY (course_id) REFERENCES Courses(course_id) ON DELETE CASCADE,
  FOREIGN KEY (student_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

-- 10. Swap Requests
CREATE TABLE Swap_Requests (
  request_id INT PRIMARY KEY AUTO_INCREMENT,
  student_id INT NOT NULL,
  current_schedule_id INT NOT NULL,
  target_schedule_id INT NOT NULL,
  is_team_swap BOOLEAN DEFAULT TRUE,
  status VARCHAR(255) DEFAULT 'PENDING',
  reason TEXT NOT NULL,
  reviewed_by INT,
  reviewer_notes TEXT,
  created_at DATETIME NOT NULL,
  FOREIGN KEY (student_id) REFERENCES Users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (current_schedule_id) REFERENCES Lab_Schedules(schedule_id) ON DELETE CASCADE,
  FOREIGN KEY (target_schedule_id) REFERENCES Lab_Schedules(schedule_id) ON DELETE CASCADE,
  FOREIGN KEY (reviewed_by) REFERENCES Users(user_id) ON DELETE SET NULL
);

-- 11. CMS Content
CREATE TABLE Cms_Content (
  content_id INT PRIMARY KEY AUTO_INCREMENT,
  key_name VARCHAR(255) UNIQUE NOT NULL,
  content_value TEXT NOT NULL,
  description TEXT,
  is_active BOOLEAN DEFAULT TRUE,
  updated_at DATETIME
);