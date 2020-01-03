from database import Database

import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


def save_urls(links: list):
    now = datetime.now().strftime("%Y_%M_%d_%h:%m:%s")
    filename = "properties_url_" + now + ".txt"

    print("Saving the URLs at " + filename)

    with open(filename, "w") as file:
        [file.write(link + "\n") for link in links]


def clean_string(text: str) -> str:
    """
    It removes special characters from the string. Such as : \t \n \r etc...
    :param text:
    :return: The formatted text
    """
    return ' '.join(text.split())


def get_properties_urls() -> list:
    links = []
    # 985

    for index in tqdm(range(0, 48, 24)):
        url = "https://www.rightmove.co.uk/property-to-rent/find.html?" \
              "locationIdentifier=REGION%5E87490&" \
              f"index={index}&" \
              "propertyTypes=&" \
              "includeLetAgreed=true&" \
              "mustHave=&" \
              "dontShow=&" \
              "furnishTypes=&" \
              "keywords="

        # print("Getting data from " + url)
        response = requests.get(url)

        soup = BeautifulSoup(response.text, features="html.parser")

        anchors = soup.find_all("a", {"class": "propertyCard-link"})

        links.extend(
            set([a.attrs['href'] for a in anchors])  # Getting the strings with the links
        )

        time.sleep(0.5)

    save_urls(links)

    return links


def get_html_value(element, index) -> str:
    """
    It gets the value from the TD for the given TR
    :param element: The Beautiful Soup object with the TR
    :param index: The column index of the element, 0 = title, 1 = value.
    :return: A string with the letting information
    """
    try:
        return clean_string(element.findChildren("td")[index].text)
    except IndexError:
        return None


def convert_station_distance(element):
    """
    The string distance has the format ( %f.%f mi ), in order to extract it
    this method is applying the regex method 'findall' and then casting to
    float value
    :param element: The Beautiful Soup object with the small
    :return: A float value with the distance in mi
    """
    float(
        re.findall(
            "(([-0-9_\.]+)\w+)",
            clean_string(element)
        )[0][0]
    )


def save_properties_informations(paths: list):
    database = Database()

    for path in tqdm(paths):
        url = "https://www.rightmove.co.uk" + path

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

        key_features_list = agent_content_div.findChildren("ul")[0].findChildren("li")
        key_features = [key_feature.text for key_feature in key_features_list]
        description = agent_content_div.find_next("p", {"itemprop": "description"}).text

        # Coordinates
        location_image_url = soup.find("a", {"class": "js-ga-minimap"}).findChildren("img")[0].attrs['src']
        latitude = re.findall("latitude=([-0-9_\.]+)\w+", location_image_url)[0]
        longitude = re.findall("longitude=([-0-9_\.]+)\w+", location_image_url)[0]

        stations_li = soup.find("ul", {"class": "stations-list"}).findChildren("li")
        stations = [
            {
                'name': clean_string(station_li.findChildren("span")[0].text),
                'distance': convert_station_distance(station_li.findChildren("small")[0].text)
            }
            for station_li in stations_li
        ]

        document = {
            'title': title,
            'address': address,
            'price': price,
            'letting': letting_info,
            'key_features': key_features,
            'description': description,
            'latitude': latitude,
            'longitude': longitude,
            'stations': stations,
            "amt_stations" : len(stations)
        }

        database.insert_property(document)

        time.sleep(0.5)

def scrap():
    print("Getting the urls...")
    properties_links = get_properties_urls()

    print("Getting the properties details...")
    save_properties_informations(properties_links)


if __name__ == "__main__":
    scrap()
