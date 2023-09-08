from rest_framework import serializers


class RuleCollectionPublishRequestSerializer(serializers.Serializer):
    collection_id = serializers.IntegerField(min_value=1)
