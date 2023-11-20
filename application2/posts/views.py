from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.generics import ListAPIView, UpdateAPIView, ListCreateAPIView, CreateAPIView, RetrieveUpdateAPIView, RetrieveAPIView, DestroyAPIView
from . import serializers, queries, models
from django.db.models import Exists, OuterRef, Q, F, Subquery, Count, Prefetch
from datetime import date
from django.db import connection
from django.http import HttpResponse
from rest_framework.response import Response
from . import paginators
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
# Create your views here.
class CategoriesAPI(ModelViewSet):
    queryset = models.Category.objects.all()[:30]
    serializer_class = serializers.CategorySerializer


class PostsAPI(ModelViewSet):
    queryset = models.Post.objects.all()   
    serializer_class = serializers.EmptySerializer
    pagination_class = paginators.Pages
    
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
    
# class PostsRecommended(ListAPIView, GenericViewSet):
#     queryset = models.Post.objects.none()
#     serializer_class = serializers.EmptySerializer
#     def list(self, request, *args, **kwargs):
#         self.serializer_class = serializers.SendRecommendedPosts
#         reset_recommendations(self.request.user)
#         populate_recommendations(self.request.user)
#         # posts = queries.recommended_from_table(request.user)
#         # serializer = self.get_serializer(posts, many=True)
#         # self.serializer_class.data = posts
#         return Response("Poppulated recommendations, go to /posts_r")
#         # return Response(serializer.data)
#         # return super().list(self, request, *args, **kwargs)
    
def create_recommendations_api(request):
    create_recommendations(request)
    return HttpResponse('Done, check /posts_recommended')
def create_recommendations(request):
    reset_recommendations(request.user)
    populate_recommendations(request.user)

class GetRecommendation(ListAPIView, GenericViewSet):
    queryset = models.Post.objects.all()[:1]
    serializer_class = serializers.EmptySerializer
    pagination_class = paginators.RecommendedPages
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
    models.Recommended.objects.bulk_create(recommended_list)

class LikeAPI(RetrieveAPIView, CreateAPIView, DestroyAPIView, GenericViewSet):
    queryset = models.Like.objects.all()
    serializer_class = serializers.LikePostSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = 'post_id'
    def perform_create(self, serializer):
        post = models.Post.objects.get(postId =self.kwargs.get('post_id') )
        serializer.save(user_id= self.request.user, post_id = post)
    def retrieve(self, request, *args, **kwargs):
        post_id = self.kwargs['post_id']
        likes = models.Like.objects.filter(
            post_id = post_id
        ).values(
            'post_id',
            'user_id'
        ).first()
        serializer = self.get_serializer(data = likes)
        try:
            serializer.is_valid(raise_exception = True)
        except Exception:
            return Response({
                'likes': 0,
                'hasLiked': False
            })

        return Response(serializer.data)
    def destroy(self, request, *args, **kwargs):
        user_id = request.user.id
        post_id = self.kwargs['post_id']
        likes = models.Like.objects.filter(user_id = user_id, post_id = post_id)
        if likes.exists():
            likes.delete()
            return Response(status =status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {
                    'error': 'Post and associated user not found in likes table'
                }, status = status.HTTP_404_NOT_FOUND
            )
