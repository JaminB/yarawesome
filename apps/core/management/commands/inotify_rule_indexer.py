import os
import typing
from hashlib import md5

import plyara
from django.core.management.base import BaseCommand
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from yarawesome.utils import search_index
from yarawesome.settings import MEDIA_ROOT

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "yarawesome.settings")


def parse_yara_rule_from_index(yara_rules_index_path: str) -> typing.List[dict]:
    """
    Parse YARA rules from a YARA rule index file and extract relevant information.
    Args:
        yara_rules_index_path: A file path containing one or more YARA rules

    Returns: A list of dictionaries containing parsed YARA rule information.

    """
    import_id = int(os.path.basename(yara_rules_index_path).split("_")[0])
    yara_rules_index_root = os.path.dirname(os.path.abspath(yara_rules_index_path))
    collection_rules = []
    with open(yara_rules_index_path, "r") as yara_rules_index_in:
        lines = yara_rules_index_in.readlines()
        for i, line in enumerate(lines):
            if not line:
                continue
            if not line.strip().startswith("include"):
                continue

            search_rule_path = " ".join(line.strip().split(" ")[1:]).strip('"')
            search_rule_directory = os.path.dirname(search_rule_path)
            search_rule_name = os.path.basename(search_rule_path)
            search_rule_full_path = f"{yara_rules_index_root}/{search_rule_directory}/{import_id}_{search_rule_name}"
            if not os.path.exists(search_rule_full_path):
                continue
            collection_rules.extend(parse_yara_rules_from_path(search_rule_full_path))

    return collection_rules


def parse_yara_rules_from_raw(yara_rules_string: str) -> typing.List[dict]:
    """
    Parse YARA rules from a string and extract relevant information.
    Args:
        yara_rules_string: A string containing one or more YARA rules

    Returns: A list of dictionaries containing parsed YARA rule information.

    """
    parser = plyara.Plyara()
    flattened_rules = []
    parsed_yara_rules = parser.parse_string(yara_rules_string)

    for parsed_yara_rule in parsed_yara_rules:
        rule_start_line = parsed_yara_rule["start_line"]
        rule_end_line = parsed_yara_rule["stop_line"]
        rule_content = "\n".join(
            yara_rules_string.split("\n")[rule_start_line:rule_end_line]
        )
        if not rule_content.strip().startswith("{"):
            rule_content = "{\n" + rule_content
        if not rule_content.strip().endswith("}"):
            rule_content = rule_content + "\n}"
        rule_content = f"rule {parsed_yara_rule['rule_name']}\n" + rule_content
        rule_id = md5(
            (
                "".join(
                    sorted(
                        [item["value"] for item in parsed_yara_rule.get("strings", [])]
                    )
                )
                + "".join(sorted(parsed_yara_rule.get("condition_terms", [])))
                + parsed_yara_rule["rule_name"]
            )
            .strip()
            .encode("utf-8")
        ).hexdigest()
        flattened_rule = {
            "content": rule_content,
            "rule_id": rule_id,
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
    try:
        with open(yara_rule_path, "r") as yara_rule_in:
            yara_rule_content = yara_rule_in.read()
    except UnicodeDecodeError:
        return []

    flattened_rules = parse_yara_rules_from_raw(yara_rule_content)
    for flattened_rule in flattened_rules:
        flattened_rule["path_on_disk"] = yara_rule_path
    return flattened_rules


class RuleIndexHandler(FileSystemEventHandler):
    def on_modified(self, event):
        """
        Handle a file system event. If a new YARA rule is added, index it.
        If a new YARA rule collection is added, index all the rules in the collection.
        Args:
            event: The file system event to handle.

        Returns: None

        """
        if event.is_directory:
            return
        if not event.src_path.lower().endswith(
            ".yara"
        ) and not event.src_path.lower().endswith(".yar"):
            return
        for rule in parse_yara_rules_from_path(event.src_path):
            search_index.index_yara_rule(rule)


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
