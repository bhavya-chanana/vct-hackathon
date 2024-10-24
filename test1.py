import json
from typing import List
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate

# Load environment variables (make sure to set OPENAI_API_KEY)
import os
from dotenv import load_dotenv
load_dotenv()

def load_json_files(file_paths: List[str]) -> List[Document]:
    documents = []
    for file_path in file_paths:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            # Convert the JSON data to a string representation
            content = json.dumps(data, indent=2)
            # Create a Document object with the content and metadata
            doc = Document(page_content=content, metadata={"source": file_path})
            documents.append(doc)
    return documents

def create_vector_store(documents: List[Document]):
    # Split the documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)

    # Create and return the vector store
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return FAISS.from_documents(texts, embeddings)

def setup_qa_chain(vector_store):
    # Initialize the OpenAI Chat model
    llm = ChatOpenAI(model_name="gpt-4o-mini-2024-07-18", temperature=0)

    # Create a custom prompt template
    prompt_template = """You are a data assistant working with esports information, including players, teams, leagues, and mappings between different games and tournaments. Your job is to accurately answer queries by mapping player IDs, team IDs, and league IDs based on the data provided.

    Data Structure:

    Players: Contains information about players (IDs, names, home_team_id, etc.).
    Teams: Contains information about teams (IDs, names, etc.).
    Leagues: Contains information about leagues (IDs, names, regions).
    Mapping Data: Provides mappings between platform-specific game data (like team and player IDs) to internal esports data.
    Mapping Tasks:

    When queried about a specific player, identify their corresponding team and league using the mapping data.
    When asked for teams, return all relevant players and their participation in specific games and tournaments.

    Context: {context}

    Question: {question}

    Answer:"""

    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    # Create and return the question-answering chain
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever(),
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT}
    )

def main():
    # Specify the paths to your JSON files
    json_files = [
        r"combined_data.json",
    ]

    # Load the documents
    documents = load_json_files(json_files)

    # Create the vector store
    vector_store = create_vector_store(documents)

    # Setup the question-answering chain
    qa_chain = setup_qa_chain(vector_store)

    # Main interaction loop
    while True:
        query = input("Enter your question (or 'quit' to exit): ")
        if query.lower() == 'quit':
            break

        # Get the answer
        result = qa_chain({"query": query})

        # Print the answer
        print("\nAnswer:", result['result'])

        # Print the sources
        print("\nSources:")
        for doc in result['source_documents']:
            print(f"- {doc.metadata['source']}")

        print("\n" + "-"*50 + "\n")

if __name__ == "__main__":
    main()