import json
from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate
from langchain.schema import BaseRetriever
from pydantic import BaseModel, Field
from langchain.schema import BaseRetriever, Document

# Load environment variables (make sure to set OPENAI_API_KEY)
import os
from dotenv import load_dotenv
load_dotenv()

def load_json_file(file_path: str) -> List[Dict]:
    with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
        try:
            return json.load(file)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {file_path}: {e}")
            return []

def load_json_files(file_paths: Dict[str, str]) -> Dict[str, List[Dict]]:
    return {key: load_json_file(path) for key, path in file_paths.items()}

def create_vector_store(documents: List[Document]):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return FAISS.from_documents(texts, embeddings)

class CustomESportsRetriever(BaseRetriever):
    json_data: Dict[str, List[Dict[str, Any]]]
    vector_store: Any

    def __init__(self, json_data: Dict[str, List[Dict[str, Any]]], vector_store: Any):
        super().__init__()
        self.json_data = json_data
        self.vector_store = vector_store

    def _get_relevant_documents(self, query: str) -> List[Document]:
        # First, try to find an exact match for IDs
        for data_type, data in self.json_data.items():
            for item in data:
                if str(item.get('id')) == query:
                    return [Document(page_content=json.dumps(item), metadata={"source": f"{data_type}.json"})]
        
        # If no exact match, fall back to vector similarity search
        return self.vector_store.similarity_search(query)

    async def _aget_relevant_documents(self, query: str) -> List[Document]:
        return self._get_relevant_documents(query)

def setup_qa_chain(custom_retriever):
    llm = ChatOpenAI(model_name="gpt-4-0125-preview", temperature=0)

    prompt_template = """You are a data assistant working with esports information. Your primary task is to accurately retrieve and map information about players, teams, leagues, and tournaments using the provided data files.

    Data Structure:
    1. players.json: Contains player information (ID, handle, name, home_team_id, etc.)
    2. teams.json: Contains team information (ID, name, acronym, etc.)
    3. leagues.json: Contains league information (ID, name, region, etc.)
    4. mapping_data.json: Provides mappings between platform-specific game data and internal esports data
    5. tournaments.json: Contains tournament information (ID, status, league_id, etc.)

    When answering queries:
    1. Always start by identifying the relevant data file(s) for the query.
    2. For player queries, first check the players.json file using the provided ID.
    3. If additional mapping is needed, refer to the mapping_data.json file to find corresponding game, tournament, or team IDs.
    4. Cross-reference information between files when necessary (e.g., using home_team_id from players.json to find team information in teams.json).
    5. Provide all relevant information found, including IDs, names, and any mapped data.
    6. If information is not found, clearly state that it's not available in the provided data.

    Context: {context}

    Question: {question}

    Answer: Begin by stating which data file(s) you're using, then provide the requested information step by step."""

    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=custom_retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT}
    )

def main():
    # Specify the paths to your JSON files
    json_files = {
        "tournaments": r"test-data\tournaments.json",
        "teams": r"test-data\teams.json",
        "players": r"test-data\players.json",
        "mapping_data": r"test-data\mapping_data.json",
        "leagues": r"test-data\leagues.json"
    }

    # Load the JSON data
    json_data = load_json_files(json_files)

    # Create documents for vector store
    documents = [
        Document(page_content=json.dumps(item), metadata={"source": f"{key}.json"})
        for key, items in json_data.items()
        for item in items
    ]

    # Create the vector store
    vector_store = create_vector_store(documents)

    # Create the custom retriever
    custom_retriever = CustomESportsRetriever(json_data=json_data, vector_store=vector_store)

    # Setup the question-answering chain
    qa_chain = setup_qa_chain(custom_retriever)

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