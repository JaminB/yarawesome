import os
import tempfile
import typing

import yara
from celery import shared_task
from django.contrib.auth.models import User
from yarawesome.settings import MEDIA_ROOT
from apps.rules.models import YaraRule
from apps.core.management.commands import inotify_rule_indexer
from .models import TestBinary, YaraRuleMatch


def rename_yara_rule_based_on_id(internal_db_rule_id: int, rule_content: str):
    yara_rule = inotify_rule_indexer.parse_yara_rules_from_raw(rule_content)[0]
    lines = yara_rule["content"].split("\n")
    lines[0] = f"rule _{internal_db_rule_id}"
    return "\n".join(lines)


@shared_task
def match_yara_rules(
    binary_id: str,
    rule_ids: typing.List[int],
    collection_ids: typing.List[int],
    user_id: int,
) -> None:
    """
    Match a set of rules to a binary file.
    """
    user = User.objects.get(id=user_id)
    test_binary_file = TestBinary.objects.get(id=binary_id)

    # Create a temporary file to store rule contents
    binary_file_path = os.path.join(MEDIA_ROOT, test_binary_file.file.name)
    temp_file = tempfile.NamedTemporaryFile(delete=False, mode="a")
    if rule_ids:
        for rule in YaraRule.objects.filter(id__in=rule_ids):
            temp_file.write(
                rename_yara_rule_based_on_id(
                    internal_db_rule_id=rule.id, rule_content=rule.content
                )
                + "\n\n"
            )
    if collection_ids:
        for collection_id in collection_ids:
            for rule in YaraRule.objects.filter(collection_id=collection_id, user=user):
                temp_file.write(
                    rename_yara_rule_based_on_id(
                        internal_db_rule_id=rule.id, rule_content=rule.content
                    )
                    + "\n\n"
                )
    temp_file.file.close()
    compiled_rules: yara.Rules = yara.compile(temp_file.name)
    matches = compiled_rules.match(binary_file_path)

    # Connect matches to each YARA rule
    for match in matches:
        match: yara.Match
        YaraRuleMatch.objects.create(
            rule_id=match.rule.replace("_", ""),
            user_id=user_id,
            test_binary=test_binary_file,
        )
