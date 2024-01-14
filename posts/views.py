from django.shortcuts import render
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from collections import defaultdict
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.generics import ListAPIView, UpdateAPIView, ListCreateAPIView, CreateAPIView, RetrieveUpdateAPIView, RetrieveAPIView, DestroyAPIView
from . import serializers, queries, models
from . import authentication
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet
from django.http import JsonResponse
from django.http import HttpResponse, HttpRequest
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

INCREASE_TO_CATEGORY_INTERACTION_PER_VIEW = 1
INCREASE_TO_USER_INTERACTION_PER_VIEW = 1
INCREASE_TO_POST_INTERACTION_PER_VIEW = 1


INCREASE_TO_CATEGORY_INTERACTION_PER_LIKE = 3
INCREASE_TO_USER_INTERACTION_PER_LIKE = 3
INCREASE_TO_POST_INTERACTION_PER_LIKE = 3


INCREASE_TO_CATEGORY_INTERACTION_PER_SAVE = 5
INCREASE_TO_USER_INTERACTION_PER_SAVE = 5
INCREASE_TO_POST_INTERACTION_PER_SAVE = 5


INCREASE_TO_CATEGORY_INTERACTION_PER_CALL = 9
INCREASE_TO_USER_INTERACTION_PER_CALL = 9
INCREASE_TO_POST_INTERACTION_PER_CALL = 9


INCREASE_TO_CATEGORY_INTERACTION_PER_SHARE = 13
INCREASE_TO_USER_INTERACTION_PER_SHARE = 13
INCREASE_TO_POST_INTERACTION_PER_SHARE = 13


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
    def list(self, request, *args, **kwargs):
        category = request.query_params.get('category')
        if category is not None:
            user = get_user_from_request(request)
            categoryId = models.Category.objects.get(id = category)
            userToCategory, _ = models.InteractionUserToCategory.objects.get_or_create(user_id = user, category_id = categoryId)
            userToCategory.strength_sum += INCREASE_TO_CATEGORY_INTERACTION_PER_VIEW
            userToCategory.save()
        return super().list(request, *args, **kwargs)
    def retrieve(self, request, *args, **kwargs):
        user = get_user_from_request(request)
        if user is not None:
            id = kwargs['pk']
            post = models.Post.objects.select_related('sellerId', 'categoryId').get(postId = id)
            seller = post.sellerId
            category = post.categoryId
            userToUser, _ = models.InteractionUserToUser.objects.get_or_create(user_performer = user, user_performed_on = seller)
            userToCategory, _ = models.InteractionUserToCategory.objects.get_or_create(user_id = user, category_id = category)
            userToPost, _ = models.InteractionUserToPost.objects.get_or_create(user_id = user, post_id = post)

            userToUser.strength_sum += INCREASE_TO_USER_INTERACTION_PER_VIEW
            userToCategory.strength_sum += INCREASE_TO_CATEGORY_INTERACTION_PER_VIEW
            userToPost.strength_sum += INCREASE_TO_POST_INTERACTION_PER_VIEW

            userToUser.save()
            userToPost.save()
            userToCategory.save()
        return super().retrieve(request, *args, **kwargs)
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
            "id": user.id,
            "myCoinsAmount": str(user.coins) + " Coins",
            "sufficientBalance": bool(user.coins > 0)

        }
        return Response(info)
class EditPostAPI(RetrieveAPIView, UpdateAPIView, DestroyAPIView, GenericViewSet):
    queryset = models.Post.objects.all()   
    serializer_class = serializers.EditPostSerializer 
    
def create_recommendations_api(request):
    create_recommendations(request)
    return HttpResponse('Done, check /posts_recommended')
def create_recommendations(request):
    user = get_user_from_request(request)
    reset_recommendations(user)
    populate_recommendations(user)

# use category with recommendation in the sliding horizontal category choices and not in search filter choices
class GetRecommendation(ListAPIView, GenericViewSet):
    queryset = models.Post.objects.all()[:1]
    serializer_class = serializers.EmptySerializer
    pagination_class = paginators.RecommendedPages
    def get_queryset(self):
        user = get_user_from_request(self.request)

        self.serializer_class = serializers.SendRecommendedPosts
        category = self.request.query_params.get('category')
        if category is not None:
            return queries.get_recommended_in_category(user, category)
        return queries.recommended_from_table(user)
    def list(self, request, *args, **kwargs):
        category = request.query_params.get('category')
        if category is not None:
            user = get_user_from_request(request)
            category = models.Category.objects.get(id = category)
            userToCategory, _ = models.InteractionUserToCategory.objects.get_or_create(user_id = user, category_id = category)
            userToCategory.strength_sum += INCREASE_TO_CATEGORY_INTERACTION_PER_VIEW
            userToCategory.save()
        return super().list(request, *args, **kwargs)
