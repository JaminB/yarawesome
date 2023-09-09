import os
import typing
from hashlib import md5

import plyara
import requests
from django.contrib.auth.models import User
from yarawesome.settings import BASE_DIR
from core.models import ImportYaraRuleJob, YaraRule, YaraRuleCollection

rule_search_index = "yara-rules"


def get_icon_id_from_string(string: str):
    """
    Get an icon ID from a string.

    Args:
        string: The string to get an icon ID from.

    Returns: An icon ID.
    """
    collections_icon_path = os.path.join(
        BASE_DIR, "core", "static", "core", "img", "icons", "collections"
    )

    return int(md5(string.encode("utf-8")).hexdigest()[:8], 16) % len(
        os.listdir(collections_icon_path)
    )


def lookup_yara_rule(rule_id: str, user: typing.Optional[User] = None) -> YaraRule:
    """
    Make a lookup request to the database for a specific rule.

    Args:
        user: The user making the search request.
        rule_id (str): The ID of the rule.

    Returns:
        requests.Response: The API response.
    """
    if not user:
        yara_rule = YaraRule.objects.filter(rule_id=rule_id).first()
    else:
        yara_rule = YaraRule.objects.filter(rule_id=rule_id, user=user).first()
    return yara_rule


def parse_lookup_rule_response(yara_rule: YaraRule) -> dict:
    """
    Parse the response from a lookup rule request.

    Args:
        yara_rule (YaraRule): The YaraRule instance.

    Returns:
        dict: Parsed rule information.
    """
    try:
        yara_rule_parser = plyara.Plyara()
        parsed_yara_rule = yara_rule_parser.parse_string(yara_rule.content)[0]
        parsed_yara_rule["metadata"] = {
            key: value
            for d in parsed_yara_rule.get("metadata", [])
            for key, value in d.items()
        }
        yara_rule = {
            "rule_id": yara_rule.rule_id,
            "name": parsed_yara_rule.get("rule_name"),
            "description": parsed_yara_rule["metadata"].get("description", ""),
            "author": parsed_yara_rule["metadata"].get("author", ""),
            "rule": yara_rule.content,
        }
        return {"yara_rule": yara_rule}
    except FileNotFoundError:
        return {"yara_rule": None}


def write_yara_rule_record(parsed_rule: dict, user: typing.Optional[User] = None):
    """
    Write a parsed YARA rule to the database. If the rule already exists, do nothing.
    Args:
        user: The user writing the rule to the database.
        parsed_rule: A dictionary containing parsed YARA rule information.

    Returns: A YaraRule instance.

    """
    if parsed_rule.get("path_on_disk"):
        import_job_id = int(os.path.basename(parsed_rule["path_on_disk"]).split("_")[0])
        collection_name = os.path.dirname(parsed_rule["path_on_disk"]).split("/")[-1]
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
            yara_rule_collection.icon = get_icon_id_from_string(collection_name)
            yara_rule_collection.save()
            print(
                f"Creating new collection {yara_rule_collection.name} ({yara_rule_collection.id})"
            )
        else:
            yara_rule_collection = (
                YaraRuleCollection.objects.filter(
                    import_job__id=import_job_id, name=collection_name
                )
                .all()
                .latest("id")
            )
        yara_rule = YaraRule(
            rule_id=parsed_rule["rule_id"],
            content=parsed_rule["content"],
            user=import_job.user,
            import_job=import_job,
            collection=yara_rule_collection,
        )
        yara_rule.save()
        return yara_rule
    else:
        yara_rule = YaraRule.objects.filter(
            rule_id=parsed_rule["rule_id"], user=user
        ).first()
        if yara_rule:
            yara_rule.content = parsed_rule["content"]
            yara_rule.save()
        return yara_rule
