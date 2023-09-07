import os

from dotenv import load_dotenv

load_dotenv()

SEARCH_DB_URI = os.getenv("SEARCH_DB_URI", "http://localhost:4080")
SEARCH_DB_USER = os.getenv("SEARCH_DB_USER", "admin")
SEARCH_DB_PASSWORD = os.getenv("SEARCH_DB_PASSWORD", "admin")

YARA_RULES_UPLOAD_DIRECTORY = os.getenv("YARA_RULES_UPLOAD_DIRECTORY", "../sample_yara_rules/")
YARA_RULES_COLLECTIONS_DIRECTORY = os.getenv("YARA_RULES_COLLECTIONS_DIRECTORY", "/tmp/yara_collections/")