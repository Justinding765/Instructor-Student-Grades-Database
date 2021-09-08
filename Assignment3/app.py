from flask import Flask, flash, render_template, redirect, request, session, abort, g, url_for
import os
import sqlite3

DATABASE = './assignment3.db'

app = Flask(__name__)

# ===================
# Sqlite Boilerplate
# ===================

#https://flask.palletsprojects.com/en/1.1.x/patterns/sqlite3/
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        # close the database if we are connected to it
        db.close()

# ===================
# Navigation Routes
# ===================

@app.route('/')
def root():
    if 'username' in session:
        return render_template('index.html', session=session)
    else:
        return render_template('login.html')

@app.route('/assignments')
def assignments():
    if 'username' in session:
        return render_template('assignments.html', session=session)
    else:
	    return redirect(url_for('root'))

@app.route('/course-team')
def course_team():
    if 'username' in session:
        return render_template('course-team.html', session=session)
    else:
	    return redirect(url_for('root'))

@app.route('/feedback', methods = ['POST', 'GET'])
def feedback():
    if 'username' not in session:
        return redirect(url_for('root'))

    db = get_db()
    db.row_factory = make_dicts
    instructors = []

    # Load the instructors from the database
    for instructor in query_db("SELECT * FROM Account WHERE type = 'instructor'"):
        instructors.append(instructor)

    if request.method == 'GET':
        if session['accounttype'] == "student":
            db.close()
            return render_template('feedback.html', session=session, instructors=instructors)
        elif session['accounttype'] == "instructor":
            username = "'{}'".format(session['username'])
            feedback = []

            # Load the feedback from the database
            for question in query_db('Select Q1, Q2, Q3, Q4 FROM Feedback WHERE Feedback.username = {}'.format(username)):
                feedback.append(question)
            
            db.close()
            return render_template('student-feedback.html', session=session, feedback=feedback)
    elif request.method == 'POST':
        # Only students can make POST requests to feedback
        if session['accounttype'] != "student":
            return redirect(url_for('feedback'))

        print(request.form)

        q1 = request.form['feedback-1']
        q2 = request.form['feedback-2']
        q3 = request.form['feedback-3']
        q4 = request.form['feedback-4']
        instructorName = request.form['instructor']

        # Error Case 1: Empty fields
        if q1.strip() == '' or q2.strip() == '' or q3.strip() == '' or q4.strip() == '':
            flash('emptyfields')
            return render_template('feedback.html', session=session, instructors=instructors, methods = ['POST', 'GET'])

        c = db.cursor() 
        c.execute("INSERT INTO Feedback(username, Q1, Q2, Q3, Q4)  VALUES (?,?,?,?,?)",(instructorName, q1, q2,q3,q4))
        db.commit()
        c.close()
        db.close()
        flash('feedbacksuccess')
        return redirect(url_for('root'))
    else:
        db.close()

@app.route('/labs')
def labs():
    if 'username' in session:
        return render_template('labs.html', session=session)
    else:
	    return redirect(url_for('root'))

@app.route('/lectures')
def lectures():
    if 'username' in session:
        return render_template('lectures.html', session=session)
    else:
	    return redirect(url_for('root'))

@app.route('/links')
def links():
    if 'username' in session:
        return render_template('links.html', session=session)
    else:
	    return redirect(url_for('root'))

@app.route('/news')
def news():
    if 'username' in session:
        return render_template('news.html', session=session)
    else:
	    return redirect(url_for('root'))

@app.route('/office-hours')
def office_hours():
    if 'username' in session:
        return render_template('office-hours.html', session=session)
    else:
	    return redirect(url_for('root'))

@app.route('/tests')
def tests():
    if 'username' in session:
        return render_template('tests.html', session=session)
    else:
	    return redirect(url_for('root'))

@app.route('/tutorials')
def tutorials():
    if 'username' in session:
        return render_template('tutorials.html', session=session)
    else:
	    return redirect(url_for('root'))

@app.route('/profile')
def profile():
    if 'username' in session:
        db = get_db()
        db.row_factory = make_dicts
        grades = []

        username = session['username']
        accounttype = session['accounttype']

        # If the user is a student, load all their grades from db
        if accounttype == 'student':
            for grade in query_db("SELECT * FROM Grades WHERE username = ?", [username], one=False):
                grades.append(grade)

            return render_template('profile.html', session=session, grades=grades)
        elif accounttype == 'instructor':
            return render_template('profile.html', session=session)

        db.close()
    else:
        return redirect(url_for('root'))

@app.route('/course-marks')
def course_marks():
    if 'username' not in session or session['accounttype'] != 'instructor':
        return redirect(url_for('root'))

    db = get_db()
    db.row_factory = make_dicts
    grades = []

    # Load grades data from db
    for grade in query_db('SELECT * FROM Grades'):
        grades.append(grade)

    db.close()
    return render_template('course-marks.html', session=session, grade=grades)

