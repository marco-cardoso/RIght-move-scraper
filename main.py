import time
import itertools
import concurrent.futures as cf

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

            outputs = []
            try:
                for i in results:
                    outputs.append(i)
            except cf._base.TimeoutError:
                print("TIMEOUT")

        # We need to add tower_hamlets manually since we're not separating the 
        # district names by syllables
        tower_hamlets = {
            "displayName":"Tower Hamlets (London Borough)",
            "locationIdentifier":"REGION^61417",
            "normalisedSearchTerm":"TOWER HAMLETS LONDON BOROUGH"
        }

        outputs.append(tower_hamlets)
        database.insert_district(tower_hamlets)
        
    return outputs


def get_properties_urls(districts : list) -> list:
    """
    Since there's no way to get the attributes of the properties directly trough a JSON document,
    It's necessary to iterate over the main pages and save all of the HTML anchor hrefs to
    process then later
    :param districts: List with districts represented by dictionaries
    :return: A list with all the obtained properties urls
    """

    # For security reasons, after each main page iteration the results are saved in DB.
    # If something happens this instruction is going to get the last processed index.
    last_processed_element = database.get_last_processed_index()

    initial_index = last_processed_element[0]['index'] + 24 if len(last_processed_element) > 0 else 0

    # The website has setted this value as default
    frequency = 24

    # Iterating though the main pages
    for index in range(initial_index, 985, frequency):

        # It prevents the script to raise the TimeoutError exception from the lack
        # of internet connection
        while True:
            try:

                get_district_links(district)

            except TimeoutError:
                print("Timeout error, trying again !")
            finally:
                break

    stored_links = database.get_stored_links()
    stored_links = set(itertools.chain.from_iterable([store_obj['links'] for store_obj in stored_links]))
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
    
    districts = get_district_codes()
    
    print("Getting the urls...")
    properties_links = get_properties_urls(districts)

    print(properties_links)
    print("Getting the properties details...")
    save_properties_informations(properties_links)


if __name__ == "__main__":
    scrap()