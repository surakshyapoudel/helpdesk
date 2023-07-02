# import flask

from flask import Flask, render_template, request, redirect, url_for, flash, session
import pymysql
from babel import dates
from datetime import datetime
conn = pymysql.connect(
    host="localhost",
    port=3306,
    user="root",
    password="root",
    db="helpsdesk",
)

app = Flask(__name__)

app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'


def getCursor():
    cursor = conn.cursor()
    cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    return cursor


@app.template_filter()
def format_datetime(value, format='medium'):

    format = "y-MM-dd HH:mm"
    return dates.format_datetime(value, format)


def isAdmin():
    if "role" in session and session['role'] == 'admin':
        return True
    else:
        return False


def getAllProblems():
    cursor = getCursor()
    cursor.execute("SELECT id , caller_id , issued_to , receptionist , resolved , description , issued_date, resolved_date, device , solution,software_name,type,software_license,device_brand,device_name FROM problems")
    problems = cursor.fetchall()
    cursor.close()
    return problems


@app.route('/')
def index():
    if 'role' in session:
        if session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif session['role'] == 'helpdesk':
            return redirect(url_for('helpdesk_dashboard'))
        elif session['role'] == 'technician':
            return redirect(url_for('technician_dashboard'))
    return render_template('index.html')


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = getCursor()
        cursor.execute(
            "SELECT name , id FROM admin WHERE username=%s AND password=%s", (username, password))
        admin = cursor.fetchone()
        cursor.close()
        if admin:
            resp = redirect(url_for('admin_dashboard'))
            session['name'] = admin[0]
            session['role'] = 'admin'
            session['id'] = admin[1]
            return resp
        else:
            flash('Invalid username or password', 'red')
            return render_template('admin/login.html')
    else:
        if 'role' in session and session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            session.pop('name', None)
            session.pop('role', None)
            session.pop('id', None)
            return render_template('admin/login.html')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    resp = redirect(url_for('index'))
    session.pop('name', None)
    session.pop('role', None)
    return resp


@app.route('/admin/dashboard')
def admin_dashboard():
    if isAdmin():
        cursor = getCursor()
        cursor.execute("SELECT id , name , username FROM specialist")
        technicians = cursor.fetchall()
        cursor.execute("SELECT id , name , username FROM receptionist")
        helpdesks = cursor.fetchall()
        cursor.execute("SELECT id , name , service FROM departments")
        departments = cursor.fetchall()
        cursor.execute(
            "SELECT p.id, c.id , c.name, s.name , s.id , p.receptionist , p.status , p.description , p.issued_date, p.resolved_date, p.device_id , p.solution,p.software_name,p.type,p.software_license,p.device_brand,p.device_name , r.name FROM problems p INNER JOIN caller c ON p.caller_id=c.id INNER JOIN departments d ON c.department=d.id INNER JOIN specialist s ON p.issued_to=s.id INNER JOIN receptionist r ON p.receptionist=r.id WHERE status='pending'")

        pending_problems = cursor.fetchall()

        cursor.execute( 
            "SELECT p.id, c.id , c.name, s.name , s.id , p.receptionist , p.status , p.description , p.issued_date, p.resolved_date, p.device_id , p.solution,p.software_name,p.type,p.software_license,p.device_brand,p.device_name , r.name FROM problems p INNER JOIN caller c ON p.caller_id=c.id INNER JOIN departments d ON c.department=d.id INNER JOIN specialist s ON p.issued_to=s.id INNER JOIN receptionist r ON p.receptionist=r.id WHERE status='resolved'")

        solved_problems = cursor.fetchall()

        cursor.execute(
            "SELECT p.id, c.id , c.name, s.name , s.id , p.receptionist , p.status , p.description , p.issued_date, p.resolved_date, p.device_id , p.solution,p.software_name,p.type,p.software_license,p.device_brand,p.device_name , r.name FROM problems p INNER JOIN caller c ON p.caller_id=c.id INNER JOIN departments d ON c.department=d.id INNER JOIN specialist s ON p.issued_to=s.id INNER JOIN receptionist r ON p.receptionist=r.id WHERE status='rejected'")
        rejected_problems = cursor.fetchall()

        cursor.close()

        return render_template('admin/dashboard.html', technicians=technicians, helpdesks=helpdesks, departments=departments, pending_problems=pending_problems, solved_problems=solved_problems, rejected_problems=rejected_problems)
    else:
        return redirect(url_for('admin_login'))


