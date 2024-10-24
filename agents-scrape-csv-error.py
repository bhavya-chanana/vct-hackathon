import csv
import requests
from bs4 import BeautifulSoup
import time

# File paths
input_csv = r'test-data\gcmulti_cleaned.csv'  # Input CSV file with errors
output_csv = r'test-data\updated_gcmulti_cleaned_error.csv'  # Output CSV to save updated data
error_log_csv = r'test-data\gcmulti_cleaned_error_log.csv'  # Error log CSV

def get_agent_data(player_name):
    """Fetch agent data for a given player handle from Liquipedia."""
    url = f"https://liquipedia.net/valorant/{player_name}/Matches"
    while True:  # Loop until we successfully get data or decide to break
        try:
            response = requests.get(url)  # Direct request without proxy
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)

            # Parse the HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Initialize an empty dictionary to store agent counts
            agent_counts = {}

            # Find all rows with win or lose classes
            rows = soup.find_all('tr', class_=['recent-matches-bg-win', 'recent-matches-bg-lose'])

            # Loop through each row
            for row in rows:
                columns = row.find_all('td')
                if len(columns) >= 7:
                    agent_column = columns[6]  # The agent column is at index 6
                    agent_images = agent_column.find_all('img')
                    
                    for agent_image in agent_images:
                        if agent_image and 'alt' in agent_image.attrs:
                            agent_name = agent_image['alt']
                            if agent_name in agent_counts:
                                agent_counts[agent_name] += 1
                            else:
                                agent_counts[agent_name] = 1
            
            # Sort agents by number of times played and return as a string
            sorted_agents = sorted(agent_counts.items(), key=lambda item: item[1], reverse=True)
            top_agents = ', '.join([agent for agent, _ in sorted_agents[:3]])  # Get top 3 agents
            
            return top_agents

        except requests.HTTPError as e:
            if e.response.status_code == 429:
                print(f"HTTP error occurred for {player_name}: {e.response.status_code}. Too many requests. Waiting for your command to continue...")
                input("Press Enter to retry...")  # Wait for your command to continue
                time.sleep(10)  # Optional: Wait for 10 seconds before retrying
            else:
                print(f"HTTP error occurred for {player_name}: {e.response.status_code}")
                log_error(player_name, e.response.status_code)
                return None

        except Exception as e:
            print(f"An error occurred for {player_name}: {str(e)}")
            log_error(player_name, str(e))
            return None

def log_error(player_handle, error_code):
    """Log errors to a text file."""
    with open(error_log_csv, 'a', encoding='utf-8') as f:
        f.write(f"{player_handle},{error_code}\n")

# Read the error log CSV to get players with 429 errors
players_to_update = set()
with open(error_log_csv, mode='r', newline='', encoding='utf-8') as error_file:
    error_reader = csv.reader(error_file)
    next(error_reader)  # Skip header if present
    for row in error_reader:
        # Check if the row has the expected number of columns
        if len(row) >= 2:  # Ensure there are at least 2 columns
            player_handle, error_code = row
            if error_code == '429':
                players_to_update.add(player_handle)
        else:
            print(f"Skipping row with insufficient columns: {row}")

# Read the input CSV and update only the targeted players
with open(input_csv, mode='r', newline='', encoding='utf-8') as file:
    reader = csv.reader(file)
    headers = next(reader)
    
    # Prepare to write to the output CSV
    with open(output_csv, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(headers)  # Write headers to the new CSV

        # Loop through each row in the original CSV
        for row in reader:
            player_handle = row[0]  # Player handle is the first column
            if player_handle in players_to_update:
                print(f"Fetching agent data for {player_handle}...")

                # Fetch agent data and update row
                agents = get_agent_data(player_handle)
                if agents:
                    row[6] = agents  # Assuming "agents" column is at index 6 in your CSV
                else:
                    row[6] = 'N/A'  # In case of an error, mark as 'N/A'

            writer.writerow(row)  # Write the updated row to the new CSV

            # Sleep for 2.5 seconds due to rate limit
            time.sleep(2.5)

print(f"Updated data saved to {output_csv}")
