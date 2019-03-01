# Functions for extracting JPGs from PDFs and creating metadata
# PyPDF2 Solution
# Garrett Morton, Sam Sciolla
# SI 699

# PYPDF2 documentation: https://pythonhosted.org/PyPDF2/PdfFileReader.html
# os documentation: https://docs.python.org/3/library/os.html#module-os

# This script uses algorithmic features of a solution posted by sylvain to a Stack Overflow question:
# https://stackoverflow.com/questions/2693820/extract-images-from-pdf-without-resampling-in-python

import os
import json
import time
import sys

import PyPDF2

def pull_links_from_index(index_pdf_file_name, relative_path):
	print('// Index: {} //'.format(index_pdf_file_name.split('/')[-1]))
	index_pdf_file_object = PyPDF2.PdfFileReader(index_pdf_file_name)

	if index_pdf_file_object.getNumPages() > 1:
		print('** More than one page: {} **'.format(str(index_pdf_file_object.getNumPages())))
	pdf_page = index_pdf_file_object.getPage(0)

	media_box = pdf_page['/MediaBox']

	links = []
	annotations = pdf_page['/Annots']
	for annotation in annotations:
		annot_object = annotation.getObject()
		# print(annot_object.keys())
		float_objects = annot_object['/Rect']
		link_coords = []
		for float_object in float_objects:
			link_coord = float(float_object)
			link_coords.append(link_coord)
		if '/A' in annot_object.keys():
			indirect_object = annot_object['/A'].getObject()
		else:
			print("** Annotation does not have a '/A' key ** ")
			print(annot_object['/AP']['/N'].getObject()['/Subtype'])
		if '/F' in indirect_object.keys():
			file_name = indirect_object['/F']['/F']
			link_dictionary = {'Linked Image File Name': file_name,
							   'Link Coordinates': link_coords,
							   'File or URI?': 'File'}
		else:
			# Link objects without an '/F' key may signal broken links.
			print("** indirectObject does not have a '/F' key **")
			print(indirect_object)
			uri_name = indirect_object['/URI']
			link_dictionary = {'Linked Image File Name': uri_name,
							   'Link Coordinates': link_coords,
							   'File or URI': 'URI'}
		links.append(link_dictionary)
	links = sorted(links, key=lambda x: x['Linked Image File Name'])
	print('Number of links identified: ' + str(len(links)))

	index_file_name = index_pdf_file_name.split('/')[-1]
	index_file_metadata = {'Index File Name': index_file_name,
						   'Source Absolute Path': index_pdf_file_name,
						   'Links': links,
						   'Media Box': media_box}
	return index_file_metadata

def extract_jpg_from_pdf(image_pdf_file_name, relative_path='', output_location=''):
	print('// Image: {} //'.format(image_pdf_file_name.split('/')[-1]))
	image_pdf_file_object = PyPDF2.PdfFileReader(image_pdf_file_name)

	if image_pdf_file_object.getNumPages() > 1:
		print('** More than one page: {} **'.format(str(test_image_pdf_file_object.getNumPages())))
	pdf_page = image_pdf_file_object.getPage(0)

	objects = pdf_page['/Resources']['/XObject']

	image_objects = []
	for object_name in objects:
		if objects[object_name]['/Subtype'] == '/Image':
			image_objects.append(objects[object_name])

	if len(image_objects) > 1:
		print("** More than one image: {} **".format(str(len(image_objects))))

	image_object = image_objects[0]
	identifier = image_pdf_file_name.split('/')[-1].replace('.pdf', '')

	image_metadata = {}
	image_metadata['File Identifier'] = identifier
	image_metadata['Source Relative Path'] = relative_path
	image_metadata['Width'] = image_object['/Width']
	image_metadata['Height']= image_object['/Height']
	image_metadata['ColorSpace'] = image_object['/ColorSpace'].replace('/', '')
	image_metadata['BitsPerComponent'] = bits_per_comp = image_object['/BitsPerComponent']
	image_metadata['Filter'] = image_object['/Filter'].replace('/', '')

	new_image_file_name = 'dte_aerial_' + identifier + '.jpg'
	jpg_file = open(output_location + new_image_file_name, 'wb')
	jpg_file.write(image_object._data)
	jpg_file.close()
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
