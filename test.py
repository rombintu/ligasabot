from tools import json_validate
from pymongo import MongoClient
import pymongo
import os
from main import InMemory

def get_database():
    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    CONNECTION_STRING = "mongodb://mongoadmin:secret@192.168.213.224:27017/"

    # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    
    client = MongoClient(CONNECTION_STRING)
    db = client.test
    collection = db["test_coll"]
   
    
    for el in collection.find():
        print(el)

    
    

if __name__ == "__main__":
    # json_validate.json_concat(b'{\n\t"message": "Hello"\n}\n')
    # mem = InMemory()
    # mem.db = MongoClient(os.getenv("CONNECTION_STRING")).bot
    # mem.concat_study(b'{"content": "content2", "url": "url2.com"}')
    # mem.refresh_study()
    # print(mem.study)
    print(json_validate.validate(open("variants.json", "rb").read().decode("utf-8")))
    # get_database()
    