@app.route('/admin/helpdesk/add', methods=['GET', 'POST'])
def admin_helpdesk_add():

    if isAdmin():
        if request.method == 'POST':
            name = request.form['name']
            username = request.form['username']
            password = request.form['password']

            cursor = getCursor()
            cursor.execute(
                "SELECT * FROM receptionist WHERE username=%s", (username))
            helpdesk = cursor.fetchone()
            cursor.close()
            if helpdesk:
                flash('Username already exists', 'red')
                return render_template('admin/addHelpdesk.html')

            cursor = getCursor()
            cursor.execute(
                "INSERT INTO receptionist (name, username, password) VALUES (%s, %s, %s)", (name, username, password))
            conn.commit()
            cursor.close()
            flash('Helpdesk added successfully', 'green')
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin/addHelpdesk.html')
    else:
        return redirect(url_for('admin_login'))


@app.route('/admin/technician/add', methods=['GET', 'POST'])
def admin_technician_add():

    if isAdmin():
        if request.method == 'POST':
            name = request.form['name']
            username = request.form['username']
            password = request.form['password']

            cursor = getCursor()
            cursor.execute(
                "SELECT * FROM specialist WHERE username=%s", (username))
            technician = cursor.fetchone()
            cursor.close()
            if technician:
                flash('Username already exists', 'red')
                return render_template('admin/addTechnician.html')

            cursor = getCursor()
            cursor.execute(
                "INSERT INTO specialist (name, username, password) VALUES (%s, %s, %s)", (name, username, password))
            conn.commit()
            cursor.close()
            flash('Technician added successfully', 'green')
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin/addTechnician.html')
    else:
        return redirect(url_for('admin_login'))


@app.route('/admin/department/add', methods=['GET', 'POST'])
def admin_department_add():

    if isAdmin():
        if request.method == 'POST':
            name = request.form['name']
            service = request.form['service']

            cursor = getCursor()
            cursor.execute(
                "INSERT INTO departments (name, service) VALUES (%s, %s)", (name, service))
            conn.commit()
            cursor.close()
            flash('Department added successfully', 'green')
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin/addDepartment.html')
    else:
        return redirect(url_for('admin_login'))


@app.route('/helpdesk/login', methods=['GET', 'POST'])
def helpdesk_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = getCursor()
        cursor.execute(
            "SELECT name , id FROM receptionist WHERE username=%s AND password=%s", (username, password))
        helpdesk = cursor.fetchone()
        cursor.close()
        if helpdesk:
            resp = redirect(url_for('helpdesk_dashboard'))
            session['name'] = helpdesk[0]
            session['role'] = 'helpdesk'
            session['id'] = helpdesk[1]

            return resp
        else:
            flash('Invalid username or password', 'red')
            return render_template('helpdesk/login.html')
    else:
        if 'role' in session and session['role'] == 'helpdesk':
            return redirect(url_for('helpdesk_dashboard'))
        else:
            session.pop('name', None)
            session.pop('id', None)
            session.pop('role', None)
            return render_template('helpdesk/login.html')


@app.route('/helpdesk/dashboard')
def helpdesk_dashboard():
    if 'role' in session and session['role'] == 'helpdesk':
        cursor = getCursor()

        cursor.execute(
            "SELECT p.id, c.id , c.name, s.name , s.id , p.receptionist , p.status , p.description , p.issued_date, p.resolved_date, p.device_id , p.solution,p.software_name,p.type,p.software_license,p.device_brand,p.device_name , r.name FROM problems p INNER JOIN caller c ON p.caller_id=c.id INNER JOIN departments d ON c.department=d.id INNER JOIN specialist s ON p.issued_to=s.id INNER JOIN receptionist r ON p.receptionist=r.id WHERE status='pending'")

        pending_problems = cursor.fetchall()
        print(pending_problems)
        cursor.execute(
            "SELECT p.id, c.id , c.name, s.name , s.id , p.receptionist , p.status , p.description , p.issued_date, p.resolved_date, p.device_id , p.solution,p.software_name,p.type,p.software_license,p.device_brand,p.device_name , r.name FROM problems p INNER JOIN caller c ON p.caller_id=c.id INNER JOIN departments d ON c.department=d.id INNER JOIN specialist s ON p.issued_to=s.id INNER JOIN receptionist r ON p.receptionist=r.id WHERE status='resolved'")

        solved_problems = cursor.fetchall()

        cursor.execute(
            "SELECT p.id, c.id , c.name, s.name , s.id , p.receptionist , p.status , p.description , p.issued_date, p.resolved_date, p.device_id , p.solution,p.software_name,p.type,p.software_license,p.device_brand,p.device_name , r.name FROM problems p INNER JOIN caller c ON p.caller_id=c.id INNER JOIN departments d ON c.department=d.id INNER JOIN specialist s ON p.issued_to=s.id INNER JOIN receptionist r ON p.receptionist=r.id WHERE status='rejected'")
        rejected_problems = cursor.fetchall()

        cursor.close()
        return render_template('helpdesk/dashboard.html', pending_problems=pending_problems, solved_problems=solved_problems, rejected_problems=rejected_problems)
    else:
        return redirect(url_for('helpdesk_login'))


