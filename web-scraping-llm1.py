import pprint
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import AsyncChromiumLoader, AsyncHtmlLoader, WebBaseLoader
from langchain_community.document_transformers import BeautifulSoupTransformer, Html2TextTransformer
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain_openai import ChatOpenAI

# Define the schema you want to extract (you can customize this)
schema = {
    "Player name": "string",
    "Ingame name": "string",
    "Team": "string",
    "Past team": "string",
    "Overall win": "integer",
    "Total games": "integer",
    "Win ratio": "float",
    "IGL": "boolean",
    "Agents": "list of strings",
    "Region": "string",
    "League": "string",
    "Team role": "string",
    "ACS per map": "dictionary of strings to float",
    "KDA": "float",
    "Standings": "string",
    "League standing": "integer",
    "Languages": "list of strings",
    "Gender": "string"
}
# schema = {
#     """
#     - Player name: Full name of the player.
#     - Ingame name: The alias or nickname used in the game.
#     - Team: Current team.
#     - Past team: Teams they have played for previously.
#     - Overall win: Total number of victories in their career.
#     - Total games: Number of games played.
#     - Win ratio: Percentage of games won.
#     - IGL: Is the player an In-Game Leader (IGL)?
#     - Agents: Agents the player primarily uses.
#     - Region: Geographic region they represent.
#     - League: The current league in which they participate.
#     - Team role: Player's role in the team (e.g., duelist, support).
#     - ACS per map: Average Combat Score (ACS) per map.
#     - KDA: Kill/Death/Assist ratio.
#     - Standings: The player's standings in tournaments or events.
#     - League standing: The current position of their team in the league.
#     - Languages: Languages the player speaks.
#     - Gender: Gender of the player."""
# }


# Function to scrape website and extract data
def scrape_with_playwright(urls, schema):
    # Use Playwright to load the pages
    loader = AsyncHtmlLoader(urls)
    docs = loader.load()

    # Apply BeautifulSoup to transform the HTML content
    bs_transformer = BeautifulSoupTransformer()
    docs_transformed = bs_transformer.transform_documents(docs, tags_to_extract=["span", "div", "p", "ul"])

    print("Extracting content with LLM")

    # Split the documents into manageable chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = splitter.split_documents(docs_transformed)

    # LLM for schema-based extraction
    llm = ChatOpenAI(model_name="gpt-4o-mini-2024-07-18")

    # Create a custom prompt template for extraction
    prompt_template = """Extract the following details from the web content:
    
    {schema}
    this is the defination of the schema
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

    Content:
    {content}

    Extracted Information:"""
    
    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["schema", "content"]
    )
    
    chain = LLMChain(llm=llm, prompt=PROMPT)
    
    # Extract from the first split
    extracted_content = chain.run({"schema": schema, "content": splits[0].page_content})
    
    pprint.pprint(extracted_content)
    return extracted_content

# Define the URLs to scrape
urls = ["https://www.vlr.gg/player/438/boaster/?timespan=all"]

# Run the scraper and extract data based on schema
extracted_content = scrape_with_playwright(urls, schema=schema)
