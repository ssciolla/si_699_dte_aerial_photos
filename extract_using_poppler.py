# DTE Aerial Photo Collection curation project
# Workflow for extracting JPGs and metadata from PDFs
# Poppler Solution
# Garrett Morton, Sam Sciolla
# SI 699

# Written and tested using Python 3.7.0

# os documentation: https://docs.python.org/3/library/os.html#module-os
# subprocess documentation: https://docs.python.org/3/library/subprocess.html

# Poppler requires a Linux operating system, or an equivalent setup.
# Poppler documentation: https://poppler.freedesktop.org/
# PyGObject documentation: https://pygobject.readthedocs.io/en/latest/index.html
# PyGObject and poppler API: https://lazka.github.io/pgi-docs/#Poppler-0.18

# standard modules
import time
import json
import os
import subprocess

# third-party modules
import gi
gi.require_version('Poppler', '0.18')
from gi.repository import Gio, Poppler, cairo

# local modules
import misc_functions

## Functions

# Identify embedded links in Index PDF and collect metadata
def pull_links_from_index(relative_path):
	index_pdf_file_name = relative_path.split('/')[-1]
	print('// Index: {} //'.format(index_pdf_file_name))
	gio_file_object = Gio.File.new_for_path(relative_path)
	new_pdf_object = Poppler.Document.new_from_gfile(gio_file_object)
	# print(new_pdf_object.get_pdf_version())

	if new_pdf_object.get_n_pages() > 1:
		print('?? More than one page: {} ??'.format(str(new_pdf_object.getNumPages())))
	pdf_page = new_pdf_object.get_page(0)

	size_result = pdf_page.get_size()
	page_size = [size_result[0], size_result[1]]

	# annot_mappings = pdf_page.get_annot_mapping()
	# print(len(annot_mappings))
	# for annot_mapping in annot_mappings:
	# 	annot_rect_obj = annot_mapping.area
	# 	annot_coords = {
	# 		'x1': annot_rect_obj.x1,
	# 		'x2': annot_rect_obj.x2,
	# 		'y1': annot_rect_obj.y1,
	# 		'y2': annot_rect_obj.y2
	# 	}
	# 	print(annot_coords)
	# 	annot = annot_mapping.annot
	# 	print(annot.get_annot_type())

	links = []
	link_mappings = pdf_page.get_link_mapping()

	for link_mapping in link_mappings:
		rect_obj = link_mapping.area
		link_coords = {
			'x1': rect_obj.x1,
			'x2': rect_obj.x2,
			'y1': rect_obj.y1,
			'y2': rect_obj.y2
		}

		action = link_mapping.action
		file_name = action.launch.file_name
		link_dictionary = {
			'Photo File Name': file_name,
			'Link Coordinates': link_coords
		}
		links.append(link_dictionary)

	links = sorted(links, key=lambda x: x['Photo File Name'])
	print('** Number of links identified: {} **'.format(str(len(links))))
	index_file_name = index_pdf_file_name.split('/')[-1]
	index_file_metadata = {
		'Index File Name': index_file_name,
		'Source Relative Path': relative_path,
		'Links': links,
		'Page Size': page_size
	}
	return index_file_metadata

# Identify JPEG bytestream in Image PDF, write it to a new file, and collect image-level metadata
def extract_jpg_from_pdf(relative_path, output_location=''):
	image_pdf_file_name = relative_path.split('/')[-1]
	print('// Image: {} //'.format(image_pdf_file_name))
	absolute_path = os.getcwd() + '/' + relative_path
	gio_file_object = Gio.File.new_for_path(absolute_path)
	new_pdf_object = Poppler.Document.new_from_gfile(gio_file_object)

	# print(new_pdf_object.get_pdf_version())

	if new_pdf_object.get_n_pages() > 1:
		print('** More than one page: {} **'.format(str(test_image_pdf_file_object.getNumPages())))
	pdf_page = new_pdf_object.get_page(0)

	# This block is used to enable the collection of the dimensions of the image (height, width).
	# However, this seems to add a couple of seconds to the processing time required.
	image_mappings = pdf_page.get_image_mapping()
	if len(image_mappings) > 1:
		print("?? More than one image: {} ??".format(str(len(image_mappings))))
	image_identifier = image_mappings[0].image_id
	surface_object = pdf_page.get_image(image_identifier)
	image_object = surface_object.map_to_image(None)
	# bytestream = image_object.get_data().tobytes()

	image_pdf_metadata = {
		'Image File Name': image_pdf_file_name,
		'Source Relative Path': relative_path,
		'Height': image_object.get_height(),
		'Width': image_object.get_width()
	}

	# This uses one of the poppler-utils, a command-line tool called pdfimages.
  	# I haven't yet found a way to accomplish the following through the Python interfaces.
	# This particular command-line tool can also output images as TIFFs.

	identifier = image_pdf_file_name.replace('.pdf', '')
	new_image_file_name = 'dte_aerial_' + identifier + '.jpg'
	subprocess.run(['pdfimages', '-j', relative_path, (output_location + new_image_file_name).replace('.jpg', '')])
	image_pdf_metadata['Created Image File Name'] = new_image_file_name

	return image_pdf_metadata

# Manage function invocations and write resulting metadata to a JSON file
def run_poppler_workflow(pdf_file_paths, output_location, output_name):
	poppler_start = time.time()
	image_metadata_dicts = []
	index_metadata_dicts = []
	for pdf_file_path in pdf_file_paths:
		if 'Index' in pdf_file_path:
			new_index_metadata_dict = pull_links_from_index(pdf_file_path)
			index_metadata_dicts.append(new_index_metadata_dict)
		else:
			image_metadata_dict = extract_jpg_from_pdf(pdf_file_path, output_location)
			image_metadata_dicts.append(image_metadata_dict)
	sample_poppler_batch_metadata = {}
	sample_poppler_batch_metadata['Index Records'] = index_metadata_dicts
	sample_poppler_batch_metadata['Image Records'] = image_metadata_dicts
	poppler_metadata_file = open('output/poppler/' + output_name, 'w', encoding='utf-8')
	poppler_metadata_file.write(json.dumps(sample_poppler_batch_metadata, indent=4))
	poppler_metadata_file.close()
	poppler_end = time.time()
	print('** Time to Run: {} **'.format(str(poppler_end - poppler_start)))

## Main Program

if __name__=="__main__":
	print("\n** DTE Aerial Batch Processing Script **")
	print("** Poppler Solution **")
	output_location = 'output/poppler/'
	pdf_file_paths = misc_functions.collect_relative_paths_for_files('input/part1/macomb/1961')
	run_poppler_workflow(pdf_file_paths, output_location, 'sample_poppler_batch_metadata.json')
