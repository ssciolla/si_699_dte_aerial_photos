# DTE Aerial Photo Collection curation project
# Workflow integrating PyPDF2 JPEG extraction and georeferencing
# Garrett Morton, Sam Sciolla
# SI 699

# Written and tested using Python 3.7.0

# standard modules
import sys
import json
import csv
import copy

# local modules
import extract_using_pypdf
import georeference_links
import misc_functions

# Global variable
MANUAL_PAIRS_FILENAME = 'manual_pairs.csv'
FILES_WITHOUT_LINKS = 'files_without_links.csv'

## Functions

# Using functions from georeference_links.py, calculate geocoordinates and county for an image file based on
# the file identifier's coordinates in the index PDF
# Arguments: PDF coordinate pair (pair or list) and dictionary of formula coefficients (dictionary). Returns: dictionary with real-world coordinates (dictionary) and name of county (string)
def collect_arcgis_info_for_coordinate_pair(xy_pair, constants):
    geocoordinates = {}
    latitude = georeference_links.convert_between_systems(float(xy_pair[0]), constants['X Slope'], constants['X Intercept'])
    longitude = georeference_links.convert_between_systems(float(xy_pair[1]), constants['Y Slope'], constants['Y Intercept'])
    geocoordinates['Latitude'] = latitude
    geocoordinates['Longitude'] = longitude
    current_county = georeference_links.check_county_using_geocoordinates([latitude, longitude])
    return geocoordinates, current_county

# Use image, index and link metadata to create full records for each image file
def create_full_record(base_record, image_record, location_input, match_mode='identifier'):
    full_image_record = copy.deepcopy(base_record)
    full_image_record['File Name'] = image_record['Created Image File Name']
    full_image_record['Descriptive']['File Identifier'] = image_record['Image File Name'].replace('.pdf', '')

    # Determine location based on location_input
    if match_mode in ['identifier', 'manual']:
        georeferenced_link_record = location_input
        full_image_record['Descriptive']['ArcGIS Current County'] = georeferenced_link_record['Current County']
        full_image_record['Descriptive']['ArcGIS Geocoordinates'] = {
            'Latitude': georeferenced_link_record['Latitude'],
            'Longitude': georeferenced_link_record['Longitude']
        }
    elif match_mode == 'visual':
        geocoordinates, current_county = location_input
        full_image_record['Descriptive']['ArcGIS Current County'] = current_county
        full_image_record['Descriptive']['ArcGIS Geocoordinates'] = geocoordinates
    else:
        print('-- Invalid match mode input--')

    full_image_record['Technical'] = {
        'Width': image_record['Width'],
        'Height': image_record['Height'],
        'ColorSpace': image_record['ColorSpace'],
        'BitsPerComponent': image_record['BitsPerComponent'],
        'Filter': image_record['Filter']
    }

    if match_mode == 'identifier':
        match_details = {
            'Matching Method': 'String matching on image file identifiers and file identifiers from links',
            'Link PDF Object ID Number': georeferenced_link_record['PDF Object ID Number']
        }
    elif match_mode == 'manual':
        match_details = {
            'Matching Method': 'Image file identifier and PDF Object ID number pair from manual_pairs.csv',
            'Link PDF Object ID Number': georeferenced_link_record['PDF Object ID Number']
        }
    elif match_mode == 'visual':
        match_details = {
            'Matching Method': 'Visually collected PDF coordinates for missing link',
            'Link PDF Object ID Number': None
        }

    full_image_record['Preservation']['Match Details'] = match_details
    full_image_record['Preservation']['PDF Source Relative Path'] = image_record['Source Relative Path']
    full_image_record['Preservation']['Date and Time Created'] = misc_functions.make_timestamp()
    return full_image_record

def create_base_record(batch_metadata):
    index_file_name = batch_metadata['Index Records'][0]['Index File Name']
    source_relative_path = batch_metadata['Index Records'][0]['Source Relative Path']
    year = source_relative_path.split('\\')[-2]
    index_county = source_relative_path.split('\\')[-3]
    base_record = {
        'Descriptive': {
            'Year': year,
            'Index County': index_county
        },
        'Technical': {},
        'Preservation': {
            'Related Index File Name': index_file_name
        }
    }
    return base_record

