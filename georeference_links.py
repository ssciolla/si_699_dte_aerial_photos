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

ARCGIS_CACHE_FILE_NAME = 'arcgis_geocoding_cache.json'
ADDRESS_PAIRS_FILE_PATH = 'input/address_pairs.csv'
global HIT_API_YET
HIT_API_YET = False

## Caching

# Setting up geocoding caching dictionary.
try:
    file_open = open(ARCGIS_CACHE_FILE_NAME, "r")
    json_string = file_open.read()
    CACHE_DICTION = json.loads(json_string)
    file_open.close()
except:
    CACHE_DICTION = {}

# Function either geocodes (converts street address to coordinates) or reverse geocodes (converts coordinates to street address).
# When reverse == False, input_data should be a single-line address (string) that is used to query a set of coordinates.
# When reverse == True, input_data should be a longitude latitude pair (tuple or list) that is used to look up a street address (used here to find county name).
def fetch_geocoding_data_with_caching(input_data, reverse=False):
    print(input_data)
    global HIT_API_YET
    if reverse == True:
        input_string = str(input_data[0]) + ', ' + str(input_data[1]) #convert lat-lon pair into string for ArcGIS API
    else:
        input_string = input_data
    if input_string in CACHE_DICTION:
        # print("** Pulling data from cache **")
        return CACHE_DICTION[input_string]
    else:
        print("** Fetching new data from API **")
        if not HIT_API_YET:
            gis = GIS()
            HIT_API_YET = True
        if reverse == False:
            data = geocode(input_string) #geocode() argument is a string
        else:
            data = reverse_geocode(input_data) #reverse_geocode() argument is a list
        CACHE_DICTION[input_string] = data
        cache_file_open = open(ARCGIS_CACHE_FILE_NAME, "w")
        cache_file_open.write(json.dumps(CACHE_DICTION, indent=4))
        cache_file_open.close()
        return data

## General Functions

# Standardize point on index PDF link box to correspond to rough real-world map location. Argument: PDF coordinates defining link box.
def find_mid_left_point(link_coords):
    x_one = link_coords[0]
    x_two = link_coords[2]
    y_one = link_coords[1]
    y_two = link_coords[3]
    x_value = x_one
    y_value = (y_two - y_one)/2 + y_one
    return (x_value, y_value)

# Extract photo PDF metadata (photo identifier, PDF object number, PDF x and y coordinates) from batch_metadata, store in list of intermediary dictionaries
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
    longitude = geocoding_dict['location']['x']
    latitude = geocoding_dict['location']['y']
    return longitude, latitude

# Function to calculate coefficient and constant for coordinate conversion formula.
# Takes as input dictionary with two street intersection information pairs (street address, PDF coordinates) pulled from address pair CSV file
def find_constants_for_formulas(address_pair_dict):
    # for each address, reverse geocode address to find real-world coordinaes
    address_one = address_pair_dict['Address 1']
    address_one_lon, address_one_lat = pull_lat_and_lon(fetch_geocoding_data_with_caching(address_one)[0])
    address_one_x = float(address_pair_dict['Address 1 GIMP X Coordinate'])
    address_one_y = float(address_pair_dict['Address 1 GIMP Y Coordinate'])

    # repeat reverse geocoding to find real-world coordinates of second address
    address_two = address_pair_dict['Address 2']
    address_two_lon, address_two_lat = pull_lat_and_lon(fetch_geocoding_data_with_caching(address_two)[0])
    address_two_x = float(address_pair_dict['Address 2 GIMP X Coordinate'])
    address_two_y = float(address_pair_dict['Address 2 GIMP Y Coordinate'])

    # use PDF coordinates and real-world coordinates to solve system of equations to find conversion formula for each dimension
    x_slope = (address_one_lon - address_two_lon) / (address_one_x - address_two_x)
    x_intercept = address_one_lon - (x_slope * address_one_x)

    # repeat equaltion solving for y dimension
    y_slope = (address_one_lat - address_two_lat) / (address_one_y - address_two_y)
    y_intercept = address_one_lat - (y_slope * address_one_y)

    # return equation coefficients and constants to use in converting link PDF coordinates to image real-world coordinates
    return (x_slope, x_intercept, y_slope, y_intercept)

