import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy 
from flask_migrate import Migrate
from flask_mail import Mail
from config import Config
from flask_jwt_extended import JWTManager

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
    
    # load the configuration settings from the Config class
    '''
        load database uri, secret key, and track object modification
    '''
    app.config.from_object(Config)
    app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    
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