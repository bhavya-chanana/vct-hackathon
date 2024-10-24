import requests
from bs4 import BeautifulSoup

# Substitute player_name with the desired player's handle
player_name = "Sacy"  # Replace with the player's handle
url = f"https://liquipedia.net/valorant/{player_name}/Matches"

# Send a GET request to the website
response = requests.get(url)

# Check if the request was successful (status code 200)
if response.status_code == 200:
    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')

    # Initialize an empty dictionary to store agent counts
    agent_counts = {}

    # Find all rows with win or lose classes
    rows = soup.find_all('tr', class_=['recent-matches-bg-win', 'recent-matches-bg-lose'])

    # Loop through each row
    for row in rows:
        # Ensure the row has at least 7
        columns = row.find_all('td')
        if len(columns) >= 12:
            # The agent column is at 6
            agent_column = columns[6]
            
            # Find the agent image inside the column (using alt text for the agent's name)
            agent_images = agent_column.find_all('img')
            
            # Loop through all found agents in the column
            for agent_image in agent_images:
                if agent_image and 'alt' in agent_image.attrs:
                    agent_name = agent_image['alt']

                    # Increment count if agent already exists, otherwise add it with count 1
                    if agent_name in agent_counts:
                        agent_counts[agent_name] += 1
                    else:
                        agent_counts[agent_name] = 1

    # Sort the agent_counts dictionary by value (i.e., the count) in descending order
    sorted_agents = sorted(agent_counts.items(), key=lambda item: item[1], reverse=True)

    # Get the top 3 agents
    top_3_agents = sorted_agents[:3]

    # Print the top 3 agents
    print("Top 3 Agents:")
    for agent, count in top_3_agents:
        print(f"{agent}: {count}")

    # Save the top 3 agents to a text file
    with open(f"{player_name}_top_3_agents.txt", "w", encoding="utf-8") as file:
        for agent, count in top_3_agents:
            file.write(f"{agent}: {count}\n")

    print(f"Top 3 agents saved to {player_name}_top_3_agents.txt")

else:
    print(f"Failed to retrieve page. Status code: {response.status_code}")
