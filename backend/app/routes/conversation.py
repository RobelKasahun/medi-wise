from app import db
from app.models.chat import Chat, Conversation
from app.models.user import User
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import uuid
from datetime import datetime, timezone

conversation_blueprint = Blueprint('conversation', __name__)

@conversation_blueprint.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    """Get all conversations for the logged-in user"""
    try:
        user_id = str(get_jwt_identity())
        
        conversations = Conversation.query.filter_by(user_id=user_id).order_by(Conversation.updated_at.desc()).all()
        
        result = []
        for conv in conversations:
            # Get the first message to use as preview
            first_message = Chat.query.filter_by(conversation_id=conv.id).first()
            preview = first_message.user_prompt[:50] + '...' if first_message and len(first_message.user_prompt) > 50 else (first_message.user_prompt if first_message else '')
            
            result.append({
                'id': conv.id,
                'title': conv.title,
                'preview': preview,
                'created_at': conv.created_at.isoformat() if conv.created_at else None,
                'updated_at': conv.updated_at.isoformat() if conv.updated_at else None
            })
        
        return jsonify({'conversations': result}), 200
        
    except Exception as e:
        print(f"Error fetching conversations: {str(e)}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@conversation_blueprint.route('/conversations/<conversation_id>', methods=['GET'])
@jwt_required()
def get_conversation(conversation_id):
    """Get a specific conversation with all its messages"""
    try:
        user_id = str(get_jwt_identity())
        
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        messages = Chat.query.filter_by(conversation_id=conversation_id).order_by(Chat.created_at.asc()).all()
        
        message_list = []
        for msg in messages:
            message_list.append({
                'role': 'user',
                'content': msg.user_prompt,
                'timestamp': msg.created_at.isoformat() if msg.created_at else None
            })
            if msg.llm_response:
                message_list.append({
                    'role': 'assistant',
                    'content': msg.llm_response,
                    'timestamp': msg.created_at.isoformat() if msg.created_at else None
                })
        
        return jsonify({
            'conversation': {
                'id': conversation.id,
                'title': conversation.title,
                'created_at': conversation.created_at.isoformat() if conversation.created_at else None,
                'updated_at': conversation.updated_at.isoformat() if conversation.updated_at else None
            },
            'messages': message_list
        }), 200
        
    except Exception as e:
        print(f"Error fetching conversation: {str(e)}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@conversation_blueprint.route('/conversations', methods=['POST'])
@jwt_required()
def create_conversation():
    """Create a new conversation"""
    try:
        user_id = str(get_jwt_identity())
        data = request.get_json()
        
        title = data.get('title', 'New Conversation')
        
        conversation = Conversation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.session.add(conversation)
        db.session.commit()
        
        return jsonify({
            'conversation': {
                'id': conversation.id,
                'title': conversation.title,
                'created_at': conversation.created_at.isoformat(),
                'updated_at': conversation.updated_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        print(f"Error creating conversation: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@conversation_blueprint.route('/conversations/<conversation_id>', methods=['DELETE'])
@jwt_required()
def delete_conversation(conversation_id):
    """Delete a conversation"""
    try:
        user_id = str(get_jwt_identity())
        
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        db.session.delete(conversation)
        db.session.commit()
        
        return jsonify({'message': 'Conversation deleted successfully'}), 200
        
    except Exception as e:
        print(f"Error deleting conversation: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@conversation_blueprint.route('/conversations/<conversation_id>/title', methods=['PUT'])
@jwt_required()
def update_conversation_title(conversation_id):
    """Update conversation title"""
    try:
        user_id = str(get_jwt_identity())
        data = request.get_json()
        
        title = data.get('title')
        if not title:
            return jsonify({'error': 'Title is required'}), 400
        
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        conversation.title = title
        conversation.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({
            'conversation': {
                'id': conversation.id,
                'title': conversation.title,
                'updated_at': conversation.updated_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        print(f"Error updating conversation title: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500