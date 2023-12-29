from . import models
from django.db.models import Case, When, Exists, OuterRef, FloatField, ExpressionWrapper, DecimalField, Q, F,Max, Subquery, Count, Sum, Prefetch, CharField, Value, IntegerField
from django.db.models.functions import Coalesce, Ln, Cast
from datetime import date, timedelta
from itertools import chain
from django.db.models.aggregates import Avg
from django.conf import settings
NEW_POST_RECOMMENDATION_LIMIT = settings.NEW_POST_RECOMMENDATION_LIMIT
FOLLOWING_BASED_RECOMMENDATION_LIMIT = settings.FOLLOWING_BASED_RECOMMENDATION_LIMIT
CATEGORY_BASED_RECOMMENDATION_LIMIT = settings.CATEGORY_BASED_RECOMMENDATION_LIMIT
IICF_RECOMMENDATION_LIMIT = settings.IICF_RECOMMENDATION_LIMIT
UUCF_RECOMMENDATION_LIMIT = settings.UUCF_RECOMMENDATION_LIMIT
UCCF_RECOMMENDATION_LIMIT = settings.UCCF_RECOMMENDATION_LIMIT
RECOMMENDATION_LIMIT = settings.RECOMMENDATION_LIMIT
POSTS_INITIAL_IICF = settings.POSTS_INITIAL_IICF
USERS_INITIAL_IICF = settings.USERS_INITIAL_IICF

USERS_INITIAL_UUCF = settings.USERS_INITIAL_UUCF

CATEGORIES_INITIAL_UCCF = settings.CATEGORIES_INITIAL_UCCF
SELLERS_INITIAL_UCCF = settings.SELLERS_INITIAL_UCCF

FOLLOWING_INITIAL_FOLLOWING = settings.FOLLOWING_INITIAL_FOLLOWING

CATEGORY_REDUCER_CONSTANT = settings.CATEGORY_REDUCER_CONSTANT
USER_REDUCER_CONSTANT = settings.USER_REDUCER_CONSTANT
def reduce_seen_posts_influence(user):
    return Coalesce(
                # Ln(
                    
                    Value(10, output_field=IntegerField())
                    **
                    Coalesce(
                        Coalesce(
                            models.Seen.objects.filter(
                            user = user.id,
                            post = OuterRef('postId')
                        ).values('count')[:1]
                            , 0, output_field=FloatField()
                        ) 
                        /
                        Value(10, output_field=FloatField())
                        ,0,output_field=DecimalField()
                    )
                   
                    
                     
                    # + 
                    # Value(2, output_field=IntegerField())
                    # , 
                    # output_field=FloatField()
                    # )
                    ,
                
                3, output_field=FloatField())
def reduce_category_influence(user):
    return Coalesce(
        Value(1.0, output_field=FloatField()) +  
        models.InteractionUserToCategory.objects.filter(
                        Q(
                            category_id = OuterRef('categoryId')
                        ) 
                        | 
                        Q(
                            category_id = OuterRef('categoryId__parent')
                        )
                        |
                        Q(
                            category_id = OuterRef('categoryId__parent__parent')
                        ) 
                        | 
                        Q(
                            category_id = OuterRef('categoryId__parent__parent__parent')
                        )
                        |
                        Q(
                            category_id = OuterRef('categoryId__parent__parent__parent__parent')
                        ),
                        user_id=user.id
                    ).annotate(
                        total_strength = Sum('strength_sum')
                    ).values('total_strength')[:1]
                    
        /              
        Value(CATEGORY_REDUCER_CONSTANT, output_field=FloatField()) ,
        1.0, output_field=FloatField()
        )
def reduce_user_influence(user):
    return Coalesce(
        Value(1.0, output_field=FloatField()) +  
        models.InteractionUserToUser.objects.filter(
                        user_performer=user.id,
                        user_performed_on__in = OuterRef('sellerId')
                    ).values('strength_sum')[:1]
        /             
        Value(USER_REDUCER_CONSTANT, output_field=FloatField()) ,
        1.0, output_field=FloatField()
        )
def reduce_follower_influence():
    return Coalesce(
                Value(1.0, output_field=FloatField()) + 
                Avg('sellerId__followers__strength') / 
                Value(models.HOW_MUCH_FOLLOWER_STRENGTH_SHOULD_REDUCE_INFLUENCE_ON_NEW_POSTS, output_field=FloatField()) ,
                1.0, output_field=FloatField()
            )

