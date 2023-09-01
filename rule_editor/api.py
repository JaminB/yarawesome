import json
import requests
import plyara
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rule_browser.serializers import RuleLookupSerializer
from rule_browser.api import make_lookup_rule_request


from yarawesome import config


def parse_lookup_rule_response_verbose(response: requests.Response) -> dict:
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
            hit["_source"].pop("path_on_disk")
            hit["_source"].pop("@timestamp")
            parser = plyara.Plyara()
            raw_rule = fin.read().strip()
            parsed_yara_rule = parser.parse_string(raw_rule)[-1]
            yara_rule = {
                **parsed_yara_rule,
                "rule": raw_rule,

            }

            return {
                "yara_rule": yara_rule
            }
    except FileNotFoundError:
        return {
            "yara_rule": None
        }


class RuleDebugOpenResource(APIView):
    def get(self, request, *args, **kwargs):
        serializer = RuleLookupSerializer(data=kwargs)
        serializer.is_valid(raise_exception=True)
        rule_id = serializer.validated_data["rule_id"]
        response = make_lookup_rule_request(rule_id)
        if response.status_code == 200:
            parsed_response = parse_lookup_rule_response_verbose(response)
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
