# DTE Aerial Photo Collection curation project
# Workflow for georeferencing links from a PDF index file
# Garrett Morton, Sam Sciolla
# SI 699

# Written and tested using Python 3.7.0

# ArcGIS documentation: https://esri.github.io/arcgis-python-api/apidoc/html/

# standard modules
import json
import csv
import sys

# third-party modules
from arcgis import GIS
from arcgis.geocoding import geocode, reverse_geocode

# local modules
import misc_functions

CACHE_FILE_NAME = 'arcgis_geocoding_cache.json'
ADDRESS_PAIRS_FILE_PATH = 'input/address_pairs.csv'

gis = GIS()

## Caching

# Setting up geocoding caching dictionary.
try:
    file_open = open(CACHE_FILE_NAME, "r")
    json_string = file_open.read()
    CACHE_DICTION = json.loads(json_string)
    file_open.close()
except:
    CACHE_DICTION = {}

def fetch_geocoding_data_with_caching(input_data, reverse=False):
    if reverse == True:
        input_string = str(input_data[0]) + ', ' + str(input_data[1])
    else:
        input_string = input_data
    if input_string in CACHE_DICTION:
        # print("** Pulling data from cache **")
        return CACHE_DICTION[input_string]
    else:
        print("** Fetching new data from API **")
        if reverse == False:
            data = geocode(input_string)
        else:
            data = reverse_geocode(input_string)
        CACHE_DICTION[input_string] = data
        cache_file_open = open(CACHE_FILE_NAME, "w")
        cache_file_open.write(json.dumps(CACHE_DICTION, indent=4))
        cache_file_open.close()
        return data

## General Functions

def find_mid_left_point(link_coords):
    x_one = link_coords[0]
    x_two = link_coords[2]
    y_one = link_coords[1]
    y_two = link_coords[3]
    x_value = x_one
    y_value = (y_two - y_one)/2 + y_one
    return (x_value, y_value)

def create_new_link_records(batch_metadata):
    links = batch_metadata['Index Records'][0]['Links']
    link_location_dicts = []
    for link in links:
        link_location_dict = {}
        link_location_dict['PDF Object ID Number'] = link['PDF Object ID Number']
        link_location_dict['Linked Image PDF Identifier'] = link['Linked Image File Name'].replace('.pdf', '')
        x_value, y_value = find_mid_left_point(link['Link Coordinates'])
        link_location_dict['PDF X Coordinate'] = x_value
        link_location_dict['PDF Y Coordinate'] = y_value
        link_location_dicts.append(link_location_dict)
    return link_location_dicts

def pull_lat_and_lon(geocoding_dict):
    latitude = geocoding_dict['location']['x']
    longitude = geocoding_dict['location']['y']
    return latitude, longitude

def find_constants_for_formulas(address_pair_dict):
    address_one = address_pair_dict['Address 1']
    address_one_lat, address_one_lon = pull_lat_and_lon(fetch_geocoding_data_with_caching(address_one)[0])
    address_one_x = float(address_pair_dict['Address 1 GIMP X Coordinate'])
    address_one_y = float(address_pair_dict['Address 1 GIMP Y Coordinate'])

    address_two = address_pair_dict['Address 2']
    address_two_lat, address_two_lon = pull_lat_and_lon(fetch_geocoding_data_with_caching(address_two)[0])
    address_two_x = float(address_pair_dict['Address 2 GIMP X Coordinate'])
    address_two_y = float(address_pair_dict['Address 2 GIMP Y Coordinate'])

    x_slope = (address_one_lat - address_two_lat) / (address_one_x - address_two_x)
    x_intercept = address_one_lat - (x_slope * address_one_x)

    y_slope = (address_one_lon - address_two_lon) / (address_one_y - address_two_y)
    y_intercept = address_one_lon - (y_slope * address_one_y)
    return (x_slope, x_intercept, y_slope, y_intercept)

