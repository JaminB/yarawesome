import json
import requests
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import RuleLookupSerializer, RuleSearchSerializer


from yarawesome import config


def make_search_request(
    term: str, start: int = 0, max_results: int = 100
) -> requests.Response:
    """
    Make a search request to the database.

    Args:
        term (str): The search term.
        start (int, optional): Starting index of results. Defaults to 0.
        max_results (int, optional): Maximum number of results to retrieve. Defaults to 100.

    Returns:
        requests.Response: The API response.
    """
    headers = {"Content-Type": "application/json"}
    search_url = f"{config.SEARCH_DB_URI}/es/_search"
    search_payload = {
        "query": {"bool": {"must": [{"query_string": {"query": term}}]}},
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


def make_lookup_rule_request(rule_id: str) -> requests.Response:
    """
    Make a lookup request to the database for a specific rule.

    Args:
        rule_id (str): The ID of the rule.

    Returns:
        requests.Response: The API response.
    """
    headers = {"Content-Type": "application/json"}
    search_url = f"{config.SEARCH_DB_URI}/es/_search"
    search_payload = {
        "query": {"bool": {"must": [{"query_string": {"query": f'_id: {rule_id}'}}]}},
        "sort": ["-@timestamp"],
        "from": 0,
        "size": 1,
    }
    with requests.post(
        url=search_url,
        json=search_payload,
        headers=headers,
        auth=(config.SEARCH_DB_USER, config.SEARCH_DB_PASSWORD),
    ) as response:
        return response


def parse_search_response(response: requests.Response) -> dict:
    """
    Parse the response from a search request.

    Args:
        response (requests.Response): The API response.

    Returns:
        dict: Parsed search results.
    """
    results = []
    original_query = json.loads(response.request.body.decode("utf-8"))

    for hit in response.json().get("hits", {}).get("hits", []):
        with open(hit["_source"]["path_on_disk"], "r") as fin:
            results.append(
                {
                    "id": hit["_source"]["rule_id"],
                    "name": hit["_source"]["name"],
                    "description": hit["_source"].get("description", ""),
                    "rule": fin.read().strip(),
                }
            )
    return {
        "search_parameters": {
            "term": original_query["query"]["bool"]["must"][0]["query_string"]["query"],
            "start": original_query["from"],
            "max_results": original_query["size"],
        },
        "search_time": response.json().get("hits", {}).get("took", 0),
        "available": response.json().get("hits", {}).get("total", {}).get("value", 0),
        "displayed": len(results),
        "results": results,
    }


def parse_lookup_rule_response(response: requests.Response) -> dict:
    """
    Parse the response from a lookup rule request.

    Args:
        response (requests.Response): The API response.

    Returns:
        dict: Parsed rule information.
    """
    try:
        hit = response.json().get("hits", {}).get("hits", [])[-1]
    except IndexError:
        return {
            "yara_rule": None
        }
    try:
        with open(hit["_source"]["path_on_disk"], "r") as fin:
            yara_rule = {
                "rule_id": hit["_source"].get("rule_id", ""),
                "name": hit["_source"]["name"],
                "description": hit["_source"].get("description", ""),
                "author": hit["_source"].get("author", ""),
                "rule": fin.read().strip(),
            }
            return {
                "yara_rule": yara_rule
            }
    except FileNotFoundError:
        return {
            "yara_rule": None
        }


class RuleSearchResource(APIView):
    def get(self, request, *args, **kwargs):
        serializer = RuleSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        term = serializer.validated_data["term"]
        start = serializer.validated_data["start"]
        max_results = serializer.validated_data["max_results"]
        response = make_search_request(term, start, max_results)
        if response.status_code == 200:
            return Response(parse_search_response(response), status=status.HTTP_200_OK)

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
        response = make_lookup_rule_request(rule_id)
        if response.status_code == 200:
            parsed_response = parse_lookup_rule_response(response)
            if parsed_response.get("yara_rule"):
                return Response(parsed_response, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "Could not locate a rule with this id."},
                    status=status.HTTP_404_NOT_FOUND,
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
