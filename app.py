<<<<<<< HEAD
from flask import Flask, render_template, request, redirect, url_for, send_file, session
import sqlite3
import pandas as pd
from fpdf import FPDF
import os
from flask import abort, flash


from scheduling.graph_coloring import generate_initial_schedule
from scheduling.backtracking import resolve_conflicts

app = Flask(__name__)
app.secret_key = 'supersecretkey'
DB_PATH = 'database/smartsched.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()

    teachers = conn.execute('SELECT * FROM teachers').fetchall()
    classes = conn.execute('SELECT * FROM classes').fetchall()
    classrooms = conn.execute('SELECT * FROM classrooms').fetchall()
    subjects = conn.execute(
        '''SELECT s.*, t.name AS teacher_name, c.name AS class_name 
           FROM subjects s 
           LEFT JOIN teachers t ON s.teacher_id = t.id
           LEFT JOIN classes c ON s.class_id = c.id'''
    ).fetchall()

    # Fetch and group teacher availability
    availability_raw = conn.execute(
        '''SELECT ta.*, t.name AS teacher_name 
           FROM teacher_availability ta 
           JOIN teachers t ON ta.teacher_id = t.id'''
    ).fetchall()
    conn.close()

    teacher_availability = {}
    for row in availability_raw:
        name = row['teacher_name']
        if name not in teacher_availability:
            teacher_availability[name] = []
        teacher_availability[name].append({
            'day': row['day'],
            'start_hour': row['start_hour'],
            'end_hour': row['end_hour']
        })

    return render_template('index.html',
                           teachers=teachers,
                           classes=classes,
                           classrooms=classrooms,
                           subjects=subjects,
                           teacher_availability=teacher_availability)

