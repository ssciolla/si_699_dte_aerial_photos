# Functions for extracting JPGs from PDFs and creating metadata
# Poppler Solution
# Garrett Morton, Sam Sciolla
# SI 699

# os documentation: https://docs.python.org/3/library/os.html#module-os
# subprocess documentation: https://docs.python.org/3/library/subprocess.html

# Poppler requires a Linux operating system, or an equivalent setup.
# Poppler documentation: https://poppler.freedesktop.org/
# PyGObject documentation: https://pygobject.readthedocs.io/en/latest/index.html
# PyGObject and poppler API: https://lazka.github.io/pgi-docs/#Poppler-0.18

import time
import json
import os
import subprocess
import sys

import gi
gi.require_version('Poppler', '0.18')
from gi.repository import Gio, Poppler, cairo

def pull_links_from_index(index_pdf_file_name, relative_path=''):
	print('// Index: {} //'.format(index_pdf_file_name.split('/')[-1]))
	gio_file_object = Gio.File.new_for_path(index_pdf_file_name)
	new_pdf_object = Poppler.Document.new_from_gfile(gio_file_object)

	# print(new_pdf_object.get_pdf_version())

	if new_pdf_object.get_n_pages() > 1:
		print('** More than one page: {} **'.format(str(new_pdf_object.getNumPages())))
	pdf_page = new_pdf_object.get_page(0)

	size_result = pdf_page.get_size()
	page_size = [size_result[0], size_result[1]]

	# annot_mappings = pdf_page.get_annot_mapping()
	# print(len(annot_mappings))
	# for annot_mapping in annot_mappings:
	# 	annot_rect_obj = annot_mapping.area
	# 	annot_coords = {'x1': annot_rect_obj.x1,
	# 				    'x2': annot_rect_obj.x2,
	# 				    'y1': annot_rect_obj.y1,
	# 				    'y2': annot_rect_obj.y2}
	# 	print(annot_coords)
	# 	annot = annot_mapping.annot
	# 	print(annot.get_annot_type())

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
	print('Number of links identified: ' + str(len(links)))
	index_file_name = index_pdf_file_name.split('/')[-1]
	index_file_metadata = {'Index File Name': index_file_name,
						   'Source Relative Path': relative_path,
						   'Links': links,
						   'Page Size': page_size}
	return index_file_metadata

def extract_jpg_from_pdf(image_pdf_file_name, relative_path='', output_location=''):
	print('// Image: {} //'.format(image_pdf_file_name.split('/')[-1]))
	gio_file_object = Gio.File.new_for_path(image_pdf_file_name)
	new_pdf_object = Poppler.Document.new_from_gfile(gio_file_object)

	# print(new_pdf_object.get_pdf_version())

	if new_pdf_object.get_n_pages() > 1:
		print('** More than one page: {} **'.format(str(test_image_pdf_file_object.getNumPages())))
	pdf_page = new_pdf_object.get_page(0)

	# This block is used to enable the collection of the dimensions of the image (height, width).
	# However, this seems to add a couple of seconds to the processing time required.
	image_mappings = pdf_page.get_image_mapping()
	if len(image_mappings) > 1:
		print("** More than one image: {} **".format(str(len(image_mappings))))
	image_identifier = image_mappings[0].image_id
	surface_object = pdf_page.get_image(image_identifier)
	image_object = surface_object.map_to_image(None)
	# bytestream = image_object.get_data().tobytes()

	identifier = image_pdf_file_name.split('/')[-1].replace('.pdf', '')

	image_metadata = {}
	image_metadata['File Identifier'] = identifier
	image_metadata['Source Relative Path'] = relative_path
	image_metadata['Height'] = image_object.get_height()
	image_metadata['Width'] = image_object.get_width()

	# This uses one of the poppler-utils, a command-line tool called pdfimages.
  	# I haven't yet found a way to accomplish the following through the Python interfaces.
	# This particular command-line tool can also output images as TIFFs.
	new_image_file_name = 'dte_aerial_' + identifier + '.jpg'
	subprocess.run(['pdfimages', '-j', image_pdf_file_name, (output_location + new_image_file_name).replace('.jpg', '')])
	image_metadata['Created Image File Name'] = new_image_file_name

	return image_metadata

if __name__=="__main__":
	file_name = sys.argv[1]
	absolute_path = os.path.abspath(file_name)
	print(absolute_path)
	sample_file_metadata = {}
	if 'Index' in file_name:
		sample_file_metadata['Index_Files'] = pull_links_from_index(absolute_path, file_name)
	else:
		sample_file_metadata['Image Files'] = extract_jpg_from_pdf(absolute_path, file_name)
	print(sample_file_metadata)
