import json
from typing import List
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders import WebBaseLoader, AsyncHtmlLoader, AsyncChromiumLoader
from langchain_community.document_transformers import Html2TextTransformer
from bs4 import BeautifulSoup


# Load environment variables (make sure to set OPENAI_API_KEY)
import os
from dotenv import load_dotenv
load_dotenv()

def load_web_data(url: str) -> List[Document]:
    loader = AsyncHtmlLoader(url)
    documents = loader.load()
    print("documents-", documents)
    
    # Process the documents to replace image tags with alt texts
    for doc in documents:
        soup = BeautifulSoup(doc.page_content, 'html.parser')  # Parse the HTML content
        img_tags = soup.find_all('img')  # Find all img tags
        
        # Replace each img tag with its alt text
        for img in img_tags:
            alt_text = img.get('alt', '')  # Get alt text, default to empty string if not found
            img.insert_before(alt_text)  # Insert alt text before the image
            img.decompose()  # Remove the img tag

        # Update the document's page content with modified HTML
        doc.page_content = str(soup)

    # Transform the HTML to text after modifications
    html2text = Html2TextTransformer()
    docs_transformed = html2text.transform_documents(documents)
    print("docs transformed-", docs_transformed)
    
    # Save raw HTML for debugging purposes
    transformed_documents_str = str(docs_transformed)
    with open('html.txt', 'w', encoding='utf-8') as file:
        file.write(transformed_documents_str)
        print('html.txt saved')

    return docs_transformed


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
    # Create a custom prompt template
    prompt_template = """You are a web scraping assistant. Based on the context scraped from the webpage, extract and provide detailed information about Valorant players. Specifically, return the following details:

    - Player name: Full name of the player.
    - Ingame name: The alias or nickname used in the game.
    - Team: Current team.
    - Past team: Teams they have played for previously.
    - Overall win: Total number of victories in their career.
    - Total games: Number of games played.
    - Win ratio: Percentage of games won.
    - IGL: Is the player an In-Game Leader (IGL)?
    - Agents: Agents the player primarily uses.
    - Region: Geographic region they represent.
    - League: The current league in which they participate.
    - Team role: Player's role in the team (e.g., duelist, support).
    - ACS per map: Average Combat Score (ACS) per map.
    - KDA: Kill/Death/Assist ratio.
    - Standings: The player's standings in tournaments or events.
    - League standing: The current position of their team in the league.
    - Languages: Languages the player speaks.
    - Gender: Gender of the player.

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
    # Define the URL to scrape
    # url = ["https://www.vlr.gg/player/9/tenz/?timespan=all", "https://www.vlr.gg/player/438/boaster/?timespan=all"]
    url = ["https://www.vlr.gg/player/438/boaster/?timespan=all"]

    # Load the web content
    documents = load_web_data(url)

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
            print(f"- {doc.metadata.get('source', 'webpage')}")

        print("\n" + "-"*50 + "\n")

if __name__ == "__main__":
    main()
