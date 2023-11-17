from . import models
from django.db.models import Exists, OuterRef, FloatField, ExpressionWrapper, DecimalField, Q, F,Max,Avg, Subquery, Count, Sum, Prefetch, CharField, Value, IntegerField
from django.db.models.functions import Coalesce, Ln
from datetime import date, timedelta
from itertools import chain

NEW_POST_RECOMMENDATION_LIMIT = 30
FOLLOWING_BASED_RECOMMENDATION_LIMIT = 35
CATEGORY_BASED_RECOMMENDATION_LIMIT = 5
IICF_RECOMMENDATION_LIMIT = 45
UUCF_RECOMMENDATION_LIMIT = 20
UCCF_RECOMMENDATION_LIMIT = 15
RECOMMENDATION_LIMIT = 25
POSTS_INITIAL_IICF = 5
USERS_INITIAL_IICF = 20

USERS_INITIAL_UUCF = 20

CATEGORIES_INITIAL_UCCF = 5
SELLERS_INITIAL_UCCF = 20

FOLLOWING_INITIAL_FOLLOWING = 50

CATEGORY_REDUCER_CONSTANT = 100
USER_REDUCER_CONSTANT = 10
def reduce_seen_posts_influence(user):
    return Coalesce(
                Ln(
                    models.Seen.objects.filter(
                        user = user.id,
                        post = OuterRef('postId')
                    ).values('count')[:1] 
                    + 
                    Value(2, output_field=IntegerField()), 
                    output_field=FloatField()),
                1.0, output_field=FloatField())
def reduce_category_influence(user):
    return Coalesce(
        Value(1, output_field=IntegerField()) +  
        models.InteractionUserToCategory.objects.filter(
                        user_id=user.id,
                        category_id = OuterRef('categoryId')
                    ).values('strength_sum')[:1]
        /              
        Value(CATEGORY_REDUCER_CONSTANT, output_field=IntegerField()) ,
        1.0, output_field=FloatField()
        )
def reduce_user_influence(user):
    return Coalesce(
        Value(1, output_field=IntegerField()) +  
        models.InteractionUserToUser.objects.filter(
                        user_performer=user.id,
                        user_performed_on__in = OuterRef('sellerId')
                    ).values('strength_sum')[:1]
        /             
        Value(USER_REDUCER_CONSTANT, output_field=IntegerField()) ,
        1.0, output_field=FloatField()
        )

def reduce_follower_influence():
    return Coalesce(
                Value(1, output_field=IntegerField()) + 
                Avg('sellerId__followers__strength') / 
                Value(models.HOW_MUCH_FOLLOWER_STRENGTH_SHOULD_REDUCE_INFLUENCE_ON_NEW_POSTS, output_field=IntegerField()) ,
                1.0, output_field=FloatField()
            )
def get_all_posts(request):
    posts = models.Post.objects.select_related(
        'categoryId', 
        'sellerId', 
        'categoryId__parent', 
        'categoryId__parent__parent', 
        'categoryId__parent__parent__parent', 
        'categoryId__parent__parent__parent__parent', 
        'categoryId__parent__parent__parent__parent__parent', 
        'categoryId__parent__parent__parent__parent__parent__parent', 
        'categoryId__parent__parent__parent__parent__parent__parent__parent', 
        'categoryId__parent__parent__parent__parent__parent__parent__parent__parent', 
        'categoryId__parent__parent__parent__parent__parent__parent__parent__parent__parent',
        'categoryId__parent__parent__parent__parent__parent__parent__parent__parent__parent__parent'
        ).annotate(hasLiked= Exists(models.Like.objects.filter(
            user_id = request.user, post_id = OuterRef('postId')
        )), hasSaved= Exists(models.Favourite.objects.filter(
            user_id = request.user, post_id = OuterRef('postId')
        ))).all()[:10]
    return posts

