from flask import Blueprint, render_template, redirect, url_for, request, session, jsonify, Response
from flask_login import login_required, current_user
from camera import Video
import re, threading, time, json

from .models import Educator, Coordinator, Sessions
from . import db

views = Blueprint('views', __name__)

# Global variables
session_active = False
emotion_data = {}
start_time = None  # Variable to store the start time of the session

# Initialize the camera instance outside of any functions
video_camera = Video()

# ----- VIEWS -----
@views.route('/dashboard/educator')
@login_required
def dashboard_educator():
    user = current_user
    if user.role == "coordinator":
        return redirect(url_for('views.dashboard_coordinator'))
    return render_template('dashboard_educator.html', user=user)

@views.route('/dashboard/coordinator')
@login_required
def dashboard_coordinator():
    user = current_user
    if user.role == "educator":
        return redirect(url_for('views.dashboard_educator'))
    return render_template('dashboard_coordinator.html', user=user)

@views.route('/start/<id>')
@login_required
def start(id):
    global emotion_data
    user = current_user
    
    # Clear emotion data and start time for the next session
    emotion_data = {}

    return render_template('start.html', user=user)

# EMOTION DETECTION SECTION
def gen(camera):
    while True:
        frame, obj_info = camera.get_frame()
        # Print ID and emotion information continuously
        for info in obj_info:
            obj_id = info.split(",")[0].split(":")[1].strip()
            emotion = info.split(",")[1].split(":")[1].strip()
            print("==========\n" + f"ID:{obj_id}\nEMOTION:{emotion}" + "\n==========")
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + 
               b'\r\n\r\n')

@views.route('/video')
def video():
    return Response(gen(video_camera), mimetype='multipart/x-mixed-replace; boundary=frame')

# Function to start emotion detection session
def start_emotion_detection():
    global session_active, emotion_data

    while session_active:
        frame, obj_info = video_camera.get_frame()
        # Process the detected emotions
        for info in obj_info:
            obj_id = info.split(",")[0].split(":")[1].strip()
            emotion = info.split(",")[1].split(":")[1].strip()
            
            # Check if the obj_id exists in emotion_data
            if obj_id in emotion_data:
                # If the obj_id exists, append the emotion to the list
                emotion_data[obj_id].append(emotion)
            else:
                # If the obj_id doesn't exist, create a new list with the emotion
                emotion_data[obj_id] = [emotion]
        time.sleep(5)

@views.route('/start_session', methods=['GET', 'POST'])
@login_required
def start_session():
    global session_active, emotion_data, start_time
    session_active = True

    # Set the start time only if it hasn't been set yet
    if start_time is None:
        start_time = time.time()

    # Start emotion detection thread
    threading.Thread(target=start_emotion_detection).start()
    return jsonify({'message': 'Session started'})

@views.route('/stop_session',  methods=['POST'])
@login_required
def stop_session():
    global session_active, emotion_data, start_time

    session_active = False
    # Save emotion data to JSON file
    filename = f'{current_user.id}_emotion_data.json'
    with open(filename, 'w') as f:
        json.dump(emotion_data, f)

    # Calculate percentage of Interested and Uninterested emotions
    interested_count = 0
    uninterested_count = 0

    for emotions in emotion_data.values():
        for emotion in emotions:
            if emotion in ["Happy", "Surprise"]:
                interested_count += 1
            elif emotion in ["Angry", "Disgust", "Fear", "Sad"]:
                uninterested_count += 1

    total_count = interested_count + uninterested_count

    # Handle case where total_count is zero to avoid division by zero
    if total_count != 0:
        interested_percentage = round((interested_count / total_count) * 100)
        uninterested_percentage = round((uninterested_count / total_count) * 100)
    else:
        interested_percentage = 0
        uninterested_percentage = 0

    # Calculate total time of the session in seconds
    total_time_seconds = int(time.time() - start_time)

    # Clear emotion data for the next session
    emotion_data = {}

    # Reset start time to None for the next session
    start_time = None

    return jsonify({'message': 'Session stopped', 
                    'emotion_data': emotion_data, 
                    'interested_percentage': interested_percentage,
                    'uninterested_percentage': uninterested_percentage,
                    'total_time_seconds': total_time_seconds})


# save changes route
@views.route('/save_change', methods=['POST'])
@login_required
def save_change():
    try:
        # Retrieve data from the request
        title = request.form.get('subject-title')
        interested_percentage = request.form.get('interested')
        uninterested_percentage = request.form.get('uninterested')
        total_time_seconds = request.form.get('total_time_seconds')

        # Create a new session object
        session = Sessions(
            user_id=current_user.id,
            title=title,
            interested=interested_percentage,
            uninterested=uninterested_percentage,
            duration=total_time_seconds
        )

        # Add the session to the database session
        db.session.add(session)
        db.session.commit()

        return jsonify({'message': 'Session data saved successfully!'})
    except Exception as e:
        # Handle any errors that occur during the database operation
        return jsonify({'error': str(e)}), 500
