from rest_framework import serializers
from rest_framework.fields import empty
from .models import *
from django.db.models import Count
from collections import OrderedDict
from datetime import datetime, timedelta
from django.utils import timezone
from itertools import groupby
from rest_framework.reverse import reverse
import pytz
from . import queries
import math
from . import authentication
app_name = __package__.split('.')[-1]


timezone = pytz.timezone('UTC')
SECONDS_BEFORE_OFFLINE = 5 * 60
MAX_CATEGORY_LEVELS = 5
USERNAME_TO_LINK_JSON_BOOLEAN = True


WEB_BASE_URL = "https://emishopapp.onrender.com/"
PROFILE_WEB_URL = WEB_BASE_URL + "profile/?s="
POST_WEB_URL = WEB_BASE_URL + "post/?p="




class EmptySerializer(serializers.Serializer):
    pass
class CategoryForTraversalSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only = True)
    children = serializers.SerializerMethodField()
    parent = serializers.SerializerMethodField()
    class Meta:
        model = Category
        fields = ['id', 'name', 'children', 'parent']
    def get_children(self, obj):
        request = self.context.get('request')
        url = reverse('categories-detail', kwargs={'pk': obj.id}, request=request)
        return url
    def get_parent(self, obj):
        request = self.context.get('request')
        parent = obj.parent
        if parent is not None:
            if parent.parent is not None:
                url = reverse('categories-detail', kwargs={'pk': parent.parent.id}, request=request)
                return url
            else:
                url = reverse('categories-list', request=request)
                return url
        return None
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

class UserSerializer(serializers.ModelSerializer):
    brandName = serializers.SerializerMethodField()
    profilePicture = serializers.SerializerMethodField()
    online = serializers.SerializerMethodField()
    last_seen = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
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
    def get_is_admin(self, obj):
        return obj.is_superuser
    class Meta:
        model = User
        fields = ['id', 'profilePicture', 'is_admin', 'brandName', 'last_seen', 'online', 'username', 'phoneNumber']
SHOW_SIMILAR_POSTS_JSON_BOOLEAN = True
class PostSerializer(serializers.ModelSerializer):
    postId = serializers.UUIDField(read_only = True)
    hasLiked = serializers.BooleanField(read_only = True)
    hasSaved = serializers.BooleanField(read_only = True)
    categories = serializers.SerializerMethodField()
    originalPrice = serializers.SerializerMethodField()
    discountedPrice = serializers.SerializerMethodField()
    sellerId = UserSerializer()
    image = serializers.SerializerMethodField(read_only = True)
    link = serializers.SerializerMethodField(read_only=True)

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
    def get_link(self, obj):
        if obj.link == "":
            return POST_WEB_URL + str(obj.postId)
        return obj.link
    def get_originalPrice(self, obj):
        return get_originalPrice_string(obj)
    def get_discountedPrice(self, obj):
        return get_discountedPrice_string(obj)
    def get_image(self, obj):
        # image = Image.objects.filter(post = obj).order_by('order').first()
        image = obj.postImage.first()
        if image:
            return image.image.url
        return None
    def get_categories(self, obj):
        category = obj.categoryId
        ancestors = []
        depth = 0
        while category and depth < MAX_CATEGORY_LEVELS:
            c = CategorySerializer(category, many = False).data
            ancestors.append(c)
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
        image = obj.image
        if image:
            return image.url
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
    link = serializers.SerializerMethodField(read_only=True)
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
    def get_link(self, obj):
        if obj.link == "":
            return POST_WEB_URL + str(obj.postId)
        return obj.link
    def get_originalPrice(self, obj):
        return get_originalPrice_string(obj)
    def get_discountedPrice(self, obj):
        return get_discountedPrice_string(obj)
    def get_images(self, obj):
        images = obj.postImage.all().values('image').order_by('order')
        images = list(images)
        if images:
            return [image['image'].url for image in images]
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
        representation['showSimilarPosts'] = SHOW_SIMILAR_POSTS_JSON_BOOLEAN

        return representation