def get_post_ids_with_item_item_collaborative_filtering(user):
    most_interacted_posts = posts_for_IICF(user)
    most_interacted_users = users_for_IICF(user, most_interacted_posts)
    iposts = models.InteractionUserToPost.objects.filter(
                Q(user_id__in=Subquery(most_interacted_users.values('user_id'))) & 
                ~Q(post_id__in=Subquery(most_interacted_posts.values('post_id')))
            ).order_by(
                '-strength_sum'
            )[:IICF_RECOMMENDATION_LIMIT]
    posts = models.Post.objects.filter(
         Q(postId__in = Subquery(iposts.values('post_id')))
        ).select_related('categoryId', 'sellerId').annotate(
                tag=Value('iicf', output_field=CharField()),
                hasLiked=Exists(models.Like.objects.filter(
                    user_id = user, post_id = OuterRef('postId')
                )),
                hasSaved=Exists(models.Favourite.objects.filter(
                    user_id = user, post_id = OuterRef('postId')
                )),
                rank = ExpressionWrapper(F('strength'), output_field=FloatField()) 
                    / reduce_seen_posts_influence(user)
                    
            ).values(
                'postId',
                'tag',
                'rank'
            )
    return posts
def get_post_ids_with_user_user_collaborative_filtering(user):
    most_interacted_users = users_for_UUCF(user)
    iposts = models.InteractionUserToPost.objects.filter(
                Q(user_id__in=Subquery(most_interacted_users.values('user_performed_on')))
            ).exclude(
                user_id=user.id
            ).order_by(
                '-strength_sum'
            )[:UUCF_RECOMMENDATION_LIMIT]
    posts = models.Post.objects.filter(
        Q(postId__in = Subquery(iposts.values('post_id')))
    ).select_related('categoryId', 'sellerId').annotate(
                tag=Value('uucf', output_field=CharField()),
                hasLiked=Exists(models.Like.objects.filter(
                    user_id = user, post_id = OuterRef('postId')
                )),
                hasSaved=Exists(models.Favourite.objects.filter(
                    user_id = user, post_id = OuterRef('postId')
                )),
                rank = ExpressionWrapper(F('strength'), output_field=FloatField())
                    / reduce_seen_posts_influence(user)
            ).values(
                'postId',
                'tag',
                'rank'
            )
    return posts

def get_post_ids_with_user_category_collaborative_filtering(user):
    most_interacted_categories = categories_for_UCCF(user)
    most_interacted_users = sellers_for_UCCF(user, most_interacted_categories)

    posts = models.Post.objects.filter(
                Q(sellerId__in=Subquery(most_interacted_users.values('seller_id')))
            ).exclude(
                sellerId=user.id
            ).select_related('categoryId', 'sellerId').annotate(
                post_id = F('postId'),
                tag=Value('uccf', output_field=CharField()),
                hasLiked=Exists(models.Like.objects.filter(
                    user_id = user, post_id = OuterRef('postId')
                )),
                hasSaved=Exists(models.Favourite.objects.filter(
                    user_id = user, post_id = OuterRef('postId')
                )),
                rank = 
                    reduce_category_influence(user)
                    / 
                    reduce_seen_posts_influence(user)
            ).values(
                'postId',
                'tag',
                'rank'
            ).order_by(
                '-strength'
            )[:UCCF_RECOMMENDATION_LIMIT]
    return posts

def get_post_ids_by_following(user):
    most_interacted_following = following_for_FollowingBased(user)
    posts = models.Post.objects.filter(
                Q(sellerId__in=Subquery(most_interacted_following.values('user_performed_on')))
            ).exclude(
                sellerId=user.id
            ).select_related('categoryId', 'sellerId').annotate(   
                post_id = F('postId'),
                tag=Value('following', output_field=CharField()),
                hasLiked=Exists(models.Like.objects.filter(
                    user_id = user, post_id = OuterRef('postId')
                )),
                hasSaved=Exists(models.Favourite.objects.filter(
                    user_id = user, post_id = OuterRef('postId')
                )),
                rank = models.InteractionUserToUser.objects.filter(
                        user_performer=user.id,
                        user_performed_on__in = OuterRef('sellerId')
                    ).values('strength_sum')[:1] 
                    / reduce_seen_posts_influence(user)
            ).values(
                'postId',
                'tag',
                'rank'
            ).order_by(
                '-strength'
            )[:FOLLOWING_BASED_RECOMMENDATION_LIMIT]
    return posts

