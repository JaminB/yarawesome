from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from apps.rule_lab.models import TestBinary
from apps.rule_lab.tasks import match_yara_rules


class Command(BaseCommand):
    help = "Run one or more YARA rules or collections against a file."

    def add_arguments(self, parser):
        # Define your command-line arguments here
        parser.add_argument(
            "--user_id", type=str, help="The id of the user to run the rules for."
        )
        parser.add_argument(
            "--collection_ids",
            type=str,
            help="A list of collection_ids to run against the file.",
        )
        parser.add_argument(
            "--rule_ids",
            type=str,
            help="A list of rule_ids to run against the file.",
            nargs="+",
        )
        parser.add_argument(
            "--binary_id",
            type=int,
            help="The id of the test binary to run the rules against.",
        )

    def handle(self, *args, **options):
        user = User.objects.get(id=options.get("user_id"))
        test_binary = TestBinary.objects.filter(
            id=options.get("binary_id"), user=user
        ).first()
        if not test_binary:
            return None

        print(
            match_yara_rules(
                user=user,
                test_binary_file=test_binary,
                rule_ids=options.get("rule_ids"),
                collection_ids=options.get("collection_ids"),
            )
        )
