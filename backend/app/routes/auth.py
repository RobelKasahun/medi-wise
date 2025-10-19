from flask import Blueprint

auth_blueprint = Blueprint('auth', __name__)

# API endpoint for Sign Up
@auth_blueprint.route('/signup', methods=['GET', 'POST'])
def register():
    return f'Sign Up...'

# API endpoint for login
@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    return 'Log In...'