def get_post_ids_by_category_personalized(user):
    most_interacted_categories = categories_for_UCCF(user)
    posts = models.Post.objects.filter(
                Q(categoryId__in=Subquery(most_interacted_categories.values('category_id')))
            ).exclude(
                sellerId=user.id
            ).select_related('categoryId', 'sellerId').annotate(
                post_id = F('postId'),
                tag=Value('category', output_field=CharField()),
                hasLiked=Exists(models.Like.objects.filter(
                    user_id = user, post_id = OuterRef('postId')
                )),
                hasSaved=Exists(models.Favourite.objects.filter(
                    user_id = user, post_id = OuterRef('postId')
                )),
                rank = 
                    reduce_category_influence(user)
                    / 
                    reduce_seen_posts_influence(user)
                ).values(
                'postId',
                'tag',
                'rank'
            ).order_by(
                '-strength'
            )[:CATEGORY_BASED_RECOMMENDATION_LIMIT]
    return posts
def get_new_post_ids_personalized(user):
    most_interacted_categories = categories_for_UCCF(user)
    now = date.today()
    one_week = now - timedelta(days=models.HOW_LONG_A_POST_STAYS_NEW_IN_DAYS)
    posts = models.Post.objects.filter(
                categoryId__in=Subquery(most_interacted_categories.values('category_id')),
                date__range = [one_week, now]
            ).exclude(
                sellerId=user.id
            ).select_related('categoryId', 'sellerId').annotate(
                post_id = F('postId'),
                tag=Value('new', output_field=CharField()),
                hasLiked=Exists(models.Like.objects.filter(
                    user_id = user, post_id = OuterRef('postId')
                )),
                hasSaved=Exists(models.Favourite.objects.filter(
                    user_id = user, post_id = OuterRef('postId')
                )),
                rank = 
                    models.InteractionUserToCategory.objects.filter(
                        user_id= user.id,
                        category_id = OuterRef('categoryId')
                    ).values('strength_sum')[:1] 
                    / reduce_seen_posts_influence(user)
                    / reduce_follower_influence()
                
            ).values(
                'postId',
                'tag',
                'rank'
            ).order_by(
                '-rank'
            )[:NEW_POST_RECOMMENDATION_LIMIT]
    return posts

def combined_queryset(user):
    iicf = get_post_ids_with_item_item_collaborative_filtering(user)
    uucf = get_post_ids_with_user_user_collaborative_filtering(user)
    uccf = get_post_ids_with_user_category_collaborative_filtering(user)
    categoryBased = get_post_ids_by_category_personalized(user)
    followingBased = get_post_ids_by_following(user)
    newPost = get_new_post_ids_personalized(user)
    combined = iicf.union(uucf, uccf, categoryBased, followingBased, newPost).order_by('-rank')
    return combined
def get_recommendations(user):
    queryset = combined_queryset(user)
    return queryset



def posts_for_IICF(user):
    most_interacted_posts = models.InteractionUserToPost.objects.filter(
            user_id=user.id
            ).values(
                'post_id', 'strength_sum'
            ).order_by(
                '-strength_sum'
            )[:POSTS_INITIAL_IICF]
    return most_interacted_posts

def users_for_IICF(user, most_interacted_posts):
    most_interacted_users = models.InteractionUserToPost.objects.filter(
                post_id__in=Subquery(most_interacted_posts.values('post_id'))
            ).annotate(
                cumulative = models.InteractionUserToPost.objects.filter(
            user_id=user.id,
            post_id = F('post_id')
            ).values('strength_sum')[:1] * F('strength_sum')
            ).exclude(
                user_id=user.id
            ).values(
                'post_id', 'cumulative'
            ).order_by(
                '-cumulative'
            )[:USERS_INITIAL_IICF]
    return most_interacted_users
