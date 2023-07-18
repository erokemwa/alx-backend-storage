#!/usr/bin/env python3
""" MongoDB Operations with Python using pymongo """


import pymongo


def list_all(mongo_collection):
    """ List all documents in Python """
    if mongo_collection is None:
        return []
    docs = mongo_collection.find()
    return [doc for doc in docs]
