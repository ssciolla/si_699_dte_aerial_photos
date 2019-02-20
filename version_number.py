# Script extracting PDF version number from a PDF file
# Sam Sciolla, Garrett Morton
# SI 699

#work in progress

def extract_pdf_version_number(target_pdf_path):
	with open(target_pdf_path, 'r') as pdf_file:
		version number = pdf_file.readline()[5:8]

	return version_number