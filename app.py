from flask import Flask, render_template, request, jsonify
from dbconnector import get_db_conn, close_conn, init_db, mock_data
from resources.score_resource import ScoreResource
from functools import wraps
from aws_access_key import aws_access_key_id, aws_secret_access_key

import boto3
import json

def sns_middleware(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Execute the original function
        response = func(*args, **kwargs)

        # Extract scores from the response
        scores = response.get_json()

        # Prepare the message for SNS
        table_header = "The Average Score of past 5 years:\nYear \tAverage Score\n"
        table_rows = [f"{year}\t{round(score, 4)}" for year, score in scores]
        table_string = table_header + "\n".join(table_rows)
        message = json.dumps({"table": table_string})

        # Trigger SNS and Lambda
        sns_client = boto3.client('sns', 
                                  aws_access_key_id=aws_access_key_id,
                                  aws_secret_access_key=aws_secret_access_key,
                                  region_name='us-east-2')

        sns_topic_arn = 'arn:aws:sns:us-east-2:006813630962:snstriggledbygetscore'
        sns_client.publish(TopicArn=sns_topic_arn, Message=message)

        # Return the original response
        return response

    return wrapper

app = Flask(__name__)
instance = ScoreResource()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/dashboard/async_search_student', methods=['GET', 'POST'])
async def search_student_async():
    if request.method == 'POST':
        id = request.form.get('student_id')
        result = await instance.get_score_async(id)
        if result:
            print(result)
            return render_template('search_student.html', results=result['score']['score'], info=result['student']['student'])

    return render_template('search_student.html')


@app.route('/api/dashboard/sync_search_student', methods=['GET', 'POST'])
async def search_student_sync():
    if request.method == 'POST':
        id = request.form.get('student_id')
        result = await instance.get_score_sync(id)
        if result:
            print(result)
            return render_template('search_student.html', results=result['score']['score'], info=result['student']['student'])

    return render_template('search_student.html')


@app.route('/api/dashboard/view_score')
def view_score():
    return render_template('view_score.html')


@app.route('/insert_scores', methods=['POST'])
def add_score():
    student_id = request.json.get('student_id')
    student_name = request.json.get('student_name')
    course_id = request.json.get('course_id')
    course_name = request.json.get('course_name')
    score = request.json.get('score')

    conn = get_db_conn()
    conn.execute(f"INSERT INTO scores VALUES ({student_id}, '{student_name}', {course_id}, '{course_name}', {score})")
    close_conn(conn)

    return '', 201


@app.route('/average_scores', methods=['POST'])
@sns_middleware
def get_average_scores():
    course_id = request.json.get('course_id')

    conn = get_db_conn()
    result = conn.execute(f"SELECT year, AVG(score) FROM history_scores WHERE course_id = {course_id} GROUP BY year")
    scores = result.fetchall()
    conn.close()

    return jsonify(scores)


@app.route('/get_score_info_json/<id>')
def get_score_info(id):
    conn = get_db_conn()
    result = conn.execute(f"SELECT * FROM scores WHERE student_id = {id}")
    score = result.fetchall()
    close_conn(conn)
    return jsonify({'score': score})


@app.route('/get_student_info_json/<id>')
def get_student_json(id):
    conn = get_db_conn()
    result = conn.execute(f"SELECT * FROM students WHERE student_id = '{id}'")
    student = result.fetchone()
    close_conn(conn)
    return jsonify({'student': student})


if __name__ == '__main__':
    init_db()
    # mock_data()
    app.run(host='0.0.0.0', port=8000)