# Uses full records to create a GeoJSON file for output
# Argument: list of record dictionaries. Returns geojson-formatted dictionary describing a GIS point feature for each image.
def crosswalk_to_geojson(records):
    geojson_dicts = []
    for record in records:
        descriptive_metadata = record['Descriptive']
        geocoordinates = descriptive_metadata['ArcGIS Geocoordinates']
        geojson_dict = {}
        geojson_dict['type'] = 'Feature'
        geojson_dict['geometry'] = {}
        geojson_dict['geometry']['type'] = 'Point'
        geojson_dict['geometry']['coordinates'] = [geocoordinates['Latitude'], geocoordinates['Longitude']]
        geojson_dict['properties'] = {
            'file_identifier': descriptive_metadata['File Identifier'],
            'county': descriptive_metadata['ArcGIS Current County'],
            'year': descriptive_metadata['Year']
        }
        geojson_dicts.append(geojson_dict)
    geojson_wrapper = {}
    geojson_wrapper['type'] = 'FeatureCollection'
    geojson_wrapper['features'] = geojson_dicts
    return geojson_wrapper

# Fetch a link record from all the link records based on its PDF Object ID Number
def find_link_record_with_id(id_num, link_records):
    for link_record in link_records:
        if link_record['PDF Object ID Number'] == int(id_num):
            return link_record
    return None

# Take previous records, combine them, and accumulate a list of full records
def match_and_combine_records(batch_metadata, georeferenced_link_data, manual_pairs, files_without_links):
    print('\n** Image and Link Matching **')

    #pull image records out of batch_metadata
    image_records = batch_metadata['Image Records']

    #create base descriptive metadata dictionary for values shared by all image files
    base_record = create_base_record(batch_metadata)

    link_records = georeferenced_link_data['Georeferenced Link Records']
    constants = georeferenced_link_data['Georeferencing Metadata']['Constants']

    full_image_records = []
    matched_link_record_ids = []
    match_issues = False

    for image_record in image_records:
        file_identifier = image_record['Image File Name'].replace('.pdf', '')
        # If an image and link match has been made manually in manual_pairs.csv, make the match
        if file_identifier in manual_pairs.keys():
            link_record_found = find_link_record_with_id(manual_pairs[file_identifier], link_records)
            full_image_record = create_full_record(base_record, image_record, link_record_found, 'manual')
            full_image_records.append(full_image_record)
            matched_link_record_ids.append(link_record_found['PDF Object ID Number'])
        # If an image had no accompanying link but coordinates were visually collected, create location metadata
        elif file_identifier in files_without_links.keys():
            visual_coordinate_pair = files_without_links[file_identifier]
            arcgis_location_dict = collect_arcgis_info_for_coordinate_pair(visual_coordinate_pair, constants)
            full_image_record = create_full_record(base_record, image_record, arcgis_location_dict, 'visual')
            full_image_records.append(full_image_record)
        else:
            # Otherwise find all links pointing to the same file as the image
            matching_link_records = []
            for link_record in link_records:
                if link_record['Linked Image PDF Identifier'] == file_identifier:
                    matching_link_records.append(link_record)
            # If there is exactly one link, make the match
            if len(matching_link_records) == 1:
                matching_link_record = matching_link_records[0]
                full_image_record = create_full_record(base_record, image_record, matching_link_record)
                full_image_records.append(full_image_record)
                matched_link_record_ids.append(matching_link_record['PDF Object ID Number'])
            else:
                # Otherwise, report the match issue
                if not match_issues:
                    match_issues = True
                if len(matching_link_records) == 0:
                    print('-- No link records found for file identifier: {} --'.format(file_identifier))
                else:
                    print('-- More than one link record found for file identifier: {} --'.format(file_identifier))
                    for matching_link_record in matching_link_records:
                        print('     -- PDF Object ID Number: {} --'.format(matching_link_record['PDF Object ID Number']))
        # print(full_image_record) #for testing
    # Checking if any link records were not matched
    link_record_object_ids = []
    for link_record in link_records:
        link_record_object_ids.append(link_record['PDF Object ID Number'])
    unmatched_link_record_ids = []
    for link_record_object_id in link_record_object_ids:
        if link_record_object_id not in matched_link_record_ids:
            unmatched_link_record_ids.append(link_record_object_id)
    if len(unmatched_link_record_ids) > 0:
        print('?? {} link records were not matched ??'.format(len(unmatched_link_record_ids)))
        for unmatched_link_record_id in unmatched_link_record_ids:
            print('     ?? PDF Object ID Number: {} ??'.format(unmatched_link_record_id))
    return (full_image_records, match_issues)

