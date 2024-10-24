import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Function to log errors to a CSV file
def log_error(player_name: str, error_message: str, error_log_csv: str):
    """Log errors to a CSV file."""
    with open(error_log_csv, mode='a', newline='', encoding='utf-8') as error_file:
        writer = csv.writer(error_file)
        writer.writerow([player_name, error_message])  # Write player name and error message

# Function to perform Google search, open first link, and scrape country
def search_and_scrape_country(player_name: str) -> str:
    """Search for the player and scrape their country."""
    driver = webdriver.Chrome()
    
    try:
        # Step 1: Perform Google search with site:vlr.gg
        driver.get("https://www.google.com")
        search_box = driver.find_element(By.NAME, 'q')
        search_query = f"{player_name} site:vlr.gg"
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.RETURN)

        # Step 2: Open first search result
        time.sleep(2)  # Wait for results to load
        first_result = driver.find_elements(By.CSS_SELECTOR, 'h3')[0]
        first_result.click()

        # Step 3: Wait for the page to load
        time.sleep(3)

        # Step 4: Locate the country element using WebDriverWait
        country_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.ge-text-light"))
        )
        
        # Step 5: Extract the country information
        if country_element:
            country_text = country_element.text.strip()
            return country_text.split()[-1]  # Extract the country name (last word)
        return None

    except Exception as e:
        error_message = str(e)
        print(f"An error occurred while scraping {player_name}: {error_message}")
        log_error(player_name, error_message, error_log_csv)
        return None  # Return None if error occurs
    finally:
        driver.quit()  # Ensure the browser is closed

# Read the input CSV, scrape data, and update the same CSV
def update_country_in_csv(input_csv: str, error_log_csv: str):
    """Update missing countries in the CSV by scraping data."""
    rows = []

    # Step 1: Read the CSV content
    with open(input_csv, mode='r', newline='', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        headers = next(reader)  # Read the headers

        # Write back the headers to the CSV (if needed)
        rows.append(headers)  # Append headers to rows

        # Loop through each row in the original CSV
        for row in reader:
            player_handle = row[0]  # Assuming player handle is the first column
            player_country = row[1]  # Assuming country is the second column
            
            # Initialize country variable to None before attempting to scrape
            country = None
            
            if not player_country:  # Check if the country is missing or empty
                print(f"Fetching country data for {player_handle}...")
                
                # Fetch country data
                country = search_and_scrape_country(player_handle)
                
                # Only update the country column if valid data is scraped
                if country:
                    row[1] = country  # Update the country column
                    print(f"Player: {player_handle}, Country: {country}")
                else:
                    print(f"No country data found for {player_handle}")
            
            # Append the updated row to the rows list
            rows.append(row)
            
            # Step 2: Write the updated row back to the CSV immediately after fetching
            with open(input_csv, mode='w', newline='', encoding='utf-8') as outfile:
                writer = csv.writer(outfile)
                writer.writerows(rows)  # Write all rows back to the CSV

# Example usage
input_csv_path = r'test-data\\missing_coun_lang.csv'
error_log_csv = r'test-data\\missing_coun_lang_error_log.csv'  # Path for the error log
update_country_in_csv(input_csv_path, error_log_csv)