@app.route('/caller/search', methods=['POST'])
def searchCaller():
    if 'role' in session and session['role'] == 'helpdesk':
        phone_number = int(request.form['phone_number'])
        cursor = getCursor()
        cursor.execute(
            "SELECT id , name , phone_number , jobtitle , department FROM caller WHERE phone_number=%s", (phone_number))
        caller = cursor.fetchone()
        cursor.close()
        if caller:
            return redirect(url_for("caller", caller_id=caller[0]))
        else:
            return redirect(url_for("addCaller", phone_number=phone_number))
    else:
        return redirect(url_for('helpdesk_login'))


@app.route('/caller/add', methods=['POST', 'GET'])
def addCaller():
    if 'role' in session and session['role'] == 'helpdesk':
        if request.method == 'GET':
            phone_number = request.args.get('phone_number')
            cursor = getCursor()
            cursor.execute("SELECT id , name FROM departments")
            departments = cursor.fetchall()
            cursor.close()
            return render_template('helpdesk/addCaller.html', phone_number=phone_number, departments=departments)
        else:
            print(request.form)
            name = request.form['name']
            phone_number = request.form['phone_number']
            jobtitle = request.form['jobtitle']
            department = int(request.form['department'])
            cursor = getCursor()
            cursor.execute(
                "INSERT INTO caller (name, phone_number, jobtitle, department) VALUES (%s, %s, %s, %s)", (name, phone_number, jobtitle, department))
            conn.commit()
            cursor.execute(
                "SELECT id FROM caller WHERE phone_number=%s", (phone_number))
            caller = cursor.fetchone()
            cursor.close()
            assert caller is not None
            return redirect(url_for("caller", caller_id=caller[0]))
    else:
        return redirect(url_for('helpdesk_login'))


@app.route('/caller/<int:caller_id>', methods=['GET'])
def caller(caller_id):
    if 'role' in session:
        cursor = getCursor()
        cursor.execute(
            "SELECT c.id, c.name , c.phone_number , d.name , d.service , c.jobtitle  FROM caller c INNER JOIN departments d ON c.department=d.id WHERE c.id=%s", (caller_id))
        caller = cursor.fetchone()
        cursor.close()
        if caller:
            cursor = getCursor()
            cursor.execute("SELECT p.id, c.id , c.name, s.name , s.id , p.receptionist , p.status , p.description , p.issued_date, p.resolved_date, p.device_id , p.solution,p.software_name,p.type,p.software_license,p.device_brand,p.device_name , r.name FROM problems p INNER JOIN caller c ON p.caller_id=c.id INNER JOIN departments d ON c.department=d.id INNER JOIN specialist s ON p.issued_to=s.id INNER JOIN receptionist r ON p.receptionist=r.id WHERE caller_id=%s", (caller_id))
            problems = cursor.fetchall()
            print(problems)
            cursor.close()
            return render_template('helpdesk/caller.html', caller=caller, problems=problems)
        else:
            return "Caller not found"
    else:
        return redirect(url_for('index'))


@app.route('/caller/<int:caller_id>/problem/add', methods=['GET', 'POST'])
def addProblem(caller_id):

    if 'role' in session and session['role'] == 'helpdesk':
        if request.method == 'GET':
            cursor = getCursor()
            cursor.execute(
                "SELECT id , name FROM specialist")
            technicians = cursor.fetchall()
            cursor.close()
            return render_template('helpdesk/addProblem.html', caller_id=caller_id, technicians=technicians)
        else:
            print(request.form)
            type = request.form['type']
            receptionist = session['id']
            device_id = request.form['device_id']
            software_name = None
            software_license = None
            if type == 'software':
                software_name = request.form['software_name']
                software_license = request.form['software_license']
            device_brand = request.form['device_brand']
            device_name = request.form['device_name']
            issued_to = request.form['issued_to']
            description = request.form['description']
            issued_date = datetime.now()
            cursor = getCursor()
            cursor.execute(
                "INSERT INTO problems (caller_id, issued_to, receptionist, description, device_id, software_name, type, software_license, device_brand, device_name , issued_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s , %s)", (caller_id, issued_to, receptionist, description, device_id, software_name, type, software_license, device_brand, device_name, issued_date))
            conn.commit()
            cursor.close()
            return redirect(url_for('caller', caller_id=caller_id))
    else:
        print("here")
        return redirect(url_for('helpdesk_login'))


