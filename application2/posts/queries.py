from . import models
from django.db.models import Exists, OuterRef, Q, F, Subquery, Count, Sum, Prefetch, CharField, Value
from itertools import chain
def get_all_posts(self):
    posts = models.Post.objects.all().select_related('categoryId', 'sellerId').annotate(hasLiked= Exists(models.Like.objects.filter(
            user_id = self.request.user, post_id = OuterRef('postId')
        )), hasSaved= Exists(models.Favourite.objects.filter(
            user_id = self.request.user, post_id = OuterRef('postId')
        )))[:10]
    return posts
def get_posts_with_item_item_collaborative_filtering(self):
    most_interacted_posts = posts_for_IICF(self)
    most_interacted_users = users_for_IICF(self, most_interacted_posts)

    posts = models.InteractionUserToPost.objects.filter(
                Q(user_id__in=Subquery(most_interacted_users.values('user_id'))) & 
                ~Q(post_id__in=Subquery(most_interacted_posts.values('post_id')))
            ).select_related('post_id', 'post_id__categoryId', 'post_id__sellerId').annotate(
                hasLiked=Exists(models.Like.objects.filter(
                    user_id = self.request.user, post_id = OuterRef('post_id')
                )),
                hasSaved=Exists(models.Favourite.objects.filter(
                    user_id = self.request.user, post_id = OuterRef('post_id')
                ))
            ).order_by(
                '-strength_sum'
            )[:20]
    return posts

def get_post_ids_with_item_item_collaborative_filtering(self):
    most_interacted_posts = posts_for_IICF(self)
    most_interacted_users = users_for_IICF(self, most_interacted_posts)

    # posts = models.InteractionUserToPost.objects.filter(
    #             Q(user_id__in=Subquery(most_interacted_users.values('user_id'))) & 
    #             ~Q(post_id__in=Subquery(most_interacted_posts.values('post_id')))
    #         ).select_related('post_id', 'post_id__categoryId', 'post_id__sellerId').annotate(
    #             postId = F('post_id__postId'), title= F('post_id__title'), description= F('post_id__description'), link= F('post_id__link'), price= F('post_id__price'), currency= F('post_id__currency'), hasDiscount= F('post_id__hasDiscount'), discountedPrice= F('post_id__discountedPrice'), discountCurrency= F('post_id__discountCurrency'), categoryId= F('post_id__categoryId'), sellerId= F('post_id__sellerId'), likes= F('post_id__likes'),nextIconAction = F('post_id__nextIconAction') ,  
    #             tag=Value('iicf', output_field=CharField()),
    #             hasLiked=Exists(models.Like.objects.filter(
    #                 user_id = self.request.user, post_id = OuterRef('post_id')
    #             )),
    #             hasSaved=Exists(models.Favourite.objects.filter(
    #                 user_id = self.request.user, post_id = OuterRef('post_id')
    #             )),
    #             strength=F('strength_over_time')
    #         ).values(
    #             'postId',
    #             'title',
    #             'description',
    #             'link',
    #             'price',
    #             'currency',
    #             'hasDiscount',
    #             'discountedPrice',
    #             'discountCurrency',
    #             'categoryId',
    #             'sellerId',
    #             'likes',
    #             'nextIconAction',
    #             'tag',
    #             'hasLiked',
    #             'hasSaved',
    #             'strength'
    #         ).order_by(
    #             '-strength'
    #         )[:20]
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
                    user_id = self.request.user, post_id = OuterRef('postId')
                )),
                hasSaved=Exists(models.Favourite.objects.filter(
                    user_id = self.request.user, post_id = OuterRef('postId')
                )),
                rank = F('strength')
            ).values(
                'postId',
                'title',
                'description',
                'link',
                'price',
                'currency',
                'hasDiscount',
                'discountedPrice',
                'discountCurrency',
                'categoryId',
                'sellerId',
                'likes',
                'nextIconAction',
                'tag',
                'hasLiked',
                'hasSaved',
                'strength',
                'rank'
            )
    return posts
def get_posts_with_user_user_collaborative_filtering(self):
    most_interacted_users = users_for_UUCF(self)
    posts = models.InteractionUserToPost.objects.filter(
                Q(user_id__in=Subquery(most_interacted_users.values('user_performed_on')))
            ).exclude(
                user_id=self.request.user.id
            ).select_related('post_id', 'post_id__categoryId', 'post_id__sellerId').annotate(
                hasLiked=Exists(models.Like.objects.filter(
                    user_id = self.request.user, post_id = OuterRef('post_id')
                )),
                hasSaved=Exists(models.Favourite.objects.filter(
                    user_id = self.request.user, post_id = OuterRef('post_id')
                ))
            ).order_by(
                '-strength_sum'
            )[:10]
    return posts
