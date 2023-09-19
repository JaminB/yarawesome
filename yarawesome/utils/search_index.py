import json
import os
import typing

import requests
from django.contrib.auth.models import User
from django.db import IntegrityError

from apps.rules.models import YaraRule
from yarawesome import config

from . import database

rule_search_index = "yara-rules"


def bulk_index_yara_rules(
    yara_rules: typing.List[dict],
    chunk_size: int = 200,
    user: typing.Optional[User] = None,
):
    """
    Bulk insert a list of documents into an Elasticsearch index using the requests library in chunks.

    Args:
        user: The user making the bulk index request.
        yara_rules (list): A list of YARA rules to insert into the index.
        chunk_size (int): The maximum number of documents to include in each bulk request.

    Returns:
        bool: True if all bulk inserts were successful, False otherwise.
    """
    try:
        success = True
        num_documents = len(yara_rules)

        for i in range(0, num_documents, chunk_size):
            # Split the documents list into chunks
            chunk = yara_rules[i : i + chunk_size]

            # Prepare the bulk data for this chunk
            bulk_data = []
            for doc in chunk:
                index_action = {
                    "index": {
                        "_index": rule_search_index,
                    }
                }
                bulk_data.append(index_action)
                bulk_data.append(doc)

            # Combine the bulk data into a single JSON string
            bulk_data_str = "\n".join(map(lambda x: json.dumps(x), bulk_data))
            # Create the URL for the bulk insert request
            bulk_url = f"{config.SEARCH_DB_URI}/{rule_search_index}/_bulk"
            if user:
                bulk_url = f"{config.SEARCH_DB_URI}/{user.id}-{rule_search_index}/_bulk"

            # Send the bulk insert request to Elasticsearch
            response = requests.post(
                bulk_url,
                headers={"Content-Type": "application/x-ndjson"},
                data=bulk_data_str,
                auth=(config.SEARCH_DB_USER, config.SEARCH_DB_PASSWORD),
            )
            if response.status_code != 200:
                success = False
                print(
                    f"Bulk insert failed with status code {response.status_code}: {response.text}"
                )

        return success

    except Exception as e:
        print(f"Error during bulk insert: {e}")
        return False


def get_rule_ids_in_collection(collection_id: int) -> typing.List[str]:
    """
    Get the rule IDs in a collection.
    Args:
        collection_id: The ID of the collection.

    Returns:
        List[str]: A list of rule IDs.
    """
    try:
        rule_ids = YaraRule.objects.filter(collection__id=collection_id).values_list(
            "rule_id", flat=True
        )
    except YaraRule.DoesNotExist:
        return []
    return rule_ids


def get_rule_ids_in_import_job(import_id: int) -> typing.List[str]:
    """
    Get the rule IDs in an import job.
    Args:
        import_id: The ID of the import job.

    Returns:
        List[str]: A list of rule IDs.
    """
    try:
        rule_ids = YaraRule.objects.filter(import_job__id=import_id).values_list(
            "rule_id", flat=True
        )
    except YaraRule.DoesNotExist:
        return []
    return rule_ids


def contextualize_yara_rules_search_response(
    response: requests.Response,
    term: str,
    start: int,
    max_results: int,
    user: typing.Optional[User] = None,
) -> dict:
    """
    Contextualize the search response with additional information from our database.

    Args:
        user: The user making the search request.
        max_results: The maximum number of results to retrieve.
        start: The starting index of results.
        response (requests.Response): The API response.
        term (str): The search term.

    Returns:
        dict: Parsed search results.
    """
    results = []
    for hit in response.json().get("hits", {}).get("hits", []):
        collection = {}
        yara_rule_collection = (
            YaraRule.objects.filter(
                rule_id=hit["_source"]["rule_id"], user=user
            ).first()
            if user
            else YaraRule.objects.filter(
                rule_id=hit["_source"]["rule_id"], public=True
            ).first()
        )
        if yara_rule_collection:
            collection = {
                "id": yara_rule_collection.collection.id,
                "name": yara_rule_collection.collection.name,
            }
        try:
            results.append(
                {
                    "id": hit["_source"]["rule_id"],
                    "name": hit["_source"]["name"],
                    "collection": collection,
                    "description": hit["_source"].get("description", ""),
                    "rule": YaraRule.objects.filter(
                        rule_id=hit["_source"]["rule_id"], user=user
                    )
                    .first()
                    .content
                    if user
                    else YaraRule.objects.filter(
                        rule_id=hit["_source"]["rule_id"], public=True
                    )
                    .first()
                    .content,
                }
            )
        except Exception as e:
            print("Orphaned rule found in search index.", e)
            results.append(
                {
                    "id": hit["_source"]["rule_id"],
                    "name": hit["_source"]["name"],
                    "collection": collection,
                    "description": hit["_source"].get("description", ""),
                    "rule": None,
                    "warning": "This rule has been deleted by the original owner, "
                    "and will be removed from the index soon.",
                }
            )
    if term.strip().startswith("import_id:"):
        import_id = int(term.strip().split(":")[1])
        available = (
            YaraRule.objects.filter(import_job__id=import_id, user=user).count()
            if user
            else YaraRule.objects.filter(import_job__id=import_id, public=True).count()
        )
    elif term.strip().startswith("collection_id:"):
        collection_id = int(term.strip().split(":")[1])
        available = (
            YaraRule.objects.filter(collection__id=collection_id, user=user).count()
            if user
            else YaraRule.objects.filter(
                collection__id=collection_id, public=True
            ).count()
        )
    else:
        available = response.json().get("hits", {}).get("total", {}).get("value", 0)
    return {
        "search_parameters": {
            "term": term,
            "start": start,
            "max_results": max_results,
        },
        "search_time": response.json().get("hits", {}).get("took", 0),
        "available": available,
        "displayed": len(results),
        "results": results,
    }


