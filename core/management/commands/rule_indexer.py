import json
import os
import typing
from hashlib import md5

import plyara
import requests
from yarawesome.settings import MEDIA_ROOT
from django.core.management.base import BaseCommand
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from yarawesome import config


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "yarawesome.settings")


def parse_yara_rules_from_raw(yara_rules_string: str) -> typing.List[dict]:
    parser = plyara.Plyara()
    flattened_rules = []
    parsed_yara_rules = parser.parse_string(yara_rules_string)
    for parsed_yara_rule in parsed_yara_rules:
        rule_start_line = parsed_yara_rule["start_line"]
        rule_end_line = parsed_yara_rule["stop_line"]
        rule_content = "\n".join(yara_rules_string.split("\n")[rule_start_line:rule_end_line])
        if not rule_content.strip().startswith("{"):
            rule_content = "{\n" + rule_content
        if not rule_content.strip().endswith("}"):
            rule_content = rule_content + "\n}"
        flattened_rule = {
            "content": f"rule {parsed_yara_rule['rule_name']}\n"
                       + rule_content,
            "rule_id": md5(
                "".join(sorted(str(val) for val in parsed_yara_rule.values())).encode(
                    "utf-8"
                )
            ).hexdigest(),
            "name": parsed_yara_rule["rule_name"],
            "condition": " ".join(parsed_yara_rule.get("condition_terms", [])),
            "imports": parsed_yara_rule.get("imports", []),
            "variables": [item["name"] for item in parsed_yara_rule.get("strings", [])],
            "values": [item["value"] for item in parsed_yara_rule.get("strings", [])],
        }

        for meta_item in parsed_yara_rule.get("metadata", []):
            flattened_rule[list(meta_item.keys())[0]] = list(meta_item.values())[0]

        flattened_rules.append(flattened_rule)
    return flattened_rules


def parse_yara_rules_from_path(yara_rule_path: str) -> typing.List[dict]:
    """
    Parse YARA rules from a file or a string and extract relevant information.

    Args:
        yara_rule_path (str): A file path containing one or more YARA rules

    Returns:
        List[dict]: A list of dictionaries containing parsed YARA rule information.
    """

    with open(yara_rule_path, "r") as yara_rule_in:
        yara_rule_content = yara_rule_in.read()
    flattened_rules = parse_yara_rules_from_raw(yara_rule_content)
    for flattened_rule in flattened_rules:
        flattened_rule["path_on_disk"] = yara_rule_path
    return flattened_rules


def index_yara_rule(parsed_rule: dict):
    """
    Index a parsed YARA rule into the search database.

    Args:
        parsed_rule (dict): A dictionary containing parsed YARA rule information.

    Returns:
        requests.Response: The response from the indexing request.
    """
    if not os.path.exists(config.YARA_RULES_COLLECTIONS_DIRECTORY):
        os.mkdir(config.YARA_RULES_COLLECTIONS_DIRECTORY)
    path_on_disk = (
        f"{config.YARA_RULES_COLLECTIONS_DIRECTORY}/{parsed_rule['rule_id']}.yara"
    )
    with open(path_on_disk, "w") as yara_sig_out:
        if parsed_rule.get("imports", []):
            _import_str = ""
            for _import in parsed_rule.get("imports", []):
                if f"{_import}." in parsed_rule["content"]:
                    _import_str += f'import "{_import}"\n'
            parsed_rule["content"] = _import_str + "\n" + parsed_rule["content"]
        yara_sig_out.write(parsed_rule["content"].strip())
    headers = {"Content-Type": "application/json"}
    create_document_with_id_url = (
        f"{config.SEARCH_DB_URI}/api/yara-rules/_doc/{parsed_rule['rule_id']}"
    )
    parsed_rule["path_on_disk"] = path_on_disk
    parsed_rule.pop("content")
    with requests.put(
        url=create_document_with_id_url,
        json=parsed_rule,
        headers=headers,
        auth=(config.SEARCH_DB_USER, config.SEARCH_DB_PASSWORD),
    ) as response:
        return response


class RuleIndexHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        print(f"New rule added: {event.src_path}")
        try:
            for rule in parse_yara_rules_from_path(event.src_path):
                index_yara_rule(rule)
        except Exception as e:
            print(e)


class Command(BaseCommand):
    help = "Watch for newly added YARA rules and index them"

    def handle(self, *args, **options):
        rule_indexing_handler = RuleIndexHandler()
        rule_indexing_observer = Observer()
        rule_indexing_observer.schedule(
            rule_indexing_handler,
            f"{MEDIA_ROOT}/rule-uploads/",
            recursive=True,
        )
        rule_indexing_observer.start()
