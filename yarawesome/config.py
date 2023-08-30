from dotenv import load_dotenv
import os

load_dotenv()

SEARCH_DB_URI = os.getenv("SEARCH_DB_URI", "http://localhost:4080")
SEARCH_DB_USER = os.getenv("SEARCH_DB_USER", "admin")
SEARCH_DB_PASSWORD = os.getenv("SEARCH_DB_PASSWORD", "admin")

YARA_RULES_DIRECTORY = os.getenv("YARA_RULES_DIRECTORY", "../sample_yara_rules/")
