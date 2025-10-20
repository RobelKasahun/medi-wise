from app import db
from app.models.chat import Chat
from app.models.user import User
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token, set_refresh_cookies, set_access_cookies

# create auth blueprint
auth_blueprint = Blueprint('auth', __name__)

# API endpoint for Sign Up
@auth_blueprint.route('/signup', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # get form data
        form_data = request.get_json()
        first_name = form_data.get('first_name')
        last_name = form_data.get('last_name')
        email = form_data.get('email')
        password = form_data.get('password')
        
        # make sure all the required fields are not empty
        if not all([first_name, last_name, email, password]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # check for user existance using the given email
        if User.query.filter_by(email=email.lower()).first():
            return jsonify({'error': 'An account with this email already exists. Please try logging in or use a different email.'}), 409
        
        # create a user
        user = User(first_name=first_name, last_name=last_name, email=email.lower(), password_hash=generate_password_hash(password))
        
        # add user to the database
        db.session.add(user)
        db.session.commit()
        
        # redirect to the login page
        return jsonify({'message': 'User registered successfully'}), 201
    
    if request.method == 'GET':
        return jsonify({'message', f'Sign Up page'}), 200

# API endpoint for login
@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    # get form data
    form_data = request.get_json()
    email = form_data.get('email')
    password = form_data.get('password')
    
    # get the user using email if exists
    user = User.query.filter_by(email=email.lower()).first()
    
    # check if the user exists and password is correct
    if user and check_password_hash(user.password_hash, password):
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        # redirect to the landing page
        response = jsonify({'message': 'Login successful', 'access_token': access_token})
        
        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)
        
        return response, 200
    else:
        # The user with email address does not exist
        # a user associated with the given email does not exist     
        if not user:
            return jsonify({'error': 'Oops! That email doesn\'t match our records.'}), 401
        
         # the given password with the password in the database does not match
        if not check_password_hash(user.password_hash, password):
            return jsonify({'error': 'Oops! That password doesn\'t match our records.'}), 401
    