def get_post_ids_with_user_user_collaborative_filtering(self):
    most_interacted_users = users_for_UUCF(self)
    # posts = models.InteractionUserToPost.objects.filter(
    #             Q(user_id__in=Subquery(most_interacted_users.values('user_performed_on')))
    #         ).exclude(
    #             user_id=self.request.user.id
    #         ).select_related('post_id', 'post_id__categoryId', 'post_id__sellerId').annotate(
    #             postId = F('post_id__postId'), title= F('post_id__title'), description= F('post_id__description'), link= F('post_id__link'), price= F('post_id__price'), currency= F('post_id__currency'), hasDiscount= F('post_id__hasDiscount'), discountedPrice= F('post_id__discountedPrice'), discountCurrency= F('post_id__discountCurrency'), categoryId= F('post_id__categoryId'), sellerId= F('post_id__sellerId'), likes= F('post_id__likes'),nextIconAction = F('post_id__nextIconAction') ,
    #             tag=Value('uucf', output_field=CharField()),
    #             hasLiked=Exists(models.Like.objects.filter(
    #                 user_id = self.request.user, post_id = OuterRef('post_id')
    #             )),
    #             hasSaved=Exists(models.Favourite.objects.filter(
    #                 user_id = self.request.user, post_id = OuterRef('post_id')
    #             ))
    #         ).values(
    #             'postId',
    #             'title',
    #             'description',
    #             'link',
    #             'price',
    #             'currency',
    #             'hasDiscount',
    #             'discountedPrice',
    #             'discountCurrency',
    #             'categoryId',
    #             'sellerId',
    #             'likes',
    #             'nextIconAction',
    #             'tag',
    #             'hasLiked',
    #             'hasSaved',
    #             'strength'
    #         ).order_by(
    #             '-strength'
    #         )[:10]
    iposts = models.InteractionUserToPost.objects.filter(
                Q(user_id__in=Subquery(most_interacted_users.values('user_performed_on')))
            ).exclude(
                user_id=self.request.user.id
            ).order_by(
                '-strength_sum'
            )[:10]
    posts = models.Post.objects.filter(
        Q(postId__in = Subquery(iposts.values('post_id')))
    ).select_related('categoryId', 'sellerId').annotate(
                tag=Value('uucf', output_field=CharField()),
                hasLiked=Exists(models.Like.objects.filter(
                    user_id = self.request.user, post_id = OuterRef('postId')
                )),
                hasSaved=Exists(models.Favourite.objects.filter(
                    user_id = self.request.user, post_id = OuterRef('postId')
                )),
                rank = F('strength')
            ).values(
                'postId',
                'title',
                'description',
                'link',
                'price',
                'currency',
                'hasDiscount',
                'discountedPrice',
                'discountCurrency',
                'categoryId',
                'sellerId',
                'likes',
                'nextIconAction',
                'tag',
                'hasLiked',
                'hasSaved',
                'strength',
                'rank'
            )
    return posts
def get_posts_with_user_category_collaborative_filtering(self):
    most_interacted_categories = categories_for_UCCF(self)
    most_interacted_users = sellers_for_UCCF(self, most_interacted_categories)

    posts = models.Post.objects.filter(
                Q(sellerId__in=Subquery(most_interacted_users.values('seller_id')))
            ).exclude(
                sellerId=self.request.user.id
            ).select_related('categoryId', 'sellerId').annotate(
                hasLiked=Exists(models.Like.objects.filter(
                    user_id = self.request.user, post_id = OuterRef('postId')
                )),
                hasSaved=Exists(models.Favourite.objects.filter(
                    user_id = self.request.user, post_id = OuterRef('postId')
                ))
            ).order_by(
                '-strength'
            )[:10]
    return posts
def get_post_ids_with_user_category_collaborative_filtering(self):
    most_interacted_categories = categories_for_UCCF(self)
    most_interacted_users = sellers_for_UCCF(self, most_interacted_categories)

    posts = models.Post.objects.filter(
                Q(sellerId__in=Subquery(most_interacted_users.values('seller_id')))
            ).exclude(
                sellerId=self.request.user.id
            ).select_related('categoryId', 'sellerId').annotate(
                post_id = F('postId'),
                tag=Value('uccf', output_field=CharField()),
                hasLiked=Exists(models.Like.objects.filter(
                    user_id = self.request.user, post_id = OuterRef('postId')
                )),
                hasSaved=Exists(models.Favourite.objects.filter(
                    user_id = self.request.user, post_id = OuterRef('postId')
                )),
                rank = models.InteractionUserToCategory.objects.filter(
                        user_id=self.request.user.id,
                        category_id = OuterRef('categoryId')
                    ).values('strength_sum')[:1]
            ).values(
                'postId',
                'title',
                'description',
                'link',
                'price',
                'currency',
                'hasDiscount',
                'discountedPrice',
                'discountCurrency',
                'categoryId',
                'sellerId',
                'likes',
                'nextIconAction',
                'tag',
                'hasLiked',
                'hasSaved',
                'strength',
                'rank'
            ).order_by(
                '-strength'
            )[:10]
    return posts
