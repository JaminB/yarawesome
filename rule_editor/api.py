import json
import requests
import plyara
from plyara.exceptions import ParseError
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from core.management.commands import rule_indexer
from rule_browser.serializers import RuleLookupSerializer
from rule_browser.api import make_lookup_rule_request


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
        return {"yara_rule": None}
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

            return {"yara_rule": yara_rule}
    except FileNotFoundError:
        return {"yara_rule": None}


class RuleEditorResource(APIView):
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

    def put(self, request, *args, **kwargs):
        serializer = RuleLookupSerializer(data=kwargs)
        serializer.is_valid(raise_exception=True)
        rule_id = serializer.validated_data["rule_id"]
        try:
            data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON data"}, status=400)

            # Check if 'yara_rule' is in the JSON data
        if "yara_rule" not in data:
            return Response(
                {"error": 'Missing "yara_rule" key in JSON data'}, status=400
            )

            # Extract the 'yara_rule' value
        yara_rule = data["yara_rule"]
        try:
            parsed_yara_rule = rule_indexer.parse_yara_rules_from_raw(yara_rule)[0]
        except ParseError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except IndexError:
            return Response(
                {"error": "No rule detected, perhaps missing closing bracket?"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        parsed_yara_rule["rule_id"] = rule_id
        rule_indexer.index_yara_rule(parsed_yara_rule)

        # Respond with a success message or appropriate response
        return Response({"message": "YARA rule updated successfully"})
