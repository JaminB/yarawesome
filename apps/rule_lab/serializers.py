from rest_framework import serializers
from apps.rule_lab.models import TestBinary


class TestBinarySerializer(serializers.ModelSerializer):
    class Meta:
        model = TestBinary
        fields = ["file"]


class ScanBinaryRequest(serializers.Serializer):
    rule_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1), required=False
    )
    collection_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1), required=False
    )

    def validate(self, data):
        rule_ids = data.get("rule_ids")
        collection_ids = data.get("collection_ids")

        if not rule_ids and not collection_ids:
            raise serializers.ValidationError(
                "Either rule_ids or collection_ids must be provided."
            )
        return data


class ScanBinaryLookupRequest(serializers.Serializer):
    binary_id = serializers.CharField(max_length=32)
