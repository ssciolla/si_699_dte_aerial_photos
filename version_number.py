# Script extracting PDF version number from a PDF file
# Sam Sciolla, Garrett Morton
# SI 699

#work in progress

import json

## extract PDF version number from one PDF file
def extract_pdf_version_number(target_pdf_path):
	with open(target_pdf_path, 'r') as pdf_file:
		version number = pdf_file.readline()[5:8]

	return version_number

## report on PDF versions present in a list of PDF files
def pdf_version_number_report(pdf_path_cache_file):
	with open(pdf_path_cache_file, 'r') as pdf_file:
		pdf_path_list = json.loads(pdf_file.read())

	return report


if __name__=="__main__":
	pdf_version_number_report("pdf_path_cache.json")