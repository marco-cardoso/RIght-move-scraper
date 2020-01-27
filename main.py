import time
import itertools
import concurrent.futures as cf

import numpy as np
from tqdm import tqdm

from database import Database
from req import Requests

database = Database()
requests = Requests()

def get_district_codes():
    
    outputs = database.get_districts()

    if len(outputs) == 0:
        districts = np.genfromtxt("district_names.csv", delimiter=",", dtype=str, usecols=[1])
        with cf.ThreadPoolExecutor(max_workers=50) as executor:
            results = executor.map(requests.get_district_code, districts)
            
        # We need to add tower_hamlets manually since we're not separating the 
        # district names by syllables
        tower_hamlets = {
            "displayName":"Tower Hamlets (London Borough)",
            "locationIdentifier":"61417",
            "normalisedSearchTerm":"TOWER HAMLETS LONDON BOROUGH"
        }

        database.insert_district(tower_hamlets)
        outputs = database.get_districts()
        
    return outputs

def save_properties_urls(district : str):
    print("Getting the urls of " + district['locationIdentifier'])
        
    
    # The website has setted this value as default
    frequency = 24
    
    index = frequency
    
    
    # Iterating though the main pages
    while True:

            try:

                links = requests.get_district_links(index, district['locationIdentifier'])
                print(links)
                if len(links) == 0:
                    print("leaving")
                    break
                
                index += frequency
                

            except TimeoutError:
                print("Timeout error, trying again !")


def get_properties_urls(districts : list) -> list:
    """
    Since there's no way to get the attributes of the properties directly trough a JSON document,
    It's necessary to iterate over the main pages and save all of the HTML anchor hrefs to
    process then later
    :param districts: List with districts represented by dictionaries
    :return: A list with all the obtained properties urls
    """

    with cf.ThreadPoolExecutor(max_workers=50) as executor:
        results = executor.map(save_properties_urls, districts)

        outputs = []
        try:
            for i in results:
                outputs.append(i)
        except cf._base.TimeoutError:
            print("TIMEOUT")


    stored_links = database.get_stored_links()
    
    # It gets a set from a list of dictionaries attribute
    stored_links = set(itertools.chain.from_iterable([store_obj['links'] for store_obj in stored_links]))
    
    # Removing empty strings
    stored_links -= {""}
    
    return stored_links


def save_properties_informations(paths: list):
    
    with cf.ThreadPoolExecutor(max_workers=50) as executor:
        results = executor.map(requests.get_property_information, paths)
        
        outputs = []
        try:
            for i in results:
                outputs.append(i)
        except cf._base.TimeoutError:
            print("TIMEOUT")            


def scrap():
    
    print("Getting the district codes...")
    districts = get_district_codes()

    print("Getting the urls...")
    # properties_links = get_properties_urls(districts)
    stored_links = database.get_stored_links()
    stored_links = set(itertools.chain.from_iterable([store_obj['links'] for store_obj in stored_links])) 
    
    # Removing empty strings
    stored_links -= {""}
    
    print(stored_links)
    print("Getting the properties details...")
    save_properties_informations(stored_links)


if __name__ == "__main__":
    scrap()