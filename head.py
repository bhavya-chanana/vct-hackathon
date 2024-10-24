import pandas as pd
import json

# Load JSON data
with open('test-data\\val0a63934c-9907-4b7c-a553-ac945cc9eea4.json') as file:
    data = json.load(file)

# Convert JSON to DataFrame
df = pd.DataFrame(data)

# Display head of 5 specific columns (adjust the column names to fit your data)
# Show the first 5 rows (head) of the selected columns
print(df.head())
