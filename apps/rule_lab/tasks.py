import os
import shutil
import tempfile
import typing

import yara
from celery import shared_task
from django.contrib.auth.models import User
from yarawesome.settings import MEDIA_ROOT
from apps.rules.models import YaraRule
from .models import TestBinary, YaraRuleMatch


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
    test_binary_file = TestBinary.objects.get(binary_id=binary_id)
    # Create a temporary file to store rule contents
    binary_file_path = os.path.join(MEDIA_ROOT, test_binary_file.file.name)
    temp_file = tempfile.NamedTemporaryFile(delete=False, mode="a")
    if rule_ids:
        for rule in YaraRule.objects.filter(id__in=rule_ids):
            temp_file.write(rule.content + "\n\n")
    if collection_ids:
        for collection_id in collection_ids:
            for rule in YaraRule.objects.filter(collection_id=collection_id, user=user):
                temp_file.write(rule.content + "\n\n")
    compiled_rules = yara.compile(filepath=temp_file.name)
    matches = compiled_rules.match(binary_file_path)
    return matches
