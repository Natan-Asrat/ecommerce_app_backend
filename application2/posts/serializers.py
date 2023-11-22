from rest_framework import serializers
from .models import *
from django.db.models import Count
from collections import OrderedDict
from datetime import datetime, timedelta
from django.utils import timezone
from itertools import groupby
import pytz
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
timezone = pytz.timezone('UTC')
SECONDS_BEFORE_OFFLINE = 5 * 60
class UserSerializer(serializers.ModelSerializer):
    brandName = serializers.SerializerMethodField()
    profilePicture = serializers.SerializerMethodField()
    online = serializers.SerializerMethodField()
    last_seen = serializers.SerializerMethodField()
    def get_profilePicture(self, obj):
        image = obj.profilePicture
        if image:
            return image.url
        return None
    def get_brandName(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    def get_last_seen(self, obj):
        last_seen = obj.last_seen.astimezone(timezone)
        now = datetime.now().astimezone(timezone)
        hours = int((now - last_seen).total_seconds() // 3600)
        return hours
    def get_online(self, obj):
        last_seen = obj.last_seen.astimezone(timezone)
        now = datetime.now().astimezone(timezone)
        seconds = int((now - last_seen).total_seconds())
        if seconds < SECONDS_BEFORE_OFFLINE:
            return True
        return False
    class Meta:
        model = User
        fields = ['id', 'profilePicture', 'brandName', 'last_seen', 'online']

class PostSerializer(serializers.ModelSerializer):
    postId = serializers.UUIDField(read_only = True)
    hasLiked = serializers.BooleanField(read_only = True)
    hasSaved = serializers.BooleanField(read_only = True)
    categories = serializers.SerializerMethodField()
    originalPrice = serializers.SerializerMethodField()
    discountedPrice = serializers.SerializerMethodField()
    sellerId = UserSerializer()
    image = serializers.SerializerMethodField(read_only = True)
    class Meta:
        model = Post
        fields = [
            'postId', 
            'title', 
            'description',
            'link',  
            'originalPrice',
            'discountedPrice',
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
    def get_originalPrice(self, obj):
        return get_originalPrice_string(obj)
    def get_discountedPrice(self, obj):
        return get_discountedPrice_string(obj)
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
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.discountedPrice is None:
            representation.pop('discountedPrice')
        return representation
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
    sellerId = UserSerializer(read_only = True)
    images = serializers.SerializerMethodField(read_only = True)
    originalPrice = serializers.SerializerMethodField()
    discountedPrice = serializers.SerializerMethodField()
    class Meta:
        model = Post
        fields = [
            'postId', 
            'title', 
            'description',
            'link', 
            'originalPrice',
            'discountedPrice',
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
    def get_originalPrice(self, obj):
        return get_originalPrice_string(obj)
    def get_discountedPrice(self, obj):
        return get_discountedPrice_string(obj)
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
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.discountedPrice is None:
            representation.pop('discountedPrice')
        return representation
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
            num = user.phoneNumber
            if num is not None:
                return num
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
   

class WideCardSerializer(serializers.ModelSerializer):
    sellerId = UserSerializer()
    image = serializers.SerializerMethodField(read_only = True)
    attributes = serializers.SerializerMethodField(read_only = True)
    class Meta:
        model = Post
        fields = ['postId', 'title', 'sellerId', 
            'nextIconAction', 'link', 'image', 'attributes']
    def get_image(self, obj):
        image = Image.objects.filter(post = obj).order_by('order').first()
        if image:
            return image.image.url
        return None
    def get_attributes(self, obj):
        attr = []
        if obj.discountedPrice is not None:
            attr.append(get_discountedPrice_string(obj))
            attr.append(strike(get_originalPrice_string(obj)))
        else:
            attr.append(get_originalPrice_string(obj))
        if obj.categoryId is not None:
            attr.append(str(obj.categoryId))
            parent = obj.categoryId.parent
            if parent is not None:
                attr.append(str(parent))
        return attr

class FavouriteSerializer(serializers.Serializer):
    favourites = serializers.SerializerMethodField()
    def get_favourites(self, obj):
        return WideCardSerializer(obj.post_id).data
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data['favourites']

class LikedListSerializer(serializers.Serializer):
    liked = serializers.SerializerMethodField()
    def get_liked(self, obj):
        return WideCardSerializer(obj.post_id).data
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data['liked']

class ProfileSerializer(serializers.ModelSerializer):
    brandName = serializers.SerializerMethodField()
    profilePicture = serializers.SerializerMethodField()
    online = serializers.SerializerMethodField()
    last_seen = serializers.SerializerMethodField()
    adCount = serializers.SerializerMethodField()
    followerCount = serializers.SerializerMethodField()
    followingCount = serializers.SerializerMethodField()
    hasWebsite = serializers.SerializerMethodField()
    def get_hasWebsite(self, obj):
        link = obj.website
        if link is not None and link != "":
            return True
        return False
    def get_adCount(self, obj):
        return obj.seller.count()
    def get_followerCount(self, obj):
        return obj.followers.count()
    def get_followingCount(self, obj):
        return obj.following.count()
    def get_profilePicture(self, obj):
        image = obj.profilePicture
        if image:
            return image.url
        return None
    def get_brandName(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    def get_last_seen(self, obj):
        last_seen = obj.last_seen.astimezone(timezone)
        now = datetime.now().astimezone(timezone)
        hours = int((now - last_seen).total_seconds() // 3600)
        return hours
    def get_online(self, obj):
        last_seen = obj.last_seen.astimezone(timezone)
        now = datetime.now().astimezone(timezone)
        seconds = int((now - last_seen).total_seconds())
        if seconds < SECONDS_BEFORE_OFFLINE:
            return True
        return False
    class Meta:
        model = User
        fields = ['id', 'profilePicture', 'brandName', 'phoneNumber', 'last_seen', 'online', 'adCount', 'followerCount', 'followingCount', 'hasWebsite', 'website']
  

def get_originalPrice_string(obj):
    return str(obj.currency) + ' ' + str(obj.price)
def get_discountedPrice_string(obj):
    return str(obj.discountCurrency) + ' ' + str(obj.discountedPrice)

def strike(text):
    text = " " + text + " "
    return ''.join([u'\u0336{}'.format(c) for c in text])