# Prepare data by running extraction and georeferencing workflows or by loading previous output files
def process_or_load(mode, batch_directory_path, output_directory_path, county_year_combo):
    batch_metadata_file_name = county_year_combo + '_batch_metadata.json'
    georeferenced_links_file_name = county_year_combo + '_georeferenced_links.json'
    if mode == 'process':
        print('~~ Executing extraction and georeferencing workflows ~~')
        pdf_file_paths = misc_functions.collect_relative_paths_for_files(batch_directory_path)
        batch_metadata = extract_using_pypdf.run_pypdf2_workflow(pdf_file_paths, output_directory_path + 'pypdf2/', batch_metadata_file_name)
        georeferenced_link_data = georeference_links.run_georeferencing_workflow(output_directory_path + 'pypdf2/' + batch_metadata_file_name, georeferenced_links_file_name)
    elif mode == 'load':
        print('~~ Loading data from previous workflow executions ~~')
        batch_metadata_file = open(output_directory_path + 'pypdf2/' + batch_metadata_file_name, 'r', encoding='utf-8')
        batch_metadata = json.loads(batch_metadata_file.read())
        batch_metadata_file.close()
        georeferenced_links_file = open(output_directory_path + georeferenced_links_file_name, 'r', encoding='utf-8')
        georeferenced_link_data = json.loads(georeferenced_links_file.read())
        georeferenced_links_file.close()
    else:
        print("-- Invalid mode input --")
    return (batch_metadata, georeferenced_link_data)

## Main Program

if __name__=="__main__":
    print("\n** DTE Aerial Batch Processing Script **")

    data_gathering_mode = sys.argv[1]

    # Setting target directory path for batch processing
    try:
        batch_directory_path = sys.argv[2]
    except:
        # proof of concept directory
        batch_directory_path = 'input/pdf_files/part1/macomb/1961'

    # Setting output directory for new files (output directory must have a pypdf subdirectory)
    try:
        output_directory_path = sys.argv[3]
        if output_directory_path[-1] != "/":
            output_directory_path = output_directory_path + "/" #to handle output directories with or without trailing slash
    except:
        # proof of concept directory
        output_directory_path = 'output/'

    # Create subdirectory of output directory named "pypdf2" if it does not already exist
    misc_functions.output_subdirectory(output_directory_path, "pypdf2")

    # Creating or loading image records and georeferenced link records
    county_year_combo = '_'.join(batch_directory_path.split('/')[-2:])
    batch_metadata, georeferenced_link_data = process_or_load(data_gathering_mode, batch_directory_path, output_directory_path, county_year_combo)

    index_file_name = batch_metadata['Index Records'][0]['Index File Name']

    # Setting up manual pairs dictionary, with image identifiers as values and PDF object ID numbers as
    # their associated keys
    manual_pairs_csv_data = misc_functions.load_csv_data('input/' + MANUAL_PAIRS_FILENAME)
    manual_pairs = {}
    for manual_pair_dict in manual_pairs_csv_data:
        if manual_pair_dict['Index File Name'] == index_file_name:
            manual_pairs[manual_pair_dict['Image Identifier']] = manual_pair_dict['PDF Object ID Number']

    # Setting up files without links dictionary, with image identifiers as values and x and y coordinate
    # tuples as values
    files_without_links_csv_data = misc_functions.load_csv_data('input/files_without_links.csv')
    files_without_links = {}
    for file_without_link_dict in files_without_links_csv_data:
        if file_without_link_dict['Index File Name'] == index_file_name:
            files_without_links[file_without_link_dict['File Identifier']] = (file_without_link_dict['GIMP X Coordinate'], file_without_link_dict['GIMP Y Coordinate'])

    # Running matching algorithm
    full_image_records, match_issues = match_and_combine_records(batch_metadata, georeferenced_link_data, manual_pairs, files_without_links)

    # Writing full records to output file
    full_image_records_file = open(output_directory_path + 'dte_aerial_{}_image_records.json'.format(county_year_combo), 'w', encoding='utf-8')
    full_image_records_file.write(json.dumps(full_image_records, indent=4))
    full_image_records_file.close()

    # Crosswalking records to GeoJSON and writing to output file
    geojson_feature_collection = crosswalk_to_geojson(full_image_records)
    geojson_file = open(output_directory_path + county_year_combo + '_image_locations.geojson', 'w', encoding='utf-8')
    geojson_file.write(json.dumps(geojson_feature_collection, indent=4))
    geojson_file.close()

    # Outputting report to command prompt
    print('\n** Script Results Summary **')
    if match_issues:
        print('-- One or more matches failed, or one or more image records had multiple matches --')
        print('-- Investigate and add file name and PDF object pairs to manual_pairs.csv --')
    else:
        print('++ No match issues occurred ++')
    print('Number of image records after extraction: ' + str(len(batch_metadata['Image Records'])))
    print('Number of link records after extraction: ' + str(len(batch_metadata['Index Records'][0]['Links'])))
    print('Number of complete image records created: ' + str(len(full_image_records)))