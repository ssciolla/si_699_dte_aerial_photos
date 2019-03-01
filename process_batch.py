# Batch processing script for DTE Aerial Collection
# Garrett Morton, Sam Sciolla
# SI 699

# os documentation: https://docs.python.org/3/library/os.html#module-os

import json
import os
import time
import sys

import extract_using_pypdf
import extract_using_poppler

# Collect all relative paths from root directory for files in input directory
def collect_absolute_paths_in_directory(root_directory_path, target_directory_path):
	os.chdir(root_directory_path + target_directory_path)
	# print(os.getcwd())
	dir_objects = os.scandir()
	pdf_file_paths = []
	for dir_object in dir_objects:
		if '.pdf' in dir_object.name:
			absolute_path = os.path.abspath(dir_object.name)
			pdf_file_paths.append(absolute_path)
		else:
			("** Non-PDF file present! **")
	os.chdir(root_directory)
	return pdf_file_paths

# Extract jpegs and metadata for a list of files
def process_batch(pdf_file_paths, root_directory, output_location, extraction_method):
	image_metadata_dicts = []
	index_metadata_dicts = []
	if extraction_method == 'pypdf2':
		for pdf_file_path in pdf_file_paths:
			relative_path = pdf_file_path.replace(root_directory, '')
			print(relative_path)
			if 'Index' in pdf_file_path:
				new_index_metadata_dict = extract_using_pypdf.pull_links_from_index(pdf_file_path, relative_path)
				index_metadata_dicts.append(new_index_metadata_dict)
			else:
				image_metadata_dict = extract_using_pypdf.extract_jpg_from_pdf(pdf_file_path, relative_path, output_location)
				image_metadata_dicts.append(image_metadata_dict)
	elif extraction_method == 'poppler':
		for pdf_file_path in pdf_file_paths:
			relative_path = pdf_file_path.replace(root_directory, '')
			print(relative_path)
			if 'Index' in pdf_file_path:
				new_index_metadata_dict = extract_using_poppler.pull_links_from_index(pdf_file_path, relative_path)
				index_metadata_dicts.append(new_index_metadata_dict)
			else:
				image_metadata_dict = extract_using_poppler.extract_jpg_from_pdf(pdf_file_path, relative_path, output_location)
				image_metadata_dicts.append(image_metadata_dict)
	else:
		print("** No extraction method given **")
	return (index_metadata_dicts, image_metadata_dicts)

def run_pypdf2_workflow():
	print("\n** PyPDF2 **")
	pypdf_start = time.time()
	pypdf2_results = process_batch(pdf_file_paths, root_directory, 'output/pypdf2/', 'pypdf2')
	sample_pypdf2_batch_metadata = {}
	sample_pypdf2_batch_metadata['Index Records'] = pypdf2_results[0]
	sample_pypdf2_batch_metadata['Image Records'] = pypdf2_results[1]
	pypdf2_metadata_file = open('output/pypdf2/sample_batch_metadata.json', 'w', encoding='utf-8')
	pypdf2_metadata_file.write(json.dumps(sample_pypdf2_batch_metadata, indent=4))
	pypdf2_metadata_file.close()
	pypdf_end = time.time()
	print('Time to Run: ' + str(pypdf_end - pypdf_start))

def run_poppler_workflow():
	print("\n** Poppler **")
	poppler_start = time.time()
	poppler_results = process_batch(pdf_file_paths, root_directory, 'output/poppler/', 'poppler')
	sample_poppler_batch_metadata = {}
	sample_poppler_batch_metadata['Index Records'] = poppler_results[0]
	sample_poppler_batch_metadata['Image Records'] = poppler_results[1]
	poppler_metadata_file = open('output/poppler/sample_batch_metadata.json', 'w', encoding='utf-8')
	poppler_metadata_file.write(json.dumps(sample_poppler_batch_metadata, indent=4))
	poppler_metadata_file.close()
	poppler_end = time.time()
	print('Time to Run: ' + str(poppler_end - poppler_start))

if __name__ == "__main__":
	print("\n** DTE Aerial Batch Processing Script **")
	root_directory = os.getcwd()
	pdf_file_paths = collect_absolute_paths_in_directory(root_directory, '/input')

	mode = sys.argv[1]
	if mode == 'pypdf2':
		run_pypdf2_workflow()
	elif mode == 'poppler':
		run_poppler_workflow()
	elif mode == 'both':
		run_pypdf2_workflow()
		run_poppler_workflow()
	else:
		print("** Invalid input **")
