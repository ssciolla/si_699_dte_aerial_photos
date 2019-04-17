# Miscellaneous functions for DTE Aerial Photo Collection project
# Garrett Morton, Sam Sciolla
# SI 699

# os documentation: https://docs.python.org/3/library/os.html#module-os

# standard modules
import os
import sys
import time

# Uses time module to create a timestamp to indicate when a record was created
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

# Takes a row from a CSV and makes it into a Python dictionary using the CSVs headers as keys
def create_dictionary_from_row(headers, csv_row):
    entity_dict = {}
    for field in headers:
        entity_dict[field.strip()] = csv_row[headers.index(field)]
    return entity_dict
