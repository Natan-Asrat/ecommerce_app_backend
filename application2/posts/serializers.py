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


    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     if data['tag'] == 'iicf':
    #         post_serializer = PostSerializer(instance)
    #         data['post'] = post_serializer.to_representation(post_serializer.instance)
    #     return data
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
        fields = ['strength_sum', 'post_id', 'hasLiked', 'hasSaved']
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        return {'rank': ret['strength_sum'],'hasLiked': ret['hasLiked'],'hasSaved': ret['hasSaved'], **ret['post_id']}
class InteractionSerializer(serializers.ModelSerializer):
    # post_title = serializers.CharField(max_length=255)
    class Meta:
        model = Interaction
        fields = ['action_performed_on_id']
# class RecommendedSerializer(serializers.Serializer):
#     tag = serializers.ChoiceField()
#     postId = serializers.UUIDField()
#     title = serializers.CharField()
#     description = serializers.CharField()
#     link = serializers.CharField()
#     price = serializers.IntegerField()
#     currency = serializers.CharField()
#     hasDiscount = serializers.BooleanField()
#     discountedPrice = serializers.IntegerField()
#     discountCurrency = serializers.CharField()
#     categoryId = serializers.UUIDField()
#     sellerId = serializers.UUIDField()
#     likes = serializers.IntegerField()
#     engagement = serializers.IntegerField()
#     nextIconAction = serializers.CharField()
#     tag = serializers.ChoiceField()
class RecommendedSerializer(serializers.Serializer):
    postId = serializers.UUIDField()
    tag = serializers.CharField()
    rank = serializers.DecimalField(decimal_places=2, max_digits=10)

