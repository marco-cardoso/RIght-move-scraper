import concurrent.futures as cf
from functools import partial

from property_anomaly_detector.database import Database
from property_anomaly_detector.scraper.rightmove.rightmove_requests import Requests

database = Database("rightmove")
requests = Requests()


def scrap():
    """

    The main goal of this method is to download all UK properties available in
    the website. It takes a lof of time !

    First, each UK district has a specific number in the website. It starts from 0
    and ends in 2926. A Few numbers are not related to any district at all.

    Each district number has N properties that are displayed in M listing pages. Every
    listing page and property has an unique URL. Just the district number and page index
    are necessary to generate the listing page URL. Meanwhile, it's not possible to
    generate the property URL. The only way to get it is by iterating through all
    listing pages and parsing the HTML looking for the anchors with them.

    This method iterates through the district numbers and attempts to download the first
    listing page for a given district number. If the response is a blank page then is
    because the given number is not related to any UK districts (Exception case). Otherwise
    it will get the name of the UK district and the amount of properties for the particular district
    number from the header title. This gives the capability to automatically calculate the amount of page indexes.
    By default each listing page has 24 properties. Another loop is necessary to iterate through
    the page indexes of the district. In each iteration of the page index loop the unique properties
    URLs are collected and appended to a set. After all the iterations of the page index loop
    a pool of threads is started to get and save in the database all the properties details.

    """

    # The script does not save the processing state yet. In order
    # to avoid duplicates it's necessary to remove the districts
    database.remove_districts()
    for district_nb in range(0, 2927):

        # Get the first page properties
        amt_properties_per_page = 24
        index = 0

        soup = requests.get_properties(district_nb, index)

        anchors = soup.find_all("a", {"class": "propertyCard-link"})
        unique_links = set([a.attrs['href'] for a in anchors])

        # This try-except is necessary because for some reason some district numbers are not related to
        # any UK district at all
        try:
            district = soup.find("h1", {"data-test": "header-title"}).text.split(",")[0].split()[-1]
        except AttributeError:
            print(f"{district_nb} has no districts ! Skipping ... ")
            continue

        amt_district_properties = soup.find("span", {"class": "searchHeader-resultCount"}).text.replace(",", "")

        # save the district properties
        database.insert_district({
            'district_number': district_nb,
            'district_code': district,
            'district_properties_amt': amt_district_properties
        })

        # If the district has no properties there's no reason to keep the iteration
        print(f" DISTRICT {district_nb} - {district} | {amt_district_properties} properties available")
        if int(amt_district_properties) == 0:
            continue

        # With the amount of district properties is possible to calculate
        # the amount of page indexes
        idxs = range(
            index + amt_properties_per_page,
            int(amt_district_properties) + amt_properties_per_page,
            amt_properties_per_page
        )

        for idx in idxs:

            soup = requests.get_properties(district_nb, idx)

            # Each listing page has N properties. This parses the anchors from the
            # specific page and append to the set unique_links
            anchors = soup.find_all("a", {"class": "propertyCard-link"})
            links = set([a.attrs['href'] for a in anchors])
            unique_links = unique_links.union(links)

        # Remove null values
        try:
            unique_links.remove("")
        except KeyError:
            # It means the set has no null values
            pass

        print(f" DISTRICT {district_nb} - {district} | {len(unique_links)} urls")

        print(f"{district_nb} - {district} - Downloading the properties details...")
        save_properties_informations(list(unique_links), district)
        print(f"{district_nb} - {district} - Downloading the properties details...DONE")


def save_properties_informations(paths: list, district: str):
    """
    It gets and stores the properties details of the given paths.

    :param paths: A String list with the paths of the properties
    :param district: A String with the UK district name
    """
    with cf.ThreadPoolExecutor(max_workers=50) as executor:
        f = partial(requests.get_property_information, district, )
        results = executor.map(f, paths)

        outputs = []
        try:
            for i in results:
                outputs.append(i)
        except cf._base.TimeoutError:
            print("TIMEOUT")


if __name__ == "__main__":
    scrap()
