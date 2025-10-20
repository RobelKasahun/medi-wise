from app.models.chat import Chat
from app.models.user import User
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

# create auth blueprint
auth_blueprint = Blueprint('auth', __name__)

# API endpoint for Sign Up
@auth_blueprint.route('/signup', methods=['GET', 'POST'])
def register():
    return 'Sign up...'

# API endpoint for login
@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    return 'Log In...'
