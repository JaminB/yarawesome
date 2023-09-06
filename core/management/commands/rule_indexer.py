import re
import json
import time
from django.db import connections
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
from core.models import ImportYaraRuleJob, YaraRule, YaraRuleCollection


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "yarawesome.settings")


def parse_yara_rule_from_index(yara_rules_index_path: str) -> typing.List[dict]:
    attempts = 0
    wait_interval_seconds = 1
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
        flattened_rule = {
            "content": f"rule {parsed_yara_rule['rule_name']}\n" + rule_content,
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
    try:
        with open(yara_rule_path, "r") as yara_rule_in:
            yara_rule_content = yara_rule_in.read()
    except UnicodeDecodeError:
        return []

    flattened_rules = parse_yara_rules_from_raw(yara_rule_content)
    import_job_cache = {}
    for flattened_rule in flattened_rules:
        flattened_rule["path_on_disk"] = yara_rule_path
        import_id = int(os.path.basename(flattened_rule["path_on_disk"]).split("_")[0])
        if import_id in import_job_cache:
            import_job = import_job_cache[import_id]
        else:
            try:
                import_job_cache[import_id] = ImportYaraRuleJob.objects.get(
                    id=import_id
                )
                import_job = import_job_cache[import_id]
            except ImportYaraRuleJob.DoesNotExist:
                continue
        YaraRule(
            yara_id=flattened_rule["rule_id"],
            user=import_job.user,
            import_job=import_job,
        ).save()

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
        import_job_id = int(os.path.basename(event.src_path).split("_")[0])
        collection_name = os.path.dirname(event.src_path).split("/")[-1]
        import_job = ImportYaraRuleJob.objects.get(id=import_job_id)

        yara_rule_collection = YaraRuleCollection()
        yara_rule_collection.name = collection_name
        yara_rule_collection.description = (
            f"Generated from {yara_rule_collection.name}."
        )
        if not YaraRuleCollection.objects.filter(
            import_job=import_job_id, name=collection_name
        ).exists():
            yara_rule_collection.user = import_job.user
            yara_rule_collection.import_job = import_job
            yara_rule_collection.save()
            print(
                f"Creating new collection {yara_rule_collection.name} ({yara_rule_collection.id})"
            )
        else:
            yara_rule_collection = YaraRuleCollection.objects.filter(
                import_job=import_job_id, name=collection_name
            ).first()

        for rule in parse_yara_rules_from_path(event.src_path):
            index_yara_rule(rule)
            try:
                YaraRule(
                    yara_id=rule["rule_id"],
                    user=import_job.user,
                    import_job=import_job,
                    collection=yara_rule_collection,
                ).save()
            except ValueError:
                print(
                    f"Skipping {rule['rule_id']} as collection record wasn't properly written."
                )
                continue


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
