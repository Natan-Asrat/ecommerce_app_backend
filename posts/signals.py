from django.db.models.signals import post_save
from django.dispatch import receiver
from fcm_django.models import FCMDevice
from .models import Transaction, Ads, Like, Post, AssociationCategoryToSeller, Package, Notification, GET_NOTIFICATION_IMAGE_FROM
from django.conf import settings
from .utils import should_allow_free_post

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
        if should_allow_free_post(seller) is False:
            seller.coins -= 1
            seller.save()


from .notifications import send_notification_to_user

@receiver(post_save, sender = Notification)
def send_notification(sender, instance: Notification, created, **kwargs):
    title = instance.message
    user = instance.notifyUser
    date = str(instance.date)
    img_from = instance.image_from
    imgUrl = ""
    if img_from is GET_NOTIFICATION_IMAGE_FROM[0]:
        profile = instance.profileId
        if profile is not None:
            img = profile.profilePicture
            if img is not None:
                imgUrl = img.url
    elif img_from is GET_NOTIFICATION_IMAGE_FROM[1]:
        post = instance.postId
        if post is not None:
            img = post.postImage.first()
            if img is not None:
                imgUrl = img.image.url
    send_notification_to_user(user, title, date, imgUrl, id)
