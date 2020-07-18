from os import path

import re
import pandas as pd

DATASETS_FOLDER_PATH = path.join("..", "datasets", "uk_postcodes")


def clean_string(text: str) -> str:
    """
    It removes special characters from the string. Such as : \t \n \r etc...
    :param text: A string with the text to be formatted
    :return: The formatted text
    """
    return ' '.join(text.split())


def get_uk_districts():
    postcodes_path = path.join(DATASETS_FOLDER_PATH, "postcodes.csv")
    postcodes_df = pd.read_csv(postcodes_path)

    postcodes = postcodes_df['Postcode area'].values

    districts_df = pd.concat(
        [*map(
            lambda postcode:
            pd.read_csv(path.join(DATASETS_FOLDER_PATH, f"{postcode}.csv")), postcodes)
         ]
    )

    districts = districts_df['Postcode district'].values
    return districts
