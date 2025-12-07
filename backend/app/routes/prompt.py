import os
from app import db
from app.models.chat import Chat
from app.models.user import User
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bs4 import BeautifulSoup
import requests
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI
from dotenv import load_dotenv
import os

# load environment variables
load_dotenv()

# get OpenAI API Key
openai_api_key = os.getenv('OPENAI_API_KEY')

# encode text into numeric vectors
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    # embedding model = text-embedding-3-small
    api_key=openai_api_key, model_name="text-embedding-3-small"
)

# Initialize the Chroma client with persistence
chromadb_client = chromadb.PersistentClient(path="./chroma_persistent_storage")
collection_name = "document_qa_collection"
collection = chromadb_client.get_or_create_collection(
    name=collection_name, embedding_function=openai_ef
)

client = OpenAI(api_key=openai_api_key)



prompt_blueprint = Blueprint('prompt', __name__)

@prompt_blueprint.route('/prompt', methods=['GET', 'POST'])
@jwt_required()
def prompt():
    logged_in_user = str(get_jwt_identity())
    
    data = request.get_json()
    user_prompt = data.get('user_prompt')
    
    url = f'https://api.fda.gov/drug/label.json?search=openfda.brand_name:{user_prompt.lower()}&limit=1'
    
    response = requests.get(url=url)
    
    if response.status_code != 200:
        return f"Response for {user_prompt} not found", 404
    
    result = ''
    for data in response.json()['results']:
        flat = [item for sublist in data.values() for item in sublist]  # flatten nested list
        result += " ".join(flat)
        
    soup = BeautifulSoup(result, "html.parser")
    clean_text = soup.get_text(separator="\n", strip=True)
        
    # write data to text file
    with open(f'/Users/robelayelew/Desktop/medi-wise/backend/app/files/{user_prompt.lower()}.txt', mode='w', encoding="utf-8") as file:
        file.write(clean_text)
        
    # Load documents from the directory
    directory_path = "/Users/robelayelew/Desktop/medi-wise/backend/app/files/"
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

    # Upsert documents with embeddings into Chroma
    for doc in chunked_documents:
        print("==== Inserting chunks into db;;; ====")
        collection.upsert(
            ids=[doc["id"]], documents=[doc["text"]], embeddings=[doc["embedding"]]
        )
        
    question = user_prompt.lower()
    relevant_chunks = query_documents(question)
    answer = generate_response(question, relevant_chunks)
    
    if not Chat.query.filter_by(user_id=logged_in_user, user_prompt=question).first():
        chat = Chat(user_id=logged_in_user, user_prompt=question, llm_response=answer.content)
        db.session.add(chat)
        db.session.commit()
    else:
        print('Chat exists...')
        
    # delete the text file
    file = f'/Users/robelayelew/Desktop/medi-wise/backend/app/files/{user_prompt.lower()}.txt'
    os.remove(file)
    
    return answer.content, 200



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
    # query_embedding = get_openai_embedding(question)
    results = collection.query(query_texts=question, n_results=n_results)

    # Extract the relevant chunks
    relevant_chunks = [doc for sublist in results["documents"] for doc in sublist]
    print("==== Returning relevant chunks ====")
    return relevant_chunks
    # for idx, document in enumerate(results["documents"][0]):
    #     doc_id = results["ids"][0][idx]
    #     distance = results["distances"][0][idx]
    #     print(f"Found document chunk: {document} (ID: {doc_id}, Distance: {distance})")


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