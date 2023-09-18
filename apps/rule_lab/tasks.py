import os
import shutil
import tempfile
import typing
from celery import shared_task
from django.contrib.auth.models import User
from apps.rules.models import YaraRule


@shared_task
def match_yara_rules(
    binary_file_path: str,
    rule_ids: typing.List[int],
    collection_ids: typing.List[int],
    user: typing.Optional[User] = None,
) -> None:
    """
    Match a set of rules to a binary file.
    """
    # Create a temporary file to store rule contents
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    if rule_ids:
        for rule in YaraRule.objects.filter(id__in=rule_ids):
            temp_file.write(rule.content.encode("utf-8") + "\n\n")
    if collection_ids:
        for collection_id in collection_ids:
            for rule in YaraRule.objects.filter(collection_id=collection_id, user=user):
                temp_file.write(rule.content.encode("utf-8") + "\n\n")