def get_posts_by_following(self):
    most_interacted_following = following_for_FollowingBased(self)
    posts = models.Post.objects.filter(
                Q(sellerId__in=Subquery(most_interacted_following.values('user_performed_on')))
            ).exclude(
                sellerId=self.request.user.id
            ).select_related('categoryId', 'sellerId').annotate(
                hasLiked=Exists(models.Like.objects.filter(
                    user_id = self.request.user, post_id = OuterRef('postId')
                )),
                hasSaved=Exists(models.Favourite.objects.filter(
                    user_id = self.request.user, post_id = OuterRef('postId')
                ))
            ).order_by(
                '-strength'
            )[:20]
    return posts

def get_post_ids_by_following(self):
    most_interacted_following = following_for_FollowingBased(self)
    posts = models.Post.objects.filter(
                Q(sellerId__in=Subquery(most_interacted_following.values('user_performed_on')))
            ).exclude(
                sellerId=self.request.user.id
            ).select_related('categoryId', 'sellerId').annotate(   
                post_id = F('postId'),
                tag=Value('following', output_field=CharField()),
                hasLiked=Exists(models.Like.objects.filter(
                    user_id = self.request.user, post_id = OuterRef('postId')
                )),
                hasSaved=Exists(models.Favourite.objects.filter(
                    user_id = self.request.user, post_id = OuterRef('postId')
                )),
                rank = models.InteractionUserToUser.objects.filter(
                        user_performer=self.request.user.id,
                        user_performed_on__in = OuterRef('sellerId')
                    ).values('strength_sum')[:1]
            ).values(
                'postId',
                'title',
                'description',
                'link',
                'price',
                'currency',
                'hasDiscount',
                'discountedPrice',
                'discountCurrency',
                'categoryId',
                'sellerId',
                'likes',
                'nextIconAction',
                'tag',
                'hasLiked',
                'hasSaved',
                'strength',
                'rank'
            ).order_by(
                '-strength'
            )[:20]
    return posts

def get_posts_by_category_personalized(self):
    most_interacted_categories = categories_for_UCCF(self)
    posts = models.Post.objects.filter(
                Q(categoryId__in=Subquery(most_interacted_categories.values('category_id')))
            ).exclude(
                sellerId=self.request.user.id
            ).select_related('categoryId', 'sellerId').annotate(
                hasLiked=Exists(models.Like.objects.filter(
                    user_id = self.request.user, post_id = OuterRef('postId')
                )),
                hasSaved=Exists(models.Favourite.objects.filter(
                    user_id = self.request.user, post_id = OuterRef('postId')
                ))
            ).order_by(
                '-strength'
            )[:10]
    return posts
def get_post_ids_by_category_personalized(self):
    most_interacted_categories = categories_for_UCCF(self)
    posts = models.Post.objects.filter(
                Q(categoryId__in=Subquery(most_interacted_categories.values('category_id')))
            ).exclude(
                sellerId=self.request.user.id
            ).select_related('categoryId', 'sellerId').annotate(
                post_id = F('postId'),
                tag=Value('category', output_field=CharField()),
                hasLiked=Exists(models.Like.objects.filter(
                    user_id = self.request.user, post_id = OuterRef('postId')
                )),
                hasSaved=Exists(models.Favourite.objects.filter(
                    user_id = self.request.user, post_id = OuterRef('postId')
                )),
                rank = models.InteractionUserToCategory.objects.filter(
                        user_id=self.request.user.id,
                        category_id = OuterRef('categoryId')
                    ).values('strength_sum')[:1]
            ).values(
                'postId',
                'title',
                'description',
                'link',
                'price',
                'currency',
                'hasDiscount',
                'discountedPrice',
                'discountCurrency',
                'categoryId',
                'sellerId',
                'likes',
                'nextIconAction',
                'tag',
                'hasLiked',
                'hasSaved',
                'strength',
                'rank'
            ).order_by(
                '-strength'
            )[:10]
    return posts
def get_new_posts_personalized(self):
    most_interacted_categories = categories_for_UCCF(self)
    new_posts = models.NewPost.objects.filter(
                category_id__in=Subquery(most_interacted_categories.values('category_id'))
            ).exclude(
                seller_id=self.request.user.id
            )[:20]
    posts = models.Post.objects.filter(
        postId__in = Subquery(new_posts.values('post_id'))
    ).select_related('categoryId', 'sellerId').annotate(
                hasLiked=Exists(models.Like.objects.filter(
                    user_id = self.request.user, post_id = OuterRef('postId')
                )),
                hasSaved=Exists(models.Favourite.objects.filter(
                    user_id = self.request.user, post_id = OuterRef('postId')
                ))
            )
    # posts = NewPost.objects.all()
    return posts
