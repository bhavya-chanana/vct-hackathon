import csv
import time
from helium import start_chrome, find_all, click, write, press, go_to, kill_browser
from bs4 import BeautifulSoup

# Function to log errors to a CSV file
def log_error(player_name: str, error_message: str, error_log_csv: str):
    """Log errors to a CSV file."""
    with open(error_log_csv, mode='a', newline='', encoding='utf-8') as error_file:
        writer = csv.writer(error_file)
        writer.writerow([player_name, error_message])  # Write player name and error message

# Function to perform Google search, open first link, append timespan, and scrape data
def search_and_scrape(player_name: str, error_log_csv: str) -> tuple:
    """Search for the player and scrape their top agents."""
    driver = start_chrome("https://www.google.com", headless=True)  # Run in headless mode for faster performance
    
    try:
        # Step 1: Perform Google search
        search_query = f"{player_name} vlr"
        write(search_query, into="Search")
        press(press.ENTER)
        time.sleep(2)  # Wait for results to load
        
        # Step 2: Click the first result
        result = find_all('h3')[0]
        click(result)
        time.sleep(1)  # Wait for the page to load

        # Step 3: Get current URL, append `/?timespan=all`
        current_url = driver.current_url
        full_url = current_url + "/?timespan=all"
        go_to(full_url)
        time.sleep(3)  # Wait for the new page to load

        # Step 4: Extract page source and parse with BeautifulSoup
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Step 5: Target the table rows and extract alt texts of agent images
        img_tags = soup.select('tr img')  # Select all img tags within tr elements
        alt_texts = [img.get('alt') for img in img_tags if img.get('alt')]  # Extract alt texts

        # Return the player name and top 3 agents as a comma-separated string
        agents = ', '.join(alt_texts[:3])  # Get top 3 agents
        return (player_name, agents)  # Return tuple with player name and scraped agents

    except Exception as e:
        error_message = str(e)
        print(f"An error occurred while scraping {player_name}: {error_message}")
        log_error(player_name, error_message, error_log_csv)
        return (player_name, None)  # Return None to indicate an error occurred
    finally:
        kill_browser()  # Ensure the browser is closed

# Function to process one player at a time
def process_player(row, error_log_csv):
    player_handle = row[0]
    print(f"Fetching agent data for {player_handle}...")
    agents = search_and_scrape(player_handle, error_log_csv)
    return (player_handle, agents)  # Return scraped agents or None

# Function to handle sequential scraping and update the CSV
def update_agents_in_csv_sequential(input_csv: str, output_csv: str, error_log_csv: str, start_row: int):
    """Update agents in the CSV by scraping data for all players, one by one."""
    rows = []  # To store all rows temporarily
    players_to_process = []  # For players that need scraping

    # Open the CSV file with 'latin-1' encoding to avoid UnicodeDecodeError
    with open(input_csv, mode='r', newline='', encoding='latin-1') as infile:
        reader = csv.reader(infile)
        headers = next(reader)  # Read the headers
        rows.append(headers)  # Store the headers
        
        # Loop through each row and add rows to the list for processing
        for idx, row in enumerate(reader, start=2):  # Start counting from row 2 (first row is headers)
            if idx < start_row:
                rows.append(row)  # Add row unchanged if before start_row
                continue

            players_to_process.append(row)  # Add all rows for processing

    # Process each player sequentially
    for row in players_to_process:
        player_name, agents = process_player(row, error_log_csv)
        if agents:
            # Update agents data
            row[6] = agents
            print(f"Player: {player_name}, Agents: {agents}")
        rows.append(row)  # Add the updated row to rows

    # Now write all rows to the new output CSV
    with open(output_csv, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerows(rows)  # Write all rows to the new output file

# Example usage
input_csv_path = r'test-data\\two.csv'  # Original input file
output_csv_path = r'test-data\\two_final.csv'  # New output file
error_log_csv = r'test-data\\two_error_log.csv'  # Error log file
start_row = 0  # You can adjust this to start from a specific row

update_agents_in_csv_sequential(input_csv_path, output_csv_path, error_log_csv, start_row)
