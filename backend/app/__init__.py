from flask import Flask

def create_app():
    app = Flask(__name__)
    
    with app.app_context():
        # Register the blueprints with the app
        from app.routes.auth import auth_blueprint
        
        app.register_blueprint(auth_blueprint, url_prefix='/auth')
    return app