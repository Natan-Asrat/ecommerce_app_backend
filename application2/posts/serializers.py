from rest_framework import serializers
from .models import *
app_name = __package__.split('.')[-1]

class EmptySerializer(serializers.Serializer):
    pass
class CategorySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only = True)
    class Meta:
        model = Category
        fields = ['id', 'name']

class CategoryListSerializer(serializers.Serializer):
    categories = serializers.ListField
    def to_representation(self, instance):
        category_names = []
        for item in instance:
            category_names.append(item['name'])
        return category_names
    def to_internal_value(self, data):
        category_names = data
        validated_data = []
        parent = None
        for name in category_names:
            category = Category.objects.filter(name = name, parent = parent).first()
            if not category:
                category = Category.objects.create(name = name, parent = parent)
            validated_data.append({'name': name, 'parent': parent})
            parent = category
        return validated_data
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
    hasLiked = serializers.BooleanField(read_only = True)
    hasSaved = serializers.BooleanField(read_only = True)
    categories = serializers.SerializerMethodField()
    sellerId = UserSerializer()
    class Meta:
        model = Post
        fields = [
            'postId', 
            'title', 
            'description',
            'link', 
            'price',
            'currency', 
            'discountedPrice',
            'discountCurrency', 
            'categoryId',
            'categories', 
            'sellerId',
            'likes',
            'engagement', 
            'nextIconAction', 
            'hasDiscount',
            'hasLiked', 
            'hasSaved'
            ]
    def get_categories(self, obj):
        category = obj.categoryId
        ancestors = []
        depth = 0
        while category and depth < 10:
            ancestors.append(category.name)
            category = category.parent
            depth+=1
        ancestors = list(reversed(ancestors))
        return ancestors
    
    # def create(self, validated_data):
    #     category_names = validated_data.pop('categoryId')
        # last_category = None
        # for name in category_names:
        #     category, _ = Category.objects.get_or_create(name = name, parent = last_category)
        #     last_category = category
        # validated_data['categoryId'] = last_category
    #     # post = Post.objects.create(**validated_data)
    #     instance = self.Meta.model(**validated_data)
    #     instance.save()
    #     return instance
MAX_CATEGORY_LEVELS = 5
class NewPostSerializer(serializers.ModelSerializer):
    categories = serializers.ListField(child = serializers.CharField(), required = False)
    postId = serializers.UUIDField(read_only = True)
    class Meta:
        model = Post
        fields = [
            'postId',
            'title', 
            'description',
            'link', 
            'price',
            'currency', 
            'discountedPrice',
            'discountCurrency', 
            'categoryId',
            'categories', 
            'sellerId',
            'likes',
            'engagement', 
            'nextIconAction', 
            'hasDiscount'
            ]
    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request else None
        if user and (user.id != validated_data["sellerId"].id) and not user.has_perm(f'{app_name}.edit_and_add_posts_of_others'):
            raise serializers.ValidationError("This is not your account, so you cant post with it")
        else:
            category_names = validated_data.pop('categories')
            if not isinstance(category_names, list):
                category_names = [category_names]
            if len(category_names)>MAX_CATEGORY_LEVELS:
                category_names = category_names[:MAX_CATEGORY_LEVELS]
            last_category = None
            # category_names = category_names[:-1]
            for name in category_names:
                category, _ = Category.objects.get_or_create(name = name, parent = last_category)
                last_category = category
            
            validated_data['categoryId'] = last_category
            print(validated_data)
            instance = self.Meta.model(**validated_data)
            instance.save()
            return instance

class EditPostSerializer(serializers.ModelSerializer):
    categories = serializers.ListField(child = serializers.CharField(), required = False)    
    postId = serializers.UUIDField(read_only = True)

    class Meta:
        model = Post
        fields = [
            'postId',
            'title', 
            'description',
            'link', 
            'price',
            'currency', 
            'discountedPrice',
            'discountCurrency', 
            'categoryId',
            'categories', 
            'sellerId',
            'likes',
            'engagement', 
            'nextIconAction', 
            'hasDiscount'
            ]
    def update(self, instance, validated_data):
        request = self.context.get('request')
        user = request.user if request else None
        if user and (user.id != instance.sellerId.id) and not user.has_perm(f'{app_name}.edit_and_add_posts_of_others'):
            raise serializers.ValidationError("This is not your post, so you cant edit it")
        else:
            category_names = validated_data.pop('categories')
            if not isinstance(category_names, list):
                category_names = [category_names]
            if len(category_names)>MAX_CATEGORY_LEVELS:
                category_names = category_names[:MAX_CATEGORY_LEVELS]
            last_category = None
            for name in category_names:
                category, _ = Category.objects.get_or_create(name = name, parent = last_category)
                last_category = category
            
            validated_data['categoryId'] = last_category
            print(validated_data)
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance
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
    class Meta(PostSerializer.Meta):
        fields = ['postId', 
            'title', 
            'description',
            'link', 
            'price',
            'currency', 
            'discountedPrice',
            'discountCurrency', 
            'categoryId',
            'categories', 
            'sellerId',
            'likes',
            'engagement', 
            'nextIconAction', 
            'hasDiscount',
            'hasLiked', 
            'hasSaved',
            'tag', 
            'rank'
            ]