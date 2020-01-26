import re

def clean_string(text: str) -> str:
    """
    It removes special characters from the string. Such as : \t \n \r etc...
    :param text:
    :return: The formatted text
    """
    return ' '.join(text.split())


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
    

def convert_station_distance(element) -> float:
    """
    The string distance has the format ( %f.%f mi ), in order to extract
    only the numerical value this method is applying the regex method
    'findall' and then casting to float value
    :param element: The Beautiful Soup object with the small html node
    :return: A float value with the distance in mi
    """
    return float(
        re.findall(
            "(([-0-9_\.]+)\w+)",
            clean_string(element)
        )[0][0]
    )