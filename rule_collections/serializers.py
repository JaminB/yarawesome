from rest_framework import serializers


class YaraRuleCollectionDeleteRequest(serializers.Serializer):
    collection_id = serializers.IntegerField(min_value=1)


class YaraRuleCollectionUpdateRequest(serializers.Serializer):
    collection_id = serializers.IntegerField(min_value=1)
    name = serializers.CharField(max_length=128)
    description = serializers.CharField(max_length=512, required=True)
    icon = serializers.IntegerField(min_value=1, required=True)


class YaraRuleCollectionPublishRequest(serializers.Serializer):
    collection_id = serializers.IntegerField(min_value=1)