class CategoriesAPI(ListAPIView, RetrieveAPIView, GenericViewSet):
    queryset = models.Category.objects.none()
    serializer_class = serializers.CategoryForTraversalSerializer
    pagination_class = paginators.Pages
    def get_queryset(self):
        user = get_user_from_request(self.request)

        if self.action == 'list':
            return queries.children_categories(user, parent=None)
        elif self.action == 'retrieve':
            return queries.children_categories(user, self.kwargs['pk'])
        return super().get_queryset()
    def retrieve(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
class CategoriesRecommendedAPI(ListAPIView, RetrieveAPIView, GenericViewSet):
    queryset = models.Category.objects.none()
    serializer_class = serializers.CategoryForTraversalSerializer
    pagination_class = paginators.Pages
    def get_queryset(self):
        user = get_user_from_request(self.request)
        if self.action == 'list':
            return queries.recommended_categories(user)
        elif self.action == 'retrieve':
            return queries.children_categories(user, self.kwargs['pk'])
        return super().get_queryset()
    def retrieve(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
class CategoryAPI(ListAPIView, RetrieveAPIView, GenericViewSet):
    queryset = models.Category.objects.none()
    serializer_class = serializers.CategorySerializer
    def get_queryset(self):
        user = get_user_from_request(self.request)
        if self.action == 'list':
            return queries.children_categories(user, parent=None)
        elif self.action == 'retrieve':
            return queries.children_categories(user, self.kwargs['pk'])
        return super().get_queryset()
    def retrieve(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
def reset_recommendations(user):
    user_id = None
    if user is not None:
        user_id = user.id
    models.Recommended.objects.filter(userId=user_id).delete()

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
        user = get_user_from_request(self.request)
        post = models.Post.objects.get(postId =self.kwargs.get('post_id') )
        serializer.save(user_id= user, post_id = post)
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
        user = get_user_from_request(self.request)
        user_id = None
        if user is not None:
            user_id = user.id
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
        user = get_user_from_request(self.request)
        post = models.Post.objects.get(postId =self.kwargs.get('post_id') )
        serializer.save(user_id= user, post_id = post)
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
        user = get_user_from_request(self.request)
        user_id = None
        if user is not None:
            user_id = user.id
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
        user = get_user_from_request(self.request)
        return models.Notification.objects.filter(
                notifyUser = user.id
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
        user = get_user_from_request(self.request)
        return models.Favourite.objects.filter(user_id = user).select_related('post_id', 'post_id__sellerId', 'post_id__categoryId', 'post_id__categoryId__parent')

class FCM(FCMDeviceAuthorizedViewSet):
    authentication_classes = [authentication.FirebaseAuthentication]

class LikedAPI(ListAPIView, GenericViewSet):
    queryset = models.Post.objects.all()
    serializer_class = serializers.LikedListSerializer
    pagination_class = paginators.Pages
    def get_queryset(self):
        user = get_user_from_request(self.request)
        return models.Like.objects.filter(user_id = user).select_related('post_id', 'post_id__sellerId', 'post_id__categoryId', 'post_id__categoryId__parent')
class MyPostsAPI(ListAPIView, GenericViewSet):
    queryset = models.Post.objects.all()
    serializer_class = serializers.WideCardSerializer
    pagination_class = paginators.Pages
    def get_queryset(self):
        user = get_user_from_request(self.request)
        return models.Post.objects.filter(sellerId = user).select_related('sellerId', 'categoryId', 'categoryId__parent')
class MyProfileAPI(ListAPIView, GenericViewSet):
    queryset = models.User.objects.none()
    serializer_class = serializers.ProfileSerializer
    def get_queryset(self):
        return get_user_from_request(self.request)
    def list(self, request, *args, **kwargs):
        q = self.get_queryset()
        serializer = self.get_serializer(q, many = False)
        return Response(serializer.data)
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = get_user_from_request(self.request)
        return context
class ProfileAPI(ListAPIView, RetrieveAPIView, GenericViewSet):
    queryset = models.User.objects.all()
    serializer_class = serializers.ProfileSerializer
    pagination_class = paginators.Pages
    filter_backends = [Search]
    search_fields = [
        'first_name', 
        'last_name', 
        'phoneNumber', 
        'username',
        'website'
        ]
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = get_user_from_request(self.request)
        return context
    def retrieve(self, request, *args, **kwargs):
        user = get_user_from_request(self.request)
        if user is not None:
            seller = models.User.objects.get(id = kwargs['pk'])
            userToUser, _ = models.InteractionUserToUser.objects.get_or_create(user_performer = user, user_performed_on = seller)
            userToUser.strength_sum += INCREASE_TO_USER_INTERACTION_PER_VIEW
            userToUser.save()
        return super().retrieve(request, *args, **kwargs)
    
class SimilarPostsAPI(ListAPIView,RetrieveAPIView, GenericViewSet):
    queryset = models.Post.objects.none()
    serializer_class = serializers.WideCardSerializer
    pagination_class = paginators.SimilarPages
    def get_queryset(self):
        user = get_user_from_request(self.request)
        if  self.action == 'retrieve':
            self.pk = self.kwargs['pk']
            paginators.similar_pk = self.pk
            q =queries.get_similar_posts(user, self.pk)
            return q
        return super().get_queryset()
    def retrieve(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
def update_last_seen(request):
    user = get_user_from_request(request)
    user.last_seen = datetime.now().astimezone(serializers.timezone)
    user.save()
    return HttpResponse('Updated last seen of user: ' + str(user))

class GetMyTransactions(ListAPIView, GenericViewSet):
    queryset = models.Transaction.objects.none()
    serializer_class = serializers.TransactionSerializer
    pagination_class = paginators.Pages
    def get_queryset(self): 
        user = get_user_from_request(self.request)
        return models.Transaction.objects.filter(Q(issuedFor = user ) | Q(issuedBy = user)).select_related('issuedBy','issuedFor', 'payMethod').order_by('-created_at')

class GetMyPendingTransactions(ListAPIView, GenericViewSet):
    queryset = models.Transaction.objects.none()
    serializer_class = serializers.TransactionSerializer
    pagination_class = paginators.Pages

    def get_queryset(self):
        user = get_user_from_request(self.request)
        return models.Transaction.objects.filter(Q(issuedFor = user ) | Q(issuedBy = user), payVerified = False, rejected = False).select_related('issuedBy','issuedFor', 'payMethod').order_by('-created_at')
    
class GetMyVerifiedTransactions(ListAPIView, GenericViewSet):
    queryset = models.Transaction.objects.none()
    serializer_class = serializers.TransactionSerializer
    pagination_class = paginators.Pages
    def get_queryset(self):
        user = get_user_from_request(self.request)
        return models.Transaction.objects.filter(Q(issuedFor = user ) | Q(issuedBy = user), payVerified = True, rejected = False).select_related('issuedBy','issuedFor', 'payMethod').order_by('-created_at')

class GetMyRejectedTransactions(ListAPIView, GenericViewSet):
    queryset = models.Transaction.objects.none()
    serializer_class = serializers.TransactionSerializer
    pagination_class = paginators.Pages
    def get_queryset(self):
        user = get_user_from_request(self.request)
        return models.Transaction.objects.filter(Q(issuedFor = user ) | Q(issuedBy = user), rejected = True).select_related('issuedBy','issuedFor', 'payMethod').order_by('-created_at')


class AdminRecentTransactions(ListAPIView, GenericViewSet):
    queryset = models.Transaction.objects.none()
    serializer_class = serializers.TransactionSerializer
    pagination_class = paginators.Pages
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
        user = get_user_from_request(self.request)
        if user.is_superuser is False:
            return models.Transaction.objects.none()
        return models.Transaction.objects.all().select_related('issuedBy','issuedFor', 'payMethod').order_by('-created_at')
    

class AdminPendingTransactions(ListAPIView, GenericViewSet):
    queryset = models.Transaction.objects.none()
    serializer_class = serializers.TransactionSerializer
    pagination_class = paginators.Pages
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
    pagination_class = paginators.Pages
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
        user = get_user_from_request(self.request)
        if user.is_superuser is False:
            return models.Transaction.objects.none()
        return models.Transaction.objects.filter(payVerified = True, rejected = False).select_related('issuedBy','issuedFor', 'payMethod').order_by('-amount', '-created_at')

class AdminRejectedTransactions(ListAPIView, GenericViewSet):
    queryset = models.Transaction.objects.none()
    serializer_class = serializers.TransactionSerializer
    pagination_class = paginators.Pages
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
        user = get_user_from_request(self.request)
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
            'adsCount': len(created_ads),
            'transaction': created_ads[0].transaction.id
        }
        print(response_data)

        return Response(response_data, status = 200)
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
        user = get_user_from_request(self.request)
        if self.action == 'list':
            return queries.children_ad_categories(user, parent=None)
        elif self.action == 'retrieve':
            return queries.children_ad_categories(user, self.kwargs['pk'])
        return super().get_queryset()
    def retrieve(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
class GetPaymentMethods(ListAPIView, RetrieveAPIView, GenericViewSet):
    queryset = models.PayMethod.objects.all()
    serializer_class = serializers.PaymentMethodsSerializer 
    def get_queryset(self):
        showVirtual = self.request.query_params.get('virtual')
        if showVirtual is not None and showVirtual == 'false':
            return models.PayMethod.objects.filter(isVirtualCurrency=False)
        
        if showVirtual is not None and showVirtual == 'true':
            return models.PayMethod.objects.filter(isVirtualCurrency=True)
        return super().get_queryset()
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(data = queryset, many=True)
        serializer.is_valid()
        data = serializer.data
        amount = self.request.query_params.get('amount')
        if amount is not None:
            required = int(amount)
            deposit = request.user.coins
            for  payment in data:
                virtual = payment['isVirtualCurrency']
                if virtual is True:
                    if deposit >= required:
                        payment['sufficientBalance'] = True
                    else:
                        payment['sufficientBalance'] = False

        return Response(data)

class BuyPackagesAPI(ListAPIView,CreateAPIView, GenericViewSet):
    queryset = models.Package.objects.all()
    serializer_class = serializers.PackageSerializer
    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.BuyPackageSerializer
        elif self.action == 'list':
            return serializers.PackageSerializer
        return super().get_serializer_class()
    def create(self, request):
        serializer = serializers.BuyPackageSerializer(data=request.data)
        serializer.setRequest(request)
        serializer.is_valid(raise_exception=True)
        transaction = serializer.save()  # This will call the serializer's create method
        pending = True
        # for ad in created_ads:
        #     if ad.payVerified is False:
        #         pending = True
        if pending is True:
            message = 'Transaction is pending'
        else:
            message = 'Your request was successful!'
        response_data = {
            'detail': message,
            'transaction': transaction.id
        }
        print(response_data)

        return Response(response_data, status = 200)
    def get_serializer_context(self):
        c = super().get_serializer_context()
        c['request'] = self.request
        return c
   
class ProfilePostsAPI(ListAPIView, GenericViewSet):
    queryset = models.Post.objects.all()
    serializer_class = serializers.WideCardSerializer
    pagination_class = paginators.Pages
    def get_queryset(self):
        return models.Post.objects.filter(sellerId = self.kwargs['seller_pk']).select_related('sellerId', 'categoryId', 'categoryId__parent')
    
def check_if_user_is_new(request, phone):
    user = None
    try:
        user = models.User.objects.get(phoneNumber=phone)
        userIsNew = False
    except Exception:
        userIsNew = True

    if user is not None:
        imgUrl = None
        if user.profilePicture is not None:
            imgUrl = user.profilePicture.url
        response = {
            'is_new': userIsNew,
            'id': user.id,
            'profilePicture': imgUrl,
            'name': user.first_name
        }
        
    else:
        response = {
            'is_new': userIsNew,
            'id': None,
            'profilePicture': None,
            'name': None
        }
    return JsonResponse(response)

@api_view(['POST'])
def update_user(request):
        user = get_user_from_request(request)
        profile_picture = request.FILES.get('imageBitmap')
        user.profilePicture = profile_picture
        user.first_name = request.data.get('name')
        user.save()
        return JsonResponse({})

INITIAL_CATEGORIES_STRENGTH = 100
@api_view(['POST'])

def initial_categories(request):
    user = get_user_from_request(request)
    if user is None:
        return JsonResponse({}, status=500)
    try:
        categories = list(request.data['categories'])
        if len(categories) == 0:
            print("empty")
            return JsonResponse({}, status=500)
        categories_obj = models.Category.objects.filter(id__in = categories)
        categories_list = [
            models.InteractionUserToCategory(
                        category_id=category,
                        user_id=user,
                        strength_sum = INITIAL_CATEGORIES_STRENGTH
                    )
                    for category in categories_obj
            
        ]
        models.InteractionUserToCategory.objects.bulk_create(categories_list)
        return JsonResponse({})
    except Exception as e:
        print(e)
        return JsonResponse({}, status = 500)
    
@api_view(['POST'])
def send_screenshot(request):
    user = get_user_from_request(request)
    transactionId = request.data.get('transactionId')
    image = request.FILES.get('imageBitmap')
    try:
        if user.is_superuser:
            transaction = models.Transaction.objects.get(id = transactionId)
        else:
            transaction = models.Transaction.objects.get(issuedFor=user, id = transactionId)
        transaction.verificationScreenshot = image
        transaction.save()
        serializer = serializers.TransactionSerializer(data=transaction, many=False)
        serializer.is_valid()
        return Response(serializer.data)
    except Exception:
        return JsonResponse({}, status = 401)


@api_view(['POST'])
def transaction_verification_status(request):
    user = get_user_from_request(request)
    transactionId = request.data.get('transactionId')
    trueForVerifyFalseForReject = bool(request.data.get('trueForVerifyFalseForReject'))
    if user is not None and user.is_superuser:
        try:
            transaction = models.Transaction.objects.get(id = transactionId)
            transaction.payVerified = trueForVerifyFalseForReject
            transaction.rejected = not trueForVerifyFalseForReject
            transaction.save()
            serializer = serializers.TransactionSerializer(data=transaction, many=False)
            serializer.is_valid()
            return Response(serializer.data)
        except Exception:
            return JsonResponse({}, status = 401)
    else:
        return JsonResponse({}, status = 401)





@api_view(['POST'])
def call_post(request):
    user = get_user_from_request(request)
    id = request.data.get('id')
    if user is not None:
        post = models.Post.objects.select_related('sellerId', 'categoryId').get(postId = id)
        seller = post.sellerId
        if user.id != seller.id:

            category = post.categoryId
            userToUser, _ = models.InteractionUserToUser.objects.get_or_create(user_performer = user, user_performed_on = seller)
            userToCategory, _ = models.InteractionUserToCategory.objects.get_or_create(user_id = user, category_id = category)
            userToPost, _ = models.InteractionUserToPost.objects.get_or_create(user_id = user, post_id = post)

            userToUser.strength_sum += INCREASE_TO_USER_INTERACTION_PER_CALL
            userToCategory.strength_sum += INCREASE_TO_CATEGORY_INTERACTION_PER_CALL
            userToPost.strength_sum += INCREASE_TO_POST_INTERACTION_PER_CALL

            userToUser.save()
            userToPost.save()
            userToCategory.save()
        return JsonResponse({})

    else:
        return JsonResponse({}, status = 401)


@api_view(['POST'])
def call_profile(request):
    user = get_user_from_request(request)
    id = request.data.get('id')
    if user is not None:
        seller = models.User.objects.get(id = id)
        if user.id != seller.id:

            userToUser, _ = models.InteractionUserToUser.objects.get_or_create(user_performer = user, user_performed_on = seller)

            userToUser.strength_sum += INCREASE_TO_USER_INTERACTION_PER_CALL

            userToUser.save()
        return JsonResponse({})

    else:
        return JsonResponse({}, status = 401)


@api_view(['POST'])
def share_profile(request):
    user = get_user_from_request(request)
    id = request.data.get('id')
    if user is not None:
        seller = models.User.objects.get(id = id)
        if user.id != seller.id:

            userToUser, _ = models.InteractionUserToUser.objects.get_or_create(user_performer = user, user_performed_on = seller)

            userToUser.strength_sum += INCREASE_TO_USER_INTERACTION_PER_SHARE

            userToUser.save()
        return JsonResponse({})

    else:
        return JsonResponse({}, status = 401)


@api_view(['POST'])
def share_post(request):
    user = get_user_from_request(request)
    id = request.data.get('id')
    if user is not None:
        post = models.Post.objects.select_related('sellerId', 'categoryId').get(postId = id)
        seller = post.sellerId
        if user.id != seller.id:
            category = post.categoryId
            userToUser, _ = models.InteractionUserToUser.objects.get_or_create(user_performer = user, user_performed_on = seller)
            userToCategory, _ = models.InteractionUserToCategory.objects.get_or_create(user_id = user, category_id = category)
            userToPost, _ = models.InteractionUserToPost.objects.get_or_create(user_id = user, post_id = post)

            userToUser.strength_sum += INCREASE_TO_USER_INTERACTION_PER_SHARE
            userToCategory.strength_sum += INCREASE_TO_CATEGORY_INTERACTION_PER_SHARE
            userToPost.strength_sum += INCREASE_TO_POST_INTERACTION_PER_SHARE

            userToUser.save()
            userToPost.save()
            userToCategory.save()
        return JsonResponse({})

    else:
        return JsonResponse({}, status = 401)



def get_user_from_request(request):
    user = request.user
    if isinstance(user, tuple):
        user_obj, _ = user
        return user_obj
    return user