def users_for_UUCF(user):
    most_interacted_users = models.InteractionUserToUser.objects.filter(
            user_performer=user.id
            ).values(
                'user_performed_on', s = F('strength_sum')
            ).order_by(
                '-s'
            )[:USERS_INITIAL_UUCF]
    return most_interacted_users
def categories_for_UCCF(user):
    most_interacted_categories = models.InteractionUserToCategory.objects.filter(
            user_id=user.id
            ).values(
                'category_id', s=F('strength_sum')
            ).order_by(
                '-s'
            )[:CATEGORIES_INITIAL_UCCF]
    return most_interacted_categories
def sellers_for_UCCF(user, most_interacted_categories):
    most_interacted_users = models.AssociationCategoryToSeller.objects.filter(
                category_id__in=Subquery(most_interacted_categories.values('category_id'))
            ).annotate(
                cumulative = models.InteractionUserToCategory.objects.filter(
                        user_id=user.id,
                        category_id = F('category_id')
                    ).values('strength_sum')[:1] * F('strength')
            ).exclude(
                seller_id=user.id
            ).values(
                'seller_id', 'cumulative'
            ).order_by(
                '-cumulative'
            )[:SELLERS_INITIAL_UCCF]
    return most_interacted_users
def following_for_FollowingBased(user):
    following = models.Follower.objects.filter(
        user_follower = user.id
    ).values(
        'user_followed'
    ).order_by(
        '-strength'
    )
    most_interacted_following = models.InteractionUserToUser.objects.filter(
            user_performer=user.id,
            user_performed_on__in = Subquery(following.values('user_followed'))
            ).values(
                'user_performed_on', s = F('strength_sum')
            ).order_by(
                '-s'
            )[:FOLLOWING_INITIAL_FOLLOWING]
    return most_interacted_following

def recommended_from_table(user):
    recommended = models.Recommended.objects.filter(userId = user.id).values('postId').distinct().annotate(
        sum = Subquery(
            models.Recommended.objects.filter(postId=OuterRef('postId'), userId = user.id).values('postId').annotate(
            sum=Sum('rank')
        ).values('sum')[:1]), 
        recommender = Subquery(
            models.Recommended.objects.filter(
                postId=OuterRef('postId'), 
                userId = user.id
                ).order_by('-rank')[:1].values('tag')[:1]
          
        )).order_by('-sum')
    posts = models.Post.objects.filter(
         Q(postId__in = Subquery(recommended.values('postId')))
        ).select_related('categoryId', 'sellerId', 
        'categoryId__parent', 
        'categoryId__parent__parent', 
        'categoryId__parent__parent__parent', 
        'categoryId__parent__parent__parent__parent', 
        'categoryId__parent__parent__parent__parent__parent', 
        'categoryId__parent__parent__parent__parent__parent__parent', 
        'categoryId__parent__parent__parent__parent__parent__parent__parent', 
        'categoryId__parent__parent__parent__parent__parent__parent__parent__parent', 
        'categoryId__parent__parent__parent__parent__parent__parent__parent__parent__parent',
        'categoryId__parent__parent__parent__parent__parent__parent__parent__parent__parent__parent').annotate(
                tag=recommended.filter(postId=OuterRef('postId')).values('recommender')[:1],
                hasLiked=Exists(models.Like.objects.filter(
                    user_id = user, post_id = OuterRef('postId')
                )),
                hasSaved=Exists(models.Favourite.objects.filter(
                    user_id = user, post_id = OuterRef('postId')
                )),
                rank = recommended.filter(postId=OuterRef('postId')).values('sum')[:1],
            ).order_by(
                '-rank'
            )[:RECOMMENDATION_LIMIT]
    return posts