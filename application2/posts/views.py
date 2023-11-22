from django.shortcuts import render
from collections import defaultdict
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.generics import ListAPIView, UpdateAPIView, ListCreateAPIView, CreateAPIView, RetrieveUpdateAPIView, RetrieveAPIView, DestroyAPIView
from . import serializers, queries, models

from datetime import datetime, timedelta
from django.db.models import Exists, OuterRef, Q, F, Subquery, Count, Prefetch, Sum
from django.db.models.functions import Coalesce
from datetime import date
from django.db import connection
from django.http import HttpResponse
from rest_framework.response import Response
from . import paginators
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Prefetch
# Create your views here.
class CategoriesAPI(ModelViewSet):
    queryset = models.Category.objects.all()[:30]
    serializer_class = serializers.CategorySerializer

class PostsAPI(ListAPIView, RetrieveAPIView, GenericViewSet):
    queryset = models.Post.objects.all()   
    serializer_class = serializers.EmptySerializer
    pagination_class = paginators.Pages
    
    def get_queryset(self):
        self.serializer_class = serializers.PostSerializer
        if self.action == 'retrieve':
            self.serializer_class = serializers.PostDetailSerializer
        return queries.get_all_posts(self.request)
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
class CategoriesAPI(ListAPIView, RetrieveAPIView, GenericViewSet):
    queryset = models.Category.objects.none()
    serializer_class = serializers.CategoryForTraversalSerializer
    def get_queryset(self):
        if self.action == 'list':
            return queries.root_categories(self.request.user)
        elif self.action == 'retrieve':
            return queries.children_categories(self.request.user, self.kwargs['pk'])
        return super().get_queryset()
    def retrieve(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
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



class NotificationsAPI(ListAPIView, RetrieveAPIView, GenericViewSet):
    queryset = models.Notification.objects.all(
    ).values(
        'action', 
        'buttonPressed', 
        'date', 
        'id', 
        'image_from',
        'message', 
        'notifyUser', 
        'postId', 
        'profileId', 
        'seen'
    )
    def get_queryset(self):
        return models.Notification.objects.filter(
                notifyUser = self.request.user.id
            ).values(
                'action', 
                'buttonPressed', 
                'date', 
                'id', 
                'image_from',
                'message', 
                'notifyUser', 
                'postId', 
                'profileId', 
                'seen'
            )
    pagination_class = paginators.Pages
    serializer_class = serializers.NotificationSerializer
    def list(self, request, *args, **kwargs):
        notifications = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(notifications)
        serialized = []
        if page is not None:
            groups = group_by_days(page)
            
            for daysBefore, notifications in groups.items():
                serialized.append(
                    {
                        "daysBefore": daysBefore,
                        "notificationsThatDay": serializers.NotificationSerializer(notifications, many = True).data
                    }
                )

        return self.get_paginated_response(serialized)
    
def group_by_days(notifications):
    groups = defaultdict(list)
    for notification in notifications:
        daysBefore = (date.today() - notification['date']).days
        groups[daysBefore].append(notification)
    return groups

class FavouritesAPI(ListAPIView, GenericViewSet):
    queryset = models.Post.objects.all()
    serializer_class = serializers.FavouriteSerializer
    pagination_class = paginators.Pages
    def get_queryset(self):
        return models.Favourite.objects.filter(user_id = self.request.user).select_related('post_id', 'post_id__sellerId', 'post_id__categoryId', 'post_id__categoryId__parent')

class LikedAPI(ListAPIView, GenericViewSet):
    queryset = models.Post.objects.all()
    serializer_class = serializers.LikedListSerializer
    pagination_class = paginators.Pages
    def get_queryset(self):
        return models.Like.objects.filter(user_id = self.request.user).select_related('post_id', 'post_id__sellerId', 'post_id__categoryId', 'post_id__categoryId__parent')
class MyPostsAPI(ListAPIView, GenericViewSet):
    queryset = models.Post.objects.all()
    serializer_class = serializers.WideCardSerializer
    pagination_class = paginators.Pages
    def get_queryset(self):
        return models.Post.objects.filter(sellerId = self.request.user).select_related('sellerId', 'categoryId', 'categoryId__parent')
class MyProfileAPI(ListAPIView, GenericViewSet):
    queryset = models.User.objects.none()
    serializer_class = serializers.ProfileSerializer
    def get_queryset(self):
        return self.request.user
    def list(self, request, *args, **kwargs):
        q = self.get_queryset()
        serializer = self.get_serializer(q, many = False)
        return Response(serializer.data)
class ProfileAPI(ListAPIView, RetrieveAPIView, GenericViewSet):
    queryset = models.User.objects.all()
    serializer_class = serializers.ProfileSerializer
    pagination_class = paginators.Pages
def update_last_seen(request):
    user = request.user
    user.last_seen = datetime.now().astimezone(serializers.timezone)
    user.save()
    return HttpResponse('Updated last seen of user: ' + str(user))