class NewPostSerializer(serializers.ModelSerializer):
    categories = serializers.ListField(child = serializers.CharField(), required = False)
    sellerId = UserSerializer(read_only = True)
    postId = serializers.UUIDField(read_only = True)
    # imageBitmaps = serializers.ListField(child = serializers.ImageField(), required = False)
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
            'nextIconAction', 
            'hasDiscount',
            # 'imageBitmaps'
            ]
    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request else None
        images = request.FILES.getlist('imageBitmaps')
        if user is None:
            raise serializers.ValidationError("You need to login before posting a post")
        else:
            validated_data['sellerId'] = user
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
            instance = self.Meta.model(**validated_data)
            instance.save()
            print(f"Number of images: {len(images)}")
            for i, image in enumerate(images):
                order_number = i + 1
                image.name = f"image_{order_number}.jpg"
                obj = Image.objects.create(post=instance, image=image, order=order_number)
            return instance
        
class EditPostSerializer(serializers.ModelSerializer):
    categories = serializers.ListField(child = serializers.CharField(), required = False)    
    postId = serializers.UUIDField(read_only = True)
    chosenCategories = serializers.SerializerMethodField(read_only = True)
    nextCategories = serializers.SerializerMethodField(read_only = True)
    images = serializers.SerializerMethodField(read_only = True)
    currencies = serializers.SerializerMethodField(read_only = True)
    imageBitmaps = serializers.ListField(child = serializers.ImageField(), required = False)

    class Meta:
        model = Post
        fields = [
            'postId',
            'title', 
            'description',
            'price',
            'currency', 
            'currencies',
            'discountedPrice',
            'discountCurrency', 
            'categories',
            'nextIconAction', 
            'hasDiscount', 
            'chosenCategories',
            'nextCategories',
            'images',
            'imageBitmaps'
            ]
        
    def get_currencies(self, obj):
        choices = Post._meta.get_field('currency').choices
        return [choice[0] for choice in choices]
    def get_chosenCategories(self, obj):
        category = obj.categoryId
        ancestors = []
        depth = 0
        while category and depth < MAX_CATEGORY_LEVELS:
            c = CategorySerializer(category, many = False).data
            ancestors.append(c)
            category = category.parent
            depth+=1
        ancestors = list(reversed(ancestors))
        return ancestors
    def get_images(self, obj):
        images = obj.postImage.all().values('image').order_by('order')
        images = list(images)
        if images:
            return [image['image'].url for image in images]
        return []
    def get_nextCategories(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        category = obj.categoryId
        if user:
            data = queries.children_categories(user, category)
            serializer = CategorySerializer(data, many = True)
            return serializer.data
        return []
    def update(self, instance, validated_data):
        request = self.context.get('request')
        user = request.user if request else None
        if user is None or (user.id != instance.sellerId.id):
            raise serializers.ValidationError("This is not your post, so you cant edit it")
        else:
            category_names = validated_data.pop('categories')
            imageBitmaps = validated_data.pop('imageBitmaps')
            if not isinstance(imageBitmaps, list):
                imageBitmaps = [imageBitmaps]
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
            instance.postImage.all().delete()
            for i in range(len(imageBitmaps)):
                image = imageBitmaps[i]
                obj = Image.objects.create(post = instance, image = image, order = i+1)
            return instance
    def to_representation(self, instance):
        request = self.context.get('request')
        user = request.user if request else None
        if user and user.id != instance.sellerId.id:
            raise serializers.ValidationError("This is not your post, so you can't edit it")
        return super().to_representation(instance)
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
    image = serializers.SerializerMethodField(read_only = True)
    class Meta(PostSerializer.Meta):
        fields = ['postId', 
            'title', 
            'description',
            'link', 
            'price',
            'currency', 
            'originalPrice',
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
            'rank',
            'image'
            ]
    def get_image(self, obj):
        # image = Image.objects.filter(post = obj).order_by('order').first()
        image = obj.postImage.first()
        if image:
            return image.image.url
        return None
        
class SavePostSerializer(serializers.ModelSerializer):
    hasSaved = serializers.SerializerMethodField(read_only = True)
    post_id = serializers.UUIDField(required = False)
    user_id = serializers.UUIDField(required = False, read_only = True)
    class Meta:
        model = Like
        fields = ['user_id', 'post_id', 'hasSaved']
    
    def create(self, validated_data):
        save, created = Favourite.objects.get_or_create(**validated_data)
        

        return save
    def get_hasSaved(self, obj):
        user = self.context['request'].user
        if isinstance(obj, OrderedDict) :
            post_id = obj['post_id']
        else:            
            post_id = obj.post_id
        return Favourite.objects.filter(post_id = post_id, user_id = user.id).exists()
 
        
class LikePostSerializer(serializers.ModelSerializer):
    likes = serializers.SerializerMethodField(read_only = True)
    hasLiked = serializers.SerializerMethodField(read_only = True)
    post_id = serializers.UUIDField(required = False)
    user_id = serializers.UUIDField(required = False, read_only = True)
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

class FollowProfileSerializer(serializers.ModelSerializer):
    follows = serializers.SerializerMethodField(read_only = True)
    hasFollowed = serializers.SerializerMethodField(read_only = True)
    user_followed = serializers.UUIDField(required = False)
    user_follower = serializers.UUIDField(required = False, read_only = True)
    class Meta:
        model = Follower
        fields = ['follows', 'hasFollowed', 'user_followed', 'user_follower']
    
    def create(self, validated_data):
        follow, created = Follower.objects.get_or_create(**validated_data)
        return follow
    def get_follows(self, obj):
        if isinstance(obj, OrderedDict) :
            followed = obj['user_followed']
        else:            
            followed = obj.user_followed
        return Follower.objects.filter(user_followed=followed).count()
    def get_hasFollowed(self, obj):
        if isinstance(obj, OrderedDict) :
            user = obj['user_follower']
        else:            
            user = obj.user_follower
        if isinstance(obj, OrderedDict) :
            followed = obj['user_followed']
        else:            
            followed = obj.user_followed
        return Follower.objects.filter(user_followed = followed, user_follower = user.id).exists()

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
            if image:
                return image.url
        return None
    def to_representation(self, instance):
        representation = super().to_representation(instance)
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
        if obj.hasDiscount is True:
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
    follows = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    coins_in_words = serializers.SerializerMethodField()
    website = serializers.SerializerMethodField(read_only=True)
    def get_website(self, obj):
        if obj.website == "":
            return PROFILE_WEB_URL + str(obj.id)
        return obj.website
    def get_hasWebsite(self, obj):
        link = obj.website
        if link is not None and link != "":
            return True
        return False
    def get_adCount(self, obj):
        return obj.seller.count()
    def get_follows(self, obj):
        user = self.context.get('user')
        user_follows_profile = Follower.objects.filter(user_follower=user,user_followed=obj).exists()
        profile_follows_user = Follower.objects.filter(user_follower=obj, user_followed=user).exists()
        if user_follows_profile and profile_follows_user:
            return 2
        elif user_follows_profile:
            return -1
        elif profile_follows_user:
            return 1
        else:
            return 0
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
    def get_is_admin(self, obj):
        return obj.is_superuser
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["usernameToLink"] = USERNAME_TO_LINK_JSON_BOOLEAN
        return representation
    def get_coins_in_words(self, obj):
        return str(obj.coins) + " Coins"
    class Meta:
        model = User
        fields = ['id', 'is_admin', 'coins_in_words', 'follows', 'profilePicture', 'brandName', 'phoneNumber', 'last_seen', 'online', 'adCount', 'followerCount', 'followingCount', 'hasWebsite', 'website']
  
COIN_TO_MONEY_MULTIPLIER = 20
class SingleCategoryBidSerializer(serializers.Serializer):
    categoryId = serializers.UUIDField()
    amount = serializers.IntegerField()
    subcategoriesCount = serializers.IntegerField()
    hasChildren = serializers.BooleanField()

PRICE_PER_CATEGORY = 2
MINIMUM_TO_STANDARD_MULTIPLIER = 3
INCREMENT_MULTIPLE = 1
PREMIUM_MULTIPLIER = 1.5
COUNT_ADS_THRESHOLD_BEFORE_AVERAGING_FOR_STANDARD = 5
class AdCategoriesSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only = True)
    subcategoriesCount = serializers.IntegerField()
    countAds = serializers.IntegerField()
    hasChildren = serializers.BooleanField()
    minimumPrice = serializers.SerializerMethodField()
    standardPrice = serializers.SerializerMethodField()
    highestBid = serializers.SerializerMethodField()
    secondHighestBid = serializers.SerializerMethodField()
    thirdHighestBid = serializers.SerializerMethodField()
    premiumBidMultiplier = serializers.SerializerMethodField()
    trueForSuffixFalseForPrefixCurrency = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    incrementPrice = serializers.SerializerMethodField()
    class Meta:
        model = Category
        fields = [
            'id', 
            'name', 
            'countAds',
            'subcategoriesCount', 
            'hasChildren',
            'minimumPrice',
            'standardPrice',
            'highestBid',
            'secondHighestBid',
            'thirdHighestBid',
            'premiumBidMultiplier',
            'trueForSuffixFalseForPrefixCurrency',
            'currency',
            'incrementPrice'
            ]
    
    def get_minimumPrice(self, obj):
        return self.get_minimum_coins(obj) * COIN_TO_MONEY_MULTIPLIER
    def get_minimum_coins(self, obj):
        count = obj.subcategoriesCount + 1
        return PRICE_PER_CATEGORY * count
    def get_standardPrice(self, obj):
        median = obj.averagePrice
        count = obj.countAds
        minimum = self.get_minimum_coins(obj) * MINIMUM_TO_STANDARD_MULTIPLIER
        if median < minimum or count < COUNT_ADS_THRESHOLD_BEFORE_AVERAGING_FOR_STANDARD:
            return minimum * COIN_TO_MONEY_MULTIPLIER
        return median * COIN_TO_MONEY_MULTIPLIER
    def get_highestBid(self, obj):
        highest = obj.highestBid
        minimum = self.get_minimum_coins(obj)
        if highest < minimum:
            return  minimum * COIN_TO_MONEY_MULTIPLIER
        return highest * COIN_TO_MONEY_MULTIPLIER
    def get_secondHighestBid(self, obj):
        secondHighest = obj.secondHighestBid
        minimum = self.get_minimum_coins(obj)
        if secondHighest < minimum:
            return  minimum * COIN_TO_MONEY_MULTIPLIER
        return secondHighest * COIN_TO_MONEY_MULTIPLIER
    def get_thirdHighestBid(self, obj):
        thirdHighest = obj.thirdHighestBid
        minimum = self.get_minimum_coins(obj)
        if thirdHighest < minimum:
            return  minimum * COIN_TO_MONEY_MULTIPLIER
        return thirdHighest * COIN_TO_MONEY_MULTIPLIER
    def get_premiumBidMultiplier(self, obj):
        return PREMIUM_MULTIPLIER
    def get_trueForSuffixFalseForPrefixCurrency(self, obj):
        return False
    def get_currency(self, obj):
        return CURRENCY_CHOICES[0][0]
    def get_incrementPrice(self, obj):
        minimum = self.get_minimum_coins(obj)
        return minimum * INCREMENT_MULTIPLE * COIN_TO_MONEY_MULTIPLIER
    
