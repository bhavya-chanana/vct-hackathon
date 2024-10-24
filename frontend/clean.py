import pandas as pd
import unidecode

# Load the CSV file ensuring proper UTF-8 encoding
input_csv = "D:\\vct-hackathon\\test-data\\final.csv"  # Replace with your CSV file path
output_csv = "final_cleaned.csv"

# Read the CSV with UTF-8 encoding, handling encoding errors
data = pd.read_csv(input_csv, encoding='latin-1')

# Function to clean names: removes non-ASCII characters and ensures proper formatting
def clean_name(name):
    if pd.isna(name):  # Check for NaN values
        return ""
    name = unidecode.unidecode(name)  # Convert to closest ASCII representation
    return name.strip()  # Remove extra spaces

# Apply the cleaning function to name-related columns
data['first_name'] = data['first_name'].apply(clean_name)
data['last_name'] = data['last_name'].apply(clean_name)

# Save the cleaned data back to a CSV file, ensuring UTF-8 encoding
data.to_csv(output_csv, index=False, encoding='utf-8')

print(f"Cleaned CSV data saved to {output_csv}")