def get_all_posts(request):
    posts = models.Post.objects.select_related(
        'categoryId', 
        'sellerId', 
        'categoryId__parent', 
        'categoryId__parent__parent', 
        'categoryId__parent__parent__parent', 
        'categoryId__parent__parent__parent__parent'
        ).prefetch_related('postImage').annotate(hasLiked= Exists(models.Like.objects.filter(
            user_id = request.user, post_id = OuterRef('postId')
        )), hasSaved= Exists(models.Favourite.objects.filter(
            user_id = request.user, post_id = OuterRef('postId')
        ))).all()
    return posts

def get_ad_by_category(user):
    most_interacted_categories = categories_for_UCCF(user)
    personalized_ads = ads_for_categories(most_interacted_categories)
    posts = models.Post.objects.filter(
                postId__in=Subquery(personalized_ads.values('postId')) 
            ).exclude(
                sellerId=user.id
            ).select_related('categoryId', 'sellerId').annotate(
                tag=Value('ads', output_field=CharField()),
                hasLiked=Exists(models.Like.objects.filter(
                    user_id = user, post_id = OuterRef('postId')
                )),
                hasSaved=Exists(models.Favourite.objects.filter(
                    user_id = user, post_id = OuterRef('postId')
                )),
                rank = 
                    ad_weight() *
                    reduce_category_influence(user)
                    / 
                    reduce_seen_posts_influence(user)
            ).order_by(
                '-rank'
            )
    return posts
def get_ad_for_category(user, category):
    personalized_ads = models.Ads.objects.filter(
                Q(
                    categoryId=category
                    ) 
                |Q(
                    categoryId__parent=category
                    ) 
                | Q(
                    categoryId__parent__parent=category
                    ) 
                |Q(
                    categoryId__parent__parent__parent=category
                    ) 
                |Q(
                    categoryId__parent__parent__parent__parent=category
                    ) ,
                    payVerified = True
            ).order_by('-strength').values(
                'postId'
            )
    posts = models.Post.objects.filter(
                postId__in=Subquery(personalized_ads.values('postId')) 
            ).exclude(
                sellerId=user.id
            ).select_related('categoryId', 'sellerId').annotate(
                tag=Value('ads', output_field=CharField()),
                hasLiked=Exists(models.Like.objects.filter(
                    user_id = user, post_id = OuterRef('postId')
                )),
                hasSaved=Exists(models.Favourite.objects.filter(
                    user_id = user, post_id = OuterRef('postId')
                )),
                rank = 
                    ad_weight() *
                    reduce_category_influence(user)
                    / 
                    reduce_seen_posts_influence(user)
            ).order_by(
                '-rank'
            )
    return posts
def get_similar_ads(user, postId):
    post = models.Post.objects.filter(postId=postId).values('categoryId')
    similar_ads = ads_similar(post)
    posts = models.Post.objects.filter(
                postId__in=Subquery(similar_ads.values('postId')) 
            ).exclude(
                sellerId=user.id
            ).select_related('categoryId', 'sellerId').annotate(
                tag=Value('ads', output_field=CharField()),
                hasLiked=Exists(models.Like.objects.filter(
                    user_id = user, post_id = OuterRef('postId')
                )),
                hasSaved=Exists(models.Favourite.objects.filter(
                    user_id = user, post_id = OuterRef('postId')
                )),
                rank = 
                    ad_weight() *
                    reduce_category_influence(user)
                    / 
                    reduce_seen_posts_influence(user)
            ).order_by(
                '-rank'
            )
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
                rank = 
                    reduce_category_influence(user)
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
                rank = 
                    reduce_category_influence(user)
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
                '-rank'
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
                        user_performed_on = OuterRef('sellerId')
                    ).values('strength_sum')[:1] 
                    / reduce_seen_posts_influence(user)
            ).values(
                'postId',
                'tag',
                'rank'
            ).order_by(
                '-rank'
            )[:FOLLOWING_BASED_RECOMMENDATION_LIMIT]
    return posts
def get_post_ids_by_category_personalized(user):
    most_interacted_categories = categories_for_UCCF(user)
    posts = models.Post.objects.filter(
                Q(
                    categoryId__in=Subquery(most_interacted_categories.values('category_id'))
                    ) 
                |Q(
                    categoryId__parent__in=Subquery(most_interacted_categories.values('category_id'))
                    ) 
                | Q(
                    categoryId__parent__parent__in=Subquery(most_interacted_categories.values('category_id'))
                    ) 
                |Q(
                    categoryId__parent__parent__parent__in=Subquery(most_interacted_categories.values('category_id'))
                    ) 
                |Q(
                    categoryId__parent__parent__parent__parent__in=Subquery(most_interacted_categories.values('category_id'))
                    ) 
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
                '-rank'
            )[:CATEGORY_BASED_RECOMMENDATION_LIMIT]
    return posts
