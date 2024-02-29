from flask import current_app as app
from ..app import db_name
from pymongo import MongoClient
from datetime import datetime

# Connect to MongoDB
database = app.mongo[db_name]

quizzes_schema = {
    'profileId': {'type': 'string', 'required': True},
    'jobId': {'type': 'string', 'required': True},
    'randomSlug': {'type': 'string', 'required': True},
    'questions': {'type': 'array', 'items': 'dict', 'required': True},
    'userAnswers': {'type': 'array', 'items': 'int', 'required': True},
    'score': {'type': 'int', 'default': None}
}

database.create_collection('quizzes', validator=quizzes_schema)
