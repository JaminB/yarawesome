from rest_framework.generics import CreateAPIView
from rest_framework.parsers import MultiPartParser
from .serializers import SuricataRuleUploadSerializer


class UploadRulesResource(CreateAPIView):
    serializer_class = SuricataRuleUploadSerializer
    parser_classes = [MultiPartParser]

    def perform_create(self, serializer):
        serializer.save()
