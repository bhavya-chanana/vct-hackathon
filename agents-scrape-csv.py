import csv
import requests
from bs4 import BeautifulSoup
import time

# File paths
input_csv = r'test-data\gcmulti_cleaned.csv'  # Input CSV file
output_csv = r'test-data\updated_gcmulti_cleaned_error.csv'  # Output CSV file
error_log_csv = r'test-data\gcmulti_cleaned_error_log.csv'  # Error log CSV

# Initialize request counter
request_counter = 0

def get_agent_data(player_name):
    """Fetch agent data for a given player handle from Liquipedia."""
    global request_counter  # Use the global request_counter
    url = f"https://liquipedia.net/valorant/{player_name}/Matches"
    try:
        response = requests.get(url)  # Direct request without proxy
        request_counter += 1  # Increment the request counter
        print(request_counter)
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
            print(f"HTTP 429 error occurred for {player_name}. Too many requests. Waiting for your input to continue...")
            input("Press Enter to retry...")
        else:
            print(f"HTTP error occurred for {player_name}: {e.response.status_code}")
            log_error(player_name, e.response.status_code)
        return None
    except Exception as e:
        print(f"An error occurred for {player_name}: {str(e)}")
        log_error(player_name, str(e))
        return None

def log_error(player_handle, error_code):
    """Log errors to a CSV file."""
    # Open the CSV in append mode, and write the player handle and error code
    with open(error_log_csv, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([player_handle, error_code])  # Write the error in "Player Handle, Error Code" format

# Ensure the error log file has a header if it's empty
with open(error_log_csv, 'a', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    if f.tell() == 0:  # File is empty, so write the header
        writer.writerow(["Player Handle", "Error Code"])

# Read the input CSV
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
            print(f"Fetching agent data for {player_handle}...")

            # Fetch agent data and update row
            agents = get_agent_data(player_handle)
            if agents:
                row[6] = agents  # Assuming "agents" column is at index 6 in your CSV
            else:
                row[6] = 'N/A'  # In case of an error, mark as 'N/A'

            # Print the player handle and agents data before writing to the CSV
            print(f"Player: {player_handle}, Agents: {row[6]}")

            writer.writerow(row)  # Write the updated row to the new CSV

            # Sleep for 2.5 seconds due to rate limit
            time.sleep(2.5)

# Print the total number of requests made
print(f"Total requests made: {request_counter}")
print(f"Updated data saved to {output_csv}")
