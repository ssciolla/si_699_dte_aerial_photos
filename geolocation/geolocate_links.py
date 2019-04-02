# DTE Aerial Photo Collection curation project
# Workflow for converting PDF Coordinates to geolocations
# Garrett Morton, Sam Sciolla
# SI 699

# Written and tested using Python 3.7.0

from arcgis import GIS
from arcgis.geocoding import geocode

import json
import csv

CACHE_FILE_NAME = 'arcgis_geocoding_cache.json'

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

def fetch_geocoding_data_with_caching(unique_address):
    global hit_api_yet
    if unique_address in CACHE_DICTION:
        print("** Pulling data from cache **")
        return CACHE_DICTION[unique_address]
    else:
        print("** Fetching new data from API **")
        data = geocode(unique_address)
        CACHE_DICTION[unique_address] = data
        cache_file_open = open(CACHE_FILE_NAME, "w")
        cache_file_open.write(json.dumps(CACHE_DICTION, indent=4))
        cache_file_open.close()
        return data

## General Functions

# Takes a row from a CSV and makes it into a Python dictionary using the CSVs headers as keys
def create_dictionary_from_row(headers, csv_row):
    work_dict = {}
    for field in headers:
        work_dict[field.strip()] = csv_row[headers.index(field)]
    return work_dict

def find_mid_left_point(link_coords):
    x_one = link_coords[0]
    x_two = link_coords[2]
    y_one = link_coords[1]
    y_two = link_coords[3]

    x_value = x_one
    y_value = (y_two - y_one)/2 + y_one

    return (x_value, y_value)

def pull_lat_and_lon(geocoding_dict):
    latitude = geocoding_dict['location']['x']
    longitude = geocoding_dict['location']['y']
    return latitude, longitude

# May want to consider changing variables names to address_one and address_two
def find_constants_for_formulas(address_pair_dict):
    upper_left_address = address_pair_dict['Upper Left Address']
    upper_left_lat, upper_left_lon = pull_lat_and_lon(fetch_geocoding_data_with_caching(upper_left_address)[0])
    upper_left_x = float(address_pair_dict['Upper Left GIMP X Coordinate'])
    upper_left_y = float(address_pair_dict['Upper Left GIMP Y Coordinate'])

    bottom_right_address = address_pair_dict['Bottom Right Address']
    bottom_right_lat, bottom_right_lon = pull_lat_and_lon(fetch_geocoding_data_with_caching(bottom_right_address)[0])
    bottom_right_x = float(address_pair_dict['Bottom Right GIMP X Coordinate'])
    bottom_right_y = float(address_pair_dict['Bottom Right GIMP Y Coordinate'])

    x_slope = (upper_left_lat - bottom_right_lat) / (upper_left_x - bottom_right_x)
    x_intercept = upper_left_lat - (x_slope * upper_left_x)

    y_slope = (upper_left_lon - bottom_right_lon) / (upper_left_y - bottom_right_y)
    y_intercept = upper_left_lon - (y_slope * upper_left_y)

    return (x_slope, x_intercept, y_slope, y_intercept)

def convert_between_systems(value, slope, intercept):
    new_value = (slope * value) + intercept
    return new_value

def geolocate_links_from_index(link_location_dicts, address_pair_dict):
    x_slope, x_intercept, y_slope, y_intercept = find_constants_for_formulas(address_pair_dict)
    geolocated_link_dicts = []
    for link_location_dict in link_location_dicts:
        geolocated_link_dict = link_location_dict.copy()
        geolocated_link_dict['Latitude'] = convert_between_systems(geolocated_link_dict['PDF X Coordinate'], x_slope, x_intercept)
        geolocated_link_dict['Longitude'] = convert_between_systems(geolocated_link_dict['PDF Y Coordinate'], y_slope, y_intercept)
        geolocated_link_dicts.append(geolocated_link_dict)
    return geolocated_link_dicts

def crosswalk_to_geojson(entity_dict_list):
    geojson_dicts = []
    for entity_dict in entity_dict_list:
        geojson_dict = {}
        geojson_dict['type'] = 'Feature'
        geojson_dict['geometry'] = {}
        geojson_dict['geometry']['type'] = 'Point'
        geojson_dict['geometry']['coordinates'] = [entity_dict['Latitude'], entity_dict['Longitude']]
        geojson_dict['properties'] = {}
        geojson_dict['properties']['name'] = entity_dict['Linked Image PDF Identifier']
        geojson_dicts.append(geojson_dict)
    geojson_wrapper = {}
    geojson_wrapper['type'] = 'FeatureCollection'
    geojson_wrapper['features'] = geojson_dicts
    return geojson_wrapper

## Main Program

batch_file = open('sample_batch_metadata.json', 'r', encoding='utf-8')
sample_batch_metadata = json.loads(batch_file.read())
batch_file.close()

links = sample_batch_metadata['Index Records'][0]['Links']
link_location_dicts = []
for link in links:
    link_location_dict = {}
    link_location_dict['Linked Image PDF Identifier'] = link['Linked Image File Name'].replace('.pdf', '')
    x_value, y_value = find_mid_left_point(link['Link Coordinates'])
    link_location_dict['PDF X Coordinate'] = x_value
    link_location_dict['PDF Y Coordinate'] = y_value
    link_location_dicts.append(link_location_dict)

link_coordinates_csv_file = open("link_coordinates.csv", "w", newline='', encoding='utf-8')
csvwriter = csv.writer(link_coordinates_csv_file)
headers = ['File Name', 'PDF X Coordinate', 'PDF Y Coordinate']
csvwriter.writerow(headers)
for link_location_dict in link_location_dicts:
    csvwriter.writerow([
        link_location_dict['Linked Image PDF Identifier'],
        link_location_dict['PDF X Coordinate'],
        link_location_dict['PDF Y Coordinate']
    ])
link_coordinates_csv_file.close()

addresses_csv_file = open('address_pairs.csv', 'r', newline='', encoding='utf-8-sig')
csvreader = csv.reader(addresses_csv_file)
rows = []
for row in csvreader:
    rows.append(row)
headers = rows[0]
address_pairs = []
for row in rows[1:]:
    address_pairs.append(create_dictionary_from_row(headers, row))

geolocated_link_dicts = geolocate_links_from_index(link_location_dicts, address_pairs[0])

geolocated_links_file = open('geolocated_links.json', 'w', encoding='utf-8')
geolocated_links_file.write(json.dumps(geolocated_link_dicts, indent=4))
geolocated_links_file.close()

geojson_feature_collection = crosswalk_to_geojson(geolocated_link_dicts)

geojson_file = open('macomb_1961_index.geojson', 'w', encoding='utf-8')
geojson_file.write(json.dumps(geojson_feature_collection, indent=4))
geojson_file.close()
