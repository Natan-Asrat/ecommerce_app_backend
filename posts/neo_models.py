from neomodel import StructuredRel, StructuredNode, RelationshipFrom, StringProperty, IntegerProperty, RelationshipTo

class Interaction(StructuredRel):
    strength = IntegerProperty(default=1)

class NeoUser(StructuredNode):
    sql_id = StringProperty()
    posts = RelationshipTo('NeoPost', 'POSTED')
    favourites = RelationshipTo('NeoPost', 'FAVOURITED')
    likes = RelationshipTo('NeoPost', 'LIKED')
    interaction_with_posts = RelationshipTo('NeoPost', 'INTERACTED', model=Interaction)
    interaction_with_categories = RelationshipTo('NeoCategory', 'INTERACTED', model=Interaction)
    interaction_with_users = RelationshipTo('NeoUser', 'INTERACTED', model=Interaction)
    follows = RelationshipTo('NeoUser', 'FOLLOWS')
    seen_posts = RelationshipTo('NeoPost', 'SEEN')

class NeoPost(StructuredNode):
    sql_id = StringProperty()
    category = RelationshipTo('NeoCategory', 'IN_CATEGORY')
    
class NeoCategory(StructuredNode):
    sql_id = StringProperty()
    parent = RelationshipTo('NeoCategory', 'PARENT')
    

from django.db.models.signals import post_save
from .signals import *
from . import models 

@receiver(post_save, sender=models.User)
def create_neo4j_user(sender, instance, created, **kwargs):
    if created:
        neo_user = NeoUser(sql_id=str(instance.id)).save()
post_save.connect(create_neo4j_user, sender=models.User)


@receiver(post_save, sender=models.Category)
def create_neo4j_category(sender, instance: models.Category, created, **kwargs):
    if created:
        neo_category = NeoCategory(sql_id=str(instance.id), name=instance.name).save()
        if instance.parent:
            parent_category = NeoCategory.nodes.get_or_none(sql_id=str(instance.parent.id))
            if parent_category is None:
                parent_category = NeoCategory(sql_id=str(instance.parent.id)).save()
            neo_category.parent.connect(parent_category)
post_save.connect(create_neo4j_category, sender = models.Category)

@receiver(post_save, sender=models.Post)
def create_neo4j_post(sender, instance: models.Post, created, **kwargs):
    if created:
        neo_post = NeoPost(sql_id=str(instance.postId)).save()
        if instance.categoryId:
            category = NeoCategory.nodes.get_or_none(sql_id=str(instance.categoryId.id))
            if category is None:
                category = NeoCategory(sql_id=str(instance.categoryId.id)).save()
            neo_post.category.connect(category)
        if instance.sellerId:
            neo_user = NeoUser.nodes.get(sql_id=str(instance.sellerId.id))
            neo_user.posts.connect(neo_post)
post_save.connect(create_neo4j_post, sender = models.Post)

@receiver(post_save, sender=models.Like)
def likes_post(sender, instance:models.Like, created, **kwargs):
    if created:
        neo_user = NeoUser.nodes.get_or_none(sql_id=str(instance.user_id.id))
        neo_post = NeoPost.nodes.get_or_none(sql_id=str(instance.post_id.postId))
            
        if neo_user is None:
            neo_user = NeoUser(sql_id=str(instance.user_id.id)).save()
        if neo_post is None:
            neo_post = NeoPost(sql_id=str(instance.post_id.postId)).save()
        neo_user.likes.connect(neo_post)
post_save.connect(likes_post, sender = models.Like)

@receiver(post_save, sender=models.Favourite)
def favourites_post(sender, instance:models.Favourite, created, **kwargs):
    if created:
        neo_user = NeoUser.nodes.get_or_none(sql_id=str(instance.user_id.id))
        neo_post = NeoPost.nodes.get_or_none(sql_id=str(instance.post_id.postId))
        
        if neo_user is None:
            neo_user = NeoUser(sql_id=str(instance.user_id.id)).save()
        
        if neo_post is None:
            neo_post = NeoPost(sql_id=str(instance.post_id.postId)).save()
        neo_user.favourites.connect(neo_post)
post_save.connect(favourites_post, sender = models.Favourite)

