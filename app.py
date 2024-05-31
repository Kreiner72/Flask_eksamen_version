from flask import Flask, render_template, url_for, redirect, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def init_db():
    with sqlite3.connect('arbejdstider.db') as conn:
        cursor = conn.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS arbejdstider (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Date DATETIME NOT NULL,
                Start TEXT NOT NULL,
                End TEXT NOT NULL,
                BreakStart TEXT,
                BreakEnd TEXT,
                TimeChange TEXT,
                user_id INTEGER NOT NULL)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS tidsændringer (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Date TEXT NOT NULL,
                    Start TEXT NOT NULL,
                    End TEXT NOT NULL,
                    Pause_Start TEXT,
                    Pause_End TEXT,
                    user_id INTEGER NOT NULL)''')

        conn.commit()
init_db()


def get_work_hours(period, user_id):
    query = "SELECT * FROM arbejdstider WHERE user_id = ? AND Date >= ? AND Date <= ?"
    today = datetime.today().date()
    
    if period == 'day':
        start_date = today
        end_date = today
    elif period == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif period == 'month':
        start_date = today.replace(day=1)
        if start_date.month == 12:
            end_date = start_date.replace(day=31)
        else:
            end_date = (start_date.replace(month=start_date.month+1, day=1) - timedelta(days=1))
    else:
        return []
    
    with sqlite3.connect('arbejdstider.db') as conn:
        cursor = conn.cursor()
        cursor.execute(query, (user_id, start_date, end_date))
        result = cursor.fetchall()


    for i in range(len(result)):
        date_part = result[i][1].split(" ")[0]
        date = datetime.strptime(date_part, "%Y-%m-%d").date()
        result[i] = list(result[i])
        result[i][1] = date.strftime("%d-%m-%Y")

    return result
    

def create_user(username, password):
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    with sqlite3.connect('database1.db') as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            print('User created successfully')
        except sqlite3.IntegrityError:
            print('Username already exists')


@login_manager.user_loader
def load_user(user_id):
    with sqlite3.connect('database1.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        if user:
            return User(id=user[0], username=user[1], password=user[2])
        return None


class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=3, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=3, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Login")


def ændre_tid(id):
    with sqlite3.connect("arbejdstider.db") as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM tidsændringer WHERE id = ?", (id,))
        connection.commit()

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        with sqlite3.connect('database1.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (form.username.data,))
            user = cursor.fetchone()
            if user and check_password_hash(user[2], form.password.data):
                login_user(User(id=user[0], username=user[1], password=user[2]))
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)


from datetime import date as Date 

@app.route('/dashboard', methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":
        date = request.form.get("date")

        start = request.form.get("start")
        end = request.form.get("end")
        pause_start = request.form.get("pause_start")
        pause_end = request.form.get("pause_end")

        data = [date, start, end, pause_start, pause_end]

        if not all(data[:3]):
            flash("All fields for work hours are required", "danger")
        else:
            with sqlite3.connect('arbejdstider.db') as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO tidsændringer (Date, Start, End, Pause_start, Pause_end, user_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (*data, current_user.id))
                conn.commit()
            flash("Record added", "success")
        return redirect(url_for("dashboard"))

    arbejdstider_data = get_work_hours('day', current_user.id)
    return render_template("dashboard.html", arbejdstider_data=arbejdstider_data, today=Date.today())

@app.route("/delete/<entry_id>", methods=["POST"])
@login_required
def db_delete(entry_id):
    ændre_tid(entry_id)
    flash("Record removed", "danger")
    return redirect(url_for("dashboard"))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/Skema/<user>')
@login_required
def skema(user):
    if user != current_user.username:
        flash("You do not have permission to view this page.", "danger")
        return redirect(url_for("dashboard"))


    with sqlite3.connect('arbejdstider.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tidsændringer WHERE user_id = ?", (current_user.id,))
        tidsændringer_list = cursor.fetchall()

    return render_template("skema.html", tidsændringer_list=tidsændringer_list)

@app.route('/arbejdstider/<int:user_id>')
@login_required
def arbejdstider(user_id):

    today = datetime.today().date()
    today_str = today.strftime("%d-%m-%Y") 

    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    daily_hours = get_work_hours('day', user_id)
    weekly_hours = get_work_hours('week', user_id)
    monthly_hours = get_work_hours('month', user_id)

    daily_hours_today = [entry for entry in daily_hours if entry[1] == today_str] 

    weekly_hours_this_week = [entry for entry in weekly_hours if start_of_week <= datetime.strptime(entry[1], "%d-%m-%Y").date() <= end_of_week]
    return render_template('work_hours.html', daily_hours=daily_hours_today, weekly_hours=weekly_hours_this_week, monthly_hours=monthly_hours)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
