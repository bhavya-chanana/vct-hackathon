import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

# Function to perform Google search, open first link, append timespan, and scrape data
def search_and_scrape(player_name: str) -> str:
    """Search for the player and scrape their top agents."""
    # Initialize WebDriver
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
        time.sleep(5)

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
        print(f"An error occurred while scraping {player_name}: {str(e)}")
        return 'N/A'  # Return 'N/A' if any error occurs
    finally:
        driver.quit()  # Ensure the browser is closed

# Read the input CSV, scrape data, and write to the output CSV
def update_agents_in_csv(input_csv: str, output_csv: str):
    """Update agents in the CSV by scraping data."""
    with open(input_csv, mode='r', newline='', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        headers = next(reader)  # Read the headers
        
        # Prepare to write to the output CSV
        with open(output_csv, mode='w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(headers)  # Write headers to the new CSV

            # Loop through each row in the original CSV
            for row in reader:
                player_handle = row[0]  # Assuming player handle is the first column
                print(f"Fetching agent data for {player_handle}...")
                
                # Fetch agent data
                agents = search_and_scrape(player_handle)
                
                # Update the agents column (assuming it's at index 6)
                row[6] = agents
                
                # Print the player handle and agents data before writing to the CSV
                print(f"Player: {player_handle}, Agents: {row[6]}")
                
                writer.writerow(row)  # Write the updated row to the new CSV

# Example usage
input_csv_path = 'path/to/your/input.csv'
output_csv_path = 'path/to/your/output.csv'
update_agents_in_csv(input_csv_path, output_csv_path)
