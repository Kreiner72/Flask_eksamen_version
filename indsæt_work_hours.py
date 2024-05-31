import sqlite3
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Function to insert data into arbejdstider.db
def insert_work_hours(id):
    today = datetime.today().date()
    start_date = today.replace(day=1)  # Set start date to the first day of the current month
    end_date = start_date + relativedelta(months=3)
    user_id = id

    work_hours = []
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Monday to Friday
            if current_date.weekday() == 2:  # Wednesday
                work_hours.append((current_date, "08:00", "15:00", "12:00", "13:00", None, user_id))
            else:
                work_hours.append((current_date, "08:00", "17:00", "12:00", "13:00", None, user_id))
        # No work hours on Saturday and Sunday
        current_date += timedelta(days=1)

    with sqlite3.connect('arbejdstider.db') as conn:
        cursor = conn.cursor()
        cursor.executemany("INSERT INTO arbejdstider (Date, Start, End, BreakStart, BreakEnd, TimeChange, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)", work_hours)
        conn.commit()

insert_work_hours(4)