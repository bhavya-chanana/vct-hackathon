from bs4 import BeautifulSoup
import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# Function to log errors
def log_error(player_name: str, error_message: str):
    print(f"Error for {player_name}: {error_message}")

# Scrape function to get rating and KAST
def search_and_scrape(player_name: str) -> tuple:
    """Scrape rating and KAST for the player."""
    driver = webdriver.Chrome()

    try:
        # Search on Google for player's VLR profile
        driver.get("https://www.google.com")
        search_box = driver.find_element(By.NAME, 'q')
        search_query = f"{player_name} vlr"
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.RETURN)

        time.sleep(2)
        first_result = driver.find_elements(By.CSS_SELECTOR, 'h3')[0]
        first_result.click()

        time.sleep(2)
        current_url = driver.current_url
        full_url = current_url + "/?timespan=all"
        driver.get(full_url)
        time.sleep(3)

        # Scrape data using BeautifulSoup
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Extract relevant data
        rating = soup.find_all('td', class_='mod-center')[0].text.strip()
        kast = soup.find_all('td', class_='mod-right')[5].text.strip()

        print(rating)
        print(kast)

        return rating, kast

    except Exception as e:
        log_error(player_name, str(e))
        return None, None
    finally:
        driver.quit()

# Function to calculate the average of the 3rd and 7th columns
def calculate_column_averages(soup):
    col_3_values = []
    col_7_values = []

    # Find all rows and extract data from 3rd and 7th columns
    for row in soup.find_all('tr'):
        cols = row.find_all('td')
        if len(cols) > 6:
            col_3_values.append(float(cols[3].text.strip().replace(',', '')))
            col_7_values.append(float(cols[7].text.strip().replace(',', '')))

    # Calculate averages
    avg_col_3 = sum(col_3_values) / len(col_3_values) if col_3_values else 0
    avg_col_7 = sum(col_7_values) / len(col_7_values) if col_7_values else 0

    print(f"Average of 3rd column: {avg_col_3}")
    print(f"Average of 7th column: {avg_col_7}")
    return avg_col_3, avg_col_7
def update_averages_in_csv(input_csv: str, output_csv: str):
    """Update rating and KAST if missing, and save the updated data to a CSV file."""
    with open(input_csv, mode='r', newline='', encoding='latin1') as infile:
        reader = csv.reader(infile)
        headers = next(reader)  # Read and store the headers

        rows = []
        for row in reader:
            player_name = row[0]
            rating = row[8]
            kast = row[11]

            # Check if rating or KAST is missing
            if not rating or not kast:
                print(f"Missing data for {player_name}. Scraping...")
                new_rating, new_kast = search_and_scrape(player_name)

                # Update the row if scraping was successful
                if new_rating and new_kast:
                    row[8] = new_rating  # Update rating in row
                    row[11] = new_kast  # Update KAST in row
                    print(f"Scraped data for {player_name}: Rating={new_rating}, KAST={new_kast}")
                else:
                    print(f"Failed to update {player_name}")

            rows.append(row)  # Append the updated row to the list

    # Write the updated rows back to a new CSV file
    with open(output_csv, mode='w', newline='', encoding='latin1') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(headers)  # Write the headers first
        writer.writerows(rows)  # Write the updated rows

    print(f"Updated data has been saved to {output_csv}")


# # Example usage with HTML
# html_content = ''' # Add your HTML content here '''
# soup = BeautifulSoup(html_content, 'html.parser')

# # Calculate column averages
# calculate_column_averages(soup)
input_csv_path = 'test-data/ch_final_updated.csv'
output_csv_path = 'test-data/ch_final_updated1.csv'
update_averages_in_csv(input_csv_path, output_csv_path)
