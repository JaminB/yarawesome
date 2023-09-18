from rest_framework import serializers
from apps.rule_lab.models import TestBinary


class TestBinarySerializer(serializers.ModelSerializer):
    class Meta:
        model = TestBinary
        fields = ["file"]
