from rest_framework import serializers
from .models import *

class EmptySerializer(serializers.Serializer):
    pass
class CategorySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only = True)
    class Meta:
        model = Category
        fields = ['id', 'name']

class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = "__all__"
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id']

class PostSerializer(serializers.ModelSerializer):
    postId = serializers.UUIDField(read_only = True)
    hasLiked = serializers.BooleanField()
    hasSaved = serializers.BooleanField()
    categoryId = CategorySerializer()
    sellerId = UserSerializer()
    class Meta:
        model = Post
        fields = '__all__'
class RecommendedSerializer(serializers.Serializer):
    postId = serializers.UUIDField()
    tag = serializers.CharField(max_length = 10)
    rank = serializers.DecimalField(decimal_places=2, max_digits=10)
class GetR(serializers.Serializer):
    postId = serializers.UUIDField()
    sum = serializers.DecimalField(decimal_places=2, max_digits=10)

class SendRecommendedPosts(PostSerializer):
    tag = serializers.CharField(max_length = 10)
    rank = serializers.DecimalField(decimal_places=2, max_digits=10)