import os
import pandas as pd
from datetime import date, datetime

# Date formatting constants
datetoday = date.today().strftime("%m_%d_%y")
datetoday2 = date.today().strftime("%d-%B-%Y")

# Message status codes
SUCCESS_MESSAGE = "success"
ERROR_MESSAGE = "error"
WARNING_MESSAGE = "warning"

def ensure_directories():
    """Ensure all required directories exist"""
    if not os.path.isdir('data/Attendance'):
        os.makedirs('data/Attendance')
    if not os.path.isdir('src/static'):
        os.makedirs('src/static')
    if not os.path.isdir('src/static/faces'):
        os.makedirs('src/static/faces')
    if not os.path.isdir('src/static/models'):
        os.makedirs('src/static/models')
    
    # Create today's attendance file if it doesn't exist
    if f'Attendance-{datetoday}.csv' not in os.listdir('data/Attendance'):
        with open(f'data/Attendance/Attendance-{datetoday}.csv','w') as f:
            f.write('Name,Roll,Time')

def extract_attendance():
    """Extract info from today's attendance file"""
    df = pd.read_csv(f'data/Attendance/Attendance-{datetoday}.csv')
    names = df['Name']
    rolls = df['Roll']
    times = df['Time']
    l = len(df)
    return names, rolls, times, l

def add_attendance(name):
    """Add attendance for a specific user"""
    username = name.split('_')[0]
    userid = name.split('_')[1]
    current_time = datetime.now().strftime("%H:%M:%S")
    
    df = pd.read_csv(f'data/Attendance/Attendance-{datetoday}.csv')
    if int(userid) not in list(df['Roll']):
        with open(f'data/Attendance/Attendance-{datetoday}.csv','a') as f:
            f.write(f'\n{username},{userid},{current_time}')