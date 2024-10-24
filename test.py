import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import io
import openai
import chromadb
import pandas as pd
import numpy as np
import json
from typing import List
from chromadb.utils import embedding_functions
from sklearn.metrics.pairwise import cosine_similarity
from streamlit_option_menu import option_menu
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Placeholder for OpenAI API Key
OPENAI_API_KEY = "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"
openai.api_key = OPENAI_API_KEY

# ChromaDB setup
chroma_client = chromadb.Client()
EMBEDDING_MODEL = "text-embedding-3-small"  # OpenAI embedding model

# Helper function to extract text from a JSON file
def extract_text_from_json(file) -> str:
    json_data = json.load(file)
    return json.dumps(json_data, indent=2)

# Helper function to chunk text into smaller parts
def chunk_text(text: str, chunk_size: int = 500) -> List[str]:
    words = text.split()
    return [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

# Updated function to get embeddings for a list of texts
def get_embeddings(texts: List[str]) -> List[np.ndarray]:
    response = openai.Embedding.create(model=EMBEDDING_MODEL, input=texts)
    return [np.array(embedding['embedding']) for embedding in response['data']]

# AIChatbot class that interacts with ChromaDB
class AIChatbot:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.collection = chroma_client.get_or_create_collection(name=collection_name)

    def generate_response(self, user_input: str):
        # Embed the user query
        query_embedding = get_embeddings([user_input])[0].reshape(1, -1)  # Reshape for cosine_similarity

        # Retrieve all documents and embeddings from the collection
        all_results = self.collection.get()
        documents = all_results['documents']
        embeddings = np.array(all_results['embeddings'])  # Assuming embeddings are stored as lists

        # Calculate cosine similarity
        similarities = cosine_similarity(query_embedding, embeddings)[0]

        # Get indices of the top N similar documents
        top_n_indices = similarities.argsort()[-3:][::-1]  # Get top 3 indices

        # Build context from the top retrieved documents
        context = " ".join([documents[i] for i in top_n_indices])

        # Generate a streaming response using GPT-4 with context
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {user_input}"}
            ],
            stream=True  # Enable streaming
        )
        return response

# Helper functions for managing collections in ChromaDB
def add_files_to_collection(collection_name: str, files: List):
    collection = chroma_client.get_or_create_collection(name=collection_name)

    for file in files:
        # Extract text from the JSON file
        text = extract_text_from_json(file)
        
        # Chunk the extracted text
        chunks = chunk_text(text)
        
        # Get embeddings for each chunk
        embeddings = get_embeddings(chunks)

        # Add chunks and embeddings to the collection
        collection.add(
            documents=chunks,
            embeddings=[emb.tolist() for emb in embeddings],
            ids=[f"{file.name}_{i}" for i in range(len(chunks))]
        )

    st.success(f"Added {len(files)} JSON files to collection '{collection_name}'.")

def delete_files_from_collection(collection_name: str, file_names: List[str]):
    collection = chroma_client.get_or_create_collection(name=collection_name)
    for file_name in file_names:
        # Get all chunk IDs for this file
        chunk_ids = [id for id in collection.get()['ids'] if id.startswith(f"{file_name}_")]
        if chunk_ids:
            # Delete chunks
            collection.delete(ids=chunk_ids)
            st.success(f"Deleted file '{file_name}' from collection '{collection_name}'.")
        else:
            st.warning(f"No chunks found for file '{file_name}' in collection '{collection_name}'.")

def delete_collection(collection_name: str):
    chroma_client.delete_collection(name=collection_name)
    st.success(f"Deleted collection '{collection_name}'.")

def list_collections() -> List[str]:
    return [collection.name for collection in chroma_client.list_collections()]

def list_files_in_collection(collection_name: str) -> List[str]:
    collection = chroma_client.get_or_create_collection(name=collection_name)
    all_ids = collection.get()['ids']
    return list(set([id.split('_')[0] for id in all_ids]))