class PaymentMethodsSerializer(serializers.ModelSerializer):
    payImage = serializers.SerializerMethodField()
    class Meta:
        model = PayMethod
        fields = '__all__'
    def get_payImage(self, obj):
        image = obj.image
        if image:
            return image.url
        return obj.image.url
class CreateAdSerializer(serializers.Serializer):
    contextRequest = None
    def setRequest(self, request):
        self.contextRequest = request
    payMethod = serializers.UUIDField()
    issuedFor = serializers.UUIDField()
    currency = serializers.CharField(max_length=CURRENCY_LENGTH)
    useVirtualCurrency = serializers.BooleanField()
    postIds = serializers.ListField(child=serializers.UUIDField())
    categories = SingleCategoryBidSerializer(many=True)
    def create(self, validated_data):
        request = self.contextRequest
        is_issued_by_admin = self.contextRequest.headers.get('by_admin', False)
        is_issued_by_admin = bool(is_issued_by_admin)

        if is_issued_by_admin is True:
            issuedByObj, _ = authentication.getUserFromAuthHeader(self.contextRequest)
        else:
            issuedByObj = request.user

        payMethodObj = PayMethod.objects.get(id=validated_data['payMethod'])
        issuedForObj = User.objects.get(id=validated_data['issuedFor'])
        categoriesSelected = validated_data['categories']
        virtual = validated_data['useVirtualCurrency']
        totalAmount = 0
        subcategoriesTotal = 0
        adCount = 0
        for category in categoriesSelected:
            totalAmount += category['amount']
            adCount += 1
            if category['hasChildren'] is False:
                subcategoriesTotal += 1
            else:
                subcategoriesTotal += category['subcategoriesCount'] + 1
        if virtual is True:
            totalAmount /= COIN_TO_MONEY_MULTIPLIER
        totalAmount = math.ceil(totalAmount)

        transaction = Transaction.objects.create(
            issuedBy = issuedByObj, 
            issuedFor = issuedForObj, 
            amount = totalAmount,
            currency = validated_data['currency'],
            payMethod = payMethodObj,
            payVerified = False,
            title = "Boost Ads",
            reason = str(adCount) + " ads in " + str(subcategoriesTotal) + " subcategories",
            trueForDepositFalseForWithdraw = True,
            pay_for = 'A'
        )

        posts = validated_data['postIds']
        createdAds = []
        for post in posts:
            postObj = Post.objects.get(postId=post)
            for category in categoriesSelected:
                categoryObj = Category.objects.get(id = category['categoryId'])
                adCreated = Ads.objects.create(
                    postId = postObj,
                    categoryId = categoryObj,
                    strength = category['amount'],
                    payVerified = False,
                    transaction = transaction
                )
                createdAds.append(adCreated)
            
        return createdAds
    