def get_new_post_ids_personalized(user):
    most_interacted_categories = categories_for_UCCF(user)
    now = date.today()
    one_week = now - timedelta(days=models.HOW_LONG_A_POST_STAYS_NEW_IN_DAYS)
    posts = models.Post.objects.filter(
                Q(
                    categoryId__in=Subquery(most_interacted_categories.values('category_id'))
                    ) 
                |Q(
                    categoryId__parent__in=Subquery(most_interacted_categories.values('category_id'))
                    ) 
                | Q(
                    categoryId__parent__parent__in=Subquery(most_interacted_categories.values('category_id'))
                    ) 
                |Q(
                    categoryId__parent__parent__parent__in=Subquery(most_interacted_categories.values('category_id'))
                    ) 
                |Q(
                    categoryId__parent__parent__parent__parent__in=Subquery(most_interacted_categories.values('category_id'))
                    ) 
                ,
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
                    reduce_category_influence(user) 
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
def ad_weight():
    return models.Ads.objects.filter(
                        postId=OuterRef('postId'),
                    ).values('strength').order_by('-strength')[:1]
def ads_for_categories(categories):
    ads = models.Ads.objects.filter( 
                Q(
                    categoryId__in=Subquery(categories.values('category_id'))
                    ) 
                |Q(
                    categoryId__parent__in=Subquery(categories.values('category_id'))
                    ) 
                | Q(
                    categoryId__parent__parent__in=Subquery(categories.values('category_id'))
                    ) 
                |Q(
                    categoryId__parent__parent__parent__in=Subquery(categories.values('category_id'))
                    ) 
                |Q(
                    categoryId__parent__parent__parent__parent__in=Subquery(categories.values('category_id'))
                    ) 
                    ,
                    payVerified = True
            ).order_by('-strength').values(
                'postId'
            )
    return ads
def ads_similar(post):
    ads = models.Ads.objects.filter(
                Q(categoryId__in=Subquery(post.values('categoryId'))) 
                |Q(categoryId__in=Subquery(post.values('categoryId__parent'))) 
                |Q(categoryId__in=Subquery(post.values('categoryId__parent__parent'))) 
                |Q(categoryId__in=Subquery(post.values('categoryId__parent__parent__parent'))) 
                |Q(categoryId__in=Subquery(post.values('categoryId__parent__parent__parent__parent')))
                ,
                payVerified = True
            ).order_by('-strength').values(
                'postId'
            )
    return ads
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
                Q(
                    category_id__in=Subquery(most_interacted_categories.values('category_id'))
                    ) 
                |Q(
                    category_id__parent__in=Subquery(most_interacted_categories.values('category_id'))
                    ) 
                | Q(
                    category_id__parent__parent__in=Subquery(most_interacted_categories.values('category_id'))
                    ) 
                |Q(
                    category_id__parent__parent__parent__in=Subquery(most_interacted_categories.values('category_id'))
                    ) 
                |Q(
                    category_id__parent__parent__parent__parent__in=Subquery(most_interacted_categories.values('category_id'))
                    ) 
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
        'categoryId__parent__parent__parent__parent'
        ).prefetch_related('postImage').annotate(
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
            )
    return posts

def subquery_for_categories(user):
    return models.InteractionUserToCategory.objects.filter(
                user_id=user,
                category_id=OuterRef('id')
            ).values('category_id').annotate(
                interaction_sum=Coalesce(Sum('strength_sum'), 0)
            ).values('interaction_sum')
def children_categories(user, parent):
    return models.Category.objects.filter(parent = parent).annotate(
                tree = Count('children__id', distinct=True) +
                               Count('children__children__id', distinct=True) +
                               Count('children__children__children__id', distinct=True) +
                               Count('children__children__children__children__id', distinct=True),
                posts = Count('posts_in_category'),
                interaction_with_user = Coalesce(Subquery(subquery_for_categories(user)), 0),
                interaction_for_category = Coalesce(Sum('interaction__strength_sum'), 0)
            ).order_by('-interaction_with_user', '-posts', '-interaction_for_category', '-tree')

def recommended_categories(user):
    return models.Category.objects.all().annotate(
                tree = Count('children__id', distinct=True) +
                               Count('children__children__id', distinct=True) +
                               Count('children__children__children__id', distinct=True) +
                               Count('children__children__children__children__id', distinct=True),
                posts = Count('posts_in_category'),
                interaction_with_user = Coalesce(Subquery(subquery_for_categories(user)), 0),
                interaction_for_category = Coalesce(Sum('interaction__strength_sum'), 0)
            ).order_by('-interaction_with_user', '-posts', '-interaction_for_category', '-tree')

