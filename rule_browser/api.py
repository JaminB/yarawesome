import requests
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import RuleSearchSerializer

from yarawesome import config


def make_search_request(term: str, start: int = 0, max_results: int = 100):
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


def parse_search_response(response):
    results = []
    for hit in response.json().get("hits", {}).get("hits", []):
        with open(hit["_source"]["path_on_disk"], "r") as fin:
            results.append(
                {
                    "name": hit["_source"]["name"],
                    "description": hit["_source"].get("description", ""),
                    "rule": fin.read().strip(),
                }
            )
    return {
        "search_time": response.json().get("hits", {}).get("took", 0),
        "results": results,
    }


class RuleSearchView(APIView):
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