class BuyPackageSerializer(serializers.Serializer):
    contextRequest = None
    def setRequest(self, request):
        self.contextRequest = request
    payMethod = serializers.UUIDField()
    issuedFor = serializers.UUIDField()
    currency = serializers.CharField(max_length=CURRENCY_LENGTH)
    useVirtualCurrency = serializers.BooleanField()
    price = serializers.IntegerField()
    amount = serializers.CharField(max_length=100)
    coinAmountInt = serializers.IntegerField()
    tip = serializers.BooleanField()
    def create(self, validated_data):
        request = self.contextRequest
        is_issued_by_admin = self.contextRequest.headers.get('by_admin', False)
        is_issued_by_admin = bool(is_issued_by_admin)

        if is_issued_by_admin is True:
            issuedByObj, _ = authentication.getUserFromAuthHeader(self.contextRequest)
        else:
            issuedByObj = request.user

        payMethodObj = PayMethod.objects.get(id=validated_data['payMethod'])
        issuedForObj = User.objects.get(id=validated_data['issuedFor'])
        virtual = validated_data['useVirtualCurrency']
        price = validated_data['price']
        currency = validated_data['currency']
        amountInWords = validated_data['amount']
        coinAmountInt = validated_data['coinAmountInt']
        tip = validated_data['tip']
        reason = ""
        title = ""
        if virtual is True:
            amountToSave = coinAmountInt
        else:
            amountToSave = price
        verified = False
        if virtual is True:
            if tip is True and issuedByObj.coins > coinAmountInt :
                verified = True
                issuedByObj.coins -= coinAmountInt
                issuedByObj.save()
                #adding to the issuedFor coins is done in signals.py
            
        if tip is True:
            if virtual is True:
                reason = "Tip " +  " " + str(coinAmountInt) + " " + currency + " to " + str(issuedForObj.first_name)
            else:
                reason = "Tip " +  " " + str(price) + " " + currency + " to " + str(issuedForObj.first_name)

            title = "Tip"
        else:
            reason = "Buy " + amountInWords + " Package"
            title = "Package"
        transaction = Transaction.objects.create(
            issuedBy = issuedByObj, 
            issuedFor = issuedForObj, 
            amount = amountToSave,
            currency = currency,
            usedVirtualCurrency = virtual,
            payMethod = payMethodObj,
            payVerified = verified,
            title = title,
            reason = reason,
            coin_amount = coinAmountInt,
            trueForDepositFalseForWithdraw = True,
            pay_for = 'P'
        )

        

        return transaction


