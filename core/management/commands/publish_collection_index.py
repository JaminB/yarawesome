import plyara
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from core.models import YaraRule, YaraRuleCollection
from core.utils import database, search_index


def build_rule_index_from_private_collection(
    collection: YaraRuleCollection, user: User
):
    """
    Build the rule index from a private collection.
    Args:
        collection: The collection to build the index from.
        user: The user building the index.

    Returns:
    """
    if user != collection.user:
        return None
    yara_rules = YaraRule.objects.filter(collection=collection, user=user).all()
    rule_chunk = []
    upload_results = []
    for rule in yara_rules.iterator():
        rule_chunk.append(database.parse_lookup_rule_response(rule))
        if len(rule_chunk) == 600:
            upload_results.append(search_index.bulk_index_yara_rules(rule_chunk))
            rule_chunk = []
    upload_results.append(search_index.bulk_index_yara_rules(rule_chunk))
    return all(upload_results)


class Command(BaseCommand):
    help = "Watch for newly added YARA rules and index them"

    def add_arguments(self, parser):
        # Define your command-line arguments here
        parser.add_argument(
            "--user_id", type=str, help="The id of the user to build the index for."
        )
        parser.add_argument(
            "--collection_id",
            type=int,
            help="The id of the collection to build the index from.",
        )

    def handle(self, *args, **options):
        user_id = options.get("user_id")
        collection_id = options.get("collection_id")
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
        try:
            yara_rule_collection = YaraRuleCollection.objects.get(
                id=collection_id, user=user
            )
        # Occurs when the collection does not exist or the user does not own the collection.
        except YaraRuleCollection.DoesNotExist:
            return None
        build_rule_index_from_private_collection(yara_rule_collection, user)
