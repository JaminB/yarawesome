import re

import django.db.utils
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import TestBinary, TestBinaryScan
from .serializers import (
    TestBinarySerializer,
    ScanBinaryRequest,
    ScanBinaryLookupRequest,
)
from .tasks import match_yara_rules
from ..rule_collections.models import YaraRuleCollection


class PersonalBinaryUploadsResource(APIView):
    """
    A view to get information about a specific test binary.
    """

    def get(self, request, *args, **kwargs):
        """
        Get a list of all test binaries uploaded by the current user.
        """
        user_test_binary_uploads = sorted(
            [
                {
                    "id": binary.binary_id,
                    "name": binary.name,
                    "uploaded_time": binary.created_time.isoformat(),
                }
                for binary in TestBinary.objects.filter(user=request.user)
            ],
            key=lambda x: x["uploaded_time"],
            reverse=True,
        )
        seen_binary_ids = set()
        deduplicated_user_test_binary_uploads = []

        for test_binary in user_test_binary_uploads:
            if test_binary["id"] in seen_binary_ids:
                continue
            seen_binary_ids.add(test_binary["id"])
            deduplicated_user_test_binary_uploads.append(test_binary)
        return Response(
            status=status.HTTP_200_OK, data=deduplicated_user_test_binary_uploads[:100]
        )


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
            try:
                serializer.save(user=user, name=alphanumeric_filename)
            except django.db.utils.IntegrityError:
                return Response(
                    {"error": "This binary has already been uploaded."},
                    status=status.HTTP_409_CONFLICT,
                )
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
        collection_ids = serializer.validated_data.get("collection_ids", [])
        test_binary_obj = TestBinary.objects.filter(binary_id=binary_id).first()
        if not test_binary_obj:
            return Response(
                {"error": "This binary has not been uploaded."},
                status=status.HTTP_404_NOT_FOUND,
            )
        test_binary_scan_obj = TestBinaryScan.objects.create(
            binary=test_binary_obj, user=request.user
        )

        test_binary_scan_obj.collections.add(
            *YaraRuleCollection.objects.filter(id__in=collection_ids)
        )
        test_binary_scan_obj.save()
        scan_id = test_binary_scan_obj.id
        match_yara_rules.delay(
            scan_id,
            binary_id,
            collection_ids=collection_ids,
            user_id=request.user.id,
        )
        return Response(
            status=status.HTTP_201_CREATED,
            data={
                "scan": {
                    "id": scan_id,
                    "binary_id": binary_id,
                    "collection_ids": collection_ids,
                }
            },
        )
