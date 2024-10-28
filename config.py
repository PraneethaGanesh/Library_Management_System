# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'library_secret')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///library.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