def get_highest_bid():
    return Coalesce(
                    Subquery(
                        models.Ads.objects.filter(
                            categoryId = OuterRef('id')
                            ,
                            payVerified = True
                        ).order_by('-strength').values('strength')[:1]

                    ), 0, output_field=IntegerField()
                )


def get_second_highest_bid():
    return Coalesce(
                    Subquery(
                        models.Ads.objects.filter(
                            categoryId = OuterRef('id')
                            ,
                            payVerified = True
                        ).order_by('-strength').values('strength')[1:2]
                    ), 0, output_field=IntegerField()
                )
def get_third_highest_bid():
    return Coalesce(
                    Subquery(
                        models.Ads.objects.filter(
                            categoryId = OuterRef('id')
                            ,
                            payVerified = True
                        ).order_by('-strength').values('strength')[2:3]

                    ), 0, output_field=IntegerField()
                )
def children_ad_categories(user, parent):
    return models.Category.objects.filter(parent = parent).annotate(
                subcategoriesCount = Count('children__id', distinct=True) +
                               Count('children__children__id', distinct=True) +
                               Count('children__children__children__id', distinct=True) +
                               Count('children__children__children__children__id', distinct=True),
                countAds = Coalesce(
                        Subquery(
                            models.Ads.objects.filter(
                                categoryId = OuterRef('id')
                                ,
                                payVerified = True
                            ).values('categoryId').annotate(
                                count = Count('categoryId')
                            ).values('count')[:1]
                        ), 0, output_field=IntegerField()
                ),
                hasChildren = Exists(models.Category.objects.filter(
                    parent = OuterRef('id')
                )),
                averagePrice = Coalesce(
                        Subquery(
                            models.Ads.objects.filter(
                                categoryId = OuterRef('id')
                                ,
                                payVerified = True
                    
                            ).values('categoryId').annotate(
                                average = Avg('strength')
                            ).values('average')[:1]
                        ), 0, output_field=IntegerField()
                )
                ,
                highestBid = get_highest_bid(),
                secondHighestBid = get_second_highest_bid(),
                thirdHighestBid = get_third_highest_bid(),
                posts = Count('posts_in_category'),
                interaction_with_user = Coalesce(Subquery(subquery_for_categories(user)), 0),
                interaction_for_category = Coalesce(Sum('interaction__strength_sum'), 0)
            ).order_by('-interaction_with_user', '-posts', '-interaction_for_category', '-subcategoriesCount')

def get_similar_posts(user, postId):
    post = models.Post.objects.get(postId=postId)
    category = post.categoryId
    posts = models.Post.objects.filter(
                Q(
                    categoryId=category
                    ) 
                |Q(
                    categoryId__parent=category
                    ) 
                | Q(
                    categoryId__parent__parent=category
                    ) 
                |Q(
                    categoryId__parent__parent__parent=category
                    ) 
                |Q(
                    categoryId__parent__parent__parent__parent=category
                    ) 
            ).exclude(
                Q(
                    sellerId=user.id
                  ) 
                  |
                Q(
                    postId = postId
                )
                
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
                ).order_by(
                '-rank'
            )
    return posts

def get_recommended_in_category(user, category):
    posts = models.Post.objects.filter(
                Q(
                    categoryId=category
                    ) 
                |Q(
                    categoryId__parent=category
                    ) 
                | Q(
                    categoryId__parent__parent=category
                    ) 
                |Q(
                    categoryId__parent__parent__parent=category
                    ) 
                |Q(
                    categoryId__parent__parent__parent__parent=category
                    ) 
            ).exclude(
                sellerId=user.id
            ).select_related(
                'categoryId', 'sellerId'
            ).prefetch_related('postImage').annotate(
                post_id = F('postId'),
                tag=Value('category', output_field=CharField()),
                hasLiked=Exists(models.Like.objects.filter(
                    user_id = user, post_id = OuterRef('postId')
                )),
                hasSaved=Exists(models.Favourite.objects.filter(
                    user_id = user, post_id = OuterRef('postId')
                )),
                rank = reduce_category_influence(user) *
                Case(
                        When(categoryId=category, then= 5),
                        When(categoryId__parent=category, then= 4),
                        When(categoryId__parent__parent=category, then= 3),
                        When(categoryId__parent__parent__parent=category, then= 2),
                        default= 1
                    )
                    / 
                    reduce_seen_posts_influence(user)
                ).order_by(
                '-rank'
            )
    return posts