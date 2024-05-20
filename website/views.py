# from flask import Blueprint, render_template, redirect, url_for, request, session, jsonify, Response
# from flask_login import login_required, current_user
# from camera import Video
# import re, threading, time, json

# from .models import Educator, Coordinator, Sessions
# from . import db

# views = Blueprint('views', __name__)

# # Global variables
# session_active = False
# emotion_data = {}
# start_time = None  # Variable to store the start time of the session




# # ----- VIEWS -----
# @views.route('/dashboard/educator')
# @login_required
# def dashboard_educator():
#     user = current_user
#     if user.role == "coordinator":
#         return redirect(url_for('views.dashboard_coordinator'))
#     return render_template('dashboard_educator.html', user=user)

# @views.route('/dashboard/coordinator')
# @login_required
# def dashboard_coordinator():
#     user = current_user
#     if user.role == "educator":
#         return redirect(url_for('views.dashboard_educator'))
#     return render_template('dashboard_coordinator.html', user=user)

# @views.route('/start/<id>')
# @login_required
# def start(id):
#     global emotion_data
#     user = current_user
    
#     # Clear emotion data and start time for the next session
#     emotion_data = {}

#     return render_template('start.html', user=user)

# # EMOTION DETECTION SECTION
# def gen(camera):
#     while True:
#         frame, obj_info = camera.get_frame()
#         # Print ID and emotion information continuously
#         for info in obj_info:
#             obj_id = info.split(",")[0].split(":")[1].strip()
#             emotion = info.split(",")[1].split(":")[1].strip()
#             print("==========\n" + f"ID:{obj_id}\nEMOTION:{emotion}" + "\n==========")
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame + 
#                b'\r\n\r\n')

# @views.route('/video')
# def video():
#     video_camera = Video()
#     return Response(gen(video_camera), mimetype='multipart/x-mixed-replace; boundary=frame')

# # Function to start emotion detection session
# def start_emotion_detection():
#     global session_active, emotion_data

#     video_camera = Video()
#     # useCam = use_camera()

#     while session_active:
#         frame, obj_info = video_camera.get_frame()
#         # Process the detected emotions
#         for info in obj_info:
#             obj_id = info.split(",")[0].split(":")[1].strip()
#             emotion = info.split(",")[1].split(":")[1].strip()
            
#             # Check if the obj_id exists in emotion_data
#             if obj_id in emotion_data:
#                 # If the obj_id exists, append the emotion to the list
#                 emotion_data[obj_id].append(emotion)
#             else:
#                 # If the obj_id doesn't exist, create a new list with the emotion
#                 emotion_data[obj_id] = [emotion]
#         time.sleep(5)

# @views.route('/start_session', methods=['GET', 'POST'])
# @login_required
# def start_session():
#     global session_active, emotion_data, start_time
#     session_active = True

#     # Set the start time only if it hasn't been set yet
#     if start_time is None:
#         start_time = time.time()

#     # Start emotion detection thread
#     threading.Thread(target=start_emotion_detection).start()
#     return jsonify({'message': 'Session started'})

# @views.route('/stop_session',  methods=['POST'])
# @login_required
# def stop_session():
#     global session_active, emotion_data, start_time

#     session_active = False
#     # Save emotion data to JSON file
#     filename = f'{current_user.id}_emotion_data.json'
#     with open(filename, 'w') as f:
#         json.dump(emotion_data, f)

#     # Calculate percentage of Interested and Uninterested emotions
#     interested_count = 0
#     uninterested_count = 0

#     for emotions in emotion_data.values():
#         for emotion in emotions:
#             if emotion in ["Happy", "Surprise"]:
#                 interested_count += 1
#             elif emotion in ["Angry", "Disgust", "Fear", "Sad"]:
#                 uninterested_count += 1

#     total_count = interested_count + uninterested_count

#     # Handle case where total_count is zero to avoid division by zero
#     if total_count != 0:
#         interested_percentage = round((interested_count / total_count) * 100)
#         uninterested_percentage = round((uninterested_count / total_count) * 100)
#     else:
#         interested_percentage = 0
#         uninterested_percentage = 0

#     # Calculate total time of the session in seconds
#     total_time_seconds = int(time.time() - start_time)

#     # Clear emotion data for the next session
#     emotion_data = {}

#     # Reset start time to None for the next session
#     start_time = None

#     return jsonify({'message': 'Session stopped', 
#                     'emotion_data': emotion_data, 
#                     'interested_percentage': interested_percentage,
#                     'uninterested_percentage': uninterested_percentage,
#                     'total_time_seconds': total_time_seconds})


# # save changes route
# @views.route('/save_change', methods=['POST'])
# @login_required
# def save_change():
#     try:
#         # Retrieve data from the request
#         title = request.form.get('subject-title')
#         interested_percentage = request.form.get('interested')
#         uninterested_percentage = request.form.get('uninterested')
#         total_time_seconds = request.form.get('total_time_seconds')

#         # Create a new session object
#         session = Sessions(
#             user_id=current_user.id,
#             title=title,
#             interested=interested_percentage,
#             uninterested=uninterested_percentage,
#             duration=total_time_seconds
#         )

#         # Add the session to the database session
#         db.session.add(session)
#         db.session.commit()

#         return jsonify({'message': 'Session data saved successfully!'})
#     except Exception as e:
#         # Handle any errors that occur during the database operation
#         return jsonify({'error': str(e)}), 500




from flask import Blueprint, render_template, redirect, url_for, request, session, jsonify, Response
from flask_login import login_required, current_user
from camera import Video
import re, threading, time, json
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .models import Educator, Coordinator, Sessions
from . import db

views = Blueprint('views', __name__)

