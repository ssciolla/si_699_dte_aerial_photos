# Script extracting a JPG image from an Aerial Photo PDF
# Sam Sciolla, Garrett Morton
# SI 699

# PYPDF2 documentation: https://pythonhosted.org/PyPDF2/PdfFileReader.html
# os documentation: https://docs.python.org/3/library/os.html#module-os

# This script uses algorithmic features of a solution posted by sylvain to a Stack Overflow question:
# https://stackoverflow.com/questions/2693820/extract-images-from-pdf-without-resampling-in-python

import os
import PyPDF2
import json

def pull_links_from_index(image_pdf_file_name):
	print(image_pdf_file_name)
	image_pdf_file_object = PyPDF2.PdfFileReader(image_pdf_file_name)

	if image_pdf_file_object.getNumPages() > 1:
		print('** More than one page: {} **'.format(str(test_image_pdf_file_object.getNumPages())))
	pdf_page = image_pdf_file_object.getPage(0)

	media_box = pdf_page['/MediaBox']
	print(media_box)

	links = []
	annotations = pdf_page['/Annots']
	for annotation in annotations:
		annot_object = annotation.getObject()
		float_objects = annot_object['/Rect']
		link_coords = []
		for float_object in float_objects:
			link_coord = float(float_object)
			print(type(link_coord))
			link_coords.append(link_coord)
		if '/A' in annot_object.keys():
			indirect_object = annot_object['/A'].getObject()
		else:
			print("** Annotation does not have a '/A' key ** ")
			print(annot_object['/AP']['/N'].getObject()['/Subtype'])
		if '/F' in indirect_object.keys():
			file_name = indirect_object['/F']['/F']
			print(file_name)
			link_dictionary = {'Image File Name': file_name,
							   'Link Coordinates': link_coords,
							   'File or URI?': 'File'}
		else:
			print("** indirectObject does not have a '/F' key **")
			print(indirect_object)
			uri_name = indirect_object['/URI']
			link_dictionary = {'Image File Name': uri_name,
							   'Link Coordinates': link_coords,
							   'File or URI': 'URI'}
		links.append(link_dictionary)
	index_file_metadata = {'Index File Name': image_pdf_file_name, 'Links': links}
	return index_file_metadata

def extract_jpg_from_pdf(image_pdf_file_name, output_location=''):
	print(image_pdf_file_name)
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
	image_metadata = {}
	image_metadata['Photo File Name'] = image_pdf_file_name
	image_metadata['Width'] = image_object['/Width']
	image_metadata['Height']= image_object['/Height']
	image_metadata['ColorSpace'] = image_object['/ColorSpace'].replace('/', '')
	image_metadata['BitsPerComponent'] = bits_per_comp = image_object['/BitsPerComponent']
	image_metadata['Filter'] = image_object['/Filter'].replace('/', '')
	# print(metadata)

	new_jpg_file_name = image_pdf_file_name.replace(".pdf", '_image.jpg')
	jpg_file = open(output_location + new_jpg_file_name, 'wb')
	jpg_file.write(image_object._data)
	jpg_file.close()

	return image_metadata

def process_batch(pdf_file_names):
	image_metadata_dicts = []
	index_metadata_dicts = []
	for pdf_file_name in pdf_file_names:
		if 'Index' in pdf_file_name:
			new_index_metadata_dict = pull_links_from_index(pdf_file_name)
			index_metadata_dicts.append(new_index_metadata_dict)
		else:
			image_metadata_dict = extract_jpg_from_pdf(pdf_file_name)
			image_metadata_dicts.append(image_metadata_dict)
	return (index_metadata_dicts, image_metadata_dicts)

if __name__=="__main__":
	dir_objects = os.scandir()
	pdf_file_names = []
	for dir_object in dir_objects:
		if '.pdf' in dir_object.name:
			pdf_file_names.append(dir_object.name)
	results = process_batch(pdf_file_names)
	sample_batch_metadata = {}
	sample_batch_metadata['Index Files'] = results[0]
	sample_batch_metadata['Image Files'] = results[1]
	metadata_file = open('sample_batch_metadata.json', 'w', encoding='utf-8')
	metadata_file.write(json.dumps(sample_batch_metadata, indent=4))
	metadata_file.close()