def search_yara_rules_index(
    term: str,
    start: int = 0,
    max_results: int = 100,
    user: typing.Optional[User] = None,
) -> requests.Response:
    """
    Make a search request to the ElasticSearch / ZincSearch backend.

    Args:
        user: The user making the search request
        term (str): The search term.
        start (int, optional): Starting index of results. Defaults to 0.
        max_results (int, optional): Maximum number of results to retrieve. Defaults to 100.

    Returns:
        requests.Response: The API response.
    """
    headers = {"Content-Type": "application/json"}
    search_url = f"{config.SEARCH_DB_URI}/{rule_search_index}/_search"
    if user:
        search_url = f"{config.SEARCH_DB_URI}/{user.id}-{rule_search_index}/_search"
    if term.strip().startswith("import_id:") or term.strip().startswith(
        "collection_id:"
    ):
        parent_id = int(term.strip().split(":")[1])
        select_function = get_rule_ids_in_import_job
        if term.strip().startswith("collection_id:"):
            select_function = get_rule_ids_in_collection

        query_strings = [
            {"query_string": {"query": rule_id}}
            for rule_id in select_function(parent_id)
        ]
        query = {"bool": {"should": query_strings[start : start + max_results]}}
        search_payload = {
            "query": query,
            "sort": ["-@timestamp"],
            "from": 0,
            "size": max_results,
        }
    else:
        query = {"bool": {"must": [{"query_string": {"query": term}}]}}
        search_payload = {
            "query": query,
            "sort": ["-@timestamp"],
            "from": start,
            "size": max_results,
        }

    with requests.post(
        url=search_url,
        json=search_payload,
        headers=headers,
        auth=(config.SEARCH_DB_USER, config.SEARCH_DB_PASSWORD),
    ) as response:
        return response


def index_yara_rule(
    parsed_rule: dict,
    user: typing.Optional[User] = None,
    collection_name: typing.Optional[str] = None,
    import_id: typing.Optional[int] = None,
) -> typing.Optional[requests.Response]:
    """
    Index a parsed YARA rule into the search backend.

    Args:
        user: The user making the search request.
        parsed_rule (dict): A dictionary containing parsed YARA rule information.
        collection_name (str): The name of the collection to index the rule into.
        import_id (int): The ID of the import job.

    Returns:
        requests.Response: The response from the indexing request.
    """
    if not os.path.exists(config.YARA_RULES_COLLECTIONS_DIRECTORY):
        os.mkdir(config.YARA_RULES_COLLECTIONS_DIRECTORY)
    if parsed_rule.get("imports", []):
        _import_str = ""
        for _import in parsed_rule.get("imports", []):
            if f"{_import}." in parsed_rule["content"]:
                _import_str += f'import "{_import}"\n'
        parsed_rule["content"] = _import_str + "\n" + parsed_rule["content"]
    headers = {"Content-Type": "application/json"}
    try:
        yara_rule_db = database.write_yara_rule_record(
            parsed_rule, user=user, collection_name=collection_name, import_id=import_id
        )
    except IntegrityError:
        return None

    create_document_with_id_url = (
        f"{config.SEARCH_DB_URI}/{rule_search_index}/_doc/{parsed_rule['rule_id']}"
    )
    if yara_rule_db.user.id:
        create_document_with_id_url = f"{config.SEARCH_DB_URI}/{yara_rule_db.user.id}-yara-rules/_doc/{parsed_rule['rule_id']}"

    parsed_rule.pop("content")
    with requests.put(
        url=create_document_with_id_url,
        json=parsed_rule,
        headers=headers,
        auth=(config.SEARCH_DB_USER, config.SEARCH_DB_PASSWORD),
    ) as response:
        return response
