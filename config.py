import os

class Config:
    SECRET_KEY = 'secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///helpdesk.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False