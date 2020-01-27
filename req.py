import time
import re
from datetime import datetime

import requests
import numpy as np
from bs4 import BeautifulSoup

from database import Database
from utils import *

database = Database()

def sleep(function):
    def wrapper(*args, **kwargs):
        result = function(*args, **kwargs)
        time.sleep(0.5)
        return result
    
    return wrapper

class Requests():
    
    def __init__(self):
        super().__init__()
        self.main_url = "https://www.rightmove.co.uk"
        self.dst_code_url = "https://www.rightmove.co.uk/typeAhead/uknostreet/"
    
    @sleep
    def get_district_code(self, district : str) -> dict:

        district = district.upper().replace(" ","")
        splitted = [ district[i:i+2] +"/"  for i in range(0, len(district), 2) ]
        final_url = self.dst_code_url + str().join(splitted)

        response = requests.get(final_url).json()['typeAheadLocations']

        location_identifier = next(filter(
            lambda dictionary : 
            dictionary['normalisedSearchTerm'].endswith("BOROUGH")
            or
            dictionary['normalisedSearchTerm'].endswith("CITY OF"),
            response
        ))
        
        # Removing the string REGION^ from the text
        location_identifier['locationIdentifier'] = location_identifier['locationIdentifier'].split("^")[1]

        database.insert_district(location_identifier)
        
    @sleep
    def get_property_information(self, path: str):
        url = self.main_url + path

        # This try-exception is necessary since some observations presented
        # a few errors. 7/27411
        try:
           
            print("Getting the data from " + url + " ...")

            response = requests.get(url)

            soup = BeautifulSoup(response.text, features="html.parser")

            ##### Attributes ####

            # Header attributes
            property_rent_and_price_div = soup.find("div", {"class": "property-header-bedroom-and-price"})

            title = clean_string(property_rent_and_price_div.findChildren("h1")[0].text)

            address = clean_string(property_rent_and_price_div.findChildren("address")[0].text)
            price = clean_string(soup.find("p", {"id": "propertyHeaderPrice"}).findChildren("strong")[0].text)

            # Letting section attributes / Optional attributes
            letting_div = soup.find("div", {"id": "lettingInformation"})
            letting_table_rows = letting_div.find_next("tbody").find_all_next("tr")

            letting_info = {get_html_value(row, 0): get_html_value(row, 1) for row in letting_table_rows}

            # Agent content attributes
            agent_content_div = soup.find("div", {"class": "agent-content"})

            key_features_list = agent_content_div.findChildren("ul")

            if len(key_features_list) > 0:
                key_features = [key_feature.text for key_feature in key_features_list[0].findChildren("li")]
            else:
                key_features = []

            description = agent_content_div.find_next("p", {"itemprop": "description"}).text

            # Coordinates
            location_image_url = soup.find("a", {"class": "js-ga-minimap"}).findChildren("img")[0].attrs['src']
            latitude = re.findall("latitude=([-0-9_\.]+)\w+", location_image_url)[0]
            longitude = re.findall("longitude=([-0-9_\.]+)\w+", location_image_url)[0]

            stations = []
            stations_li = soup.find("ul", {"class": "stations-list"})

            if stations_li is not None:

                stations_li = stations_li.findChildren("li")
                stations = [
                    {
                        'name': clean_string(station_li.findChildren("span")[0].text),
                        'distance': convert_station_distance(station_li.findChildren("small")[0].text)
                    }
                    for station_li in stations_li
                ]


            document = {
                'url' : url,
                'title': title,
                'address': address,
                'price': price,
                'letting': letting_info,
                'key_features': key_features,
                'description': description,
                'latitude': latitude,
                'longitude': longitude,
                'stations': stations,
                "amt_stations": len(stations)
            }

            database.insert_property(document)
            print("Getting the data from " + url + " ...DONE")
        except:
            print("Error " + url)
            database.save_error(url)
        
    @sleep
    def get_district_links(self, index : int, district : str):
        
        district = district.replace("^","%")
        url = "https://www.rightmove.co.uk/property-to-rent/find.html?" \
                      f"locationIdentifier=REGION%5E{district}&" \
                      f"index={index}&" \
                      "propertyTypes=&" \
                      "includeLetAgreed=true&" \
                      "mustHave=&" \
                      "dontShow=&" \
                      "furnishTypes=&" \
                      "keywords="

        response = requests.get(url)
        print(url)
        
        soup = BeautifulSoup(response.text, features="html.parser")

        anchors = soup.find_all("a", {"class": "propertyCard-link"})
        unique_links = set([a.attrs['href'] for a in anchors])
        
        if len(unique_links) > 0:
            
            database.save_processed_links(
                {
                    'index': index,
                    'created_at': datetime.now(),
                    'links': list(unique_links)
                }
            )
            print("saved")
            return unique_links
            
        return unique_links