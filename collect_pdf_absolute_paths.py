# Script collecting absolute paths of all PDF files in a specified directory tree
# Sam Sciolla, Garrett Morton
# SI 699

# This script provides a function for collecting path of all PDF files in the target directory and all its descendants.

# If running this sript as the main program, include path to top level of PDF directory system as a command line argument.

import sys
import json
from pathlib import Path

def collect_paths_in_directory(target_dir_path=".", file_type="pdf"):
	abs_target = Path(target_dir_path).resolve() #get absolute path of target directory
	result = abs_target.glob('**/*.pdf') #search for all pdf filenames recursively
	
	## move pdf paths from a generator to a list
	pdf_path_list = []
	for item in result:
		pdf_path_list.append(item)

	pdf_path_list.sort()

	try:
		f = open('pdf_path_cache.json', 'r')
		print("PDF list file already exists")

	except:
	## write list of path to a file for later use
		with open('pdf_path_chache.json', 'a') as f:
			for item in pdf_path_list:
				f.write("{}\n".format(item.as_posix())) #write path as POSIX string

if __name__=="__main__":
	# if running this file 
	pdf_directory_path = sys.argv[1]
	collect_paths_in_directory(pdf_directory_path)