import json

import plyara
import requests
from plyara.exceptions import ParseError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.management.commands import rule_indexer
from core.models import YaraRule
from core.utils import database, search_index
from rule_browser.serializers import RuleLookupSerializer


def parse_lookup_rule_response_verbose(yara_rule: YaraRule) -> dict:
    """
    Parse the response from a lookup rule request.

    Args:
        response (requests.Response): The API response.

    Returns:
        dict: Parsed rule information.
    """
    parser = plyara.Plyara()
    raw_rule = yara_rule.content
    parsed_yara_rule = parser.parse_string(raw_rule)[-1]
    yara_rule = {
        **parsed_yara_rule,
        "rule": raw_rule,
    }

    return {"yara_rule": yara_rule}


class RuleEditorResource(APIView):
    def get(self, request, *args, **kwargs):
        serializer = RuleLookupSerializer(data=kwargs)
        serializer.is_valid(raise_exception=True)
        rule_id = serializer.validated_data["rule_id"]
        yara_rule = database.lookup_yara_rule(rule_id, user=request.user)
        if yara_rule:
            parsed_response = parse_lookup_rule_response_verbose(yara_rule)
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

    def put(self, request, *args, **kwargs):
        serializer = RuleLookupSerializer(data=kwargs)
        serializer.is_valid(raise_exception=True)
        rule_id = serializer.validated_data["rule_id"]
        try:
            data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON data"}, status=400)

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
        search_index.index_yara_rule(parsed_yara_rule, user=request.user)

        # Respond with a success message or appropriate response
        return Response({"message": "YARA rule updated successfully"})
