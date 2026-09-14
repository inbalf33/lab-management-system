from datetime import datetime
from app.database import engine, SessionLocal, Base
from app import models

def init_db():
    # 1. Create all tables in the SQLite database
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        if db.query(models.College).first():
            print("Database already contains data. Skipping seed.")
            return

        print("Seeding initial data from original seed.sql into database...")

        # 1. Colleges
        c1 = models.College(college_name="עזריאלי")
        c2 = models.College(college_name="מכון לב")
        c3 = models.College(college_name="מכון טל")
        db.add_all([c1, c2, c3])
        db.commit()

        # 2. Courses
        course1 = models.Course(
            college_id=c1.college_id,
            course_name="CIM",
            course_code="CIM-2026-A",
            lab_work_weight=70,
            prep_report_weight=7,
            summary_report_weight=3,
            final_lab_weight=20,
            quiz_weight=0,
            is_active=True
        )
        db.add(course1)
        db.commit()

        # 3. Users (Admin, Lecturer, Instructors, Students)
        users_data = [
            # Admin
            models.User(id_number="307861781", first_name="ענבל", last_name="פיש", email=None, password=None, role="admin", is_miluim=False, is_active=True),
            # Lecturer
            models.User(id_number="307471201", first_name="דוד", last_name="אבישי", email=None, password=None, role="lecturer", is_miluim=False, is_active=True),
            # Instructors
            models.User(id_number="201632346", first_name="גארו", last_name="קבושיאן", email=None, password=None, role="instructor", is_miluim=False, is_active=True),
            models.User(id_number="322974866", first_name="יאנה", last_name="שפירא", email=None, password=None, role="instructor", is_miluim=False, is_active=True),
            # Group 1 Students
            models.User(id_number="311111111", first_name="סטודנט בדיקה1", last_name="ישראלי", email=None, password=None, role="student", is_miluim=False, is_active=True), # index 4
            models.User(id_number="322222222", first_name="דניאל", last_name="כהן", email=None, password=None, role="student", is_miluim=True, is_active=True),         # index 5
            models.User(id_number="333333333", first_name="דניאל", last_name="לוי", email=None, password=None, role="student", is_miluim=False, is_active=True),        # index 6
            models.User(id_number="344444444", first_name="יוסי", last_name="כהן", email=None, password=None, role="student", is_miluim=False, is_active=True),         # index 7
            models.User(id_number="355555555", first_name="מיכל", last_name="אברהם", email=None, password=None, role="student", is_miluim=False, is_active=True),       # index 8
            # Group 2 Students
            models.User(id_number="366666666", first_name="נועה", last_name="שפירא", email=None, password=None, role="student", is_miluim=False, is_active=True),       # index 9
            models.User(id_number="377777777", first_name="עומר", last_name="פרץ", email=None, password=None, role="student", is_miluim=True, is_active=True),          # index 10
            models.User(id_number="388888888", first_name="רועי", last_name="אזולאי", email=None, password=None, role="student", is_miluim=False, is_active=True),       # index 11
            models.User(id_number="399999999", first_name="מאיה", last_name="לוי", email=None, password=None, role="student", is_miluim=False, is_active=True),         # index 12
            models.User(id_number="310101010", first_name="איתי", last_name="גולן", email=None, password=None, role="student", is_miluim=True, is_active=True),          # index 13
            models.User(id_number="312121212", first_name="שירה", last_name="חדד", email=None, password=None, role="student", is_miluim=False, is_active=True),         # index 14
        ]
        db.add_all(users_data)
        db.commit()

        # 4. Lab Groups
        g1 = models.LabGroup(course_id=course1.course_id, group_code="C-A1", day="שני", time="10:00 - 12:45", instructor_id=users_data[2].user_id, lecturer_id=users_data[1].user_id)
        g2 = models.LabGroup(course_id=course1.course_id, group_code="C-A2", day="רביעי", time="09:00 - 11:45", instructor_id=users_data[3].user_id, lecturer_id=users_data[1].user_id)
        db.add_all([g1, g2])
        db.commit()

        # 5. Assign Students to Lab Groups with team_code
        group_students_data = [
            # Group 1
            {"group_id": g1.group_id, "student_id": users_data[4].user_id, "team_code": "A1"},
            {"group_id": g1.group_id, "student_id": users_data[5].user_id, "team_code": "A1"},
            {"group_id": g1.group_id, "student_id": users_data[6].user_id, "team_code": "B1"},
            {"group_id": g1.group_id, "student_id": users_data[7].user_id, "team_code": "B1"},
            {"group_id": g1.group_id, "student_id": users_data[8].user_id, "team_code": "C1"},
            # Group 2
            {"group_id": g2.group_id, "student_id": users_data[9].user_id, "team_code": "A2"},
            {"group_id": g2.group_id, "student_id": users_data[10].user_id, "team_code": "A2"},
            {"group_id": g2.group_id, "student_id": users_data[11].user_id, "team_code": "B2"},
            {"group_id": g2.group_id, "student_id": users_data[12].user_id, "team_code": "B2"},
            {"group_id": g2.group_id, "student_id": users_data[13].user_id, "team_code": "C2"},
            {"group_id": g2.group_id, "student_id": users_data[14].user_id, "team_code": "C2"},
        ]
        
        # הכנסה ישירה לטבלת המקשרת עם ה-team_code
        stmt = models.group_students.insert().values(group_students_data)
        db.execute(stmt)
        db.commit()

        # 6. Lab Topics
        topics = [
            models.LabTopic(course_id=course1.course_id, topic_name="מבוא והדגמה"),
            models.LabTopic(course_id=course1.course_id, topic_name="רובוטיקה 1"),
            models.LabTopic(course_id=course1.course_id, topic_name="רובוטיקה 2"),
            models.LabTopic(course_id=course1.course_id, topic_name="רובוטיקה 3"),
            models.LabTopic(course_id=course1.course_id, topic_name="רובוטיקה 4"),
            models.LabTopic(course_id=course1.course_id, topic_name="PLC"),
            models.LabTopic(course_id=course1.course_id, topic_name="CNC כרסומת"),
            models.LabTopic(course_id=course1.course_id, topic_name="CNC מחרטה"),
            models.LabTopic(course_id=course1.course_id, topic_name="CIM"),
            models.LabTopic(course_id=course1.course_id, topic_name="מעבדה מסכמת"),
        ]
        db.add_all(topics)
        db.commit()

        # 7. Lab Schedules
        schedules_g1 = [
            models.LabSchedule(group_id=g1.group_id, topic_id=topics[0].topic_id, lab_date=datetime(2026, 10, 12, 10, 0), week_number=1, session_type="INTRO"),
            models.LabSchedule(group_id=g1.group_id, topic_id=topics[1].topic_id, lab_date=datetime(2026, 10, 19, 10, 0), week_number=2, session_type="REGULAR"),
            models.LabSchedule(group_id=g1.group_id, topic_id=topics[2].topic_id, lab_date=datetime(2026, 10, 26, 10, 0), week_number=3, session_type="REGULAR"),
            models.LabSchedule(group_id=g1.group_id, topic_id=topics[3].topic_id, lab_date=datetime(2026, 11, 2, 10, 0), week_number=4, session_type="REGULAR"),
            models.LabSchedule(group_id=g1.group_id, topic_id=topics[4].topic_id, lab_date=datetime(2026, 11, 9, 10, 0), week_number=5, session_type="REGULAR"),
            models.LabSchedule(group_id=g1.group_id, topic_id=topics[5].topic_id, lab_date=datetime(2026, 11, 16, 10, 0), week_number=6, session_type="REGULAR"),
            models.LabSchedule(group_id=g1.group_id, topic_id=topics[6].topic_id, lab_date=datetime(2026, 11, 23, 10, 0), week_number=7, session_type="REGULAR"),
            models.LabSchedule(group_id=g1.group_id, topic_id=topics[7].topic_id, lab_date=datetime(2026, 11, 30, 10, 0), week_number=8, session_type="REGULAR"),
            models.LabSchedule(group_id=g1.group_id, topic_id=topics[8].topic_id, lab_date=datetime(2026, 12, 7, 10, 0), week_number=9, session_type="REGULAR"),
            models.LabSchedule(group_id=g1.group_id, topic_id=topics[9].topic_id, lab_date=datetime(2026, 12, 14, 10, 0), week_number=10, session_type="FINAL_LAB"),
            models.LabSchedule(group_id=g1.group_id, topic_id=topics[0].topic_id, lab_date=datetime(2026, 12, 21, 10, 0), week_number=11, session_type="COMPLETION"),
            models.LabSchedule(group_id=g1.group_id, topic_id=topics[0].topic_id, lab_date=datetime(2026, 12, 28, 10, 0), week_number=12, session_type="COMPLETION"),
            models.LabSchedule(group_id=g1.group_id, topic_id=topics[0].topic_id, lab_date=datetime(2027, 1, 4, 10, 0), week_number=13, session_type="COMPLETION"),
        ]

        schedules_g2 = [
            models.LabSchedule(group_id=g2.group_id, topic_id=topics[0].topic_id, lab_date=datetime(2026, 10, 14, 9, 0), week_number=1, session_type="INTRO"),
            models.LabSchedule(group_id=g2.group_id, topic_id=topics[1].topic_id, lab_date=datetime(2026, 10, 21, 9, 0), week_number=2, session_type="REGULAR"),
            models.LabSchedule(group_id=g2.group_id, topic_id=topics[2].topic_id, lab_date=datetime(2026, 10, 28, 9, 0), week_number=3, session_type="REGULAR"),
            models.LabSchedule(group_id=g2.group_id, topic_id=topics[3].topic_id, lab_date=datetime(2026, 11, 4, 9, 0), week_number=4, session_type="REGULAR"),
            models.LabSchedule(group_id=g2.group_id, topic_id=topics[4].topic_id, lab_date=datetime(2026, 11, 11, 9, 0), week_number=5, session_type="REGULAR"),
            models.LabSchedule(group_id=g2.group_id, topic_id=topics[5].topic_id, lab_date=datetime(2026, 11, 18, 9, 0), week_number=6, session_type="REGULAR"),
            models.LabSchedule(group_id=g2.group_id, topic_id=topics[6].topic_id, lab_date=datetime(2026, 11, 25, 9, 0), week_number=7, session_type="REGULAR"),
            models.LabSchedule(group_id=g2.group_id, topic_id=topics[7].topic_id, lab_date=datetime(2026, 12, 2, 9, 0), week_number=8, session_type="REGULAR"),
            models.LabSchedule(group_id=g2.group_id, topic_id=topics[8].topic_id, lab_date=datetime(2026, 12, 9, 9, 0), week_number=9, session_type="REGULAR"),
            models.LabSchedule(group_id=g2.group_id, topic_id=topics[9].topic_id, lab_date=datetime(2026, 12, 16, 9, 0), week_number=10, session_type="FINAL_LAB"),
            models.LabSchedule(group_id=g2.group_id, topic_id=topics[0].topic_id, lab_date=datetime(2026, 12, 23, 9, 0), week_number=11, session_type="COMPLETION"),
            models.LabSchedule(group_id=g2.group_id, topic_id=topics[0].topic_id, lab_date=datetime(2027, 1, 6, 9, 0), week_number=12, session_type="COMPLETION"),
            models.LabSchedule(group_id=g2.group_id, topic_id=topics[0].topic_id, lab_date=datetime(2027, 1, 13, 9, 0), week_number=13, session_type="COMPLETION"),
        ]
        db.add_all(schedules_g1 + schedules_g2)
        db.commit()

        # 8. Sample Grades
        grades_data = [
            # Group C-A1 Week 1
            models.Grade(schedule_id=schedules_g1[0].schedule_id, student_id=users_data[4].user_id, attendance_status="present", internal_notes="מפגש מבוא - נוכח", student_feedback="מפגש מבוא והדגמה"),
            models.Grade(schedule_id=schedules_g1[0].schedule_id, student_id=users_data[5].user_id, attendance_status="present", internal_notes="מפגש מבוא - נוכח", student_feedback="מפגש מבוא והדגמה"),
            models.Grade(schedule_id=schedules_g1[0].schedule_id, student_id=users_data[6].user_id, attendance_status="present", internal_notes="מפגש מבוא - נוכח", student_feedback="מפגש מבוא והדגמה"),
            models.Grade(schedule_id=schedules_g1[0].schedule_id, student_id=users_data[7].user_id, attendance_status="present", internal_notes="מפגש מבוא - נוכח", student_feedback="מפגש מבוא והדגמה"),
            models.Grade(schedule_id=schedules_g1[0].schedule_id, student_id=users_data[8].user_id, attendance_status="present", internal_notes="מפגש מבוא - נוכח", student_feedback="מפגש מבוא והדגמה"),
            # Group C-A1 Week 2
            models.Grade(schedule_id=schedules_g1[1].schedule_id, student_id=users_data[4].user_id, attendance_status="present", lab_work_grade=92, prep_report_grade=100, summary_report_grade=88, final_calculated_grade=93, internal_notes="תפקוד מעולה בזוג", student_feedback="עבודה מצוינת"),
            models.Grade(schedule_id=schedules_g1[1].schedule_id, student_id=users_data[5].user_id, attendance_status="miluim", internal_notes="זימון מילואים פקודתי - אושר", student_feedback="מאושר מילואים"),
            models.Grade(schedule_id=schedules_g1[1].schedule_id, student_id=users_data[6].user_id, attendance_status="present", lab_work_grade=85, prep_report_grade=90, summary_report_grade=82, final_calculated_grade=86, internal_notes="עבודה טובה, הציג יפה", student_feedback="כל הכבוד"),
            models.Grade(schedule_id=schedules_g1[1].schedule_id, student_id=users_data[7].user_id, attendance_status="present", lab_work_grade=85, prep_report_grade=90, summary_report_grade=82, final_calculated_grade=86, internal_notes="עבד בזוג עם דניאל לוי", student_feedback="כל הכבוד"),
            models.Grade(schedule_id=schedules_g1[1].schedule_id, student_id=users_data[8].user_id, attendance_status="present", lab_work_grade=78, prep_report_grade=100, summary_report_grade=75, final_calculated_grade=82, internal_notes="עבד לבד (מספר אי זוגי בצוות)", student_feedback="התמודדות טובה בעבודה יחידנית"),
            # Group C-A1 Week 3
            models.Grade(schedule_id=schedules_g1[2].schedule_id, student_id=users_data[4].user_id, attendance_status="present", lab_work_grade=95, prep_report_grade=95, summary_report_grade=90, final_calculated_grade=93, internal_notes="שליטה מצוינת בחומר", student_feedback="עבודה מעולה"),
            models.Grade(schedule_id=schedules_g1[2].schedule_id, student_id=users_data[5].user_id, attendance_status="present", lab_work_grade=88, prep_report_grade=90, summary_report_grade=85, final_calculated_grade=87, internal_notes="חזר ממילואים, ביצוע יפה", student_feedback="חזרה טובה לשגרה"),
            models.Grade(schedule_id=schedules_g1[2].schedule_id, student_id=users_data[6].user_id, attendance_status="present", lab_work_grade=90, prep_report_grade=85, summary_report_grade=88, final_calculated_grade=88, internal_notes="עבודה זוגית טובה", student_feedback="שיפור ניכר"),
            models.Grade(schedule_id=schedules_g1[2].schedule_id, student_id=users_data[7].user_id, attendance_status="present", lab_work_grade=90, prep_report_grade=85, summary_report_grade=88, final_calculated_grade=88, internal_notes="עבודה זוגית טובה", student_feedback="שיפור ניכר"),
            models.Grade(schedule_id=schedules_g1[2].schedule_id, student_id=users_data[8].user_id, attendance_status="absent", internal_notes="נעדר ללא הצדקה", student_feedback="חיסור לא מוצדק"),
            # Group C-A2 Week 1
            models.Grade(schedule_id=schedules_g2[0].schedule_id, student_id=users_data[9].user_id, attendance_status="present", internal_notes="מפגש מבוא - נוכחת", student_feedback="מפגש מבוא והדגמה"),
            models.Grade(schedule_id=schedules_g2[0].schedule_id, student_id=users_data[10].user_id, attendance_status="present", internal_notes="מפגש מבוא - נוכח", student_feedback="מפגש מבוא והדגמה"),
            models.Grade(schedule_id=schedules_g2[0].schedule_id, student_id=users_data[11].user_id, attendance_status="present", internal_notes="מפגש מבוא - נוכח", student_feedback="מפגש מבוא והדגמה"),
            models.Grade(schedule_id=schedules_g2[0].schedule_id, student_id=users_data[12].user_id, attendance_status="present", internal_notes="מפגש מבוא - נוכח", student_feedback="מפגש מבוא והדגמה"),
            models.Grade(schedule_id=schedules_g2[0].schedule_id, student_id=users_data[13].user_id, attendance_status="present", internal_notes="מפגש מבוא - נוכח", student_feedback="מפגש מבוא והדגמה"),
            models.Grade(schedule_id=schedules_g2[0].schedule_id, student_id=users_data[14].user_id, attendance_status="present", internal_notes="מפגש מבוא - נוכחת", student_feedback="מפגש מבוא והדגמה"),
            # Group C-A2 Week 2
            models.Grade(schedule_id=schedules_g2[1].schedule_id, student_id=users_data[9].user_id, attendance_status="present", lab_work_grade=90, prep_report_grade=95, summary_report_grade=92, final_calculated_grade=92, internal_notes="עבודה יפה מאוד", student_feedback="תפקוד מצוין"),
            models.Grade(schedule_id=schedules_g2[1].schedule_id, student_id=users_data[10].user_id, attendance_status="present", lab_work_grade=90, prep_report_grade=95, summary_report_grade=92, final_calculated_grade=92, internal_notes="עבודה יפה מאוד", student_feedback="תפקוד מצוין"),
            models.Grade(schedule_id=schedules_g2[1].schedule_id, student_id=users_data[11].user_id, attendance_status="present", lab_work_grade=82, prep_report_grade=80, summary_report_grade=85, final_calculated_grade=83, internal_notes="הבנה טובה של החומר", student_feedback="עבודה טובה"),
            models.Grade(schedule_id=schedules_g2[1].schedule_id, student_id=users_data[12].user_id, attendance_status="present", lab_work_grade=82, prep_report_grade=80, summary_report_grade=85, final_calculated_grade=83, internal_notes="הבנה טובה של החומר", student_feedback="עבודה טובה"),
            models.Grade(schedule_id=schedules_g2[1].schedule_id, student_id=users_data[13].user_id, attendance_status="present", lab_work_grade=88, prep_report_grade=90, summary_report_grade=85, final_calculated_grade=87, internal_notes="ביצוע חלק של התרגיל", student_feedback="כל הכבוד"),
            models.Grade(schedule_id=schedules_g2[1].schedule_id, student_id=users_data[14].user_id, attendance_status="present", lab_work_grade=88, prep_report_grade=90, summary_report_grade=85, final_calculated_grade=87, internal_notes="ביצוע חלק של התרגיל", student_feedback="כל הכבוד"),
        ]
        db.add_all(grades_data)
        db.commit()

        print("Database initialized and seeded successfully with original seed data!")

    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()