# Script extracting a JPG image from an Aerial Photo PDF
# Sam Sciolla, Garrett Morton
# SI 699

# PYPDF2 documentation: https://pythonhosted.org/PyPDF2/PdfFileReader.html
# os documentation: https://docs.python.org/3/library/os.html#module-os

import os
import PyPDF2

def extract_jpg_from_pdf(image_file_name, output_location=''):
	image_pdf_file_name = image_file_name
	image_pdf_file_object = PyPDF2.PdfFileReader(image_pdf_file_name)

	if image_pdf_file_object.getNumPages() > 1:
		print('** More than 1 page: {} **'.format(str(test_image_pdf_file_object.getNumPages())))

	pdf_page = image_pdf_file_object.getPage(0)
	objects = pdf_page['/Resources']['/XObject']

	image_objects = []
	for object_name in objects:
		if objects[object_name]['/Subtype'] == '/Image':
			image_objects.append(objects[object_name])

	if len(image_objects) > 1:
		print("** More than one image: {} **".format(str(len(image_objects))))

	image_object = image_objects[0]

	metadata = {}
	metadata['Width'] = image_object['/Width']
	metadata['Height']= image_object['/Height']
	metadata['ColorSpace'] = image_object['/ColorSpace'].replace('/', '')
	metadata['BitsPerComponent'] = bits_per_comp = image_object['/BitsPerComponent']
	metadata['Filter'] = image_object['/Filter'].replace('/', '')
	print(metadata)

	new_jpg_file_name = image_pdf_file_name.replace(".pdf", '_image.jpg')
	jpg_file = open(output_location + new_jpg_file_name, 'wb')
	jpg_file.write(image_object._data)
	jpg_file.close()

	return metadata

if __name__=="__main__":
	dir_objects = os.scandir()
	image_metadata_dicts = {}
	for dir_object in dir_objects:
		if '.pdf' in dir_object.name:
			identifier = dir_object.name.replace('.pdf', '')
			new_metadata_dict = extract_jpg_from_pdf(dir_object.name)
			image_metadata_dicts[identifier] = new_metadata_dict
	print('Files and metadata created: ' + str(', '.join(list(image_metadata_dicts.keys()))))
