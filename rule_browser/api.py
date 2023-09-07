import plyara
import requests
import typing
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import YaraRule
from yarawesome import config
from .serializers import RuleLookupSerializer, RuleSearchSerializer

rule_search_index = "yara-rules"


def get_rule_ids_in_import_job(import_id: int):
    try:
        rule_ids = YaraRule.objects.filter(import_job__id=import_id).values_list(
            "rule_id", flat=True
        )
    except YaraRule.DoesNotExist:
        return []
    return rule_ids


def get_rule_ids_in_collection(collection_id: int):
    try:
        rule_ids = YaraRule.objects.filter(collection__id=collection_id).values_list(
            "rule_id", flat=True
        )
    except YaraRule.DoesNotExist:
        return []
    return rule_ids


def make_search_request(
    term: str,
    start: int = 0,
    max_results: int = 100,
    user: typing.Optional[User] = None,
) -> requests.Response:
    """
    Make a search request to the database.

    Args:
        user: The user making the search request
        term (str): The search term.
        start (int, optional): Starting index of results. Defaults to 0.
        max_results (int, optional): Maximum number of results to retrieve. Defaults to 100.

    Returns:
        requests.Response: The API response.
    """
    headers = {"Content-Type": "application/json"}
    search_url = f"{config.SEARCH_DB_URI}/es/{rule_search_index}/_search"
    if user:
        search_url = f"{config.SEARCH_DB_URI}/es/{user.id}-{rule_search_index}/_search"
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


def make_lookup_rule_request(
    rule_id: str, user: typing.Optional[User] = None
) -> YaraRule:
    """
    Make a lookup request to the database for a specific rule.

    Args:
        user: The user making the search request.
        rule_id (str): The ID of the rule.

    Returns:
        requests.Response: The API response.
    """
    yara_rule = YaraRule.objects.filter(rule_id=rule_id, user=user).first()
    return yara_rule


def parse_search_response(
    response: requests.Response, term: str, start: int, max_results: int
) -> dict:
    """
    Parse the response from a search request.

    Args:
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
        yara_rule_collection = YaraRule.objects.filter(
            rule_id=hit["_source"]["rule_id"]
        ).first()
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
                    "rule": YaraRule.objects.filter(rule_id=hit["_source"]["rule_id"])
                    .first()
                    .content,
                }
            )
        except:
            print("Orphaned rule found in search index.")
    if term.strip().startswith("import_id:"):
        import_id = int(term.strip().split(":")[1])
        available = YaraRule.objects.filter(import_job__id=import_id).count()
    elif term.strip().startswith("collection_id:"):
        collection_id = int(term.strip().split(":")[1])
        available = YaraRule.objects.filter(collection__id=collection_id).count()
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


def parse_lookup_rule_response(yara_rule: YaraRule) -> dict:
    """
    Parse the response from a lookup rule request.

    Args:
        yara_rule (YaraRule): The YaraRule instance.

    Returns:
        dict: Parsed rule information.
    """
    try:
        yara_rule_parser = plyara.Plyara()
        parsed_yara_rule = yara_rule_parser.parse_string(yara_rule.content)[0]
        parsed_yara_rule["metadata"] = {
            key: value
            for d in parsed_yara_rule.get("metadata", [])
            for key, value in d.items()
        }

        yara_rule = {
            "rule_id": yara_rule.rule_id,
            "name": parsed_yara_rule["metadata"].get("name"),
            "description": parsed_yara_rule["metadata"].get("description"),
            "author": parsed_yara_rule["metadata"].get("author"),
            "rule": yara_rule.content,
        }
        return {"yara_rule": yara_rule}
    except FileNotFoundError:
        return {"yara_rule": None}


class RuleSearchResource(APIView):
    def get(self, request, *args, **kwargs):
        serializer = RuleSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        term = serializer.validated_data["term"]
        start = serializer.validated_data["start"]
        max_results = serializer.validated_data["max_results"]
        response = make_search_request(term, start, max_results, user=request.user)
        if response.status_code == 200:
            return Response(
                parse_search_response(response, term, start, max_results),
                status=status.HTTP_200_OK,
            )

        elif response.status_code == 401:
            return Response(
                {"error": "Could not authenticate to search backend."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        else:
            return Response(
                {"error": "An internal error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RuleOpenResource(APIView):
    def get(self, request, *args, **kwargs):
        serializer = RuleLookupSerializer(data=kwargs)
        serializer.is_valid(raise_exception=True)
        rule_id = serializer.validated_data["rule_id"]
        yara_rule = make_lookup_rule_request(rule_id, user=request.user)
        if yara_rule:
            parsed_response = parse_lookup_rule_response(yara_rule)
            if parsed_response.get("yara_rule"):
                return Response(parsed_response, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "Could not locate a rule with this id."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        else:
            return Response(
                {"error": "An internal error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
