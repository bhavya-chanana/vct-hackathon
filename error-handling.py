import csv
error_log = r'D:\vct-hackathon\test-data\chmulti_cleaned_error_log.csv'

with open(error_log, "r", encoding="utf-8") as file:
    error_reader = csv.reader(error_log)
    for row in error_reader:
        player_handle = row[0]  # Player handle is the first column
        print(row[0])