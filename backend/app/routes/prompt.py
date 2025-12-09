import os
from app import db
from app.models.chat import Chat, Conversation
from app.models.user import User
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bs4 import BeautifulSoup
import requests
# import chromadb
# from chromadb.utils import embedding_functions
from openai import OpenAI
from dotenv import load_dotenv
import os

# load environment variables
load_dotenv()

# get OpenAI API Key
openai_api_key = os.getenv('OPENAI_API_KEY')

# encode text into numeric vectors
# openai_ef = embedding_functions.OpenAIEmbeddingFunction(
#     # embedding model = text-embedding-3-small
#     api_key=openai_api_key, model_name="text-embedding-3-small"
# )

# Initialize the Chroma client with persistence
# chromadb_client = chromadb.PersistentClient(path="./chroma_persistent_storage")
# collection_name = "document_qa_collection"
# collection = chromadb_client.get_or_create_collection(
#     name=collection_name, embedding_function=openai_ef
# )

client = OpenAI(api_key=openai_api_key)



prompt_blueprint = Blueprint('prompt', __name__)

@prompt_blueprint.route('/prompt', methods=['GET', 'POST'])
@jwt_required()
def prompt():
    try:
        logged_in_user = str(get_jwt_identity())
        
        data = request.get_json()
        user_prompt = data.get('user_prompt')
        conversation_id = data.get('conversation_id')
        
        # Check if OpenAI API key is configured
        if not openai_api_key or openai_api_key == 'your-openai-api-key-here':
            return jsonify({
                'error': 'OpenAI API key not configured. Please add your API key to backend/.env file.'
            }), 500
        
        url = f'https://api.fda.gov/drug/label.json?search=openfda.brand_name:{user_prompt.lower()}&limit=1'
        
        response = requests.get(url=url)
        
        if response.status_code != 200:
            return jsonify({'error': f"Medication information for '{user_prompt}' not found"}), 404
        
        result = ''
        for data in response.json()['results']:
            flat = [item for sublist in data.values() for item in sublist]  # flatten nested list
            result += " ".join(flat)
            
        soup = BeautifulSoup(result, "html.parser")
        clean_text = soup.get_text(separator="\n", strip=True)
            
        # write data to text file
        files_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'files')
        os.makedirs(files_dir, exist_ok=True)
        file_path = os.path.join(files_dir, f'{user_prompt.lower()}.txt')
        
        with open(file_path, mode='w', encoding="utf-8") as file:
            file.write(clean_text)
            
        # Load documents from the directory
        directory_path = files_dir
        documents = load_documents_from_directory(directory_path)

        print(f"Loaded {len(documents)} documents")
        # Split documents into chunks
        chunked_documents = []
        for doc in documents:
            chunks = split_text(doc["text"])
            print("==== Splitting docs into chunks ====")
            for i, chunk in enumerate(chunks):
                chunked_documents.append({"id": f"{doc['id']}_chunk{i+1}", "text": chunk})
                
        # Generate embeddings for the document chunks
        for doc in chunked_documents:
            print("==== Generating embeddings... ====")
            doc["embedding"] = get_openai_embedding(doc["text"])
            
        question = user_prompt.lower()
        relevant_chunks = query_documents(question)
        answer = generate_response(question, relevant_chunks)
        
        # Create or get conversation
        if not conversation_id:
            # Create a new conversation with the first prompt as title
            import uuid
            from datetime import datetime, timezone
            title = user_prompt[:50] + '...' if len(user_prompt) > 50 else user_prompt
            conversation = Conversation(
                id=str(uuid.uuid4()),
                user_id=logged_in_user,
                title=title,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.session.add(conversation)
            db.session.flush()  # Get the ID without committing
            conversation_id = conversation.id
        else:
            # Update existing conversation's updated_at
            conversation = Conversation.query.filter_by(id=conversation_id, user_id=logged_in_user).first()
            if conversation:
                from datetime import datetime, timezone
                conversation.updated_at = datetime.now(timezone.utc)
        
        # Save the chat message
        chat = Chat(
            user_id=logged_in_user,
            conversation_id=conversation_id,
            user_prompt=question,
            llm_response=answer.content
        )
        db.session.add(chat)
        db.session.commit()
            
        # delete the text file
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({
            'response': answer.content,
            'conversation_id': conversation_id
        }), 200
        
    except Exception as e:
        print(f"Error in prompt endpoint: {str(e)}")
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500



# Function to load documents from a directory
def load_documents_from_directory(directory_path):
    print("==== Loading documents from directory ====")
    documents = []
    for filename in os.listdir(directory_path):
        if filename.endswith(".txt"):
            with open(
                os.path.join(directory_path, filename), "r", encoding="utf-8"
            ) as file:
                documents.append({"id": filename, "text": file.read()})
    return documents

# Function to split text into chunks
def split_text(text, chunk_size=1000, chunk_overlap=20):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - chunk_overlap
    return chunks
        
# Function to generate embeddings using OpenAI API
def get_openai_embedding(text):
    response = client.embeddings.create(input=text, model="text-embedding-3-small")
    embedding = response.data[0].embedding
    print("==== Generating embeddings... ====")
    return embedding


# Function to query documents
def query_documents(question, n_results=2):
    # Temporary implementation without ChromaDB
    # This will return all chunks from the files directory
    files_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'files')
    documents = load_documents_from_directory(files_dir)
    
    all_chunks = []
    for doc in documents:
        chunks = split_text(doc["text"])
        all_chunks.extend(chunks[:n_results])  # Take first n_results chunks from each doc
    
    print("==== Returning relevant chunks ====")
    return all_chunks[:n_results] if all_chunks else []


# Function to generate a response from OpenAI
def generate_response(question, relevant_chunks):
    context = "\n\n".join(relevant_chunks)
    prompt = (
        "You are a medical assistant specialized in medications. Using the following pieces of "
        "retrieved context, answer the question accurately. Include the following details if they are present in the context: "
        "1. Side effects\n"
        "2. Warnings\n"
        "3. Dosage & administration\n"
        "4. Missed dose instructions\n"
        "5. Contraindications\n"
        "6. Interactions with other medications, foods, or substances\n"
        "7. Indications / Uses\n"
        "8. Pregnancy & breastfeeding notes\n"
        "9. Storage instructions\n"
        "10. Administration route\n\n"
        "If the information is not present in the context, say that you don't know. "
        "Format your answer in clear sections like this:\n\n"
        "Medication: <name>\n"
        "Side Effects:\n- ...\n"
        "Warnings:\n- ...\n"
        "Dosage & Administration:\n\n- ...\n"
        "Missed Dose:\n- ...\n"
        "Contraindications:\n- ...\n"
        "Interactions:\n- ...\n"
        "Indications / Uses:\n- ...\n"
        "Pregnancy & Breastfeeding Notes:\n- ...\n"
        "Storage Instructions:\n- ...\n"
        "Administration Route:\n- ...\n"
        "At the end, include a line stating: "
        "'The information provided is solely based on the content available in the context provided.'\n\n"
        "Keep the answer concise, using a maximum of three sentences per section, "
        "and avoid giving medical advice beyond the provided information.\n\n"
        "At the end of your answer, clearly state which information came from the provided context "
        "and whether the answer is based solely on that content or external knowledge.\n\n"
        "Context:\n" + context + "\n\nQuestion:\n" + question
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": prompt,
            },
            {
                "role": "user",
                "content": question,
            },
        ],
    )
    
    return response.choices[0].message