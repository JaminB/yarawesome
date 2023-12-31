from celery import shared_task

from yarawesome.utils import database, search_index
from apps.rules.models import YaraRule

from apps.core.management.commands.inotify_rule_indexer import (
    parse_yara_rules_from_raw,
)
from apps.core.management.commands import publish_collection_index

from .models import YaraRuleCollectionDownload


@shared_task
def download_collection(collection_id: int, download_id: str) -> None:
    concat_rules = database.get_yara_rule_collection_content(collection_id)
    collection_download = YaraRuleCollectionDownload.objects.create(
        id=download_id, collection_id=collection_id, content=concat_rules
    )
    collection_download.save()


@shared_task
def clone_collection(
    copy_from_collection: dict,
    copy_to_collection: dict,
    user: dict,
) -> None:
    for yara_rule_obj in YaraRule.objects.filter(
        collection_id=copy_from_collection.get("id")
    ).all():
        try:
            parsed_rule = parse_yara_rules_from_raw(yara_rule_obj.content)[-1]
        except Exception as e:
            print(e)
            continue
        if parsed_rule:
            search_index.index_yara_rule(
                parsed_rule=parsed_rule,
                user=user,
                collection_name=copy_to_collection.get("name"),
                import_id=copy_to_collection.get("import_job"),
            )


@shared_task
def publish_collection(collection: dict, user: dict, set_to_public: bool) -> None:
    publish_collection_index.build_rule_index_from_private_collection(collection, user)

    yara_rules = YaraRule.objects.filter(
        collection__id=collection.get("id"), user_id=user.get("id")
    )

    for yara_rule in yara_rules:
        yara_rule.public = set_to_public
        yara_rule.save()
    publish_collection_index.build_rule_index_from_private_collection(collection, user)
