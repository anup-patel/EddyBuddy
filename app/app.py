import os
import gc
import sys
import json
import time
import shutil
import logging
import requests
import importlib
import pandas as pd
import datetime as dt
import warnings
from bs4 import BeautifulSoup as BS
import uuid


import requests as req
warnings.filterwarnings(
    "ignore",
    # message="The localize method is no longer necessary, as this time zone supports the fold attribute"
    message="The normalize method is no longer necessary, as this time zone supports the fold attribute"
    # category="PytzUsageWarning"
)
warnings.filterwarnings(
    "ignore",
    message="The zone attribute is specific to pytz's interface"
)

from flask import Flask, render_template, request, redirect, url_for, abort, flash, current_app, send_file, Response, jsonify,send_from_directory
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'anystringthatyoulike'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.password = user_data['password']
        self.role = user_data['role']
        self.validity = user_data.get("validity", '2050-12-31')


def load_users():
    with open('users.json', 'r') as file:
        users_data = json.load(file)
    users = []
    for user_data in users_data['users']:
        users.append(User(user_data))
    return users


current_id=None
@login_manager.user_loader
def load_user(user_id):
    users = load_users()
    for user in users:
        if user.id == user_id:
            current_id=user_id
            return user
    return None

def load_strategies():
    return [f[:-3] for f in os.listdir() if f.endswith('.py')]

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember_me = 'remember_me' in request.form
        users = load_users()
        user_found = False
        for user in users:
            if user.username == username and user.password == password:
                user_found = True
                last_date = dt.datetime.strptime(user.validity, '%Y-%m-%d').date()
                if(last_date >= dt.date.today()):
                    login_user(user, remember=remember_me)
                    if remember_me:
                        current_app.permanent_session_lifetime = dt.timedelta(days=7)
                    else:
                        current_app.permanent_session_lifetime = dt.timedelta(days=1)
                    return redirect(url_for('home'))
                else:
                    flash('User validity expired, please contact admin')
        if(not user_found):
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('User logged out. Login again to continue.')
    return redirect(url_for('login'))

@app.get('/')
@login_required
def home():
    return render_template('home.html', user=current_user,log_name='Home | Falcon Hackathon')


@app.errorhandler(404)
def page_not_found(error):
   return '404: This page could not be found.', 404

    
#######################################################################
####### ANUP UI Extra Codes ##########



#### FALCON CODE START HERE 

AI71_BASE_URL = "https://api.ai71.ai/v1/"
AI71_API_KEY = "Enter AI71 API Here"

import requests

import random