def convert_between_systems(value, slope, intercept):
    new_value = (slope * value) + intercept
    return new_value

def check_county_using_geocoordinates(coordinate_pair):
    data = fetch_geocoding_data_with_caching(coordinate_pair, True)
    county = data['address']['Subregion']
    return county

def georeference_link_records(link_records, address_pair_dict):
    x_slope, x_intercept, y_slope, y_intercept = find_constants_for_formulas(address_pair_dict)
    georeferenced_link_records = []
    for link_record in link_records:
        georeferenced_link_record = link_record.copy()
        georeferenced_link_record['Latitude'] = convert_between_systems(georeferenced_link_record['PDF X Coordinate'], x_slope, x_intercept)
        georeferenced_link_record['Longitude'] = convert_between_systems(georeferenced_link_record['PDF Y Coordinate'], y_slope, y_intercept)
        coordinate_pair = [georeferenced_link_record['Latitude'], georeferenced_link_record['Longitude']]
        georeferenced_link_record['Current County'] = check_county_using_geocoordinates(coordinate_pair)
        georeferenced_link_records.append(georeferenced_link_record)
    return georeferenced_link_records

def create_link_coordinates_csv(link_dictionaries, index_file_name, output_location='output/'):
    link_coordinates_file_name = index_file_name.replace('.pdf', '') + '_link_coordinates.csv'
    link_coordinates_csv_file = open(output_location + link_coordinates_file_name, 'w', newline='', encoding='utf-8')
    csvwriter = csv.writer(link_coordinates_csv_file)
    headers = ['File Name', 'PDF X Coordinate', 'PDF Y Coordinate']
    csvwriter.writerow(headers)
    for link_dictionary in link_dictionaries:
        csvwriter.writerow([
            link_dictionary['Linked Image PDF Identifier'],
            link_dictionary['PDF X Coordinate'],
            link_dictionary['PDF Y Coordinate']
        ])
    link_coordinates_csv_file.close()

def run_georeferencing_workflow(batch_metadata_file_path, output_name, output_location='output/'):
    print("** Link Georeferencing **")

    # Load data from batch metadata and address pairs files
    batch_metadata_file = open(batch_metadata_file_path, 'r', encoding='utf-8')
    batch_metadata = json.loads(batch_metadata_file.read())
    batch_metadata_file.close()

    index_file_name = batch_metadata['Index Records'][0]['Index File Name']

    addresses_csv_file = open(ADDRESS_PAIRS_FILE_PATH, 'r', newline='', encoding='utf-8-sig')
    csvreader = csv.reader(addresses_csv_file)
    rows = []
    for row in csvreader:
        rows.append(row)
    addresses_csv_file.close()
    headers = rows[0]
    address_pairs = []
    for row in rows[1:]:
        address_pairs.append(misc_functions.create_dictionary_from_row(headers, row))

    pair_index = 0
    for address_pair in address_pairs:
        if address_pair['Index File Name'] == index_file_name:
            batch_address_pair = address_pair
            break
        pair_index += 1
    if pair_index == len(address_pairs):
        print('?? No address pair found for {} ??'.format(index_file_name))

    # Create base link records, write coordinates to CSV, load address pair data, and add georeferencing info
    link_records = create_new_link_records(batch_metadata)
    create_link_coordinates_csv(link_records, index_file_name)

    georeferenced_link_records = georeference_link_records(link_records, batch_address_pair)

    # Write data to file as plain JSON
    georeferenced_links_file = open(output_location + output_name, 'w', encoding='utf-8')
    georeferenced_links_file.write(json.dumps(georeferenced_link_records, indent=4))
    georeferenced_links_file.close()

    return georeferenced_link_records

## Main Program

if __name__=="__main__":
    print("\n** DTE Aerial Batch Processing Script **")
    batch_metadata_file_path = sys.argv[1]
    georeferenced_link_records = run_georeferencing_workflow(batch_metadata_file_path, 'sample_georeferenced_links.json')
