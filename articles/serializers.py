from rest_framework import serializers


class ArticleBaseSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    title = serializers.CharField()
    tags = serializers.ListField(child=serializers.CharField())
    author = serializers.CharField()


class ArticleCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    content = serializers.CharField()
    tags = serializers.ListField(child=serializers.CharField(max_length=30))


class ArticleDetailSerializer(ArticleBaseSerializer):
    content = serializers.CharField()
    created_at = serializers.DateTimeField(required=False, allow_null=True)


class ArticleShortSerializer(ArticleBaseSerializer):
    pass


class ArticleDetailNoCreatedSerializer(ArticleBaseSerializer):
    content = serializers.CharField()
