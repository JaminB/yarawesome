import os
import time
import typing
import plyara
import requests
from datetime import datetime
from hashlib import md5
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from yarawesome import config
from core.middleware import Daemon

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "yarawesome.settings")


def parse_yara_rules(path_or_rule: str) -> typing.List[dict]:
    """
        Parse YARA rules from a file or a string and extract relevant information.

        Args:
            path_or_rule (str): A file path or a YARA rule string.

        Returns:
            List[dict]: A list of dictionaries containing parsed YARA rule information.
    """
    flattened_rule = {}
    parser = plyara.Plyara()
    if os.path.exists(path_or_rule):
        with open(path_or_rule, "r") as yara_rule_in:
            flattened_rule["path_on_disk"] = path_or_rule
            yara_rule_content = yara_rule_in.read()
    else:
        yara_rule_content = path_or_rule
    flattened_rules = []
    parsed_yara_rules = parser.parse_string(yara_rule_content)
    for parsed_yara_rule in parsed_yara_rules:
        for meta_item in parsed_yara_rule.get("metadata", []):
            flattened_rule[f"{list(meta_item.keys())[0]}"] = list(meta_item.values())[0]
        flattened_rule["rule_id"] = md5(parsed_yara_rule["rule_name"].encode("utf-8")).hexdigest()
        flattened_rule["name"] = parsed_yara_rule["rule_name"]
        flattened_rule["condition"] = " ".join(parsed_yara_rule.get("condition_terms", []))
        flattened_rule["variables"] = " ".join(
            [item["name"] for item in parsed_yara_rule.get("strings", [])]
        )
        flattened_rule["values"] = " ".join(
            [item["value"] for item in parsed_yara_rule.get("strings", [])]
        )
        flattened_rules.append(flattened_rule)
    return flattened_rules


def index_rule(parsed_rule: dict):
    """
        Index a parsed YARA rule into the search database.

        Args:
            parsed_rule (dict): A dictionary containing parsed YARA rule information.

        Returns:
            requests.Response: The response from the indexing request.
    """

    headers = {"Content-Type": "application/json"}
    current_date = datetime.utcnow().strftime("%Y-%m-%d")
    create_document_with_id_url = f"{config.SEARCH_DB_URI}/api/yara-rules/_doc/{parsed_rule['rule_id']}"

    with requests.put(
            url=create_document_with_id_url,
            json=parsed_rule,
            headers=headers,
            auth=(config.SEARCH_DB_USER, config.SEARCH_DB_PASSWORD)
    ) as response:
        return response


class RuleIndexHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        print(f"New rule added: {event.src_path}")
        try:
            index_rule(parse_yara_rule(event.src_path))
        except Exception as e:
            print(e)

    def on_modified(self, event):
        if event.is_directory:
            return
        print(f"Rule modified: {event.src_path}")
        try:
            index_rule(parse_yara_rule(event.src_path))
        except Exception as e:
            print(e)


class RuleIndexer(Daemon):

    def run(self):
        event_handler = RuleIndexHandler()
        observer = Observer()
        observer.schedule(event_handler, config.YARA_RULES_UPLOAD_DIRECTORY, recursive=True)
        observer.start()


if __name__ == '__main__':
    RuleIndexer().run()
    while True:
        time.sleep(1)

