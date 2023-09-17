from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from yarawesome.utils import database, search_index
from .serializers import RuleLookupSerializer, RuleSearchSerializer


class RuleSearchResource(APIView):
    public: bool = False

    def __init__(self, public=False, **kwargs):
        self.public = public
        super().__init__(**kwargs)

    def get(self, request, *args, **kwargs):
        serializer = RuleSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        term = serializer.validated_data["term"]
        start = serializer.validated_data["start"]
        max_results = serializer.validated_data["max_results"]
        if self.public:
            response = search_index.search_yara_rules_index(
                term, start, max_results, user=None
            )
        else:
            response = search_index.search_yara_rules_index(
                term, start, max_results, user=request.user
            )
        if response.status_code == 200:
            if self.public:
                return Response(
                    search_index.contextualize_yara_rules_search_response(
                        response, term, start, max_results, user=None
                    ),
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    search_index.contextualize_yara_rules_search_response(
                        response, term, start, max_results, user=request.user
                    ),
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
        yara_rule = database.lookup_yara_rule(rule_id, user=request.user)
        if not yara_rule:
            yara_rule = database.lookup_yara_rule(rule_id, user=None)
        if not yara_rule:
            return Response(
                {"error": "Rule not found"}, status=status.HTTP_404_NOT_FOUND
            )
        if yara_rule:
            parsed_response = database.parse_lookup_rule_response(yara_rule)
            if parsed_response.get("yara_rule"):
                return Response(parsed_response, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "Could not locate a rule with this id."},
                    status=status.HTTP_404_NOT_FOUND,
                )
