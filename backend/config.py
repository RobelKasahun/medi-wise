# module that lets you interact with the operating system
import os
# for loading key-value pairs from a .env
from dotenv import load_dotenv

# Load environment variables from .env
loaded = load_dotenv()

class Config:
    # Get the Database URL
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    # stop tracking every changes in objects
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Get Secret Key
    SECRET_KEY=os.getenv('SECRET_KEY')