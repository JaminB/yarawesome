from rest_framework import serializers


class RuleSearchSerializer(serializers.Serializer):
    term = serializers.CharField(max_length=128, default="*")
    start = serializers.IntegerField(min_value=0, default=0)
    max_results = serializers.IntegerField(min_value=1, default=10)
