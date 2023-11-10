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
class IICF_PostSerializer(serializers.ModelSerializer):
    postId = serializers.UUIDField(read_only = True)
    categoryId = CategorySerializer()
    sellerId = UserSerializer()
    class Meta:
        model = Post
        fields = '__all__'
    
class IICF(serializers.ModelSerializer):
    post_id = IICF_PostSerializer()
    hasLiked = serializers.BooleanField()
    hasSaved = serializers.BooleanField()
    class Meta:
        model = InteractionUserToPost
        fields = ['strength', 'post_id', 'hasLiked', 'hasSaved']
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        return {'strength': ret['strength'],'hasLiked': ret['hasLiked'],'hasSaved': ret['hasSaved'], **ret['post_id']}
class InteractionSerializer(serializers.ModelSerializer):
    # post_title = serializers.CharField(max_length=255)
    class Meta:
        model = Interaction
        fields = ['action_performed_on_id']