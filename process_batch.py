# DTE Aerial Photo Collection curation project
# Workflow integrating PyPDF2 JPEG extraction and geolocation
# Garrett Morton, Sam Sciolla
# SI 699

# Written and tested using Python 3.7.0

# standard modules
import sys
import json
import csv

# local modules
import extract_using_pypdf
import geolocate_links
import misc_functions

# Global variables
MANUAL_PAIRS_FILENAME = 'manual_pairs.csv'
BATCH_DIRECTORY_PATH = 'input/pdf_files/part1/macomb/1961'
BATCH_METADATA_FILE_NAME = 'sample_pypdf2_batch_metadata.json'

## Functions

def create_full_record(image_record, geolocated_link_record, shared_descriptive_metadata):
    full_image_record = {}
    full_image_record['File Name'] = image_record['Created Image File Name']
    full_image_record['Descriptive'] = shared_descriptive_metadata.copy()
    full_image_record['Descriptive']['ArcGIS Current County'] = geolocated_link_record['Current County']
    full_image_record['Descriptive']['ArcGIS Geolocation'] = {
        'Latitude': geolocated_link_record['Latitude'],
        'Longitude': geolocated_link_record['Longitude']
    }
    full_image_record['Technical'] = {
        'Width': image_record['Width'],
        'Height': image_record['Height'],
        'ColorSpace': image_record['ColorSpace'],
        'BitsPerComponent': image_record['BitsPerComponent'],
        'Filter': image_record['Filter']
    }
    full_image_record['Preservation'] = {
        'Source Relative Path': image_record['Source Relative Path']
    }
    return full_image_record

def process_or_load(mode, batch_directory_path, batch_metadata_file_name):
    if mode == 'process':
        print('~~ Executing extraction and geolocation workflows ~~')
        pdf_file_paths = misc_functions.collect_relative_paths_for_files(batch_directory_path)
        batch_metadata = extract_using_pypdf.run_pypdf2_workflow(pdf_file_paths, 'output/pypdf2/', batch_metadata_file_name)
        geolocated_link_records = geolocate_links.run_geolocation_workflow('output/pypdf2/' + batch_metadata_file_name)
    elif mode == 'load':
        print('~~ Loading data from previous workflow executions ~~')
        batch_metadata_file = open('output/pypdf2/' + batch_metadata_file_name, 'r', encoding='utf-8')
        batch_metadata = json.loads(batch_metadata_file.read())
        batch_metadata_file.close()
        geolocated_links_file = open('output/geolocated_links.json', 'r', encoding='utf-8')
        geolocated_link_records = json.loads(geolocated_links_file.read())
        geolocated_links_file.close()
    else:
        print("-- Invalid mode input --")
    return (batch_metadata, geolocated_link_records)

def find_link_record_with_id(id_num, geolocated_link_records):
    for geolocated_link_record in geolocated_link_records:
        if geolocated_link_record['PDF Object ID Number'] == int(id_num):
            return geolocated_link_record
    return None

## Main Program

if __name__=="__main__":
    print("\n** DTE Aerial Batch Processing Script **")

    # Setting up variables
    mode = sys.argv[1]
    batch_directory_path = 'input/pdf_files/part1/macomb/1961'
    batch_metadata_file_name = 'sample_pypdf2_batch_metadata.json'

    batch_metadata, geolocated_link_records = process_or_load(mode, BATCH_DIRECTORY_PATH, BATCH_METADATA_FILE_NAME)
    image_records = batch_metadata['Image Records']

    shared_descriptive_metadata = {}
    source_relative_path = batch_metadata['Index Records'][0]['Source Relative Path']
    shared_descriptive_metadata['Year'] = source_relative_path.split('\\')[-2]
    shared_descriptive_metadata['Index County'] = source_relative_path.split('\\')[-3]

    try:
        manual_pairs_file = open('input/' + MANUAL_PAIRS_FILENAME, 'r', newline='', encoding='utf-8')
        csvreader = csv.reader(manual_pairs_file)
        rows = []
        for row in csvreader:
            rows.append(row)
        manual_pairs_file.close()
        headers = rows[0]
        dict_rows = []
        for row in rows[1:]:
            dict_rows.append(misc_functions.create_dictionary_from_row(headers, row))
        manual_pairs = {}
        for dict_row in dict_rows:
            manual_pairs[dict_row['Image Identifier']] = dict_row['PDF Object ID Number']
    except:
        manual_pairs = {}

    # Matching pattern
    full_image_records = []
    geolocated_link_records_matched = []
    match_issues = False
    for image_record in image_records:
        batch_identifier = image_record['Image File Name'].replace('.pdf', '')
        # If an image and link match has been made manually in manual_pairs.csv, make the match
        if batch_identifier in manual_pairs.keys():
            geolocated_link_record = find_link_record_with_id(manual_pairs[batch_identifier], geolocated_link_records)
            full_image_record = create_full_record(image_record, geolocated_link_record, shared_descriptive_metadata)
            geolocated_link_records_matched.append(geolocated_link_record['PDF Object ID Number'])
            full_image_records.append(full_image_record)
        else:
            # Otherwise find a link pointing to the same file as the image, and make the match
            matching_link_records = []
            for geolocated_link_record in geolocated_link_records:
                if geolocated_link_record['Linked Image PDF Identifier'] == batch_identifier:
                    matching_link_records.append(geolocated_link_record)
                    geolocated_link_records_matched.append(geolocated_link_record['PDF Object ID Number'])
            if len(matching_link_records) == 1:
                full_image_record = create_full_record(image_record, geolocated_link_record, shared_descriptive_metadata)
                full_image_records.append(full_image_record)
            else:
                if match_issues == False:
                    match_issues = True
                if len(matching_link_records) == 0:
                    print('-- No link records found for file identifier: {} --'.format(batch_identifier))
                else:
                    print('-- More than one link record found for file identifier: {} --'.format(batch_identifier))
                    for matching_link_record in matching_link_records:
                        print('-- PDF Object ID Number: {} --'.format(matching_link_record['PDF Object ID Number']))

    full_image_records_file = open('output/dte_aerial_image_records.json', 'w', encoding='utf-8')
    full_image_records_file.write(json.dumps(full_image_records, indent=4))
    full_image_records_file.close()

    print('** Script Results Summary **')
    if match_issues == True:
        print('-- Either a match failed or an image record had multiple matches --')
        print('-- Investigate and add file name and PDF object pairs to manual_pairs.csv --')
    else:
        print('++ No match issues occurred ++')
    print('Number of image records after extraction: ' + str(len(batch_metadata['Image Records'])))
    print('Number of link records after extraction: ' + str(len(batch_metadata['Index Records'][0]['Links'])))
    print('Number of complete image records created: ' + str(len(full_image_records)))