# Global variables
session_active = False
emotion_data = {}
start_time = None  # Variable to store the start time of the session

# Initialize the camera instance outside of any functions
video_camera = Video()




def send_email(sender_email, sender_password, recipient_email, subject, message):
    # Setup the MIME
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Attach the message to the email
    msg.attach(MIMEText(message, 'plain'))

    # Create SMTP session
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()

    # Login
    server.login(sender_email, sender_password)

    # Send email
    server.sendmail(sender_email, recipient_email, msg.as_string())

    # Close the SMTP session
    server.quit()



# ----- VIEWS -----

def get_dates_of_current_week():
    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return [start_of_week + timedelta(days=i) for i in range(7)]

@views.route('/dashboard/educator')
@login_required
def dashboard_educator():
    user = current_user
    if user.role == "coordinator":
        return redirect(url_for('views.dashboard_coordinator'))
    
    # Get sessions data for the past week
    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    userSessions = Sessions.query.filter_by(user_id=current_user.id)\
                                 .filter(Sessions.date.between(start_of_week, end_of_week))\
                                 .all()

    # Initialize data for each day of the week
    session_data = {str(start_of_week.date() + timedelta(days=i)): 0 for i in range(7)}

    # Update session data with actual values
    for session in userSessions:
        session_date = session.date.date()
        session_data[str(session_date)] += 1

    # Get dates for the current week
    current_week_dates = get_dates_of_current_week()

    # Create labels for the chart using day names
    day_names = [date.strftime('%A') for date in current_week_dates]
    
    return render_template('dashboard_educator.html', user=user, session_data=session_data, day_names=day_names)


@views.route('/history/<id>')
@login_required
def history(id):
    user = current_user

    if str(id) != str(user.id):
        # Redirect to the same page if user enters the wrong id
        return redirect(request.referrer)
    
    userSessionsHistory = Sessions.query.filter_by(user_id=current_user.id).order_by(Sessions.date.desc()).all()

    session_data = []
    for session in userSessionsHistory:
        data = {
            'id': session.id,
            'title': session.title,
            'interested': session.interested,
            'uninterested': session.uninterested,
            'duration': session.duration,
            'date_time': session.date
        }
        session_data.append(data)

    return render_template('history.html', user=user, session_data=session_data)



@views.route('/dashboard/coordinator')
@login_required
def dashboard_coordinator():
    user = current_user
    if user.role == "educator":
        return redirect(url_for('views.dashboard_educator'))
    
    educators = Educator.query.all()

    for educator in educators:
        sessions = Sessions.query.filter_by(user_id=educator.id).all()
        
        # Initialize counters for interested and uninterested sessions
        interested_count = 0
        uninterested_count = 0
        
        # Count interested and uninterested sessions
        for session in sessions:
            interested_count += session.interested
            uninterested_count += session.uninterested
        
        # Calculate percentages
        total_sessions = len(sessions)
        if total_sessions > 0:
            interested_percentage = (interested_count / total_sessions) * 100
            uninterested_percentage = (uninterested_count / total_sessions) * 100
        else:
            interested_percentage = 0
            uninterested_percentage = 0
    
    return render_template('dashboard_coordinator.html', user=user, educators=educators,
                           interested_percentage=(round(interested_percentage) / 100),
                           uninterested_percentage=(round(uninterested_percentage) / 100))


@views.route('/coordinator/educatorslist')
@login_required
def educators_list():
    user = current_user
    if user.role == "educator":
        return redirect(url_for('views.dashboard_educator'))
    
    educators = Educator.query.all()

    
    return render_template('educators_list.html', user=user, educators=educators)

@views.route('/view/<id>')
@login_required
def view_educator(id):
    user = current_user

    sessions = Sessions.query.filter_by(user_id=id).all()
    educator = Educator.query.filter_by(id=id).first()

    userSessionsHistory = Sessions.query.filter_by(user_id=id).order_by(Sessions.date.desc()).all()

    session_data = []
    for session in userSessionsHistory:
        data = {
            'id' : session.id,
            'title' : session.title,
            'interested' : session.interested,
            'uninterested' : session.uninterested,
            'duration' : session.duration,
            'date_time' : session.date
        }
        session_data.append(data)

    print("NAMEEEEE: " + educator.name)

    
    return render_template('view.html', user=user, sessions=sessions, educator=educator, session_data=session_data)


@views.route('/start/<id>')
@login_required
def start(id):
    global emotion_data
    user = current_user

    if(id != user.id):
        # Redirect to the same page if user enter wrong id
        return redirect(request.referrer)
    
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
    # video_camera = Video()
    return Response(gen(video_camera), mimetype='multipart/x-mixed-replace; boundary=frame')

# Function to start emotion detection session
def start_emotion_detection():
    global session_active, emotion_data

    while session_active:
        # video_camera = Video()
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


        sender_email = 'andredummy02@gmail.com'
        sender_password = 'hmsrsuxyieshclxo'
        recipient_email = str(current_user.email)
        subject = str(title + " Session Results")
        message = ("INTERESTED: " + interested_percentage + "\n UNINTERESTED: " + uninterested_percentage)

        send_email(sender_email, sender_password, recipient_email, subject, message)

        # Redirect to the same page after saving
        return redirect(request.referrer)

    except Exception as e:
        # Handle any errors that occur during the database operation
        return jsonify({'error': str(e)}), 500



@views.route('/delete_record/<int:id>')  # Specify the type of id as int
@login_required
def delete_record(id):
    session_to_remove = Sessions.query.filter_by(id=id).first()  # Get the single record with the provided id

    if session_to_remove:  # Check if the session exists
        db.session.delete(session_to_remove)
        db.session.commit()

    # Redirect to the same page after deletion
    return redirect(request.referrer)