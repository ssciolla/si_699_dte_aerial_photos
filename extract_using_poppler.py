# Functions for extracting JPGs from PDFs and creating metadata
# Poppler Solution
# Sam Sciolla, Garrett Morton
# SI 699

# os documentation: https://docs.python.org/3/library/os.html#module-os
# subprocess documentation: https://docs.python.org/3/library/subprocess.html

# Poppler requires a Linux operating system, or an equivalent setup.
# Poppler documentation: https://poppler.freedesktop.org/
# PyGObject documentation: https://pygobject.readthedocs.io/en/latest/index.html
# PyGObject and poppler API: https://lazka.github.io/pgi-docs/#Poppler-0.18

import json
import os
import subprocess
import gi
gi.require_version('Poppler', '0.18')
from gi.repository import Gio, Poppler, cairo

def pull_links_from_index(index_pdf_file_name):
	gio_file_object = Gio.File.new_for_path(index_pdf_file_name)
	new_pdf_object = Poppler.Document.new_from_gfile(gio_file_object)

	print(new_pdf_object.get_pdf_version())

	if new_pdf_object.get_n_pages() > 1:
		print('** More than one page: {} **'.format(str(test_image_pdf_file_object.getNumPages())))
	pdf_page = new_pdf_object.get_page(0)

	size_result = pdf_page.get_size()
	page_size = [size_result[0], size_result[1]]

	links = []
	link_mappings = pdf_page.get_link_mapping()

	for link_mapping in link_mappings:
		rect_obj = link_mapping.area
		link_coords = {'x1': rect_obj.x1,
					   'x2': rect_obj.x2,
					   'y1': rect_obj.y1,
					   'y2': rect_obj.y2}

		action = link_mapping.action
		file_name = action.launch.file_name
		link_dictionary = {'Photo File Name': file_name,
						   'Link Coordinates': link_coords}
		links.append(link_dictionary)

	links = sorted(links, key=lambda x: x['Photo File Name'])
	print(len(links))
	index_file_metadata = {'Index File Name': index_pdf_file_name,
						   'Links': links,
						   'Page Size': page_size}
	return index_file_metadata

def extract_jpg_from_pdf(image_pdf_file_name, output_location=''):
	gio_file_object = Gio.File.new_for_path(image_pdf_file_name)
	new_pdf_object = Poppler.Document.new_from_gfile(gio_file_object)

	print(new_pdf_object.get_pdf_version())

	if new_pdf_object.get_n_pages() > 1:
		print('** More than one page: {} **'.format(str(test_image_pdf_file_object.getNumPages())))
	pdf_page = new_pdf_object.get_page(0)

	image_mappings = pdf_page.get_image_mapping()
	if len(image_mappings) > 1:
		print("** More than one image: {} **".format(str(len(image_mappings))))

	image_identifier = image_mappings[0].image_id
	surface_object = pdf_page.get_image(image_identifier)
	image_object = surface_object.map_to_image(None)
	# bytestream = image_object.get_data().tobytes()

	image_metadata = {}
	image_metadata['Photo File Name'] = image_pdf_file_name.replace('input/', '')
	image_metadata['Height'] = image_object.get_height()
	image_metadata['Width'] = image_object.get_width()

	# This uses one of the poppler-utils, a command-line tool called pdfimages.
  	# I haven't yet found a way to accomplish the following through the Python interfaces.
	# This particular command-line tool can also output images as TIFFs.
	new_jpg_file_name = image_pdf_file_name.replace('input/', '').replace(".pdf", '_image.jpg')
	subprocess.run(['pdfimages', '-j', image_pdf_file_name, output_location + new_jpg_file_name])

	return image_metadata

def process_batch(pdf_file_names, output_location):
	image_metadata_dicts = []
	index_metadata_dicts = []
	for pdf_file_name in pdf_file_names:
		if 'Index' in pdf_file_name:
			new_index_metadata_dict = pull_links_from_index(pdf_file_name)
			index_metadata_dicts.append(new_index_metadata_dict)
		else:
			image_metadata_dict = extract_jpg_from_pdf(pdf_file_name, output_location)
			image_metadata_dicts.append(image_metadata_dict)
	return (index_metadata_dicts, image_metadata_dicts)

if __name__=="__main__":
	root_directory = os.getcwd()
	os.chdir(root_directory + "/input")
	dir_objects = os.scandir()
	pdf_file_names = []
	for dir_object in dir_objects:
		if '.pdf' in dir_object.name:
			pdf_file_names.append('input/' + dir_object.name)
	os.chdir(root_directory)
	results = process_batch(pdf_file_names, 'output/poppler/')
	sample_batch_metadata = {}
	sample_batch_metadata['Index Files'] = results[0]
	sample_batch_metadata['Image Files'] = results[1]
	os.chdir(root_directory)
	metadata_file = open('output/poppler/sample_batch_metadata.json', 'w', encoding='utf-8')
	metadata_file.write(json.dumps(sample_batch_metadata, indent=4))
	metadata_file.close()