@app.route('/technician/login', methods=['GET', 'POST'])
def technician_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = getCursor()
        cursor.execute(
            "SELECT name , id FROM specialist WHERE username=%s AND password=%s", (username, password))
        technician = cursor.fetchone()
        cursor.close()
        if technician:
            resp = redirect(url_for('technician_dashboard'))
            session['name'] = technician[0]
            session['role'] = 'technician'
            session['id'] = technician[1]

            return resp
        else:
            flash('Invalid username or password', 'red')
            return render_template('technician/login.html')
    else:
        if 'role' in session and session['role'] == 'technician':
            return redirect(url_for('technician_dashboard'))
        else:
            session.pop('name', None)
            session.pop('id', None)
            session.pop('role', None)
            return render_template('technician/login.html')


@app.route('/technician/dashboard')
def technician_dashboard():
    if 'role' in session and session['role'] == 'technician':
        cursor = getCursor()
        cursor.execute(
            "SELECT p.id, c.id , c.name, s.name , s.id , p.receptionist , p.status , p.description , p.issued_date, p.resolved_date, p.device_id , p.solution,p.software_name,p.type,p.software_license,p.device_brand,p.device_name , r.name FROM problems p INNER JOIN caller c ON p.caller_id=c.id INNER JOIN departments d ON c.department=d.id INNER JOIN specialist s ON p.issued_to=s.id INNER JOIN receptionist r ON p.receptionist=r.id WHERE issued_to=%s", (session['id']))

        problems = cursor.fetchall()
        return render_template('technician/dashboard.html', problems=problems)
    else:
        return redirect(url_for('technician_login'))


@app.route('/problem/<int:problem_id>', methods=['GET', 'POST'])
def problem(problem_id):
    if 'role' in session:
        userType = session['role']
        userId = session['id']

        cursor = getCursor()

        if userType == 'technician':
            cursor.execute(
                "SELECT p.id, c.id , c.name, s.name , s.id , p.receptionist , p.status , p.description , p.issued_date, p.resolved_date, p.device_id , p.solution,p.software_name,p.type,p.software_license,p.device_brand,p.device_name , r.name FROM problems p INNER JOIN caller c ON p.caller_id=c.id INNER JOIN departments d ON c.department=d.id INNER JOIN specialist s ON p.issued_to=s.id INNER JOIN receptionist r ON p.receptionist=r.id WHERE p.id=%s AND p.issued_to=%s", (problem_id, userId))

        else:
            cursor.execute(
                "SELECT p.id, c.id , c.name, s.name , s.id , p.receptionist , p.status , p.description , p.issued_date, p.resolved_date, p.device_id , p.solution,p.software_name,p.type,p.software_license,p.device_brand,p.device_name , r.name FROM problems p INNER JOIN caller c ON p.caller_id=c.id INNER JOIN departments d ON c.department=d.id INNER JOIN specialist s ON p.issued_to=s.id INNER JOIN receptionist r ON p.receptionist=r.id WHERE p.id=%s", (problem_id))
        problem = cursor.fetchone()

        print(problem)
        cursor.close()

        if problem:
            if request.method == 'GET':
                if problem[6] == 'pending':
                    flash('Status : Pending', 'yellow')
                elif problem[6] == 'resolved':
                    flash('Status :  Resolved', 'green')
                elif problem[6] == 'rejected':
                    flash('Status :  Rejected.', 'red')
                cursor = getCursor()
                cursor.execute(
                    "SELECT c.id, c.name , c.phone_number , d.name , d.service , c.jobtitle  FROM caller c INNER JOIN departments d ON c.department=d.id WHERE c.id=%s", (problem[1]))

                caller = cursor.fetchone()

                cursor = getCursor()
                cursor.execute(
                    "SELECT id , name FROM specialist")
                technicians = cursor.fetchall()

                cursor.close()

                return render_template('problem.html', problem=problem, caller=caller, technicians=technicians)
            else:
                solution = request.form['solution']
                resolved_date = datetime.now()
                cursor = getCursor()
                cursor.execute(
                    "UPDATE problems SET solution=%s , resolved_date=%s , status='resolved' WHERE id=%s", (solution, resolved_date, problem_id))
                conn.commit()
                cursor.close()
                return redirect(url_for('technician_dashboard'))
        else:
            return "Problem not found"
    else:
        return redirect(url_for('index'))