# Manage Collections Page
def manage_collections():
    st.header("Manage Collections")
    collections = list_collections()

    # Use radio buttons for managing collections
    task = st.radio("What would you like to do?", ("Add Collection", "Modify Collection", "Delete Collection"))

    if task == "Add Collection":
        st.subheader("Add New Collection")
        new_collection_name = st.text_input("Collection Name")
        uploaded_files = st.file_uploader("Upload JSON Files", type="json", accept_multiple_files=True)

        if st.button("Add Collection"):
            if new_collection_name and uploaded_files:
                add_files_to_collection(new_collection_name, uploaded_files)

    elif task == "Modify Collection":
        st.subheader("Modify Existing Collection")
        selected_collection = st.selectbox("Select a Collection", collections)

        if selected_collection:
            st.write("Add new files:")
            new_files = st.file_uploader(f"Add JSON Files to {selected_collection}", type="json", accept_multiple_files=True)
            if st.button("Add Files"):
                if new_files:
                    add_files_to_collection(selected_collection, new_files)
            
            st.write("Delete existing files:")
            existing_files = list_files_in_collection(selected_collection)
            if existing_files:
                files_to_delete = st.multiselect("Select files to delete", existing_files)
                if st.button("Delete Selected Files"):
                    if files_to_delete:
                        delete_files_from_collection(selected_collection, files_to_delete)
                        st.success("Files deleted. Please refresh the page to see the updated file list.")
                        st.button("Refresh")  # Add a refresh button
            else:
                st.info("No files found in this collection.")

    elif task == "Delete Collection":
        st.subheader("Delete Collection")
        selected_collection = st.selectbox("Select a Collection to Delete", collections)

        if st.button("Delete Collection"):
            if selected_collection:
                delete_collection(selected_collection)

# AI Chatbot Page with RAG Pipeline
def chatbot_interface():
    st.header("AI Chatbot Interface")

    collections = list_collections()
    selected_collection = st.selectbox("Select a Collection", collections)

    if selected_collection:
        st.write(f"Using collection: {selected_collection}")

        # Initialize chatbot for the selected collection
        chatbot = AIChatbot(selected_collection)

        # Chat Interface using Streamlit's chat elements
        if 'messages' not in st.session_state:
            st.session_state['messages'] = []

        # Display chat history
        for message in st.session_state['messages']:
            with st.chat_message(message["role"]):
                st.write(message['content'])

        # User input
        user_input = st.chat_input("Type your message here...")

        if user_input:
            # Display user message
            with st.chat_message("user"):
                st.write(user_input)
            st.session_state['messages'].append({"role": "user", "content": user_input})

            # Get and display AI response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                for response in chatbot.generate_response(user_input):
                    if response.choices[0].delta.content is not None:
                        full_response += response.choices[0].delta.content
                        message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
            st.session_state['messages'].append({"role": "assistant", "content": full_response})

# Main App
def main():
    # --- PAGE CONFIGURATION ---
    st.set_page_config(page_title="JSON RAG Application", page_icon="💼", layout="centered")

    # --- MAIN PAGE CONFIGURATION ---
    st.title("JSON RAG Application 💼")

    # ---- NAVIGATION MENU -----
    selected = option_menu(
        menu_title=None,
        options=["Info", "About"],
        icons=["bi bi-info-square", "bi bi-globe"],  # https://icons.getbootstrap.com
        orientation="horizontal",
    )

    # Custom CSS for buttons
    st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #0E1117;
        border: none;
        color: white;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 12px;
        transition-duration: 0.4s;
    }
    .stButton>button:hover {
        background-color: #FF4B4B;
        color : black
    }
    </style>
    """, unsafe_allow_html=True)

    # Sidebar navigation with styled buttons
    with st.sidebar:
        st.sidebar.title("Navigation")
        if st.button("AI Chatbot"):
            st.session_state.page = "AI Chatbot"
        if st.button("Manage Collections"):
            st.session_state.page = "Manage Collections"

    # Initialize session state for page if not exists
    if 'page' not in st.session_state:
        st.session_state.page = "AI Chatbot"

    if st.session_state.page == "AI Chatbot":           
        chatbot_interface()

    elif st.session_state.page == "Manage Collections":
        manage_collections()

if __name__ == "__main__":
    main()
