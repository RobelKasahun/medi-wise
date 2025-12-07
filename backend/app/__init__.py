import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy 
from flask_migrate import Migrate
from flask_mail import Mail
from config import Config
from flask_jwt_extended import JWTManager
from flask_cors import CORS

# open database connection
db = SQLAlchemy()

'''
    enables database migrations, so when you change models, 
    you can update the database schema smoothly.
'''
migrate = Migrate()

# for password-reset emails
mail = Mail()

def create_app():
    app = Flask(__name__)
    
    '''
        it allows backend to accept requests from your frontend, 
        even if they are on different domains/ports
        
        Allows your frontend (maybe running on localhost:3000) 
        to talk to this Flask backend (usually on localhost:5000).
    '''
    # allows the front end to talk to the backend
    # http://localhost:5173
    CORS(app, supports_credentials=True, origins=["http://localhost:5173"])
    
    # load the configuration settings from the Config class
    '''
        load database uri, secret key, and track object modification
    '''
    app.config.from_object(Config)
    app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['JWT_TOKEN_LOCATION'] = ["cookies"]
    app.config['JWT_COOKIE_SECURE'] = False     # only for local dev
    app.config['JWT_COOKIE_SAMESITE'] = "None"  # required for cross-origin
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False
    
    # for Reset password instructions link TODO:
    
    # initialization
    mail.init_app(app)
    # initialize jwt
    jwt = JWTManager(app)
    # initialize db
    db.init_app(app)
    # initialize migration
    migrate.init_app(app, db)
    
    with app.app_context():
        # import blueprints
        from app.routes.auth import auth_blueprint
        from app.routes.prompt import prompt_blueprint

        # Register the blueprints with the app
        app.register_blueprint(auth_blueprint, url_prefix='/auth')
        app.register_blueprint(prompt_blueprint, url_prefix='/')
        
    return app