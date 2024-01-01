from django.shortcuts import render
from django.contrib.auth import get_user_model

from collections import defaultdict
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.generics import ListAPIView, UpdateAPIView, ListCreateAPIView, CreateAPIView, RetrieveUpdateAPIView, RetrieveAPIView, DestroyAPIView
from . import serializers, queries, models
from . import authentication
from django.http import JsonResponse
from django.http import HttpResponse
from datetime import datetime, timedelta
from django.db.models import Exists, OuterRef, Q, F, Subquery, Count, Prefetch, Sum
from django.db.models.functions import Coalesce
import django.db.models as dbmodels
from datetime import date
from django.db import connection
from django.http import HttpResponse
from rest_framework.response import Response
from . import paginators
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Prefetch
# Create your views here.
from django.contrib.auth.models import User, Permission
from . import authentication
from django.core.management import call_command
from rest_framework.exceptions import NotFound
from rest_framework.filters import SearchFilter
from rest_framework.authentication import TokenAuthentication
import operator
from rest_framework.compat import coreapi, coreschema, distinct
from functools import reduce
class Search(SearchFilter):
    def get_search_terms(self, request):
        params = request.query_params.get(self.search_param, '')
        params = params.replace('\x00', '')  # strip null characters
        params = params.replace('%20', ' ')
        return params.split()
    def filter_queryset(self, request, queryset, view):
        search_fields = self.get_search_fields(view, request)
        search_terms = self.get_search_terms(request)

        if not search_fields or not search_terms:
            return queryset

        orm_lookups = [
            self.construct_search(str(search_field))
            for search_field in search_fields
        ]

        base = queryset
        conditions = []
        for search_term in search_terms:
            queries = [
                dbmodels.Q(**{orm_lookup: search_term})
                for orm_lookup in orm_lookups
            ]
            conditions.append(reduce(operator.or_, queries))
        queryset = queryset.filter(reduce(operator.or_, conditions))

        if self.must_call_distinct(queryset, search_fields):
            # Filtering against a many-to-many field requires us to
            # call queryset.distinct() in order to avoid duplicate items
            # in the resulting queryset.
            # We try to avoid this if possible, for performance reasons.
            queryset = distinct(queryset, base)
        return queryset
class PostsAPI(ListAPIView, RetrieveAPIView, GenericViewSet):
    queryset = models.Post.objects.all()   
    serializer_class = serializers.EmptySerializer
    filter_backends = [Search]
    search_fields = [
        'title', 
        'description', 
        'price', 
        'discountedPrice', 
        'sellerId__first_name', 
        'sellerId__last_name', 
        'categoryId__name', 
        'categoryId__parent__parent__name',
        'categoryId__parent__parent__parent__name',
        'categoryId__parent__parent__parent__parent__name',
        'categoryId__parent__parent__parent__parent__parent__name',
        'link',
        'date'
        ]
    pagination_class = paginators.RecommendedPages
    def get_queryset(self):
        if self.action == 'retrieve':
            self.serializer_class = serializers.PostDetailSerializer
        else:  
            self.serializer_class = serializers.PostSerializer
            category = self.request.query_params.get('category')
            if category is not None:
                return queries.get_all_posts(self.request).filter(categoryId = category)
        return queries.get_all_posts(self.request)
class NewPostAPI(CreateAPIView, ListAPIView, UpdateAPIView, GenericViewSet):
    queryset = models.Post.objects.none()  
    serializer_class = serializers.NewPostSerializer
    def list(self, request, *args, **kwargs): 
        user = request.user if request else None
        categories = []
        currencies = []
        if user:
            data = queries.children_categories(user, None)
            serializer = serializers.CategorySerializer(data, many = True)
            categories = serializer.data
        choices = models.Post._meta.get_field('currency').choices
        currencies = [choice[0] for choice in choices]
        info = {
            "nextCategories": categories,
            "currencies": currencies,
            "id": user.id

        }
        return Response(info)
class EditPostAPI(RetrieveAPIView, UpdateAPIView, DestroyAPIView, GenericViewSet):
    queryset = models.Post.objects.all()   
    serializer_class = serializers.EditPostSerializer 
    
def create_recommendations_api(request):
    create_recommendations(request)
    return HttpResponse('Done, check /posts_recommended')
def create_recommendations(request):
    reset_recommendations(request.user)
    populate_recommendations(request.user)

# use category with recommendation in the sliding horizontal category choices and not in search filter choices
class GetRecommendation(ListAPIView, GenericViewSet):
    queryset = models.Post.objects.all()[:1]
    serializer_class = serializers.EmptySerializer
    pagination_class = paginators.RecommendedPages
    def get_queryset(self):
        self.serializer_class = serializers.SendRecommendedPosts
        category = self.request.query_params.get('category')
        if category is not None:
            return queries.get_recommended_in_category(self.request.user, category)
        return queries.recommended_from_table(self.request.user)
