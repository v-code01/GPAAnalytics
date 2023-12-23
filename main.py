import PySimpleGUI as sg
import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import skew, kurtosis

# Grade scale
GRADE_SCALE = {
    'A': 4.000,
    'A-': 3.670,
    'B+': 3.330,
    'B': 3.000,
    'B-': 2.670,
    'C+': 2.330,
    'C': 2.000,
    'F': 0.000,
    'I': 0.000,
    'P': 0.000
}

def create_database():
    """Create or connect to the SQLite database."""
    conn = sqlite3.connect('gpa_database.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grade TEXT,
            credit_hours INTEGER
        )
    ''')

    conn.commit()
    conn.close()

def insert_course(grade, credit_hours):
    """Insert a course into the database."""
    conn = sqlite3.connect('gpa_database.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO courses (grade, credit_hours)
        VALUES (?, ?)
    ''', (grade, credit_hours))

    conn.commit()
    conn.close()

def display_courses():
    """Retrieve and display the list of added courses from the database."""
    conn = sqlite3.connect('gpa_database.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM courses')
    courses = cursor.fetchall()

    conn.close()
    return courses

def calculate_gpa_layout():
    """Define the layout of the GPA calculator window."""
    sg.theme('DarkGrey2')

    grade_options = list(GRADE_SCALE.keys())

    layout = [
        [sg.Text('GPA Calculator', font=('Helvetica', 20), justification='center')],
        [sg.Text('Select Grade:', size=(15, 1), font=('Helvetica', 14)),
         sg.DropDown(grade_options, key='grade', size=(10, 1), font=('Helvetica', 14)),
         sg.Text('Credit Hours:', size=(15, 1), font=('Helvetica', 14)),
         sg.Input(key='credit_hours', size=(10, 1), font=('Helvetica', 14)),
         sg.Button('Add Course', size=(15, 1), font=('Helvetica', 14))],
        [sg.Text('Added Courses:', size=(15, 1), font=('Helvetica', 14)),
         sg.Listbox(values=display_courses(), size=(30, 5), key='added_courses', font=('Helvetica', 14))],
        [sg.Button('Calculate GPA', size=(15, 1), font=('Helvetica', 14)),
         sg.Button('Clear Courses', size=(15, 1), font=('Helvetica', 14))],  # Added Clear Courses button
        [sg.Output(size=(60, 10), key='output', font=('Helvetica', 14))],
        [sg.Text('Metrics:', size=(15, 1), font=('Helvetica', 14)),
         sg.Button('Calculate Metrics', size=(15, 1), font=('Helvetica', 14))],
    ]
    return layout

def calculate_current_class(credit_hours, grade_points):
    """Calculate the class standing based on credit hours."""
    if credit_hours < 30:
        return 'Freshman'
    elif 30 <= credit_hours < 54:
        return 'Sophomore'
    elif 54 <= credit_hours < 90:
        return 'Junior'
    else:
        return 'Senior'

def calculate_advanced_metrics(credit_hours, courses):
    """Calculate advanced metrics based on credit hours and grades."""
    if not courses or credit_hours <= 0:
        return "Please add courses and ensure positive credit hours."

    # Calculate a variety of advanced metrics
    total_grade_points = sum(GRADE_SCALE[course[1]] * course[2] for course in courses)
    total_credit_hours = sum(course[2] for course in courses)
    current_gpa = total_grade_points / total_credit_hours
    class_standing = calculate_current_class(total_credit_hours, current_gpa)

    metrics_result = [
        f'Your current GPA is: {round(current_gpa, 3)}',
        f'Class Standing: {class_standing}',
        f'Skewness of Grade Distribution : {round(skew([GRADE_SCALE[course[1]] for course in courses]), 3)}',
        f'Kurtosis of Grade Distribution : {round(kurtosis([GRADE_SCALE[course[1]] for course in courses]), 3)}'
    ]

    return metrics_result

def main():
    create_database()

    window = sg.Window('GPA Calculator', calculate_gpa_layout(), resizable=True, finalize=True)

    while True:
        event, values = window.read()

        if event == sg.WINDOW_CLOSED:
            break

        if event == 'Add Course':
            grade = values['grade'].upper()
            credit_hours = int(values['credit_hours'])

            if grade in GRADE_SCALE:
                insert_course(grade, credit_hours)
                sg.popup_quick_message(f'Course added: {grade} ({credit_hours} credit hours)', auto_close_duration=1)
                window['added_courses'].update(values=display_courses())
            else:
                sg.popup_error('Invalid grade. Please enter a valid grade.')

        if event == 'Calculate GPA':
            courses = display_courses()

            if courses:
                total_grade_points = sum(GRADE_SCALE[course[1]] * course[2] for course in courses)
                total_credit_hours = sum(course[2] for course in courses)
                current_gpa = total_grade_points / total_credit_hours
                class_standing = calculate_current_class(total_credit_hours, current_gpa)
                window['output'].update(f'Your current GPA is: {round(current_gpa, 3)}\n'
                                         f'Class Standing: {class_standing}')

                # Plot a bar chart showing the distribution of grades
                plt.figure(figsize=(8, 6))
                plt.bar(GRADE_SCALE.keys(), [courses.count(grade) for grade in GRADE_SCALE.keys()])
                plt.title('Grade Distribution')
                plt.xlabel('Grade')
                plt.ylabel('Number of Courses')
                plt.show()

            else:
                window['output'].update('No valid courses entered.')

        if event == 'Clear Courses':
            confirmation = sg.popup_yes_no('Are you sure you want to clear all courses?', title='Clear Courses',
                                           font=('Helvetica', 14), yes_button_color=('white', 'green'),
                                           no_button_color=('white', 'firebrick'))

            if confirmation == 'Yes':
                conn = sqlite3.connect('gpa_database.db')
                cursor = conn.cursor()

                cursor.execute('DELETE FROM courses')

                conn.commit()
                conn.close()
                window['added_courses'].update(values=display_courses())
                sg.popup_quick_message('All courses cleared.', auto_close_duration=2)

        if event == 'Calculate Metrics':
            advanced_metrics_result = calculate_advanced_metrics(total_credit_hours, courses)
            window['output'].update('\n'.join(advanced_metrics_result))

    window.close()

if __name__ == '__main__':
    main()
