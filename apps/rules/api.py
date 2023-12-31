import django.db
from django.forms.models import model_to_dict
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from yarawesome.utils import database, search_index
from apps.rules.models import YaraRule
from apps.rule_import.models import ImportYaraRuleJob
from apps.rule_collections.models import YaraRuleCollection
from .serializers import RuleCloneSerializer, RuleLookupSerializer, RuleSearchSerializer
from .tasks import clone_rule


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


class RuleResource(APIView):
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


class RuleCloneResource(APIView):
    def put(self, request, *args, **kwargs):
        serializer = RuleCloneSerializer(data=kwargs)
        serializer.is_valid(raise_exception=True)
        rule_id = serializer.validated_data["rule_id"]
        yara_rule = database.lookup_yara_rule(rule_id)
        try:
            personal_cloned_ruled_collection = YaraRuleCollection.objects.get(
                user=request.user, name="Cloned Rules"
            )
        except YaraRuleCollection.DoesNotExist:
            new_import_job = ImportYaraRuleJob(user=request.user)
            new_import_job.save()
            personal_cloned_ruled_collection = YaraRuleCollection.objects.create(
                user=request.user,
                name="Cloned Rules",
                description="A collection of cloned rules.",
                icon=1,
                import_job=new_import_job,
            )
        if not yara_rule:
            return Response(
                {"error": "Rule not found"}, status=status.HTTP_404_NOT_FOUND
            )
        clone_rule.delay(
            rule_id,
            model_to_dict(personal_cloned_ruled_collection),
            {"id": request.user.id},
        )
        return Response(
            status=status.HTTP_201_CREATED,
            data={
                "collection": {
                    "id": personal_cloned_ruled_collection.id,
                    "name": personal_cloned_ruled_collection.name,
                    "description": personal_cloned_ruled_collection.description,
                    "icon": personal_cloned_ruled_collection.icon,
                },
                "rule": {
                    "rule_id": yara_rule.rule_id,
                },
                "import_job": personal_cloned_ruled_collection.import_job.id,
                "message": "Cloned rule successfully to 'Cloned Rules' collection.",
            },
        )
