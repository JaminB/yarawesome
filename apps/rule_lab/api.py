import re
import json
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from yarawesome.utils import database
from apps.rules.models import YaraRule, YaraRuleCollection
from .serializers import (
    TestBinarySerializer,
    ScanBinaryRequest,
    ScanBinaryLookupRequest,
)
from .models import TestBinary
from .tasks import match_yara_rules


class CreateUploadBinaryResource(CreateAPIView):
    """
    A view to create an UploadTestBinary instance.
    """

    serializer_class = TestBinarySerializer
    parser_classes = [MultiPartParser]

    def create(self, request, *args, **kwargs):
        alphanumeric_filename = re.sub(
            r"[^a-zA-Z0-9.]", "_", request.data["file"].name
        ).lower()
        serializer = self.get_serializer(data=request.data)
        user = serializer.context["request"].user

        if serializer.is_valid():
            serializer.save(user=user, name=alphanumeric_filename)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScanUploadBinaryResource(APIView):
    """
    A view to get information about a specific test binary.
    """

    def post(self, request, *args, **kwargs):
        """
        Given a json payload containing the id of the test binary to scan and an array of rule_ids and collection_ids to run against
        the test binary, run the rules and return the results.
        """
        scan_lookup_binary_request = ScanBinaryLookupRequest(data=kwargs)
        scan_lookup_binary_request.is_valid(raise_exception=True)
        binary_id = scan_lookup_binary_request.validated_data["binary_id"]
        serializer = ScanBinaryRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        rule_ids = serializer.validated_data.get("rule_ids", [])
        collection_ids = serializer.validated_data.get("collection_ids", [])
        matches = match_yara_rules.delay(
            binary_id,
            rule_ids=rule_ids,
            collection_ids=collection_ids,
            user_id=request.user.id,
        )
        return Response(
            status=status.HTTP_201_CREATED,
            data={},
        )