@receiver(post_save, sender=models.InteractionUserToPost)
def interacts_with_post(sender, instance:models.InteractionUserToPost, created, **kwargs):
    neo_user : NeoUser = NeoUser.nodes.get_or_none(sql_id=str(instance.user_id.id))
    neo_post = NeoPost.nodes.get_or_none(sql_id=str(instance.post_id.postId))
    
    if neo_user is None:
        neo_user = NeoUser(sql_id=str(instance.user_id.id)).save()
    if neo_post is None:
        neo_post = NeoPost(sql_id=str(instance.post_id.postId)).save()
    if created:
        neo_user.interaction_with_posts.connect(neo_post)
    else:
        interaction = neo_user.interaction_with_posts.relationship(neo_post)
        if interaction:
            interaction.strength = instance.strength_sum
            interaction.save()
post_save.connect(interacts_with_post, sender = models.InteractionUserToPost)

@receiver(post_save, sender=models.InteractionUserToUser)
def interacts_with_user(sender, instance:models.InteractionUserToUser, created, **kwargs):
    user_performer : NeoUser = NeoUser.nodes.get_or_none(sql_id=str(instance.user_performer.id))
    user_performed_on : NeoUser = NeoUser.nodes.get_or_none(sql_id=str(instance.user_performed_on.id))
    
    if user_performer is None:
        user_performer = NeoUser(sql_id=str(instance.user_performer.id)).save()
    if user_performed_on is None:
        user_performed_on = NeoUser(sql_id=str(instance.user_performed_on.id)).save()

    if created:
        user_performer.interaction_with_users.connect(user_performed_on, {'strength': instance.strength_sum})
    else:
        existing_interaction = user_performer.interaction_with_users.relationship(user_performed_on)
        if existing_interaction:
            existing_interaction.strength = instance.strength_sum
            existing_interaction.save()
post_save.connect(interacts_with_user, sender = models.InteractionUserToUser)

@receiver(post_save, sender=models.InteractionUserToCategory)
def interacts_with_category(sender, instance:models.InteractionUserToCategory, created, **kwargs):
    neo_user: NeoUser = NeoUser.nodes.get_or_none(sql_id=str(instance.user_id.id))
    neo_category : NeoCategory = NeoCategory.nodes.get_or_none(sql_id=str(instance.category_id.id))
    
    if neo_user is None:
        neo_user = NeoUser(sql_id=str(instance.user_id.id)).save()

    if neo_category is None:
        neo_category = NeoCategory(sql_id=str(instance.category_id.id)).save()

    if created:
        neo_user.interaction_with_categories.connect(neo_category, {'strength': instance.strength_sum})
    else:
        interaction = neo_user.interaction_with_categories.relationship(neo_category)
        if interaction:
            interaction.strength = instance.strength_sum
            interaction.save()
post_save.connect(interacts_with_category, sender = models.InteractionUserToCategory)


@receiver(post_save, sender=models.Follower)
def follows_user(sender, instance : models.Follower, created, **kwargs):
    if created:
        neo_user_follower : NeoUser = NeoUser.nodes.get_or_none(sql_id=str(instance.user_follower.id))
        neo_user_followed = NeoUser.nodes.get_or_none(sql_id=str(instance.user_followed.id))
        if neo_user_follower is None:
            neo_user_follower = NeoUser(sql_id=str(instance.user_follower.id)).save()
        if neo_user_followed is None:
            neo_user_followed = NeoUser(sql_id=str(instance.user_followed.id)).save()
        neo_user_follower.follows.connect(neo_user_followed, {'strength': instance.strength})

post_save.connect(follows_user, sender=models.Follower)

@receiver(post_save, sender=models.Seen)
def user_seen_post(sender, instance: models.Seen, created, **kwargs):
    if created:
        neo_user = NeoUser.nodes.get_or_none(sql_id=str(instance.user.id))
        neo_post = NeoPost.nodes.get_or_none(sql_id=str(instance.post.postId))
        if neo_user is None:
            neo_user = NeoUser(sql_id=str(instance.user.id)).save()
        neo_user.seen_posts.connect(neo_post)

post_save.connect(user_seen_post, sender=models.Seen)



