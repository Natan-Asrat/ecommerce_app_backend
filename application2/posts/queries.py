from . import models
from django.db.models import Exists, OuterRef, Q, F,Max, Subquery, Count, Sum, Prefetch, CharField, Value, IntegerField
from itertools import chain
def get_all_posts(request):
    posts = models.Post.objects.all().select_related(
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
        )))[:10]
    return posts

def get_post_ids_with_item_item_collaborative_filtering(user):
    most_interacted_posts = posts_for_IICF(user)
    most_interacted_users = users_for_IICF(user, most_interacted_posts)
    iposts = models.InteractionUserToPost.objects.filter(
                Q(user_id__in=Subquery(most_interacted_users.values('user_id'))) & 
                ~Q(post_id__in=Subquery(most_interacted_posts.values('post_id')))
            ).order_by(
                '-strength_sum'
            )[:20]
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
                rank = F('strength')
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
            )[:10]
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
                rank = F('strength')
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
                rank = models.InteractionUserToCategory.objects.filter(
                        user_id=user.id,
                        category_id = OuterRef('categoryId')
                    ).values('strength_sum')[:1]
            ).values(
                'postId',
                'tag',
                'rank'
            ).order_by(
                '-strength'
            )[:10]
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
            ).values(
                'postId',
                'tag',
                'rank'
            ).order_by(
                '-strength'
            )[:20]
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
                rank = models.InteractionUserToCategory.objects.filter(
                        user_id=user.id,
                        category_id = OuterRef('categoryId')
                    ).values('strength_sum')[:1]
            ).values(
                'postId',
                'tag',
                'rank'
            ).order_by(
                '-strength'
            )[:10]
    return posts
def get_new_post_ids_personalized(user):
    most_interacted_categories = categories_for_UCCF(user)
    new_posts = models.NewPost.objects.filter(
                category_id__in=Subquery(most_interacted_categories.values('category_id'))
            ).values('post_id').exclude(
                seller_id=user.id
            )[:20]
    posts = models.Post.objects.filter(
                postId__in = Subquery(new_posts.values('post_id'))
            ).select_related('categoryId', 'sellerId').annotate(
                post_id = F('postId'),
                tag=Value('new', output_field=CharField()),
                hasLiked=Exists(models.Like.objects.filter(
                    user_id = user, post_id = OuterRef('postId')
                )),
                hasSaved=Exists(models.Favourite.objects.filter(
                    user_id = user, post_id = OuterRef('postId')
                )),
                rank = models.InteractionUserToCategory.objects.filter(
                        user_id= user.id,
                        category_id = OuterRef('categoryId')
                    ).values('strength_sum')[:1]
            ).values(
                'postId',
                'tag',
                'rank'
            ).order_by(
                '-strength'
            )[:20]
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
            )[:5]
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
            )[:20]
    return most_interacted_users

def users_for_UUCF(user):
    most_interacted_users = models.InteractionUserToUser.objects.filter(
            user_performer=user.id
            ).values(
                'user_performed_on', s = F('strength_sum')
            ).order_by(
                '-s'
            )[:5]
    return most_interacted_users

def categories_for_UCCF(user):
    most_interacted_categories = models.InteractionUserToCategory.objects.filter(
            user_id=user.id
            ).values(
                'category_id', s=F('strength_sum')
            ).order_by(
                '-s'
            )[:5]
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
            )[:20]
    return most_interacted_users
def following_for_FollowingBased(user):
    following = models.Follower.objects.filter(
        user_follower = user.id
    ).values(
        'user_followed'
    )
    most_interacted_following = models.InteractionUserToUser.objects.filter(
            user_performer=user.id,
            user_performed_on__in = Subquery(following.values('user_followed'))
            ).values(
                'user_performed_on', s = F('strength_sum')
            ).order_by(
                '-s'
            )[:10]
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
                rank = recommended.filter(postId=OuterRef('postId')).values('sum')[:1]
            ).order_by('-rank')
    return posts
    return posts