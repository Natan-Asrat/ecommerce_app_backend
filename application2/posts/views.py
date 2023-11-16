from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveUpdateAPIView, RetrieveAPIView
from . import serializers, queries, models
from django.db.models import Exists, OuterRef, Q, F, Subquery, Count, Prefetch
from datetime import date
from django.db import connection
from django.http import HttpResponse
from rest_framework.response import Response
# Create your views here.
class CategoriesAPI(ModelViewSet):
    queryset = models.Category.objects.all()[:30]
    serializer_class = serializers.CategorySerializer

class PostsAPI(ListAPIView, CreateAPIView, RetrieveUpdateAPIView, GenericViewSet):
    queryset = models.Post.objects.all()[:1]    
    serializer_class = serializers.EmptySerializer

    def get_queryset(self):

        self.serializer_class = serializers.PostSerializer
        return queries.get_all_posts(self.request)

class PostsRecommended(ListAPIView, GenericViewSet):
    queryset = models.Post.objects.none()
    serializer_class = serializers.RecommendedSerializer
    def list(self, request, *args, **kwargs):
        # list(self.get_queryset())
        # s = super().list(request, *args, **kwargs)
        models.Recommended.objects.filter(userId=self.request.user.id).delete()
        posts=queries.get_recommendations(request)
        recommended_list = [
            models.Recommended(
                    date=date.today(),
                    userId=self.request.user,
                    postId=post['postId'],
                    tag=post['tag'],
                    rank=post['rank']
                )
                for post in list(posts)
        ]
        models.Recommended.objects.bulk_create(recommended_list)
        self.queryset = posts
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)
  
def create_recommendations(request):
    posts = queries.get_recommendations(request)
    models.Recommended.objects.filter(userId=request.user.id).delete()
    recommended_list = [
            models.Recommended(
                    date=date.today(),
                    userId=request.user,
                    postId=post['postId'],
                    tag=post['tag'],
                    rank=post['rank']
                )
                for post in list(queries.get_recommendations(request))
        ]
    models.Recommended.objects.bulk_create(recommended_list)
    return HttpResponse('Done')

class GetRecommendation(ListAPIView, GenericViewSet):
    queryset = models.Post.objects.all()[:1]
    serializer_class = serializers.EmptySerializer
    def get_queryset(self):
        self.serializer_class = serializers.SendRecommendedPosts
        posts = queries.recommended_from_table(self.request)
        return posts
    
class InstantRecommendation(ListAPIView, GenericViewSet):
    queryset = models.Post.objects.none()
    serializer_class = serializers.SendRecommendedPosts
    def list(self, request, *args, **kwargs):
        # list(self.get_queryset())
        # s = super().list(request, *args, **kwargs)
        models.Recommended.objects.filter(userId=self.request.user.id).delete()
        recommendations=queries.get_recommendations(request)
        recommended_list = [
            models.Recommended(
                    date=date.today(),
                    userId=request.user,
                    postId=post['postId'],
                    tag=post['tag'],
                    rank=post['rank']
                )
                for post in list(recommendations)
        ]
        models.Recommended.objects.bulk_create(recommended_list)
        posts = queries.recommended_from_table(request)
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)