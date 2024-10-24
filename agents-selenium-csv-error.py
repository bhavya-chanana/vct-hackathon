import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

# Function to log errors to a CSV file
def log_error(player_name: str, error_message: str, error_log_csv: str):
    """Log errors to a CSV file."""
    with open(error_log_csv, mode='a', newline='', encoding='utf-8') as error_file:
        writer = csv.writer(error_file)
        writer.writerow([player_name, error_message])  # Write player name and error message

# Function to perform Google search, open first link, append timespan, and scrape data
def search_and_scrape(player_name: str, error_log_csv: str) -> str:
    """Search for the player and scrape their top agents."""
    driver = webdriver.Chrome()
    
    try:
        # Step 1: Perform Google search
        driver.get("https://www.google.com")
        search_box = driver.find_element(By.NAME, 'q')
        search_query = f"{player_name} vlr"
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.RETURN)

        # Step 2: Open first search result
        time.sleep(2)  # Wait for results to load
        first_result = driver.find_elements(By.CSS_SELECTOR, 'h3')[0]
        first_result.click()

        # Step 3: Wait for the page to load
        time.sleep(1)

        # Step 4: Get current URL, append `/?timespan=all`
        current_url = driver.current_url
        full_url = current_url + "/?timespan=all"
        driver.get(full_url)
        time.sleep(3)  # Wait for the new page to load

        # Step 5: Extract page source and parse with BeautifulSoup
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Step 6: Target the table rows and extract alt texts of agent images
        img_tags = soup.select('tr img')  # Select all img tags within tr elements
        alt_texts = [img.get('alt') for img in img_tags if img.get('alt')]  # Extract alt texts

        # Return the top 3 agents as a comma-separated string
        return ', '.join(alt_texts[:3])  # Get top 3 agents

    except Exception as e:
        error_message = str(e)
        print(f"An error occurred while scraping {player_name}: {error_message}")
        log_error(player_name, error_message, error_log_csv)
        return None  # Return None to indicate an error occurred
    finally:
        driver.quit()  # Ensure the browser is closed

# Read the input CSV, scrape data, and overwrite the same CSV file
def update_agents_in_csv(input_csv: str, error_log_csv: str, start_row: int):
    """Update agents in the CSV by scraping data for players with N/A agents."""
    rows = []  # To store all rows temporarily
    
    with open(input_csv, mode='r', newline='', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        headers = next(reader)  # Read the headers
        
        # Store the headers
        rows.append(headers)
        
        # Loop through each row starting from the specified row
        for idx, row in enumerate(reader, start=2):  # Start counting from row 2 (first row is headers)
            if idx < start_row:
                rows.append(row)  # Add row unchanged if before start_row
                continue

            player_handle = row[0]
            if row[6] == 'N/A':  # Target rows where agents are 'N/A'
                print(f"Fetching agent data for {player_handle}...")
                agents = search_and_scrape(player_handle, error_log_csv)
                if agents:
                    row[6] = agents
                    print(f"Player: {player_handle}, Agents: {row[6]}")
                else:
                    print(f"Failed to scrape data for {player_handle}, logging error.")
            
            rows.append(row)  # Add the row (modified or unchanged)

    # Now overwrite the original CSV with updated rows
    with open(input_csv, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerows(rows)  # Write all rows back to the CSV file

# Example usage
input_csv_path = r'test-data\\updated_chmulti_cleaned_error.csv'
error_log_csv = r'test-data\\updated_chmulti_cleaned_error_log.csv'
start_row = 0

update_agents_in_csv(input_csv_path, error_log_csv, start_row)