class CategoriesAPI(ListAPIView, RetrieveAPIView, GenericViewSet):
    queryset = models.Category.objects.none()
    serializer_class = serializers.CategoryForTraversalSerializer
    pagination_class = paginators.Pages
    def get_queryset(self):
        if self.action == 'list':
            return queries.children_categories(self.request.user, parent=None)
        elif self.action == 'retrieve':
            return queries.children_categories(self.request.user, self.kwargs['pk'])
        return super().get_queryset()
    def retrieve(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
class CategoriesRecommendedAPI(ListAPIView, RetrieveAPIView, GenericViewSet):
    queryset = models.Category.objects.none()
    serializer_class = serializers.CategoryForTraversalSerializer
    pagination_class = paginators.Pages
    def get_queryset(self):
        if self.action == 'list':
            return queries.recommended_categories(self.request.user)
        elif self.action == 'retrieve':
            return queries.children_categories(self.request.user, self.kwargs['pk'])
        return super().get_queryset()
    def retrieve(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
class CategoryAPI(ListAPIView, RetrieveAPIView, GenericViewSet):
    queryset = models.Category.objects.none()
    serializer_class = serializers.CategorySerializer
    def get_queryset(self):
        if self.action == 'list':
            return queries.children_categories(self.request.user, parent=None)
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

class SaveAPI(RetrieveAPIView, CreateAPIView, DestroyAPIView, GenericViewSet):
    queryset = models.Favourite.objects.all()
    serializer_class = serializers.SavePostSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = 'post_id'
    def perform_create(self, serializer):
        post = models.Post.objects.get(postId =self.kwargs.get('post_id') )
        serializer.save(user_id= self.request.user, post_id = post)
    def retrieve(self, request, *args, **kwargs):
        post_id = self.kwargs['post_id']
        saves = models.Favourite.objects.filter(
            post_id = post_id
        ).values(
            'post_id',
            'user_id'
        ).first()
        serializer = self.get_serializer(data = saves)
        try:
            serializer.is_valid(raise_exception = True)
        except Exception:
            return Response({
                'hasSaved': False
            })

        return Response(serializer.data)
    def destroy(self, request, *args, **kwargs):
        user_id = request.user.id
        post_id = self.kwargs['post_id']
        saves = models.Favourite.objects.filter(user_id = user_id, post_id = post_id)
        if saves.exists():
            saves.delete()
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
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context
class ProfileAPI(ListAPIView, RetrieveAPIView, GenericViewSet):
    queryset = models.User.objects.all()
    serializer_class = serializers.ProfileSerializer
    pagination_class = paginators.Pages
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context
class SimilarPostsAPI(ListAPIView,RetrieveAPIView, GenericViewSet):
    queryset = models.Post.objects.none()
    serializer_class = serializers.WideCardSerializer
    pagination_class = paginators.SimilarPages
    def get_queryset(self):
        if  self.action == 'retrieve':
            self.pk = self.kwargs['pk']
            paginators.similar_pk = self.pk
            q =queries.get_similar_posts(self.request.user, self.pk)
            return q
        return super().get_queryset()
    def retrieve(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
def update_last_seen(request):
    user = request.user
    user.last_seen = datetime.now().astimezone(serializers.timezone)
    user.save()
    return HttpResponse('Updated last seen of user: ' + str(user))

class GetMyTransactions(ListAPIView, GenericViewSet):
    queryset = models.Transaction.objects.none()
    serializer_class = serializers.TransactionSerializer
    def get_queryset(self):
        return models.Transaction.objects.filter(issuedFor = self.request.user).select_related('issuedBy','issuedFor', 'payMethod').order_by('-created_at')

class GetMyPendingTransactions(ListAPIView, GenericViewSet):
    queryset = models.Transaction.objects.none()
    serializer_class = serializers.TransactionSerializer
    def get_queryset(self):
        return models.Transaction.objects.filter(issuedFor = self.request.user, payVerified = False, rejected = False).select_related('issuedBy','issuedFor', 'payMethod').order_by('-created_at')
    
class GetMyVerifiedTransactions(ListAPIView, GenericViewSet):
    queryset = models.Transaction.objects.none()
    serializer_class = serializers.TransactionSerializer
    def get_queryset(self):
        return models.Transaction.objects.filter(issuedFor = self.request.user, payVerified = True, rejected = False).select_related('issuedBy','issuedFor', 'payMethod').order_by('-created_at')

class GetMyRejectedTransactions(ListAPIView, GenericViewSet):
    queryset = models.Transaction.objects.none()
    serializer_class = serializers.TransactionSerializer
    def get_queryset(self):
        return models.Transaction.objects.filter(issuedFor = self.request.user, rejected = True).select_related('issuedBy','issuedFor', 'payMethod').order_by('-created_at')


class AdminRecentTransactions(ListAPIView, GenericViewSet):
    queryset = models.Transaction.objects.none()
    serializer_class = serializers.TransactionSerializer
    filter_backends = [Search]
    search_fields = [
        'title', 
        'issuedFor__first_name', 
        'issuedFor__last_name', 
        'amount', 
        'currency',
        'payMethod__name',
        'transactionConfirmationCode',
        'created_at',
        'issuedBy__first_name',
        'issuedBy__last_name'
        ]
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser is False:
            return models.Transaction.objects.none()
        return models.Transaction.objects.all().select_related('issuedBy','issuedFor', 'payMethod').order_by('-created_at')
    

class AdminPendingTransactions(ListAPIView, GenericViewSet):
    queryset = models.Transaction.objects.none()
    serializer_class = serializers.TransactionSerializer
    filter_backends = [Search]
    search_fields = [
        'title', 
        'issuedFor__first_name', 
        'issuedFor__last_name', 
        'amount', 
        'currency',
        'payMethod__name',
        'transactionConfirmationCode',
        'created_at',
        'issuedBy__first_name',
        'issuedBy__last_name'
        ]
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser is False:
            return models.Transaction.objects.none()
        return models.Transaction.objects.filter(payVerified = False, rejected = False).select_related('issuedBy','issuedFor', 'payMethod').order_by('-amount', '-created_at')
    
class AdminVerifiedTransactions(ListAPIView, GenericViewSet):
    queryset = models.Transaction.objects.none()
    serializer_class = serializers.TransactionSerializer
    filter_backends = [Search]
    search_fields = [
        'title', 
        'issuedFor__first_name', 
        'issuedFor__last_name', 
        'amount', 
        'currency',
        'payMethod__name',
        'transactionConfirmationCode',
        'created_at',
        'issuedBy__first_name',
        'issuedBy__last_name'
        ]
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser is False:
            return models.Transaction.objects.none()
        return models.Transaction.objects.filter(payVerified = True, rejected = False).select_related('issuedBy','issuedFor', 'payMethod').order_by('-amount', '-created_at')

class AdminRejectedTransactions(ListAPIView, GenericViewSet):
    queryset = models.Transaction.objects.none()
    serializer_class = serializers.TransactionSerializer
    filter_backends = [Search]
    search_fields = [
        'title', 
        'issuedFor__first_name', 
        'issuedFor__last_name', 
        'amount', 
        'currency',
        'payMethod__name',
        'transactionConfirmationCode',
        'created_at',
        'issuedBy__first_name',
        'issuedBy__last_name'
        ]
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser is False:
            return models.Transaction.objects.none()
        return models.Transaction.objects.filter(rejected = True).select_related('issuedBy','issuedFor', 'payMethod').order_by('-amount', '-created_at')


class CreateAdsAPI(CreateAPIView, GenericViewSet):
    queryset = models.Ads.objects.none()
    serializer_class = serializers.CreateAdSerializer
    
    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.setRequest(request)
        serializer.is_valid(raise_exception=True)
        created_ads = serializer.save()  # This will call the serializer's create method
        pending = False
        for ad in created_ads:
            if ad.payVerified is False:
                pending = True
        if pending is True:
            message = 'Ads are pending'
        else:
            message = 'Ads were created successfully'
        response_data = {
            'detail': message,
            'Number of Ads Created': len(created_ads)
        }

        return Response(response_data, status=status.HTTP_201_CREATED)
    def get_serializer_context(self):
        c = super().get_serializer_context()
        c['request'] = self.request
        return c
class GetBids(ListAPIView, RetrieveAPIView, GenericViewSet):
    queryset = models.Category.objects.none()
    serializer_class = serializers.AdCategoriesSerializer
    filter_backends = [Search]
    search_fields = [
        'name'
        ]
    def get_queryset(self):
        if self.action == 'list':
            return queries.children_ad_categories(self.request.user, parent=None)
        elif self.action == 'retrieve':
            return queries.children_ad_categories(self.request.user, self.kwargs['pk'])
        return super().get_queryset()
    def retrieve(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
class GetPaymentMethods(ListAPIView, RetrieveAPIView, GenericViewSet):
    queryset = models.PayMethod.objects.all()
    serializer_class = serializers.PaymentMethodsSerializer 

class ProfilePostsAPI(ListAPIView, GenericViewSet):
    queryset = models.Post.objects.all()
    serializer_class = serializers.WideCardSerializer
    pagination_class = paginators.Pages
    def get_queryset(self):
        return models.Post.objects.filter(sellerId = self.kwargs['seller_pk']).select_related('sellerId', 'categoryId', 'categoryId__parent')
    
def check_if_user_is_new(request, id):
    issue = False
    user = None
    try:
        user = models.User.objects.get(username=id)
        userIsNew = False
    except User.DoesNotExist:
        userIsNew = True
    except Exception as e:
        issue = True
        print(e)
    
    if issue is True:
        return JsonResponse({
            'is_new': None,
            'user': None
        }, status = 500)
    serializer = serializers.UserSerializer(data = user, many=False)
    serializer.is_valid()
    response = {
        'is_new': userIsNew,
        'user': serializer.data
    }
    return JsonResponse(response)
