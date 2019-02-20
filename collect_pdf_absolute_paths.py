# Script collecting absolute paths of all PDF files in a specified directory tree
# Sam Sciolla, Garrett Morton
# SI 699

# This script provides a function for collecting path of all PDF files in the target directory and all its descendants.

# If running this sript as the main program, include path to top level of PDF directory system as a command line argument.

import sys
import json
from pathlib import Path

def collect_paths_in_directory(target_dir_path=".", file_type="pdf"):
	## attempt to open json cache file if it already exists
	try:
		f = open('pdf_path_cache.json', 'r')
		cache_dict = json.loads(f.read())
		print("Path cache file already exists")

	## if cache file does not exist, create it.
	except:
	## write list of path to a file for later use
		cache_dict = {}
		with open('pdf_path_cache.json', 'w') as f:
			pass

	## if cache file is new or did not contain master list of PDF paths, create master list and store in cache dictionary
	if "master_list" not in cache_dict.keys():
		absolute_target = Path(target_dir_path).resolve() #get absolute path of target directory
		path_search_result = absolute_target.glob('**/*.pdf') #search for all pdf filenames recursively
	
		## move pdf paths from a generator to a list
		pdf_path_list = []
		for item in path_search_result:
			pdf_path_list.append(item.as_posix())
			#print(item) #for debugging

		pdf_path_list.sort()
		cache_dict["master_list"] = pdf_path_list

	else:
		#if file exists and "master_list" already key in cache dictionary
		print("Path master list already cached")

	## write cache dictionary to json cache file
	with open('pdf_path_cache.json', 'w') as f:
		f.write(json.dumps(cache_dict))

if __name__=="__main__":
	# if running this file 
	pdf_directory_path = sys.argv[1]
	collect_paths_in_directory(pdf_directory_path)