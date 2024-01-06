from django.db.models.signals import post_save
from . import serializers
from django.dispatch import receiver
from .models import Transaction, Ads, Like, Post, AssociationCategoryToSeller, Package

@receiver(post_save, sender = Transaction)
def update_pay_verified(sender, instance, created, **kwargs):
    rejected = instance.rejected
    verified = instance.payVerified
    pay_for = instance.pay_for


    if rejected is False and verified is True:
        if pay_for == 'A':
            instance.ads.update(payVerified=True)
            print("payment verified: ", instance)
        elif pay_for == 'P':
            for_user = instance.issuedFor
            for_user.coins += instance.coin_amount
            for_user.save()
    else:
        if pay_for == 'A':
            instance.ads.update(payVerified=False)
            print("payment not verified: ", instance)


@receiver(post_save, sender = Like)
def update_number_of_likes(sender, instance, created, **kwargs):
    post = instance.post_id
    likesCount = post.likes_post.count()
    post.likes = likesCount
    post.save()


@receiver(post_save, sender = Post)
def associate_category_with_seller(sender, instance, created, **kwargs):
    if created:
        category = instance.categoryId
        seller = instance.sellerId
        association, created_association = AssociationCategoryToSeller.objects.get_or_create(category_id = category, seller_id = seller)
        association.strength += 1
        association.save()

@receiver(post_save, sender = Package)
def strike_through_coin_discount(sender, instance, created, **kwargs):
    if instance.hasDiscount:
        instance.discounted_price_in_words = serializers.strike(instance.discounted_price_in_words)
        instance.save()