class TransactionSerializer(serializers.ModelSerializer):
    verificationScreenshot = serializers.SerializerMethodField()
    issuedFor = UserSerializer()
    issuedBy = UserSerializer()
    date = serializers.SerializerMethodField()
    payMethod = PaymentMethodsSerializer()
    trueForSuffixFalseForPrefixCurrency = serializers.SerializerMethodField()

    def get_verificationScreenshot(self, obj):
        image = obj.verificationScreenshot
        if image:
            return image.url 
    def get_date(self, obj):
        return obj.created_at.strftime("%b %d, %Y")
    def get_trueForSuffixFalseForPrefixCurrency(self, obj):
        return False
    class Meta:
        model = Transaction
        fields = '__all__'

class PackageSerializer(serializers.ModelSerializer):
    originalPriceStrikeThrough = serializers.SerializerMethodField()
    class Meta:
        model = Package
        fields = '__all__'
    def get_originalPriceStrikeThrough(self, obj):
        if obj.hasDiscount is True:
            return strike(obj.original_price_in_words)
        else:
            return obj.original_price_in_words



def get_originalPrice_string(obj):
    return str(obj.currency) + ' ' + str(obj.price)
def get_discountedPrice_string(obj):
    return str(obj.discountCurrency) + ' ' + str(obj.discountedPrice)

def strike(text):
    text = " " + text + " "
    return ''.join([u'\u0336{}'.format(c) for c in text])