# Implements coordinate conversion formula on a single value, taking target value and formula constants as input
def convert_between_systems(value, slope, intercept):
    new_value = (slope * value) + intercept
    return new_value

# Reverse geocode input coordinates (pair or list), extract county name from result, and return county name (string).
def check_county_using_geocoordinates(coordinate_pair):
    data = fetch_geocoding_data_with_caching(coordinate_pair, reverse=True)
    county = data['address']['Subregion']
    return county

# Calculates real-world coordinates of images using link records and address pair data
def georeference_link_records(link_records, address_pair_dict):
    constants = find_constants_for_formulas(address_pair_dict)
    constant_dict = {
        'X Slope': constants[0],
        'X Intercept': constants[1],
        'Y Slope': constants[2],
        'Y Intercept': constants[3]
    }

    # calculate real-world coordinates, query ArcGIS API for county, return data
    georeferenced_link_records = []
    for link_record in link_records:
        georeferenced_link_record = link_record.copy()
        georeferenced_link_record['Longitude'] = convert_between_systems(georeferenced_link_record['PDF X Coordinate'], constant_dict['X Slope'], constant_dict['X Intercept'])
        georeferenced_link_record['Latitude'] = convert_between_systems(georeferenced_link_record['PDF Y Coordinate'], constant_dict['Y Slope'], constant_dict['Y Intercept'])
        coordinate_pair = [georeferenced_link_record['Longitude'], georeferenced_link_record['Latitude']]
        georeferenced_link_record['Current County'] = check_county_using_geocoordinates(coordinate_pair)
        georeferenced_link_records.append(georeferenced_link_record)
    return georeferenced_link_records, constant_dict

# Performs georeferencing workflow on all extracted links from one county index in one year (e.g. all Macomb 1961 images)
def run_georeferencing_workflow(batch_metadata_file_path, output_name, output_location='output/'):
    print('\n** Link Georeferencing **')

    # Load data from batch metadata file
    batch_metadata_file = open(batch_metadata_file_path, 'r', encoding='utf-8')
    batch_metadata = json.loads(batch_metadata_file.read())
    batch_metadata_file.close()

    # Load data from address pairs file
    address_pairs = misc_functions.load_csv_data(ADDRESS_PAIRS_FILE_PATH)

    index_file_name = batch_metadata['Index Records'][0]['Index File Name']

    # Find data in address_pairs associated with the index file name
    pair_index = 0
    for address_pair in address_pairs:
        if address_pair['Index File Name'] == index_file_name:
            current_index_address_pair = address_pair
            break
        pair_index += 1
    if pair_index == len(address_pairs):
        print('?? No address pair found for {} ??'.format(index_file_name))

    # Create link records to use in georeferencing
    link_records = create_new_link_records(batch_metadata)

    # Store georeferencing data and metadata (address pair used, formula constants)
    georeferenced_link_records, constants = georeference_link_records(link_records, current_index_address_pair)
    georeferenced_link_data = {}
    georeferenced_link_data['Georeferencing Metadata'] = {
        'Address Pair Data': current_index_address_pair,
        'Constants': constants,
    }
    georeferenced_link_data['Georeferenced Link Records'] = georeferenced_link_records

    # Write georeferencing data to file as JSON
    georeferenced_links_file = open(output_location + output_name, 'w', encoding='utf-8')
    georeferenced_links_file.write(json.dumps(georeferenced_link_data, indent=4))
    georeferenced_links_file.close()

    return georeferenced_link_data

## Main Program

if __name__=="__main__":
    print("\n** DTE Aerial Batch Processing Script **")
    batch_metadata_file_path = sys.argv[1]
    georeferenced_link_records = run_georeferencing_workflow(batch_metadata_file_path, 'sample_georeferenced_links.json')
