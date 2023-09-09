from rest_framework import serializers


class YaraRuleCollectionDeleteRequest(serializers.Serializer):
    collection_id = serializers.IntegerField(min_value=1)


class YaraRuleCollectionPublishRequest(serializers.Serializer):
    collection_id = serializers.IntegerField(min_value=1)
