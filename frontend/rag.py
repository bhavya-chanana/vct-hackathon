import pandas as pd
import boto3
import chromadb
from chromadb.config import Settings

# Initialize Bedrock client
bedrock = boto3.client('bedrock-runtime')

# Initialize Chroma DB
chroma_client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory="path/to/chroma/storage"))

# Load your CSV data
s3_bucket = 'your-bucket-name'
s3_file_key = 'your-file.csv'

s3 = boto3.client('s3')
csv_obj = s3.get_object(Bucket=s3_bucket, Key=s3_file_key)
data = pd.read_csv(csv_obj['Body'])

# Function to create embeddings and store in Chroma
def store_embeddings(data):
    for index, row in data.iterrows():
        text = str(row)  # Convert row to string for embedding
        # Call Bedrock to get embeddings
        response = bedrock.invoke_model(
            modelId='embedding-model-id',  # Replace with your Bedrock embedding model ID
            inputText=text
        )
        embedding = response['outputText']  # Replace with the actual key for embeddings
        chroma_client.add(text=text, embedding=embedding)

# Function to query embeddings
def query_embeddings(query):
    # Call Bedrock to get query embedding
    response = bedrock.invoke_model(
        modelId='embedding-model-id',  # Same embedding model ID
        inputText=query
    )
    query_embedding = response['outputText']  # Replace with the actual key for embeddings

    # Retrieve similar texts from Chroma
    results = chroma_client.query(embedding=query_embedding, n_results=5)  # Adjust n_results as needed
    return results

# Function to generate response using LLM
def generate_response(query):
    # Get relevant data
    relevant_data = query_embeddings(query)

    # Create input for LLM
    context = "\n".join([item['text'] for item in relevant_data])  # Adjust based on how data is returned
    input_text = f"User Query: {query}\nRelevant Information:\n{context}"

    # Call the LLM with context
    response = bedrock.invoke_model(
        modelId='your-llm-model-id',  # Replace with your Bedrock LLM model ID
        inputText=input_text
    )
    return response['outputText']

# Example usage
store_embeddings(data)  # Store CSV data embeddings once
user_query = "your question here"  # Replace with actual user query
response = generate_response(user_query)
print(f"Model Output: {response}")
