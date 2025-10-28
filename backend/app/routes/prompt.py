from app import db
from app.models.chat import Chat
from app.models.user import User
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests

prompt_blueprint = Blueprint('prompt', __name__)

@prompt_blueprint.route('/prompt', methods=['GET', 'POST'])
@jwt_required()
def prompt():
    logged_in_user = str(get_jwt_identity())
    
    data = request.get_json()
    user_prompt = data.get('user_prompt')
    llm_response = 'Hello, World!'
    
    url = f'https://api.fda.gov/drug/label.json?search=openfda.brand_name:{user_prompt.lower()}&limit=1000'
    
    response = requests.get(url=url)
    
    if not Chat.query.filter_by(user_id=logged_in_user, user_prompt=user_prompt):
        chat = Chat(user_id=logged_in_user, user_prompt=user_prompt, llm_response=llm_response)
    
        db.session.add(chat)
        db.session.commit()
    
    return jsonify(len(response.json()['results'])), 200