@app.route('/request-remark/<assignmentid>')
def access_request_remark(assignmentid):
    if 'username' in session and session['accounttype'] == 'student':
        db = get_db()
        db.row_factory = make_dicts

        # Check if the given assignment_id exists and that the student user has a grade associated with the assignment
        assignment = query_db("SELECT * FROM Assignment WHERE assignment_id = ?", [assignmentid], one=True)
        grade = query_db("SELECT * FROM Grades WHERE username = ? AND assignment_id = ?", [
            session['username'],
            assignmentid
        ], one=True)

        db.close()

        # Check if the given assignment for the given user is eligible for a remark
        if assignment is not None and grade is not None and grade['remark_status'] == '':
            return render_template('request-remark.html', session=session, assignment_id=assignmentid)
        else:
            return redirect(url_for('profile'))
    else:
        return redirect(url_for('root'))

@app.route('/edit-mark')
def access_edit_mark():
    if 'username' not in session or session['accounttype'] != 'instructor':
        return redirect(url_for('root'))

    assignmentid = request.args.get('assignmentid')
    username = request.args.get('username')

    return render_template('edit-mark.html', student_username=username, assignment_id=assignmentid)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        results = query_db('SELECT * FROM Account', args=(), one=False)

        for result in results:
            firstname = result[0]
            lastname = result[1]
            username = result[2]
            accounttype = result[5]

            # If the inputted username and password matched an existing pair
            if result[2] == request.form['username'] and result[3] == request.form['password']:
                session['firstname'] = firstname
                session['lastname'] = lastname
                session['username'] = username
                session['accounttype'] = accounttype
                return redirect(url_for('root'))
        
        flash('wrongcredentials')
        return render_template('login.html')
    else:
	    return redirect(url_for('root'))
    
    return root()

@app.route('/create-account', methods = ['POST', 'GET'])
def create_account():
    if request.method == 'GET':
        if 'username' in session:
            return redirect(url_for('root'))
        else:
            return render_template('create-account.html')
    elif request.method == 'POST':
        try:
            # Fetch form data
            firstname = request.form['firstname']
            lastname = request.form['lastname']
            username = request.form['username']
            password = request.form['password']
            dateofbirth = request.form['dateofbirth']
            accounttype = request.form['accounttype']

            db = get_db()
            cur =  db.cursor()

            # Error Case 1: Empty fields
            if firstname == '' or lastname == '' or username == '' or password == '' or dateofbirth == '' or accounttype == '':
                flash('emptyfields')
                return render_template('create-account.html')

            # Error Case 2: Account already exists:
            matching_user = query_db("SELECT * FROM Account WHERE username = ?", [username], one=True)
            
            if matching_user is not None:
                flash('existinguser')
                return render_template('create-account.html')

            # Adding data
            cur.execute("INSERT INTO Account(firstname, lastname, username, password, dateofbirth, type)  VALUES (?,?,?,?,?,?)", (
                firstname,
                lastname,
                username,
                password,
                dateofbirth,
                accounttype
            ))
           
            # Applying changes
            db.commit()
            cur.close()
            db.close()

            flash('createaccountsuccess')
            return render_template('login.html',)
        except:
            flash('error')
            return render_template('create-account.html')

    return render_template('create-account.html')

@app.route('/submit-remark-request', methods = ['POST'])
def make_remark_request():
    # Only allow instructors to make POST requests to this route
    if 'username' not in session or session['accounttype'] != 'student':
        return redirect(url_for('root'))
    elif request.method != 'POST':
        # Redirect to profile if the request was not POST
        return redirect(url_for('profile'))

    assignment_id = request.form['assignmentid']

    db = get_db()
    db.row_factory = make_dicts

    # Check if the given assignment_id exists and that the student user has a grade associated with the assignment
    assignment = query_db("SELECT * FROM Assignment WHERE assignment_id = ?", [assignment_id], one=True)
    grade = query_db("SELECT * FROM Grades WHERE username = ? AND assignment_id = ?", [
        session['username'],
        assignment_id
    ], one=True)

    # Check if the given assignment for the given user is eligible for a remark
    if assignment is not None and grade is not None and grade['remark_status'] == '':
        remark_reason = request.form['remark-reason']

        cur = db.cursor()

        cur.execute("UPDATE Grades SET remark_status = 'Pending', remark_request = ? WHERE username = ? AND assignment_id = ?", (
            remark_reason,
            session['username'],
            assignment_id
        ))

        db.commit()
        cur.close()

    db.close()

    return redirect(url_for('profile'))

