import streamlit as st
import pandas as pd
import boto3
import json
from typing import List
import numpy as np
from io import StringIO
import os
from botocore.config import Config

# AWS Configuration
AWS_ACCESS_KEY = ""
AWS_SECRET_KEY = ""
AWS_REGION = "us-east-1"  # Change to your region

# Configure AWS client with retry strategy
aws_config = Config(
    region_name=AWS_REGION,
    retries = dict(
        max_attempts = 3
    )
)

class BedrockEmbeddings:
    def __init__(self, model_id="amazon.titan-embed-text-v1"):
        self.bedrock = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION,
            config=aws_config
        )
        self.model_id = model_id

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            try:
                # Ensure text is properly encoded
                text = text.encode('latin-1', errors='ignore').decode('latin-1')
                body = json.dumps({"inputText": text})
                response = self.bedrock.invoke_model(
                    modelId=self.model_id,
                    body=body
                )
                response_body = json.loads(response['body'].read())
                embedding = response_body['embedding']
                embeddings.append(embedding)
            except Exception as e:
                st.error(f"Error getting embeddings: {str(e)}")
                raise
        return embeddings

class BedrockLLM:
    def __init__(self, model_id="mistral.mixtral-8x7b-instruct-v0:1"):
        self.bedrock = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION,
            config=aws_config
        )
        self.model_id = model_id

    def generate(self, prompt: str, context: str) -> str:
        try:
            # Ensure text is properly encoded
            prompt = prompt.encode('latin-1', errors='ignore').decode('latin-1')
            context = context.encode('latin-1', errors='ignore').decode('latin-1')
            
            body = json.dumps({
                "prompt": f"\n\nHuman: Given the following context:\n{context}\n\nAnswer this question: {prompt}\n\nAssistant:",
                "max_tokens_to_sample": 500,
                "temperature": 0.7,
                "stop_sequences": ["\n\nHuman:"]
            })
            
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=body
            )
            response_body = json.loads(response['body'].read())
            return response_body['completion']
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            raise

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def get_most_similar_chunks(query_embedding, chunk_embeddings, chunks, n=3):
    similarities = [cosine_similarity(query_embedding, chunk_emb) for chunk_emb in chunk_embeddings]
    most_similar_indices = np.argsort(similarities)[-n:][::-1]
    return [chunks[i] for i in most_similar_indices]

def check_aws_credentials():
    """Verify AWS credentials are working"""
    try:
        boto3.client('sts').get_caller_identity()
        return True
    except Exception as e:
        st.error(f"AWS Authentication Error: {str(e)}")
        return False

def clean_text(text):
    """Clean and encode text to ensure compatibility"""
    return text.encode('latin-1', errors='ignore').decode('latin-1')

def main():
    st.title("📚 RAG ChatBot with AWS Bedrock")
    
    # Add AWS credentials input in sidebar
    st.sidebar.title("AWS Configuration")
    aws_access_key = st.sidebar.text_input("AWS Access Key", value=AWS_ACCESS_KEY, type="password")
    aws_secret_key = st.sidebar.text_input("AWS Secret Key", value=AWS_SECRET_KEY, type="password")
    aws_region = st.sidebar.text_input("AWS Region", value=AWS_REGION)

    # Update environment variables if credentials changed
    if (aws_access_key != AWS_ACCESS_KEY or 
        aws_secret_key != AWS_SECRET_KEY or 
        aws_region != AWS_REGION):
        os.environ['AWS_ACCESS_KEY_ID'] = aws_access_key
        os.environ['AWS_SECRET_ACCESS_KEY'] = aws_secret_key
        os.environ['AWS_DEFAULT_REGION'] = aws_region
        
        # Clear session state to reinitialize clients with new credentials
        st.session_state.embeddings_model = None
        st.session_state.llm = None

    # Verify AWS credentials
    if not check_aws_credentials():
        st.warning("Please enter valid AWS credentials in the sidebar")
        return

    # Initialize session state
    if 'embeddings_model' not in st.session_state or st.session_state.embeddings_model is None:
        st.session_state.embeddings_model = BedrockEmbeddings()
    if 'llm' not in st.session_state or st.session_state.llm is None:
        st.session_state.llm = BedrockLLM()
    if 'chunk_embeddings' not in st.session_state:
        st.session_state.chunk_embeddings = None
    if 'chunks' not in st.session_state:
        st.session_state.chunks = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    st.write("Upload a CSV file and ask questions about its contents!")

    # File upload
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file is not None:
        try:
            # Read and process the CSV file with latin-1 encoding
            df = pd.read_csv(uploaded_file, encoding='latin-1')
            
            if st.button("Process CSV"):
                with st.spinner("Processing CSV file..."):
                    try:
                        # Create text chunks from DataFrame
                        chunks = []
                        for _, row in df.iterrows():
                            # Clean and encode each value
                            cleaned_row = {k: clean_text(str(v)) for k, v in row.items()}
                            chunk = " ".join([f"{col}: {val}" for col, val in cleaned_row.items()])
                            chunks.append(chunk)
                        
                        # Get embeddings for chunks
                        chunk_embeddings = st.session_state.embeddings_model.get_embeddings(chunks)
                        
                        # Store in session state
                        st.session_state.chunks = chunks
                        st.session_state.chunk_embeddings = chunk_embeddings
                        st.success("CSV processed successfully!")
                    except Exception as e:
                        st.error(f"Error processing CSV: {str(e)}")
        except Exception as e:
            st.error(f"Error reading CSV file: {str(e)}. Please ensure the file is properly formatted.")

    # Chat interface
    st.write("---")
    st.subheader("Chat")
    
    # Display chat history
    for q, a in st.session_state.chat_history:
        st.write("🧑 **You:** " + clean_text(q))
        st.write("🤖 **Assistant:** " + clean_text(a))
    
    # Query input
    query = st.text_input("Ask a question about your data:")
    
    if query and st.button("Send"):
        if st.session_state.chunks is None:
            st.error("Please upload and process a CSV file first!")
        else:
            with st.spinner("Thinking..."):
                try:
                    # Clean and encode query
                    query = clean_text(query)
                    
                    # Get query embedding
                    query_embedding = st.session_state.embeddings_model.get_embeddings([query])[0]
                    
                    # Get relevant chunks
                    relevant_chunks = get_most_similar_chunks(
                        query_embedding,
                        st.session_state.chunk_embeddings,
                        st.session_state.chunks
                    )
                    
                    # Combine chunks into context
                    context = "\n".join(relevant_chunks)
                    
                    # Generate response using LLM
                    response = st.session_state.llm.generate(query, context)
                    
                    # Update chat history
                    st.session_state.chat_history.append((query, response))
                    
                    # Force refresh
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error processing query: {str(e)}")

if __name__ == "__main__":
    main()