from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.generics import ListAPIView, UpdateAPIView, ListCreateAPIView, CreateAPIView, RetrieveUpdateAPIView, RetrieveAPIView
from . import serializers, queries, models
from django.db.models import Exists, OuterRef, Q, F, Subquery, Count, Prefetch
from datetime import date
from django.db import connection
from django.http import HttpResponse
from rest_framework.response import Response
from django.http import QueryDict
# Create your views here.
class CategoriesAPI(ModelViewSet):
    queryset = models.Category.objects.all()[:30]
    serializer_class = serializers.CategorySerializer

class PostsAPI(ModelViewSet):
    queryset = models.Post.objects.all()   
    serializer_class = serializers.EmptySerializer
    
    def get_queryset(self):
        self.serializer_class = serializers.PostSerializer
        return queries.get_all_posts(self.request)
    # def get_serializer(self, *args, **kwargs):
    #     if self.action == 'create':
    #         return serializers.NewPostSerializer
    #     return serializers.PostSerializer
class NewPostAPI(CreateAPIView, UpdateAPIView, GenericViewSet):
    queryset = models.Post.objects.all()[:1]    
    serializer_class = serializers.NewPostSerializer 
class EditPostAPI(ModelViewSet):
    queryset = models.Post.objects.all()   
    serializer_class = serializers.EditPostSerializer 
    
class PostsRecommended(ListAPIView, GenericViewSet):
    queryset = models.Post.objects.none()
    serializer_class = serializers.EmptySerializer
    def list(self, request, *args, **kwargs):
        self.serializer_class = serializers.SendRecommendedPosts
        reset_recommendations(self.request.user)
        populate_recommendations(self.request.user)
        posts = queries.recommended_from_table(request.user)
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)
    
def create_recommendations(request):
    reset_recommendations(request.user)
    populate_recommendations(request.user)
    return HttpResponse('Done')

class GetRecommendation(ListAPIView, GenericViewSet):
    queryset = models.Post.objects.all()[:1]
    serializer_class = serializers.EmptySerializer
    def get_queryset(self):
        self.serializer_class = serializers.SendRecommendedPosts
        posts = queries.recommended_from_table(self.request.user)
        return posts

def reset_recommendations(user):
    models.Recommended.objects.filter(userId=user.id).delete()

def populate_recommendations(user):
    recommendations=queries.get_recommendations(user)
    recommended_list = [
            models.Recommended(
                    date=date.today(),
                    userId=user,
                    postId=post['postId'],
                    tag=post['tag'],
                    rank=post['rank']
                )
                for post in list(recommendations)
        ]
    print(recommendations)
    models.Recommended.objects.bulk_create(recommended_list)

    