def generate_mcq(prompt):
    headers = {
        "Authorization": f"Bearer {AI71_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "tiiuae/falcon-11b-chat",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Generate a list of multiple-choice questions (MCQs) based on the following prompt. For each question, provide four options (a, b, c, d) and indicate the correct answer explicitly. Also shuffle all options \n\nPrompt: {prompt}"}
        ]
    }
    
    response = requests.post(
        f"{AI71_BASE_URL}chat/completions",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        choices = data.get('choices', [])
        if choices:
            content = choices[0].get('message', {}).get('content', "").strip()
            
            # Split the response into question blocks
            question_blocks = content.split('\n\n')  # Assuming each question block is separated by double newlines
            
            questions = []
            
            for block in question_blocks:
                lines = block.split('\n')
                if len(lines) >= 5:  # Expect at least a question and four options
                    question = lines[0].strip()
                    options = []
                    correct_answer = None
                    
                    # Extract options and correct answer
                    for line in lines[1:5]:
                        if line:
                            options.append({
                                'label': line,
                                'value': line[0]
                            })
                    
                    # Look for the correct answer
                    for line in lines[5:]:
                        if line.strip().startswith('Correct answer:'):
                            correct_answer = line.split(':', 1)[1].strip()
                            break
                    
                    if not correct_answer and options:
                        # Default to the first option as correct if no explicit correct answer is found
                        correct_answer = options[0]['value']
                    
                    # Shuffle options and adjust correct_answer
                    random.shuffle(options)
                    
                    # Ensure correct answer is reflected
                    correct_option = next((opt for opt in options if opt['value'] == correct_answer), None)
                    if correct_option:
                        correct_answer = correct_option['value']
                    
                    questions.append({
                        "question": question,
                        "options": options,
                        "answer": correct_answer
                    })
            
            if not questions:
                return [{"question": "No questions generated.", "options": [], "answer": ""}]
            
            return questions
        else:
            return [{"question": "No questions generated.", "options": [], "answer": ""}]
    else:
        return [{"question": f"Error: {response.status_code} {response.text}", "options": [], "answer": ""}]



@app.route('/generate-mcqs', methods=['GET'])
@login_required
def generate_mcqs():
    prompt = request.args.get('prompt', '')
    
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    
    # Call the function to generate MCQs and correct answers
    questions_with_answers = generate_mcq(prompt)
    
    if isinstance(questions_with_answers, list) and len(questions_with_answers) > 0:
        # Format the response to include both questions and correct answers
        questions = []
        answers = []
        
        for q in questions_with_answers:
            questions.append({
                "question": q['question'],
                "options": q['options']
            })
            answers.append(q['answer'])

        # print(questions)
        # print(answers)
        
        return jsonify({"questions": questions, "answers": answers})
    
    return jsonify({"error": "Failed to generate questions"}), 500


@app.route('/submit-answers', methods=['POST'])
def submit_answers():
    answers = request.json.get('answers', [])
    
    # Example scoring logic: Count number of answers
    score = len(answers)  # Replace with actual scoring logic
    return jsonify({"score": score})



@app.route('/practice')
@login_required
def practice():
    return render_template('practice.html', user=current_user,log_name="Practice Questions", )

# Construct the path to the JSON file
current_directory = os.path.dirname(__file__)  # Directory of the current script
json_file_path = os.path.abspath(os.path.join(current_directory, '..', 'db', 'students', 'students.json'))



@app.route('/peers')
@login_required
def peers():
    # Path to your JSON file
    # Read the JSON file
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    # Convert JSON data to DataFrame
    df = pd.DataFrame(data)
    # Convert DataFrame to a list of dictionaries for Jinja2
    data_list = df.to_dict(orient='records')
    # print(data_list)
    return render_template('peers.html', user=current_user,log_name="Peers",students=data_list )

@app.route('/payment')
@login_required
def payment():
    return render_template('cards.html',user=current_user, log_name="Payment", )

@app.route('/upload_notes')
@login_required
def upload_notes():
    return render_template('upload_notes.html',user=current_user, log_name="Upload Notes", )


@app.route('/notice_create')
@login_required
def notice_create():
    return render_template('create_notice.html',user=current_user, log_name="Notice Creation", )


@app.route('/tickets')
@login_required
def tickets():
    return render_template('tickets.html', user=current_user,log_name="Raise a Ticket | Falcon Hackathon", )


@app.route('/performance')
@login_required
def performance():
    return render_template('performance.html', user=current_user,log_name="Performance Bot | Falcon Hackathon")

@app.route('/learning_coach')
@login_required
def learning_coach():
    return render_template('learning_coach.html',user=current_user, log_name="Learning Coach | Falcon Hackathon", )


TICKETS_FILE = 'tickets.json'

def read_tickets():
    if os.path.exists(TICKETS_FILE):
        with open(TICKETS_FILE, 'r') as file:
            return json.load(file)
    return []

def write_tickets(tickets):
    with open(TICKETS_FILE, 'w') as file:
        json.dump(tickets, file)


@app.route('/get-tickets', methods=['GET'])
@login_required
def get_tickets():
    # Read all tickets
    tickets = read_tickets()
    
    # Check user role and filter tickets accordingly
    if current_user.role == 'student':
        # Filter tickets for the current student only
        student_id = current_user.id
        filtered_tickets = [ticket for ticket in tickets if ticket['student_id'] == student_id]
        return jsonify({'tickets': filtered_tickets})
    else:
        # Return all tickets for other roles
        return jsonify({'tickets': tickets})

@app.route('/raise-ticket', methods=['POST'])
def raise_ticket():
    data = request.json
    student_name = data.get('studentName')
    contact_number = data.get('contactNumber')
    query = data.get('query')
    
    tickets = read_tickets()
    
    ticket_id = str(uuid.uuid4())  # Generate a unique ticket ID
    
    ticket = {
        'ticketId': ticket_id,
        'studentName': student_name,
        'student_id':current_user.id,
        'contactNumber': contact_number,
        'query': query
    }
    
    tickets.append(ticket)
    write_tickets(tickets)
    
    return jsonify({'ticketId': ticket_id})

@app.route('/delete-ticket/<ticket_id>', methods=['DELETE'])
def delete_ticket(ticket_id):
    tickets = read_tickets()
    tickets = [ticket for ticket in tickets if ticket['ticketId'] != ticket_id]
    write_tickets(tickets)
    return jsonify({'status': 'success'})



NOTES_DIR = os.path.abspath(os.path.join(current_directory, '..', 'db', 'notes'))

@app.route('/list-files')
def list_files():
    try:
        files = os.listdir(NOTES_DIR)
        return jsonify(files=files)
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(NOTES_DIR, filename, as_attachment=True)


LMS_DIR = os.path.abspath(os.path.join(current_directory, '..'))
sys.path.append(LMS_DIR)
# print(LMS_DIR)
from lms_backend.student_dashboard_backend.performance_bot.call_performance_bot import PerformanceBot
from lms_backend.student_dashboard_backend.learning_coach.call_learning_coach import LearningCoach


@app.route('/performance_bot')
def performance_bot():
    prompt = request.args.get('prompt', '')
    student_id = current_user.id
    # print(prompt,student_id)
    result=PerformanceBot().run_performance_bot(prompt, student_id)
    # print(result)
    if "Learning Roadmap" in result:
        return jsonify({"result": result,"show_button":True})
    return jsonify({"result": result,"show_button":False})




@app.route('/learning_coach_api')
def learning_coach_api():
    prompt = request.args.get('prompt', '')
    result=LearningCoach().run_learning_coach(prompt)
    # print(result)
    return jsonify({"result": result})


from lms_backend.student_dashboard_backend.pwd_support_bot.call_pwd_support_bot import SupportBot
@app.route('/call_pwd_support_bot', methods=['POST'])
def call_pwd_support_bot():
    data = request.get_json()
    recognized_text = data.get('text', '')

    if not recognized_text:
        return jsonify({"message": "No text provided"}), 400

    # Assuming `current_user.id` is available in your context
    response = SupportBot().run_support_bot(student_id=current_user.id, user_query=recognized_text,language = 'en-US')
    return jsonify({"message": "SupportBot is running.", "response": response}), 200


from lms_backend.student_dashboard_backend.performance_bot.config import STUDENT_ROADMAP_PROMPT
@app.route('/generate_roadmap')
def generate_roadmap():
    # prompt = request.args.get('student_id', '')
    SupportBot().run_support_bot(student_id="1")
    # print(result)
    return
    
@app.route('/notices', methods=['GET'])
def get_notices():
    with open('notices.json', 'r') as file:
        notices = json.load(file)
    # print(notices)
    return jsonify(notices)

from lms_backend.admin_dashboard_backend.utility_action.create_a_notice import CreateANotice
@app.route('/create_notices', methods=['GET'])
def create_notices():
    cn = CreateANotice()
    prompt = request.args.get('prompt', '')
    result=cn.run_create_notice(prompt)
      # Append new notice
    new_notice = {
        "img_url": '/'+result['img_url'],
        "title": result['title'],
        "description": result['description']
    }
    
    # Save updated data back to the JSON file
    with open("recent_created_notices.json", 'w') as file:
        json.dump([new_notice], file, indent=4)

    return jsonify(result)

@app.route('/latest_created_notices', methods=['GET'])
def latest_created_notices():
    try:
        with open('recent_created_notices.json', 'r') as file:
            notices = json.load(file)
        print(notices)
        return jsonify({"result": notices})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/upload_notes_api', methods=['POST'])
def upload_notes_api():
    if 'note-file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['note-file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Save the file
    file_path = os.path.join(NOTES_DIR, file.filename)
    file.save(file_path)

    return jsonify({'message': f'File {file.filename} uploaded successfully'}), 200

import speech_recognition as sr
# @app.route('/upload_audio', methods=['POST'])
# def upload_audio():
#     if 'audio' not in request.files:
#         return jsonify({"error": "No audio file provided"}), 400

#     audio_file = request.files['audio']
    
#     # Save the uploaded audio file
#     file_path = 'recording.wav'
#     audio_file.save(file_path)

#     # Process the audio file (if needed)
#     try:
#         # Example processing step: print the file path (you can replace this with actual processing)
#         print(f"Audio file saved at: {file_path}")

#         # If you need to perform additional processing, do it here
#         # ...

#         return jsonify({"message": "Audio file processed successfully"}), 200
#     except Exception as e:
#         return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    

########### FALCON CODE ENDS HERE ###########
if __name__ == '__main__':
    # app.run(debug=True)
    
    # debug = True
    debug = False
    
    from gevent.pywsgi import WSGIServer
    import signal
    import sys
    def shutdown_server(signal, frame):
        http_server.close()
        if(not debug):
            time.sleep(1)
        sys.exit(0)
    app.debug = debug
    http_server = WSGIServer(('', 9000), app, log=None)
    signal.signal(signal.SIGINT, shutdown_server)
    


    http_server.serve_forever()
