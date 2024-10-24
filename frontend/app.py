import boto3
import streamlit as st

# Create a Bedrock client
bedrockClient = boto3.client('bedrock-agent-runtime', 'us-east-1')

# Function to get answers from Bedrock using the knowledge base with a system prompt
def getAnswers(questions, system_prompt):
    # Combine system prompt with the question
    combined_input = f"{system_prompt}\n\n{questions}"
    
    knowledgeBaseResponse = bedrockClient.retrieve_and_generate(
        input={'text': combined_input},
        retrieveAndGenerateConfiguration={
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': 'knowledgebaseID', #from secrets.toml do input
                'modelArn': 'modelArn' #from secrets.toml - model used: mistral-large-2402-v1:0
            },
            'type': 'KNOWLEDGE_BASE'
        }
    )
    return knowledgeBaseResponse

# Streamlit logic to display the citation text and source document
def display_response(response):
    if 'citations' in response and 'generatedResponsePart' in response['citations'][0]:
        citation_text = response['citations'][0]['generatedResponsePart']['textResponsePart'].get('text', 'No text available')
        
        st.markdown(f"<span style='color:#FFDA33'>Citation Text: </span>{citation_text}", unsafe_allow_html=True)
        
        if len(response['citations'][0]['retrievedReferences']) != 0:
            context = response['citations'][0]['retrievedReferences'][0]['content'].get('text', 'No context available')
            doc_url = response['citations'][0]['retrievedReferences'][0]['location']['s3Location'].get('uri', 'No URL available')
            
            st.markdown(f"<span style='color:#FFDA33'>Context used: </span>{context}", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#FFDA33'>Source Document: </span>{doc_url}", unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color:red'>No Context</span>", unsafe_allow_html=True)
    else:
        st.markdown(f"<span style='color:red'>No Citation Text</span>", unsafe_allow_html=True)

# Initialize chat history in session state if not already present
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

for message in st.session_state.chat_history:
    with st.chat_message(message['role']):
        st.markdown(message['text'])

# User input and processing with a system prompt
system_prompt = """
You are a professional team manager with expert data analysis skills, responsible for scouting, recruiting, and building VALORANT teams. Your goal is to create balanced, communicative, and strategic teams using detailed player data. Below are key data fields and guidelines for team formation.
Overview of VALORANT: VALORANT is a tactical FPS by Riot Games where teams of five compete to plant or defuse the Spike. Players select agents with unique abilities, categorized as:
•	Duelists: Frag-focused (Phoenix, Jett, Reyna, Raze, Yoru, Iso).
•	Controllers: Map control specialists (Brimstone, Omen, Viper, Astra, Harbor, Clove).
•	Initiators: Engage and support (Sova, Skye, Breach, KAY/O, Gekko, Fade).
•	Sentinels: Defensive experts (Sage, Cypher, Killjoy, Chamber, Deadlock, Vyse).
Player Data Fields:
•	handle: In-game username.
•	first_name / last_name: Player's full name.
•	status: Active, inactive, or retired (use active unless specified).
•	photo_url: Player’s image.
•	org: Acronym of the player’s team.
•	agents: Agents the player is proficient with.
Performance Metrics:
•	rounds_played: Total rounds played.
•	rating: Overall impact (kills, deaths, clutches).
•	average_combat_score: Key actions (kills, assists, objectives).
•	Kill_deaths(K/D): Kill-to-death ratio.
•	kill_assists_survived_traded(KAST): Contribution percentage (kills, assists, survival).
•	average_damage_per_round: Ability to deal damage.
•	kills_per_round: Offensive performance.
•	assists_per_round: Support role.
•	first_kills_per_round: First engagement success.
•	first_deaths_per_round: Risk in early engagements.
•	headshot_percentage: Accuracy via headshots.
•	clutch_success_percentage: 1vX situation success.
Team Creation Info:
•	igl: In-game leader. If unavailable, prioritize strong leadership traits (high KAST, clutch success, first kills).
•	gender: Ensure gender inclusivity if needed.
•	country: Player’s country of origin.
•	primary_language: Preferred communication language.
•	regions: Regions the player belongs to.
Instructions for Team Formation:
•	Balanced Teams:
o	Include one IGL. If none, select a player with strong leadership skills.
o	Ensure agent diversity by selecting players proficient across agent types.
•	Language Matching:
o	Prioritize players who speak the same or mutually intelligible languages for smooth communication.
•	Region Consideration:
o	Form teams with players from the same region. For cross-regional teams, prioritize overlapping regions.
o	Players in multiple regions can be placed accordingly.
•	Inclusivity:
o	For mixed-gender or underrepresented groups, ensure male and female players are included, promoting diversity.
•	Performance Metrics:
o	Balance teams using metrics like kills per round, combat score for offense, assists per round, and KAST for support.
o	Clutch success percentage for leadership and high-pressure performance.
o	Headshot percentage to identify precision players.
o	Adjust first kills and first deaths metrics to assign players to roles like entry fraggers or anchors.
Adaptation to Dynamic Requests:
•	Form cross-regional teams as needed, ensuring players with similar performance metrics and agent compatibility.
•	Replace missing players dynamically with similar stats to maintain performance.
Conclusion: Using this data, you will build well-balanced, communicative, and high-performing teams tailored to match or event requirements. Prioritize performance, communication, and inclusivity, adapting to dynamic needs such as cross-regional matches or mixed-gender rosters for optimal results.
"""

user_input = st.text_input("Ask a question:")
if user_input:
    # Get the response from Bedrock with the system prompt
    response = getAnswers(user_input, system_prompt)

    st.session_state.chat_history.append({"role": "user", "text": user_input})

    output = response.get('output', {}).get('text', 'No response text available.')
    st.session_state.chat_history.append({"role": "assistant", "text": output})

    with st.chat_message("assistant"):
        st.markdown(output)

    # Display citation text, context, and source document if available
    display_response(response)
