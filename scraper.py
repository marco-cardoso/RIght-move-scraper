import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


def save_urls(links : list):

    now = datetime.now().strftime("%Y_%M_%d_%h:%m:%s")
    filename = "properties_url_" + now + ".txt"

    print("Saving the URLs at " + filename)

    with open(filename, "w") as file:
        [ file.write(link + "\n") for link in links]

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

def clean_string(text : str) -> str:
    """
    It removes special characters from the string. Such as : \t \n \r etc...
    :param text:
    :return: The formatted text
    """
    return ' '.join(text.split())

def save_properties_informations(paths : list):

    for path in tqdm(paths):

        url = "https://www.rightmove.co.uk" + path

        response = requests.get(url)

        soup = BeautifulSoup(response.text)

        # Attributes

        # Header attributes
        property_rent_and_price_div = soup.find("div", {"class" : "property-header-bedroom-and-price"})

        title = clean_string(property_rent_and_price_div.findChildren("h1")[0].text)
        address = clean_string(property_rent_and_price_div.findChildren("address")[0].text)
        price = clean_string(soup.find("p", {"id" : "propertyHeaderPrice"}).findChildren("strong")[0].text)

        # Letting section attributes
        letting_div = soup.find("div", { "id" : "lettingInformation" })
        letting_table_rows = letting_div.find_next("tbody").find_all_next("tr")

        # TODO optional attributes, meaning they can assume null values. Fix it !
        date_available = letting_table_rows[0].findChildren("td")[1].text
        furnishing = letting_table_rows[1].findChildren("td")[1].text
        letting_type = letting_table_rows[2].findChildren("td")[1].text
        rightmove_reduced = letting_table_rows[3].findChildren("td")[1].text


        # TODO Key features= list
        # TODO full description = string
        # TODO latitude
        # TODO longitude

    return None

def scrap():

    print("Getting the urls...")
    properties_links = get_properties_urls()

    print("Getting the properties details...")
    save_properties_informations(properties_links)



if __name__ == "__main__":
    scrap()