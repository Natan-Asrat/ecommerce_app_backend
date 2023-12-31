from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Transaction, Ads, Like

@receiver(post_save, sender = Transaction)
def update_pay_verified(sender, instance, created, **kwargs):
    rejected = instance.rejected
    verified = instance.payVerified
    if rejected is False and verified is True:
        instance.ads.update(payVerified=True)
        print("payment verified: ", instance)
    else:
        instance.ads.update(payVerified=False)
        print("payment not verified: ", instance)


@receiver(post_save, sender = Like)
def update_number_of_likes(sender, instance, created, **kwargs):
    post = instance.post_id
    likesCount = post.likes_post.count()
    post.likes = likesCount
    post.save()