from configs import database_host, database_name, database_port

from pymongo import MongoClient

class Database():

    def __init__(self) -> None:

        self.client = MongoClient(database_host, database_port)
        self.collection = self.client[database_name]['properties']

    def insert_property(self, property : dict):
        self.collection.insert(property)