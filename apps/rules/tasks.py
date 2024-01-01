from celery import shared_task

from yarawesome.utils import search_index
from apps.rules.models import YaraRule

from apps.core.management.commands.inotify_rule_indexer import (
    parse_yara_rules_from_raw,
)


@shared_task
def clone_rule(
    rule_id: dict,
    copy_to_collection: dict,
    user: dict,
) -> None:
    yara_rule_obj = YaraRule.objects.filter(rule_id=rule_id, public=True).first()
    try:
        parsed_rule = parse_yara_rules_from_raw(yara_rule_obj.content.strip())[-1]
    except Exception as e:
        return

    if parsed_rule:
        search_index.index_yara_rule(
            parsed_rule=parsed_rule,
            user=user,
            collection_name=copy_to_collection.get("name"),
            import_id=copy_to_collection.get("import_job"),
        )