@app.route('/add_teacher', methods=['POST'])
def add_teacher():
    name = request.form['name']
    conn = get_db_connection()
    conn.execute('INSERT INTO teachers (name) VALUES (?)', (name,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/add_availability', methods=['POST'])
def add_availability():
    teacher_id = request.form['teacher_id']
    day = request.form['day']
    start_hour = request.form['start_hour']
    end_hour = request.form['end_hour']
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO teacher_availability (teacher_id, day, start_hour, end_hour)
        VALUES (?, ?, ?, ?)
    ''', (teacher_id, day, start_hour, end_hour))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/add_class', methods=['POST'])
def add_class():
    name = request.form['name']
    capacity = request.form['capacity']
    conn = get_db_connection()
    conn.execute('INSERT INTO classes (name, capacity) VALUES (?, ?)', (name, capacity))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/add_classroom', methods=['POST'])
def add_classroom():
    name = request.form['name']
    capacity = request.form['capacity']
    conn = get_db_connection()
    conn.execute('INSERT INTO classrooms (name, capacity) VALUES (?, ?)', (name, capacity))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/add_subject', methods=['POST'])
def add_subject():
    name = request.form['name']
    code = request.form['code']
    num_lectures = request.form['num_lectures']
    num_students = request.form['num_students']
    teacher_id = request.form['teacher_id']
    class_id = request.form['class_id']
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO subjects 
        (name, code, num_lectures, num_students, teacher_id, class_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, code, num_lectures, num_students, teacher_id, class_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/generate')
def generate():
    conn = get_db_connection()
    subjects = conn.execute('SELECT * FROM subjects').fetchall()
    teachers = conn.execute('SELECT * FROM teachers').fetchall()
    classrooms = conn.execute('SELECT * FROM classrooms').fetchall()
    classes = conn.execute('SELECT * FROM classes').fetchall()
    teacher_availability = conn.execute('SELECT * FROM teacher_availability').fetchall()

    initial_schedule, shortages = generate_initial_schedule(
        subjects, teachers, classrooms, classes, teacher_availability
    )
    final_schedule = resolve_conflicts(
        initial_schedule, subjects, teachers, classrooms, classes
    )

    conn.execute('DELETE FROM timetable')
    for entry in final_schedule:
        conn.execute('''
            INSERT INTO timetable (subject_id, teacher_id, classroom_id, class_id, timeslot)
            VALUES (?, ?, ?, ?, ?)
        ''', (entry['subject_id'], entry['teacher_id'],
              entry['classroom_id'], entry['class_id'], entry['timeslot']))
    conn.commit()
    conn.close()

    session['shortages'] = shortages
    return redirect(url_for('timetable'))

@app.route('/timetable')
def timetable():
    conn = get_db_connection()
    timetable = conn.execute(
        '''SELECT timetable.id, subjects.name AS subject, subjects.code AS code,
                  teachers.name AS teacher, classrooms.name AS classroom,
                  classes.name AS class, timetable.timeslot
           FROM timetable
           JOIN subjects ON timetable.subject_id = subjects.id
           JOIN teachers ON timetable.teacher_id = teachers.id
           JOIN classrooms ON timetable.classroom_id = classrooms.id
           JOIN classes ON timetable.class_id = classes.id
           ORDER BY classes.name, timetable.timeslot'''
    ).fetchall()
    conn.close()
    shortages = session.pop('shortages', [])
    return render_template('timetable.html', timetable=timetable, shortages=shortages)

@app.route('/delete_teacher/<int:teacher_id>', methods=['POST'])
def delete_teacher(teacher_id):
    try:
        conn = get_db_connection()
        # Check if teacher exists first
        teacher = conn.execute('SELECT * FROM teachers WHERE id = ?', (teacher_id,)).fetchone()
        if not teacher:
            flash('Teacher not found', 'error')
            return redirect(url_for('index'))
            
        # Use transactions for multiple operations
        with conn:
            conn.execute('DELETE FROM teacher_availability WHERE teacher_id = ?', (teacher_id,))
            conn.execute('DELETE FROM subjects WHERE teacher_id = ?', (teacher_id,))
            conn.execute('DELETE FROM teachers WHERE id = ?', (teacher_id,))
        flash('Teacher deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting teacher: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('index'))

@app.route('/delete_classroom/<int:classroom_id>', methods=['POST'])
def delete_classroom(classroom_id):
    try:
        conn = get_db_connection()
        classroom = conn.execute('SELECT * FROM classrooms WHERE id = ?', (classroom_id,)).fetchone()
        if not classroom:
            flash('Classroom not found', 'error')
            return redirect(url_for('index'))
            
        with conn:
            conn.execute('DELETE FROM classrooms WHERE id = ?', (classroom_id,))
        flash('Classroom deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting classroom: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('index'))

@app.route('/delete_subject/<int:subject_id>', methods=['POST'])
def delete_subject(subject_id):
    try:
        conn = get_db_connection()
        subject = conn.execute('SELECT * FROM subjects WHERE id = ?', (subject_id,)).fetchone()
        if not subject:
            flash('Subject not found', 'error')
            return redirect(url_for('index'))
            
        with conn:
            conn.execute('DELETE FROM subjects WHERE id = ?', (subject_id,))
        flash('Subject deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting subject: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('index'))

@app.route('/delete_class/<int:class_id>', methods=['POST'])
def delete_class(class_id):
    try:
        conn = get_db_connection()
        class_ = conn.execute('SELECT * FROM classes WHERE id = ?', (class_id,)).fetchone()
        if not class_:
            flash('Class not found', 'error')
            return redirect(url_for('index'))
            
        with conn:
            conn.execute('DELETE FROM subjects WHERE class_id = ?', (class_id,))
            conn.execute('DELETE FROM classes WHERE id = ?', (class_id,))
        flash('Class deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting class: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('index'))

@app.route('/export/excel')
def export_excel():
    conn = get_db_connection()
    df = pd.read_sql_query(
        '''SELECT classes.name AS class, subjects.name AS subject, subjects.code AS code,
                  teachers.name AS teacher, classrooms.name AS classroom, timetable.timeslot
           FROM timetable
           JOIN subjects ON timetable.subject_id = subjects.id
           JOIN teachers ON timetable.teacher_id = teachers.id
           JOIN classrooms ON timetable.classroom_id = classrooms.id
           JOIN classes ON timetable.class_id = classes.id
           ORDER BY classes.name, timetable.timeslot''', conn)
    file_path = 'exports/timetable.xlsx'
    df.to_excel(file_path, index=False)
    conn.close()
    return send_file(file_path, as_attachment=True)

@app.route('/export/pdf')
def export_pdf():
    conn = get_db_connection()
    rows = conn.execute(
        '''SELECT classes.name AS class, subjects.name AS subject, subjects.code AS code,
                  teachers.name AS teacher, classrooms.name AS classroom, timetable.timeslot
           FROM timetable
           JOIN subjects ON timetable.subject_id = subjects.id
           JOIN teachers ON timetable.teacher_id = teachers.id
           JOIN classrooms ON timetable.classroom_id = classrooms.id
           JOIN classes ON timetable.class_id = classes.id
           ORDER BY classes.name, timetable.timeslot'''
    ).fetchall()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Generated Timetable', ln=True, align='C')
    pdf.set_font('Arial', '', 10)

    current_class = ''
    for row in rows:
        if row['class'] != current_class:
            current_class = row['class']
            pdf.ln(5)
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 8, f"Class: {current_class}", ln=True)
            pdf.set_font('Arial', '', 10)
        pdf.cell(0, 8, f"{row['timeslot']} - {row['subject']} ({row['code']}) - {row['teacher']} in {row['classroom']}", ln=True)

    file_path = 'exports/timetable.pdf'
    pdf.output(file_path)
    conn.close()
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    if not os.path.exists('exports'):
        os.makedirs('exports')
    app.run(debug=True)
=======
from flask import Flask, render_template, request, redirect, url_for, send_file, session
import sqlite3
import pandas as pd
from fpdf import FPDF
import os
from flask import abort, flash


from scheduling.graph_coloring import generate_initial_schedule
from scheduling.backtracking import resolve_conflicts

app = Flask(__name__)
app.secret_key = 'supersecretkey'
DB_PATH = 'database/smartsched.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()

    teachers = conn.execute('SELECT * FROM teachers').fetchall()
    classes = conn.execute('SELECT * FROM classes').fetchall()
    classrooms = conn.execute('SELECT * FROM classrooms').fetchall()
    subjects = conn.execute(
        '''SELECT s.*, t.name AS teacher_name, c.name AS class_name 
           FROM subjects s 
           LEFT JOIN teachers t ON s.teacher_id = t.id
           LEFT JOIN classes c ON s.class_id = c.id'''
    ).fetchall()

    # Fetch and group teacher availability
    availability_raw = conn.execute(
        '''SELECT ta.*, t.name AS teacher_name 
           FROM teacher_availability ta 
           JOIN teachers t ON ta.teacher_id = t.id'''
    ).fetchall()
    conn.close()

    teacher_availability = {}
    for row in availability_raw:
        name = row['teacher_name']
        if name not in teacher_availability:
            teacher_availability[name] = []
        teacher_availability[name].append({
            'day': row['day'],
            'start_hour': row['start_hour'],
            'end_hour': row['end_hour']
        })

    return render_template('index.html',
                           teachers=teachers,
                           classes=classes,
                           classrooms=classrooms,
                           subjects=subjects,
                           teacher_availability=teacher_availability)

@app.route('/add_teacher', methods=['POST'])
def add_teacher():
    name = request.form['name']
    conn = get_db_connection()
    conn.execute('INSERT INTO teachers (name) VALUES (?)', (name,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/add_availability', methods=['POST'])
def add_availability():
    teacher_id = request.form['teacher_id']
    day = request.form['day']
    start_hour = request.form['start_hour']
    end_hour = request.form['end_hour']
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO teacher_availability (teacher_id, day, start_hour, end_hour)
        VALUES (?, ?, ?, ?)
    ''', (teacher_id, day, start_hour, end_hour))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/add_class', methods=['POST'])
def add_class():
    name = request.form['name']
    capacity = request.form['capacity']
    conn = get_db_connection()
    conn.execute('INSERT INTO classes (name, capacity) VALUES (?, ?)', (name, capacity))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/add_classroom', methods=['POST'])
def add_classroom():
    name = request.form['name']
    capacity = request.form['capacity']
    conn = get_db_connection()
    conn.execute('INSERT INTO classrooms (name, capacity) VALUES (?, ?)', (name, capacity))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/add_subject', methods=['POST'])
def add_subject():
    name = request.form['name']
    code = request.form['code']
    num_lectures = request.form['num_lectures']
    num_students = request.form['num_students']
    teacher_id = request.form['teacher_id']
    class_id = request.form['class_id']
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO subjects 
        (name, code, num_lectures, num_students, teacher_id, class_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, code, num_lectures, num_students, teacher_id, class_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/generate')
def generate():
    conn = get_db_connection()
    subjects = conn.execute('SELECT * FROM subjects').fetchall()
    teachers = conn.execute('SELECT * FROM teachers').fetchall()
    classrooms = conn.execute('SELECT * FROM classrooms').fetchall()
    classes = conn.execute('SELECT * FROM classes').fetchall()
    teacher_availability = conn.execute('SELECT * FROM teacher_availability').fetchall()

    initial_schedule, shortages = generate_initial_schedule(
        subjects, teachers, classrooms, classes, teacher_availability
    )
    final_schedule = resolve_conflicts(
        initial_schedule, subjects, teachers, classrooms, classes
    )

    conn.execute('DELETE FROM timetable')
    for entry in final_schedule:
        conn.execute('''
            INSERT INTO timetable (subject_id, teacher_id, classroom_id, class_id, timeslot)
            VALUES (?, ?, ?, ?, ?)
        ''', (entry['subject_id'], entry['teacher_id'],
              entry['classroom_id'], entry['class_id'], entry['timeslot']))
    conn.commit()
    conn.close()

    session['shortages'] = shortages
    return redirect(url_for('timetable'))

@app.route('/timetable')
def timetable():
    conn = get_db_connection()
    timetable = conn.execute(
        '''SELECT timetable.id, subjects.name AS subject, subjects.code AS code,
                  teachers.name AS teacher, classrooms.name AS classroom,
                  classes.name AS class, timetable.timeslot
           FROM timetable
           JOIN subjects ON timetable.subject_id = subjects.id
           JOIN teachers ON timetable.teacher_id = teachers.id
           JOIN classrooms ON timetable.classroom_id = classrooms.id
           JOIN classes ON timetable.class_id = classes.id
           ORDER BY classes.name, timetable.timeslot'''
    ).fetchall()
    conn.close()
    shortages = session.pop('shortages', [])
    return render_template('timetable.html', timetable=timetable, shortages=shortages)

@app.route('/delete_teacher/<int:teacher_id>', methods=['POST'])
def delete_teacher(teacher_id):
    try:
        conn = get_db_connection()
        # Check if teacher exists first
        teacher = conn.execute('SELECT * FROM teachers WHERE id = ?', (teacher_id,)).fetchone()
        if not teacher:
            flash('Teacher not found', 'error')
            return redirect(url_for('index'))
            
        # Use transactions for multiple operations
        with conn:
            conn.execute('DELETE FROM teacher_availability WHERE teacher_id = ?', (teacher_id,))
            conn.execute('DELETE FROM subjects WHERE teacher_id = ?', (teacher_id,))
            conn.execute('DELETE FROM teachers WHERE id = ?', (teacher_id,))
        flash('Teacher deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting teacher: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('index'))

@app.route('/delete_classroom/<int:classroom_id>', methods=['POST'])
def delete_classroom(classroom_id):
    try:
        conn = get_db_connection()
        classroom = conn.execute('SELECT * FROM classrooms WHERE id = ?', (classroom_id,)).fetchone()
        if not classroom:
            flash('Classroom not found', 'error')
            return redirect(url_for('index'))
            
        with conn:
            conn.execute('DELETE FROM classrooms WHERE id = ?', (classroom_id,))
        flash('Classroom deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting classroom: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('index'))

@app.route('/delete_subject/<int:subject_id>', methods=['POST'])
def delete_subject(subject_id):
    try:
        conn = get_db_connection()
        subject = conn.execute('SELECT * FROM subjects WHERE id = ?', (subject_id,)).fetchone()
        if not subject:
            flash('Subject not found', 'error')
            return redirect(url_for('index'))
            
        with conn:
            conn.execute('DELETE FROM subjects WHERE id = ?', (subject_id,))
        flash('Subject deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting subject: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('index'))

@app.route('/delete_class/<int:class_id>', methods=['POST'])
def delete_class(class_id):
    try:
        conn = get_db_connection()
        class_ = conn.execute('SELECT * FROM classes WHERE id = ?', (class_id,)).fetchone()
        if not class_:
            flash('Class not found', 'error')
            return redirect(url_for('index'))
            
        with conn:
            conn.execute('DELETE FROM subjects WHERE class_id = ?', (class_id,))
            conn.execute('DELETE FROM classes WHERE id = ?', (class_id,))
        flash('Class deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting class: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('index'))

@app.route('/export/excel')
def export_excel():
    conn = get_db_connection()
    df = pd.read_sql_query(
        '''SELECT classes.name AS class, subjects.name AS subject, subjects.code AS code,
                  teachers.name AS teacher, classrooms.name AS classroom, timetable.timeslot
           FROM timetable
           JOIN subjects ON timetable.subject_id = subjects.id
           JOIN teachers ON timetable.teacher_id = teachers.id
           JOIN classrooms ON timetable.classroom_id = classrooms.id
           JOIN classes ON timetable.class_id = classes.id
           ORDER BY classes.name, timetable.timeslot''', conn)
    file_path = 'exports/timetable.xlsx'
    df.to_excel(file_path, index=False)
    conn.close()
    return send_file(file_path, as_attachment=True)

@app.route('/export/pdf')
def export_pdf():
    conn = get_db_connection()
    rows = conn.execute(
        '''SELECT classes.name AS class, subjects.name AS subject, subjects.code AS code,
                  teachers.name AS teacher, classrooms.name AS classroom, timetable.timeslot
           FROM timetable
           JOIN subjects ON timetable.subject_id = subjects.id
           JOIN teachers ON timetable.teacher_id = teachers.id
           JOIN classrooms ON timetable.classroom_id = classrooms.id
           JOIN classes ON timetable.class_id = classes.id
           ORDER BY classes.name, timetable.timeslot'''
    ).fetchall()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Generated Timetable', ln=True, align='C')
    pdf.set_font('Arial', '', 10)

    current_class = ''
    for row in rows:
        if row['class'] != current_class:
            current_class = row['class']
            pdf.ln(5)
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 8, f"Class: {current_class}", ln=True)
            pdf.set_font('Arial', '', 10)
        pdf.cell(0, 8, f"{row['timeslot']} - {row['subject']} ({row['code']}) - {row['teacher']} in {row['classroom']}", ln=True)

    file_path = 'exports/timetable.pdf'
    pdf.output(file_path)
    conn.close()
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    if not os.path.exists('exports'):
        os.makedirs('exports')
    app.run(debug=True)
>>>>>>> c2a9b12ff70651acba4757364b54e8f4d46c2fdc
