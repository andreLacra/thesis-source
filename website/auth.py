from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from . import views
from . import db
from .models import Educator, Coordinator
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
import json, re, random, datetime

auth = Blueprint('auth', __name__)

# -----FUNCTIONS
def validate_email(email):  #email validation
    # Define the regex pattern
    pattern = r"^[a-zA-Z0-9._%+-]+@ue\.edu\.ph$"
    
    # Check if the email matches the pattern
    if re.match(pattern, email):
        return True
    else:
        return False
    
# Check if password is valid
def is_valid_password(passwordInput):
    # Check the length of the password
    if len(passwordInput) < 8:
        return False

    # Check if the password contains at least one uppercase letter, one lowercase letter, and one digit
    if not re.search(r'[A-Z]', passwordInput) or not re.search(r'[a-z]', passwordInput) or not re.search(r'\d', passwordInput):
        return False

    return True

# Check if name is valid
def validate_name(name):
    # Define the regex pattern for name validation
    name_pattern = r"^[a-zA-Z\s]+$"

    # Check if the name matches the name pattern
    if re.match(name_pattern, name):
        return True
    else:
        return False
    

def is_id_unique(id):
    # Check if the ID exists in the Educator table
    if Educator.query.filter_by(id=id).first() is not None:
        return False

    # Check if the ID exists in the Coordinator table
    if Coordinator.query.filter_by(id=id).first() is not None:
        return False

    return True
    
def generate_id():
    # Get the current year
    current_year = datetime.datetime.now().year

    while True:
        # Generate a random 7-digit number
        random_number = random.randint(1000000, 9999999)

        # Combine the current year and the random number
        unique_id = f"{current_year}{random_number}"

        # Check if the ID is unique
        if is_id_unique(unique_id):
            return unique_id



# ---------------------
loggedIn = False
currentAccountRole = None

@auth.route('/')
def home():
    global loggedIn, currentAccountRole

    if(loggedIn == True):
        if currentAccountRole == "educator":
            return redirect(url_for('views.dashboard_educator'))
        elif currentAccountRole == "coordinator":
            return redirect(url_for('views.dashboard_coordinator'))
    else:
        currentAccountRole = None

    return render_template('index.html')

@auth.route('/get-role', methods=['POST'])
def get_role():
    global currentAccountRole

    role = request.form.get('role')
    currentAccountRole = role.lower()

    if role:
        return redirect(url_for('auth.login'))  # Redirect to auth.login with the selected role
    else:
        flash('Role not selected')  # Flash a message if role is not selected
        return redirect(url_for('/'))  # Redirect to index route


# LOG IN PAGE
@auth.route('/login', methods=['GET','POST'])
def login(): 
    message = None
    user = None
    success_message = session.pop('success_message', None)

    global loggedIn, currentAccountRole
    if(loggedIn == True):
        if currentAccountRole == "educator":
            return redirect(url_for('views.dashboard_educator'))
        elif currentAccountRole == "coordinator":
            return redirect(url_for('views.dashboard_coordinator'))

    if (request.method == "POST"):
        email = request.form.get("email")
        password = request.form.get("password")

        user = None
        if(currentAccountRole == "educator"):
            user = Educator.query.filter_by(email=email).first()
        elif(currentAccountRole == "coordinator"):
            user = Coordinator.query.filter_by(email=email).first()

        if (email != None) and (password != None):
            if(user):
                if(user.role == currentAccountRole):
                    if check_password_hash(user.password, password):
                        login_user(user, remember=True)
                        loggedIn = True
                        session["user_id"] = user.id
                        
                        if(currentAccountRole == "educator"):
                            return redirect(url_for('views.dashboard_educator'))
                        elif(currentAccountRole == "coordinator"):
                            return redirect(url_for('views.dashboard_coordinator'))
                    else:
                        message = 'Invalid Password. Please Try Again.'
                else:
                    message = 'Invalid Account Type. Please Try Again.'
            else:
                message = 'Invalid Email. Please Try Again.'


    return render_template('login.html', role=currentAccountRole, message=message, success_message=success_message)


# SIGN UP PAGE
@auth.route('/signup/<role>', methods=['GET','POST'])
def signup(role):
    message = None
    user = None
    user_role = role.lower()

    global loggedIn
    if(loggedIn == True):
        if currentAccountRole == "educator":
            return redirect(url_for('views.dashboard_educator'))
        elif currentAccountRole == "coordinator":
            return redirect(url_for('views.dashboard_coordinator'))

    if (request.method == "POST"):
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        if (email != None) and (password != None) and (name !=  None):
            user = None
            if(currentAccountRole == "educator"):
                user = Educator.query.filter_by(email=email).first()
            elif(currentAccountRole == "coordinator"):
                user = Coordinator.query.filter_by(email=email).first()
        
            if(user):
                message = 'This email already exists. Please try again.'
            elif validate_name(name) == False:
                message = "Invalid name. Please try again."
            elif validate_email(email) == False:
                message = "Invalid email. Please use UE email."
            elif ((is_valid_password(password) == False)):
                message = "Password appeared to be weak. Please try again."
            else:
                # DATABASE 
                new_user = None
                if(currentAccountRole == "educator"):
                    new_user = Educator(
                            id=generate_id(),
                            name=name, 
                            email=email,
                            password=generate_password_hash(password, method='sha256'),
                            role=currentAccountRole)
                elif(currentAccountRole == "coordinator"):
                    new_user = Coordinator(
                            id=generate_id(),
                            name=name, 
                            email=email,
                            password=generate_password_hash(password, method='sha256'),
                            role=currentAccountRole)
                    
                db.session.add(new_user)
                db.session.commit()

                session['success_message'] = "Your account has been successfully created!"

                return redirect(url_for('auth.login'))

    return render_template('signup.html', role=role, message=message)


@auth.route('/logout')
@login_required
def signout():
    global loggedIn, currentAccountRole
    session.pop("user_id", None)
    logout_user()
    loggedIn = False
    currentAccountRole = None
    return redirect(url_for('auth.home'))