from . import models
from django.db.models import Exists, OuterRef, Q, F, Subquery, Count, Prefetch

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
                '-strength'
            )[:20]
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
                '-strength'
            )[:10]
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
                '-engagement'
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
                '-engagement'
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
                '-engagement'
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

def posts_for_IICF(self):
    most_interacted_posts = models.InteractionUserToPost.objects.filter(
            user_id=self.request.user.id
            ).values(
                'post_id', 'strength'
            ).order_by(
                '-strength'
            )[:5]
    return most_interacted_posts

def users_for_IICF(self, most_interacted_posts):
    most_interacted_users = models.InteractionUserToPost.objects.filter(
                post_id__in=Subquery(most_interacted_posts.values('post_id'))
            ).annotate(
                cumulative = models.InteractionUserToPost.objects.filter(
            user_id=self.request.user.id,
            post_id = F('post_id')
            ).values('strength')[:1] * F('strength')
            ).exclude(
                user_id=self.request.user.id
            ).order_by(
                '-cumulative'
            )[:20]
    return most_interacted_users

def users_for_UUCF(self):
    most_interacted_users = models.InteractionUserToUser.objects.filter(
            user_performer=self.request.user.id
            ).values(
                'user_performed_on', 'strength'
            ).order_by(
                '-strength'
            )[:5]
    return most_interacted_users

def categories_for_UCCF(self):
    most_interacted_categories = models.InteractionUserToCategory.objects.filter(
            user_id=self.request.user.id
            ).values(
                'category_id', 'strength'
            ).order_by(
                '-strength'
            )[:5]
    return most_interacted_categories

def sellers_for_UCCF(self, most_interacted_categories):
    most_interacted_users = models.AssociationCategoryToSeller.objects.filter(
                category_id__in=Subquery(most_interacted_categories.values('category_id'))
            ).annotate(
                cumulative = models.InteractionUserToCategory.objects.filter(
                        user_id=self.request.user.id,
                        category_id = F('category_id')
                    ).values('strength')[:1] * F('strength')
            ).exclude(
                seller_id=self.request.user.id
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
                'user_performed_on', 'strength'
            ).order_by(
                '-strength'
            )[:10]
    return most_interacted_following