import json

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.management.commands import publish_collection_index
from core.models import YaraRule, YaraRuleCollection

from .serializers import (
    YaraRuleCollectionDeleteRequest,
    YaraRuleCollectionPublishRequest,
)


class YaraRuleCollectionResource(APIView):
    """
    A view to view a YARA rule collection.
    """

    def delete(self, request, *args, **kwargs):
        serializer = YaraRuleCollectionDeleteRequest(data=kwargs)
        serializer.is_valid(raise_exception=True)
        collection_id = serializer.validated_data["collection_id"]
        yara_rule_collection = YaraRuleCollection.objects.filter(
            id=collection_id, user=request.user
        ).first()
        if not yara_rule_collection:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={"error": "Collection not found."},
            )
        yara_rule_collection.delete()
        return Response(status=status.HTTP_200_OK, data={"deleted": True})


class PublishYaraRuleCollectionResource(APIView):
    """
    A view to publish a YARA rule collection, and all of its rules to the public.
    """

    def put(self, request, *args, **kwargs):
        """
        Publish a YARA rule collection.
        """
        set_to_public = True
        serializer = YaraRuleCollectionPublishRequest(data=kwargs)
        serializer.is_valid(raise_exception=True)
        collection_id = serializer.validated_data["collection_id"]
        yara_rule_collection = YaraRuleCollection.objects.filter(
            id=collection_id, user=request.user
        ).first()
        request_body = request.body.decode("utf-8")
        if request_body:
            try:
                data = json.loads(request_body)
            except json.JSONDecodeError:
                return Response({"error": "Invalid JSON data"}, status=400)
            if not data.get("public"):
                set_to_public = False
        yara_rule_collection.public = set_to_public
        if not publish_collection_index.build_rule_index_from_private_collection(
            yara_rule_collection, request.user
        ):
            return Response(
                {"error": "Could not build the rule index."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        yara_rule_collection.save()
        yara_rules = YaraRule.objects.filter(collection=yara_rule_collection)

        for yara_rule in yara_rules:
            yara_rule.public = set_to_public
            yara_rule.save()
        return Response(
            data={"published": yara_rule_collection.public},
            status=status.HTTP_200_OK,
        )

    def get(self, request, *args, **kwargs):
        """
        Check if a YARA rule collection is published.
        """
        serializer = YaraRuleCollectionPublishRequest(data=kwargs)
        serializer.is_valid(raise_exception=True)
        collection_id = serializer.validated_data["collection_id"]
        yara_rule_collection = YaraRuleCollection.objects.filter(
            id=collection_id, user=request.user
        ).first()
        if not yara_rule_collection:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(
            data={"published": yara_rule_collection.public},
            status=status.HTTP_200_OK,
        )