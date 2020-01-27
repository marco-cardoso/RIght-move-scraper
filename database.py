from configs import database_host, database_name, database_port

from pymongo import MongoClient, DESCENDING

class Database():

    def __init__(self) -> None:

        self.client = MongoClient(database_host, database_port)

        database = self.client[database_name]

        self.properties = database['properties']
        self.links = database['links']
        self.districts = database['districts']
        self.errors = database["errors"]
        

    def insert_property(self, property : dict):
        self.properties.insert(property)
        
    def insert_district(self, district : dict):
        self.districts.insert(district)

    def save_error(self, link : str):
        self.errors.insert({
            'link' : link
        })
        
    def save_processed_links(self, links : dict):
        self.links.insert(links)

    def get_stored_links(self) -> list:
        return list(self.links.find({}, {"links" : 1}))

    def get_last_processed_index(self) -> list:
        return list(self.links.find({}).sort([("index", DESCENDING)]).limit(1))
    
    def get_districts(self) -> list:
        return list(self.districts.find({}))