# === init_db.py ===
import sqlite3

conn = sqlite3.connect('database/smartsched.db')
c = conn.cursor()

# Create teachers
c.execute('''
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        available_slots TEXT
    )
''')

# Create classes (student groups)
c.execute('''
    CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        capacity INTEGER
    )
''')

# Create subjects
c.execute('''
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT,
        num_lectures INTEGER,
        num_students INTEGER,
        teacher_id INTEGER,
        class_id INTEGER,
        FOREIGN KEY (teacher_id) REFERENCES teachers(id),
        FOREIGN KEY (class_id) REFERENCES classes(id)
    )
''')

# Create classrooms
c.execute('''
    CREATE TABLE IF NOT EXISTS classrooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        capacity INTEGER
    )
''')

# Create timetable
c.execute('''
    CREATE TABLE IF NOT EXISTS timetable (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER,
        teacher_id INTEGER,
        classroom_id INTEGER,
        class_id INTEGER,
        timeslot TEXT,
        FOREIGN KEY (subject_id) REFERENCES subjects(id),
        FOREIGN KEY (teacher_id) REFERENCES teachers(id),
        FOREIGN KEY (classroom_id) REFERENCES classrooms(id),
        FOREIGN KEY (class_id) REFERENCES classes(id)
    )
''')
c.execute('''
    CREATE TABLE IF NOT EXISTS teacher_availability (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id INTEGER,
        day TEXT,
        start_hour INTEGER,
        end_hour INTEGER,
        FOREIGN KEY (teacher_id) REFERENCES teachers(id)
    )
''')
conn.commit()
conn.close()

print("Database initialized successfully!")