@app.route('/problem/<int:problem_id>/resolve', methods=['POST'])
def resolveProblem(problem_id):
    if 'role' in session:
        if session['role'] == 'technician':
            techid = session['id']
            cursor = getCursor()
            cursor.execute(
                "SELECT p.id, c.id , c.name, s.name , s.id , p.receptionist , p.status , p.description , p.issued_date, p.resolved_date, p.device_id , p.solution,p.software_name,p.type,p.software_license,p.device_brand,p.device_name , r.name FROM problems p INNER JOIN caller c ON p.caller_id=c.id INNER JOIN departments d ON c.department=d.id INNER JOIN specialist s ON p.issued_to=s.id INNER JOIN receptionist r ON p.receptionist=r.id WHERE p.id=%s AND issued_to=%s", (problem_id, techid))
            problem = cursor.fetchone()

            if problem:
                solution = request.form['solution']
                resolved_date = datetime.now()
                cursor = getCursor()
                cursor.execute(
                    "UPDATE problems SET solution=%s , resolved_date=%s , status='resolved' WHERE id=%s", (solution, resolved_date, problem_id))
                conn.commit()
                cursor.close()

                flash('Problem resolved successfully', 'green')
                return redirect(url_for('problem', problem_id=problem_id))
            else:
                return "Problem not found"
        else:
            return "You are not authorized to perform this action"
    else:
        return redirect(url_for('index'))


@app.route('/problem/<int:problem_id>/reject', methods=['POST'])
def rejectProblem(problem_id):
    if 'role' in session:
        if session['role'] == 'technician':
            techid = session['id']
            cursor = getCursor()
            cursor.execute(
                "SELECT p.id, c.id , c.name, s.name , s.id , p.receptionist , p.status , p.description , p.issued_date, p.resolved_date, p.device_id , p.solution,p.software_name,p.type,p.software_license,p.device_brand,p.device_name , r.name FROM problems p INNER JOIN caller c ON p.caller_id=c.id INNER JOIN departments d ON c.department=d.id INNER JOIN specialist s ON p.issued_to=s.id INNER JOIN receptionist r ON p.receptionist=r.id WHERE p.id=%s AND issued_to=%s", (problem_id, techid))
            problem = cursor.fetchone()
            if problem:
                cursor = getCursor()
                cursor.execute(
                    "UPDATE problems SET status='rejected' WHERE id=%s", (problem_id))
                conn.commit()
                cursor.close()
                return redirect(url_for('problem', problem_id=problem_id))
            else:
                return "Problem not found"
        else:
            return "You are not authorized to perform this action"
    else:
        return redirect(url_for('index'))


@app.route('/problem/<int:problem_id>/reassign', methods=['POST'])
def reassignProblem(problem_id):
    if 'role' in session:
        if session['role'] == 'helpdesk':
            cursor = getCursor()
            cursor.execute(
                "SELECT p.id, c.id , c.name, s.name , s.id , p.receptionist , p.status , p.description , p.issued_date, p.resolved_date, p.device_id , p.solution,p.software_name,p.type,p.software_license,p.device_brand,p.device_name , r.name FROM problems p INNER JOIN caller c ON p.caller_id=c.id INNER JOIN departments d ON c.department=d.id INNER JOIN specialist s ON p.issued_to=s.id INNER JOIN receptionist r ON p.receptionist=r.id WHERE p.id=%s", (problem_id))
            problem = cursor.fetchone()
            if problem:
                issued_to = request.form['issued_to']
                cursor = getCursor()
                cursor.execute(
                    "UPDATE problems SET issued_to=%s , status='pending' WHERE id=%s", (issued_to, problem_id))

                conn.commit()
                cursor.close()
                flash('Problem reassigned', 'green')
                return redirect(url_for('problem', problem_id=problem_id))
            else:
                return "Problem not found"
        else:
            return "You are not authorized to perform this action"
    else:
        return redirect(url_for('index'))


app.run(debug=True)
