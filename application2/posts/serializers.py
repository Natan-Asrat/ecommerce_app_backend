from rest_framework import serializers
from .models import *
from django.db.models import Count
from collections import OrderedDict
from datetime import datetime, timedelta
from django.utils import timezone
from itertools import groupby
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
# class LikeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Like
#         fields = "__all__"
class UserSerializer(serializers.ModelSerializer):
    brandName = serializers.SerializerMethodField()
    profilePicture = serializers.SerializerMethodField()
    def get_profilePicture(self, obj):
        return obj.profilePicture.url
    def get_brandName(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    class Meta:
        model = User
        fields = ['id', 'profilePicture', 'brandName']

class PostSerializer(serializers.ModelSerializer):
    postId = serializers.UUIDField(read_only = True)
    hasLiked = serializers.BooleanField(read_only = True)
    hasSaved = serializers.BooleanField(read_only = True)
    categories = serializers.SerializerMethodField()
    sellerId = UserSerializer()
    image = serializers.SerializerMethodField(read_only = True)
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
            'hasSaved',
            'image'
            ]
    def get_image(self, obj):
        image = Image.objects.filter(post = obj).order_by('order').first()
        if image:
            return image.image.url
        return None
    def get_categories(self, obj):
        category = obj.categoryId
        ancestors = []
        depth = 0
        while category and depth < MAX_CATEGORY_LEVELS:
            ancestors.append(category.name)
            category = category.parent
            depth+=1
        ancestors = list(reversed(ancestors))
        return ancestors
class ImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    def get_image_url(self, obj):
        return obj.image.url
    class Meta:
        model = Image
        fields = ['image_url']
class PostDetailSerializer(serializers.ModelSerializer):
    postId = serializers.UUIDField(read_only = True)
    hasLiked = serializers.BooleanField(read_only = True)
    hasSaved = serializers.BooleanField(read_only = True)
    categories = serializers.SerializerMethodField()
    sellerId = UserSerializer()
    images = serializers.SerializerMethodField(read_only = True)
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
            'hasSaved',
            'images'
            ]
    def get_images(self, obj):
        images = Image.objects.filter(post = obj).order_by('order')
        # serializer = ImageSerializer(data = images, many = True)
        # serializer.is_valid(raise_exception=True)
        # return serializer.data
        print(images)
        if images:
            return [image.image.url for image in images]
        return []
    def get_categories(self, obj):
        category = obj.categoryId
        ancestors = []
        depth = 0
        while category and depth < MAX_CATEGORY_LEVELS:
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
        
        
class LikePostSerializer(serializers.ModelSerializer):
    likes = serializers.SerializerMethodField(read_only = True)
    hasLiked = serializers.SerializerMethodField(read_only = True)
    post_id = serializers.UUIDField(required = False)
    user_id = serializers.UUIDField(required = False)
    class Meta:
        model = Like
        fields = ['user_id', 'post_id', 'likes', 'hasLiked']
    
    def create(self, validated_data):
        like, created = Like.objects.get_or_create(**validated_data)
        return like
    def get_likes(self, obj):
        if isinstance(obj, OrderedDict) :
            post_id = obj['post_id']
        else:            
            post_id = obj.post_id
        return Like.objects.filter(post_id=post_id).count()
    def get_hasLiked(self, obj):
        user = self.context['request'].user
        if isinstance(obj, OrderedDict) :
            post_id = obj['post_id']
        else:            
            post_id = obj.post_id
        return Like.objects.filter(post_id = post_id, user_id = user.id).exists()
    
    # def create(self, validated_data):
    #     request = self.context['request']
    #     user = request.user
    #     validated_data['user_id'] = user.id
    #     return super().create(validated_data)
class NotificationSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    profileId = serializers.UUIDField()
    postId = serializers.UUIDField()
    notificationId = serializers.SerializerMethodField()
    phoneNumber = serializers.SerializerMethodField()
    link = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'notificationId', 
            'link', 
            'phoneNumber', 
            'message', 
            'image', 
            'action', 
            'seen', 
            'buttonPressed', 
            'profileId', 
            'postId']

    def get_phoneNumber(self, obj):
        if obj['profileId'] is not None:
            user = User.objects.get(id = obj['profileId'])
            if user.phone is not None:
                return user.phone
        return None
    def get_link(self, obj):
        if obj['action'] == 'L':
            post = Post.objects.get(postId = obj['postId'])
            return post.link
        return None
    def get_notificationId(self, obj):
        return obj['id']
    def get_image(self, obj):
        if obj['image_from'] == 'P':
            image = Image.objects.filter(post=obj['postId']).first()
            if image:
                return image.image.url
        elif obj['image_from'] == 'U':
            image = User.objects.get(id=obj['profileId']).profilePicture
            print(image)
            if image:
                return image.url
        return None
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        print(instance)
        if representation['postId'] is None:
            representation.pop('postId')
        if representation['profileId'] is None:
            representation.pop('profileId')
        if representation['phoneNumber'] is None:
            representation.pop('phoneNumber')
        if representation['link'] is None:
            representation.pop('link')
        return representation

class NotificationDaySerializer(serializers.ModelSerializer):
    daysBefore = serializers.IntegerField()
    notificationsThatDay = NotificationSerializer(many=True)

    class Meta:
        model = Notification
        fields = ('daysBefore', 'notificationsThatDay')

    def to_representation(self, instance):
        # Get the current date and time in the user's timezone
        now = timezone.now()
        # Group the notifications by the number of days before the notification was created
        # grouped_notifications = groupby(instance, lambda x: (now - x.date).days)
        print(instance)
        # # Create a list of dictionaries for each day
        # days = []
        # for days_before, notifications in grouped_notifications:
        #     day = {
        #         "daysBefore": str(days_before),
        #         "notificationsThatDay": NotificationSerializer(list(notifications), many=True).data
        #     }
        #     days.append(day)

        return instance