def get_new_post_ids_personalized(self):
    most_interacted_categories = categories_for_UCCF(self)
    new_posts = models.NewPost.objects.filter(
                category_id__in=Subquery(most_interacted_categories.values('category_id'))
            ).values('post_id').exclude(
                seller_id=self.request.user.id
            )[:20]
    posts = models.Post.objects.filter(
                postId__in = Subquery(new_posts.values('post_id'))
            ).select_related('categoryId', 'sellerId').annotate(
                post_id = F('postId'),
                tag=Value('new', output_field=CharField()),
                hasLiked=Exists(models.Like.objects.filter(
                    user_id = self.request.user, post_id = OuterRef('postId')
                )),
                hasSaved=Exists(models.Favourite.objects.filter(
                    user_id = self.request.user, post_id = OuterRef('postId')
                )),
                rank = models.InteractionUserToCategory.objects.filter(
                        user_id=self.request.user.id,
                        category_id = OuterRef('categoryId')
                    ).values('strength_sum')[:1]
            ).values(
                'postId',
                'title',
                'description',
                'link',
                'price',
                'currency',
                'hasDiscount',
                'discountedPrice',
                'discountCurrency',
                'categoryId',
                'sellerId',
                'likes',
                'nextIconAction',
                'tag',
                'hasLiked',
                'hasSaved',
                'strength',
                'rank'
            ).order_by(
                '-strength'
            )[:20]
    # posts = NewPost.objects.all()
    return posts

def combined_queryset(self):
    iicf = get_post_ids_with_item_item_collaborative_filtering(self)
    uucf = get_post_ids_with_user_user_collaborative_filtering(self)
    uccf = get_post_ids_with_user_category_collaborative_filtering(self)
    categoryBased = get_post_ids_by_category_personalized(self)
    followingBased = get_post_ids_by_following(self)
    newPost = get_new_post_ids_personalized(self)
    combined = iicf.union(uucf, uccf, categoryBased, followingBased, newPost).order_by('-rank')
    return combined
def get_recommendations(self):
    queryset = combined_queryset(self)
    return queryset


def posts_for_IICF(self):
    most_interacted_posts = models.InteractionUserToPost.objects.filter(
            user_id=self.request.user.id
            ).values(
                'post_id', 'strength_sum'
            ).order_by(
                '-strength_sum'
            )[:5]
    return most_interacted_posts

def users_for_IICF(self, most_interacted_posts):
    most_interacted_users = models.InteractionUserToPost.objects.filter(
                post_id__in=Subquery(most_interacted_posts.values('post_id'))
            ).annotate(
                cumulative = models.InteractionUserToPost.objects.filter(
            user_id=self.request.user.id,
            post_id = F('post_id')
            ).values('strength_sum')[:1] * F('strength_sum')
            ).exclude(
                user_id=self.request.user.id
            ).values(
                'post_id', 'cumulative'
            ).order_by(
                '-cumulative'
            )[:20]
    return most_interacted_users

def users_for_UUCF(self):
    most_interacted_users = models.InteractionUserToUser.objects.filter(
            user_performer=self.request.user.id
            ).values(
                'user_performed_on', s = F('strength_sum')
            ).order_by(
                '-s'
            )[:5]
    return most_interacted_users

def categories_for_UCCF(self):
    most_interacted_categories = models.InteractionUserToCategory.objects.filter(
            user_id=self.request.user.id
            ).values(
                'category_id', s=F('strength_sum')
            ).order_by(
                '-s'
            )[:5]
    return most_interacted_categories

def sellers_for_UCCF(self, most_interacted_categories):
    most_interacted_users = models.AssociationCategoryToSeller.objects.filter(
                category_id__in=Subquery(most_interacted_categories.values('category_id'))
            ).annotate(
                cumulative = models.InteractionUserToCategory.objects.filter(
                        user_id=self.request.user.id,
                        category_id = F('category_id')
                    ).values('strength_sum')[:1] * F('strength')
            ).exclude(
                seller_id=self.request.user.id
            ).values(
                'seller_id', 'cumulative'
            ).order_by(
                '-cumulative'
            )[:20]
    return most_interacted_users
def following_for_FollowingBased(self):
    following = models.Follower.objects.filter(
        user_follower = self.request.user.id
    ).values(
        'user_followed'
    )
    most_interacted_following = models.InteractionUserToUser.objects.filter(
            user_performer=self.request.user.id,
            user_performed_on__in = Subquery(following.values('user_followed'))
            ).values(
                'user_performed_on', s = F('strength_sum')
            ).order_by(
                '-s'
            )[:10]
    return most_interacted_following