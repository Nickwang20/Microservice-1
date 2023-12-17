import duckdb
from flask import Flask, jsonify
import random
from faker import Faker

fake = Faker()
app = Flask(__name__)


def init_db():
    conn = duckdb.connect('./resources/scores.db', read_only=False)
    conn.execute(
        'CREATE TABLE IF NOT EXISTS scores (student_id STRING, student_name STRING, course_id STRING, course_name STRING, score FLOAT)')
    conn.execute('CREATE TABLE IF NOT EXISTS history_scores (course_id STRING, year INTEGER, score FLOAT)')
    conn.execute('CREATE TABLE IF NOT EXISTS students (student_id STRING, student_name STRING)')
    conn.close()


def mock_data():
    fake = Faker()

    conn = duckdb.connect('./resources/scores.db', read_only=False)

    student_info = {}
    for i in range(1, 6):
        student_id = str(i)
        student_name = fake.name()
        student_info[student_id] = student_name
        conn.execute(f"INSERT INTO students VALUES ('{student_id}', '{student_name}')")

    course_names = ['Math', 'English', 'History', 'Physics', 'Chemistry', 'Biology', 'Computer Science', 'Art', 'Music',
                    'Physical Education']
    student_course_set = set()

    for student_id in range(1, 6):
        num_courses = random.randint(2, 5)
        for _ in range(num_courses):
            course_id = random.randint(0, 9)

            if (student_id, course_id) in student_course_set:
                continue

            student_course_set.add((student_id, course_id))

            course_name = course_names[course_id]
            score = random.randint(60, 100)
            conn.execute(
                f"INSERT INTO scores VALUES ('{student_id}', '{student_info[str(student_id)]}', '{str(course_id)}', '{course_name}', {score})")

    for course_id in range(1, 6):
        for year in range(2023, 2018, -1):
            average_score = round(random.uniform(60, 100), 1)
            conn.execute(f"INSERT INTO history_scores VALUES ('{course_id}', {year}, {average_score})")

    conn.close()


def get_db_conn():
    return duckdb.connect('./resources/scores.db', read_only=False)


def close_conn(conn):
    conn.close()
