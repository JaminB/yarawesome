from rest_framework import serializers


class RuleEditorLookupSerializer(serializers.Serializer):
    rule_id = serializers.CharField(max_length=32)


class RuleEditorSaveSerializer(serializers.Serializer):
    term = serializers.CharField(max_length=128, default="*")
    start = serializers.IntegerField(min_value=0, default=0)
    max_results = serializers.IntegerField(min_value=1, default=10)
