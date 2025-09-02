import os
from os import getenv

import pytest
from pymongo import MongoClient


@pytest.fixture(autouse=True, scope="function")
def clean_mongo():
    client = MongoClient(os.getenv('MONGODB_TEST_NAME'), 27017, username=os.getenv('MONGODB_TEST_NAME'),
                         password=os.getenv('MONGODB_TEST_PASSWORD'), authSource='admin')
    db = client[os.getenv('MONGODB_TEST_NAME')]
    yield
    for collection in db.list_collection_names():
        db[collection].delete_many({})
