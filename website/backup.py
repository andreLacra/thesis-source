from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from . import views
import json, re
from . import db
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user

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



# ---------------------
loggedIn = False
currentAccountRole = None

@auth.route('/')
def home():
    global loggedIn, currentAccountRole

    currentAccountRole = None

    if(loggedIn == True):
        if currentAccountRole == "educator":
            return redirect(url_for('views.dashboard_educator', user=current_user.id))
        elif currentAccountRole == "coordinator":
            return redirect(url_for('views.dashboard_coordinator', user=current_user.id))

    return render_template('index.html')

@auth.route('/get-role', methods=['POST'])
def get_role():
    global currentAccountRole

    role = request.form.get('role')
    currentAccountRole = role.lower()

    if role:
        return redirect(url_for('auth.login', role=role))  # Redirect to auth.login with the selected role
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
            return redirect(url_for('views.dashboard_educator', id=current_user.id))
        elif currentAccountRole == "coordinator":
            return redirect(url_for('views.dashboard_coordinator', id=current_user.id))

    if (request.method == "POST"):
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if (email != None) and (password != None):
            if(user):
                if(user.role == currentAccountRole):
                    if check_password_hash(user.password, password):
                        login_user(user, remember=True)
                        loggedIn = True
                        session["user_id"] = user.id
                        
                        if(currentAccountRole == "educator"):
                            return redirect(url_for('views.dashboard_educator', id=user.id))
                        elif(currentAccountRole == "coordinator"):
                            return redirect(url_for('views.dashboard_coordinator', id=user.id))
                    else:
                        message = 'Invalid Password. Please Try Again.'
                else:
                    message = 'Invalid Account Type. Please Try Again.'
            else:
                message = 'Invalid Email. Please Try Again.'


    return render_template('login.html', role=currentAccountRole, message=message, success_message=success_message)


# SIGN UP PAGE
@auth.route('/sign-up/<role>', methods=['GET','POST'])
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
            user = User.query.filter_by(email=email).first()
        
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
                new_user = User(
                        name=name, 
                        email=email,
                        password=generate_password_hash(password, method='sha256'),
                        role=user_role)
                db.session.add(new_user)
                db.session.commit()

                session['success_message'] = "Your account has been successfully created!"

                return redirect(url_for('auth.login'))

    return render_template('signup.html', role=role, message=message)


@auth.route('/logout')
@login_required
def signout():
    global loggedIn
    session.pop("user_id", None)
    logout_user()
    loggedIn = False
    return redirect(url_for('auth.home'))