def migrate_data_to_neo4j():
    for user in models.User.objects.all():
        neo_user = NeoUser.nodes.get_or_none(sql_id=str(user.id))
        if not neo_user:
            neo_user = NeoUser(sql_id=str(user.id)).save()
    for category in models.Category.objects.all():
        neo_category = NeoCategory.nodes.get_or_none(sql_id=str(category.id))
        if not neo_category:
            neo_category = NeoCategory(sql_id=str(category.id)).save()
    
    for post in Post.objects.all():
        neo_post = NeoPost.nodes.get_or_none(sql_id=str(post.postId))
        if not neo_post:
            neo_post = NeoPost(sql_id=str(post.postId)).save()
        
        if post.categoryId:
            neo_category = NeoCategory.nodes.get_or_none(sql_id=str(post.categoryId.id))
            if neo_category:
                neo_post.category.connect(neo_category)
        
        if post.sellerId:
            neo_user = NeoUser.nodes.get_or_none(sql_id=str(post.sellerId.id))
            if neo_user:
                neo_user.posts.connect(neo_post)
    
    for like in Like.objects.all():
        neo_user : NeoUser = NeoUser.nodes.get_or_none(sql_id=str(like.user_id.id))
        neo_post = NeoPost.nodes.get_or_none(sql_id=str(like.post_id.postId))
        if neo_user and neo_post:
            if not neo_user.likes.is_connected(neo_post):
                neo_user.likes.connect(neo_post)
    
    for favourite in models.Favourite.objects.all():
        neo_user : NeoUser = NeoUser.nodes.get_or_none(sql_id=str(favourite.user_id.id))
        neo_post = NeoPost.nodes.get_or_none(sql_id=str(favourite.post_id.postId))
        if neo_user and neo_post:
            if not neo_user.favourites.is_connected(neo_post):
                neo_user.favourites.connect(neo_post)
    
    for interaction in models.InteractionUserToPost.objects.all():
        neo_user : NeoUser = NeoUser.nodes.get_or_none(sql_id=str(interaction.user_id.id))
        neo_post = NeoPost.nodes.get_or_none(sql_id=str(interaction.post_id.postId))
        if neo_user and neo_post:
            if not neo_user.interaction_with_posts.is_connected(neo_post):
                neo_user.interaction_with_posts.connect(neo_post, {'strength': interaction.strength_sum})
    
    for interaction in models.InteractionUserToUser.objects.all():
        user_performer : NeoUser = NeoUser.nodes.get_or_none(sql_id=str(interaction.user_performer.id))
        user_performed_on = NeoUser.nodes.get_or_none(sql_id=str(interaction.user_performed_on.id))
        if user_performer and user_performed_on:
            if not user_performer.interaction_with_users.is_connected(user_performed_on):
                user_performer.interaction_with_users.connect(user_performed_on, {'strength': interaction.strength_sum})
    
    for interaction in models.InteractionUserToCategory.objects.all():
        neo_user = NeoUser.nodes.get_or_none(sql_id=str(interaction.user_id.id))
        neo_category = NeoCategory.nodes.get_or_none(sql_id=str(interaction.category_id.id))
        if neo_user and neo_category:
            if not neo_user.interaction_with_categories.is_connected(neo_category):
                neo_user.interaction_with_categories.connect(neo_category, {'strength': interaction.strength_sum})
    
    for follower in models.Follower.objects.all():
        neo_user_follower : NeoUser = NeoUser.nodes.get_or_none(sql_id=str(follower.user_follower.id))
        neo_user_followed = NeoUser.nodes.get_or_none(sql_id=str(follower.user_followed.id))
        if neo_user_follower and neo_user_followed:
            if not neo_user_follower.follows.is_connected(neo_user_followed):
                neo_user_follower.follows.connect(neo_user_followed, {'strength': follower.strength})
    
    for seen in models.Seen.objects.all():
        neo_user : NeoUser = NeoUser.nodes.get_or_none(sql_id=str(seen.user.id))
        neo_post = NeoPost.nodes.get_or_none(sql_id=str(seen.post.postId))
        if neo_user and neo_post:
            if not neo_user.seen_posts.is_connected(neo_post):
                neo_user.seen_posts.connect(neo_post)