@app.route('/submit-mark-edit', methods = ['POST'])
def make_mark_edit():
    if 'username' not in session or session['accounttype'] != 'instructor':
        return redirect(url_for('root'))
    elif request.method != 'POST':
        return redirect(url_for('course-marks'))

    student_username = request.form['student-username']
    assignment_id = request.form['assignment-id']
    new_mark = request.form['new-mark']
    update_remark_request = request.form['update-remark-request']

    # Error Case 1: Empty mark field
    if new_mark.strip() == '':
        flash('emptyfields')
        return redirect(f'edit-mark?username={student_username}&assignmentid={assignment_id}')
    
    # Error Case 2: Mark is not a number
    try:
        float(new_mark)
    except ValueError:
        flash('nonnumbererror')
        return redirect(f'edit-mark?username={student_username}&assignmentid={assignment_id}')

    # Check if the given assignment_id exists and that the student user has a grade associated with the assignment
    assignment = query_db("SELECT * FROM Assignment WHERE assignment_id = ?", [assignment_id], one=True)
    grade = query_db("SELECT * FROM Grades WHERE username = ? AND assignment_id = ?", [
        student_username,
        assignment_id
    ], one=True)

    db = get_db()
    db.row_factory = make_dicts

    # Check if the student user has a grade for the given assignment
    if assignment is not None and grade is not None:
        cur = db.cursor()

        cur.execute("UPDATE Grades SET mark = ? WHERE username = ? AND assignment_id = ?", (
            new_mark,
            student_username,
            assignment_id
        ))

        # If the instructor selected yes, update the remark status to be 'Remarked'
        if update_remark_request == 'yes':
            cur.execute("UPDATE Grades SET remark_status = 'Remarked' WHERE username = ? AND assignment_id = ?", (
                student_username,
                assignment_id
            ))

        db.commit()
        cur.close()
        flash('editmarksuccess')
    else:
        flash('nosuchgrade')

    db.close()
    return redirect(url_for('course_marks'))

@app.route('/student-names')
def student_names():
    if 'username' not in session or session['accounttype'] != 'instructor':
        return redirect(url_for('root'))

    db = get_db()
    db.row_factory = make_dicts
    names = []
    student = "'{}'".format("student")

    # Load all the student acount information from the db
    for grade in query_db('SELECT username, firstname, lastname FROM Account WHERE Account.type = {}' .format(student)):
        names.append(grade)

    db.close()
    return render_template('student-names.html', session=session, name=names)

@app.route('/enter-mark', methods = ['GET', 'POST'])
def enter_mark():
    db = get_db()
    db.row_factory = make_dicts
    cur = db.cursor()
    assignments = []

    # Load all the assignment information from the db
    for assign in query_db("SELECT * FROM Assignment"):
        assignments.append(assign)

    # Only allow instructors to access this route
    if 'username' not in session or session['accounttype'] != 'instructor':
        cur.close()
        db.close()
        return redirect(url_for('root'))
    else:
        cur.close()
        db.close()
        return render_template('enter-mark.html',session = session, assignments = assignments)

    if request.method == 'POST':
        student_username = request.form['student-username'].strip()
        assignment_id = request.form['assignment-id']
        grade = request.form['grade']
        
        # Error Case 1: Empty fields
        if student_username == '' or assignment_id == '' or grade == '':
            cur.close()
            db.close()

            flash('emptyfields')
            return render_template('enter-mark.html',session = session, assignments = assignments)            
        else:
            # Error Case 2: Student doesn't exist
            if query_db("SELECT * FROM Account WHERE username = ?", [student_username], one=True) is None:
                cur.close()
                db.close()

                flash('studentdoesnotexist')
                return render_template('enter-mark.html', session = session, assignments = assignments)
            else:
                # Check if the given assignment_id exists and that the student user has a grade associated with the assignment
                assignment_obj = query_db("SELECT * FROM Assignment WHERE assignment_id = ?", [assignment_id], one=True)
                grade_obj = query_db("SELECT * FROM Grades WHERE username = ? AND assignment_id = ?", [
                    student_username,
                    assignment_id
                ], one=True)

                # Case where grade already exists, and is modified for its respective assigment
                if assignment_obj is not None and grade_obj is not None:
                    cur.execute("UPDATE Grades SET mark = ? WHERE username = ? AND assignment_id = ?", (
                        grade,
                        student_username,
                        assignment_id
                    ))
                    db.commit()
                    cur.close()
                    db.close()
                # Case where grade doesn't exist, and we input a new grade
                else:
                    cur.execute("INSERT INTO Grades(username, assignment_id, remark_request, remark_status, mark)  VALUES (?,?,?,?,?)", (
                        student_username,
                        assignment_id,
                        "",
                        "",
                        grade
                    ))
                    db.commit()
                    cur.close()
                    db.close()

                flash('editmarksuccess')
                return redirect(url_for('enter_mark'))

    cur.close()
    db.close()
    return render_template('enter-mark.html', session = session, assignments = assignment_id)

@app.route('/logout')
def logout():
    # Pop all user data from the session
	session.pop('firstname', None)
	session.pop('lastname', None)
	session.pop('username', None)
	session.pop('accounttype', None)
	return redirect(url_for('root'))


if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True)