import re
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .serializers import TestBinarySerializer


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
