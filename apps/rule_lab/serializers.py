from rest_framework import serializers
from apps.core.models import TestBinary


class TestBinarySerializer(serializers.ModelSerializer):
    class Meta:
        model = TestBinary
        fields = "__all__"
