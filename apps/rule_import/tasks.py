import os
from celery import shared_task

from yarawesome.utils import search_index
from apps.core.management.commands.inotify_rule_indexer import (
    parse_yara_rules_from_path,
)
from yarawesome.utils import list_files_recursive


@shared_task
def import_yara_rules(yara_rules_root_directory: str, import_id: int) -> None:
    yara_rule_paths = [
        rule
        for rule in list_files_recursive(yara_rules_root_directory)
        if rule.endswith(".yar") or rule.endswith(".yara")
    ]
    for rule_path in yara_rule_paths:
        rules = parse_yara_rules_from_path(rule_path)
        for rule in rules:
            search_index.index_yara_rule(
                rule,
                collection_name=os.path.dirname(rule_path).split("/")[-1],
                import_id=import_id,
            )
