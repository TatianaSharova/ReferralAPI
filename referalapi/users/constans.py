import os

from dotenv import load_dotenv

load_dotenv()

HUNTER_API_KEY = os.getenv('HUNTER_API_KEY')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

USER_MAX_LENGTH = 20
EMAIL_LENGTH = 30
CODE_MAX_LENGTH = 10
