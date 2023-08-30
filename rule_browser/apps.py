from django.apps import AppConfig
from yarawesome.daemons.rule_indexer import RuleIndexer


class RuleBrowserConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "rule_browser"

    def ready(self):
        RuleIndexer().run()
