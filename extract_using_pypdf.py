# DTE Aerial Photo Collection curation project
# Workflow for extracting JPGs and metadata from PDFs
# PyPDF2 Solution
# Garrett Morton, Sam Sciolla
# SI 699

# PYPDF2 documentation: https://pythonhosted.org/PyPDF2/PdfFileReader.html
# os documentation: https://docs.python.org/3/library/os.html#module-os

# This script uses algorithmic features of a solution posted by sylvain to a Stack Overflow question:
# https://stackoverflow.com/questions/2693820/extract-images-from-pdf-without-resampling-in-python

# standard modules
import os
import json
import time

# third-party modules
import PyPDF2

# local modules
import misc_functions

## Functions

# Identify embedded links in Index PDF and collect metadata
def pull_links_from_index(relative_path):
	index_pdf_file_name = relative_path.split('\\')[-1]
	print('// Index: {} //'.format(index_pdf_file_name))
	index_pdf_file_object = PyPDF2.PdfFileReader(relative_path)

	if index_pdf_file_object.getNumPages() > 1:
		print('?? More than one page: {} ??'.format(str(index_pdf_file_object.getNumPages())))
	pdf_page = index_pdf_file_object.getPage(0)

	media_box = pdf_page['/MediaBox']
	links = []
	annotations = pdf_page['/Annots']
	for annotation in annotations:
		annot_object = annotation.getObject()
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
			link_dictionary = {
				'Linked Image File Name': file_name,
				'Link Coordinates': link_coords,
				'File or URI?': 'File'}
		else:
			# Link objects without an '/F' key may signal broken links.
			print("** indirectObject does not have a '/F' key **")
			print(indirect_object)
			uri_name = indirect_object['/URI']
			link_dictionary = {
				'Linked Image File Name': uri_name,
				'Link Coordinates': link_coords,
				'File or URI': 'URI'
			}
		links.append(link_dictionary)
	links = sorted(links, key=lambda x: x['Linked Image File Name'])
	print('** Number of links identified: {} **'.format(str(len(links))))

	index_file_name = index_pdf_file_name.split('\\')[-1]
	index_file_metadata = {
		'Index File Name': index_file_name,
		'Source Relative Path': relative_path,
		'Links': links,
		'Media Box': media_box
	}
	return index_file_metadata

# Identify JPEG bytestream in Image PDF, write it to a new file, and collect image-level metadata
def extract_jpg_from_pdf(relative_path, output_location=''):
	image_pdf_file_name = relative_path.split('\\')[-1]
	print('// Image: {} //'.format(image_pdf_file_name))
	image_pdf_file_object = PyPDF2.PdfFileReader(relative_path)

	if image_pdf_file_object.getNumPages() > 1:
		print('?? More than one page: {} ??'.format(str(test_image_pdf_file_object.getNumPages())))
	pdf_page = image_pdf_file_object.getPage(0)

	objects = pdf_page['/Resources']['/XObject']
	image_objects = []
	for object_name in objects:
		if objects[object_name]['/Subtype'] == '/Image':
			image_objects.append(objects[object_name])
	if len(image_objects) > 1:
		print("?? More than one image: {} ??".format(str(len(image_objects))))
	image_object = image_objects[0]

	image_metadata = {
		'Image File Name': image_pdf_file_name,
		'Source Relative Path': relative_path,
		'Width': image_object['/Width'],
		'Height': image_object['/Height'],
		'ColorSpace': image_object['/ColorSpace'].replace('/', ''),
		'BitsPerComponent': image_object['/BitsPerComponent'],
		'Filter': image_object['/Filter'].replace('/', '')
	}

	identifier = image_pdf_file_name.replace('.pdf', '')
	new_image_file_name = 'dte_aerial_' + identifier + '.jpg'
	jpg_file = open(output_location + new_image_file_name, 'wb')
	jpg_file.write(image_object._data)
	jpg_file.close()
	image_metadata['Created Image File Name'] = new_image_file_name

	return image_metadata

# Manage function invocations and write resulting metadata to a JSON file
def run_pypdf2_workflow(pdf_file_paths, output_location, output_name):
	pypdf_start = time.time()
	image_metadata_dicts = []
	index_metadata_dicts = []
	for pdf_file_path in pdf_file_paths:
		if 'Index' in pdf_file_path:
			new_index_metadata_dict = pull_links_from_index(pdf_file_path)
			index_metadata_dicts.append(new_index_metadata_dict)
		else:
			image_metadata_dict = extract_jpg_from_pdf(pdf_file_path, output_location)
			image_metadata_dicts.append(image_metadata_dict)
	sample_pypdf2_batch_metadata = {}
	sample_pypdf2_batch_metadata['Index Records'] = index_metadata_dicts
	sample_pypdf2_batch_metadata['Image Records'] = image_metadata_dicts
	pypdf2_metadata_file = open('output/pypdf2/' + output_name, 'w', encoding='utf-8')
	pypdf2_metadata_file.write(json.dumps(sample_pypdf2_batch_metadata, indent=4))
	pypdf2_metadata_file.close()
	pypdf_end = time.time()
	print('** Time to Run: {} **'.format(str(pypdf_end - pypdf_start)))

## Main Program

if __name__=="__main__":
	print("\n** DTE Aerial Batch Processing Script **")
	print("** PyPDF2 Solution **")
	output_location = 'output/pypdf2/'
	pdf_file_paths = misc_functions.collect_relative_paths_for_files('input/part1/macomb/1961')
	run_pypdf2_workflow(pdf_file_paths, output_location, 'sample_pypdf2_batch_metadata.json')
