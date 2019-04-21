# Miscellaneous functions for DTE Aerial Photo Collection project
# Garrett Morton, Sam Sciolla
# SI 699

# os documentation: https://docs.python.org/3/library/os.html#module-os

# standard modules
import os
import sys
import time
import csv

# Use time module to create a timestamp to indicate when a record was created
def make_timestamp():
    current_time = time.localtime()
    timestamp = "{}-{}-{}-{}:{}".format(
		current_time.tm_year,
		current_time.tm_mon,
		current_time.tm_mday,
		current_time.tm_hour,
		current_time.tm_min
	)
    return timestamp

# Collect all relative paths from root directory to files
def collect_relative_paths_for_files(target_directory_path):
	root_directory = os.getcwd()
	os.chdir(target_directory_path)
	dir_objects = os.scandir()
	pdf_file_paths = []
	for dir_object in dir_objects:
		if '.pdf' in dir_object.name:
			absolute_path = os.path.abspath(dir_object.name)
			relative_path = absolute_path.replace(root_directory + '\\', '').replace(root_directory + '/', '')
			pdf_file_paths.append(relative_path)
		else:
			("** Non-PDF file present! **")
	os.chdir(root_directory)
	return pdf_file_paths

# Take a row from a CSV and makes it into a Python dictionary using the CSVs headers as keys
def create_dictionary_from_row(headers, csv_row):
    entity_dict = {}
    for field in headers:
        entity_dict[field.strip()] = csv_row[headers.index(field)]
    return entity_dict

# Create dictionaries (using headers) for each row in the given CSV file
def load_csv_data(csv_file_name):
    try:
        new_csv_file = open(csv_file_name, 'r', newline='', encoding='utf-8-sig')
        csvreader = csv.reader(new_csv_file)
        rows = []
        for row in csvreader:
            rows.append(row)
        new_csv_file.close()
        headers = rows[0]
        csv_data = []
        for row in rows[1:]:
            csv_data.append(create_dictionary_from_row(headers, row))
    except:
        print('-- CSV file was not found at that path --')
        csv_data = {}
    return csv_data
