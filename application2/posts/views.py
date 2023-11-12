from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveUpdateAPIView
from . import serializers, queries, models
from django.db.models import Exists, OuterRef, Q, F, Subquery, Count, Prefetch

# Create your views here.
class CategoriesAPI(ModelViewSet):
    queryset = models.Category.objects.all()[:30]
    serializer_class = serializers.CategorySerializer

class PostsAPI(ListAPIView, CreateAPIView, RetrieveUpdateAPIView, GenericViewSet):
    queryset = models.Post.objects.all()[:1]    
    serializer_class = serializers.EmptySerializer

    def get_queryset(self):
        self.serializer_class = serializers.PostSerializer
        return queries.get_all_posts(self)

class PostsFromIICF_API(ModelViewSet):
    queryset = models.InteractionUserToPost.objects.all()[:1]
    serializer_class = serializers.EmptySerializer

    def get_queryset(self):
        self.serializer_class = serializers.IICF
        return queries.get_posts_with_item_item_collaborative_filtering(self)

class NewPostsAPI(ModelViewSet):
    queryset = models.NewPost.objects.all()[:1]
    serializer_class = serializers.EmptySerializer

    def get_queryset(self):
        self.serializer_class = serializers.PostSerializer
        return queries.get_new_posts_personalized(self)
    
class PostsFromUUCF_API(ModelViewSet):
    queryset = models.InteractionUserToUser.objects.all()[:1]
    serializer_class = serializers.EmptySerializer

    def get_queryset(self):
        self.serializer_class = serializers.IICF
        return queries.get_posts_with_user_user_collaborative_filtering(self)
    
class PostsFromUCCF_API(ModelViewSet):
    queryset = models.InteractionUserToCategory.objects.all()[:1]
    serializer_class = serializers.EmptySerializer
    def get_queryset(self):
        self.serializer_class = serializers.PostSerializer
        return queries.get_posts_with_user_category_collaborative_filtering(self)
class PostsFromCategories(ModelViewSet):
    queryset = models.Post.objects.all()[:1]
    serializer_class = serializers.EmptySerializer
    def get_queryset(self):
        self.serializer_class = serializers.PostSerializer
        return queries.get_posts_by_category_personalized(self)
class PostsFromFollowing(ModelViewSet):
    queryset = models.Post.objects.all()[:1]
    serializer_class = serializers.EmptySerializer
    def get_queryset(self):
        self.serializer_class = serializers.PostSerializer
        return queries.get_posts_by_following(self)
class PostsRecommended(ModelViewSet):
    queryset = models.Post.objects.all()[:1]
    serializer_class = serializers.EmptySerializer
    def get_queryset(self):
        self.serializer_class = serializers.RecommendedSerializer
        return queries.get_recommendations(self)
