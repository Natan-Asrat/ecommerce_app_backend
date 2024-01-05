from django.db import models
import uuid
from django.contrib.auth.models import AbstractUser
from cloudinary.models import CloudinaryField
from django.db.models import Count
from django.utils import timezone
CURRENCY_CHOICES = [
    ('Br', 'Birr')
]
CURRENCY_LENGTH = 5

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    phoneNumber = models.CharField(max_length=25)
    profilePicture = CloudinaryField('image', null=True)
    last_seen = models.DateTimeField(default=timezone.now)
    website = models.TextField(default = "", blank=True)
    REQUIRED_FIELDS = ['phoneNumber']
    created_at = models.DateTimeField(auto_now_add=True)



NEXT_ICON_ACTION_CHOICES = [
    ('D', 'detail'),
    ('L', 'link'),
    ('P', 'pay')
]

HOW_LONG_A_POST_STAYS_NEW_IN_DAYS = 7
class Post(models.Model):
    postId = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.CharField(max_length=255)
    description = models.TextField(default = "", blank=True)
    link = models.TextField(default = "", blank=True)
    price = models.PositiveIntegerField()
    currency = models.CharField(max_length=CURRENCY_LENGTH, choices=CURRENCY_CHOICES)
    hasDiscount = models.BooleanField(default=False)
    discountedPrice = models.PositiveIntegerField(blank=True, null=True)
    discountCurrency = models.CharField(max_length=CURRENCY_LENGTH, choices=CURRENCY_CHOICES, null=True, blank = True)
    categoryId = models.ForeignKey(related_name='posts_in_category', to="Category", on_delete=models.SET_NULL, null=True, blank = True)
    sellerId = models.ForeignKey(to="User", on_delete=models.PROTECT, related_name = 'seller')
    likes = models.IntegerField(default=0, blank = True)
    engagement = models.DecimalField(decimal_places=2, max_digits=10, default=0, blank = True)
    nextIconAction = models.CharField(max_length=1, choices=NEXT_ICON_ACTION_CHOICES)
    date = models.DateTimeField(auto_now_add=True)
    def __str__(self) -> str:
        return self.title
    class Meta:
        permissions = [
            ("edit_and_add_posts_of_others", "Can edit and add posts of others"),
        ]
        ordering = ['-date']
class Category(models.Model):
    id = models.UUIDField(primary_key = True, default=uuid.uuid4)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null = True, blank=True, related_name='children')
    name = models.CharField(max_length=255)
    def __str__(self) -> str:
        return self.name
    

NOTIFICATION_ACTIONS = [
    ('L', 'link'),
    ('C', 'call'),
    ('F', 'follow'),
]
GET_NOTIFICATION_IMAGE_FROM = [
    ('U', 'User'),
    ('P', 'Post')
]
class Notification(models.Model):
    # date = models.DateField(auto_now_add=True)
    date = models.DateField()
    message = models.CharField(max_length=255)
    notifyUser = models.ForeignKey(to = "User", on_delete=models.CASCADE, related_name='notify_to')
    profileId = models.ForeignKey(to = "User", on_delete=models.CASCADE, blank=True, null = True, related_name='profile_seller')
    postId = models.ForeignKey(to = "Post", on_delete=models.CASCADE, blank=True, null = True)
    image_from = models.CharField(max_length=1, choices = GET_NOTIFICATION_IMAGE_FROM)
    buttonPressed = models.BooleanField(default=False)
    seen = models.BooleanField(default=False)
    action = models.CharField(max_length=1, choices=NOTIFICATION_ACTIONS)
    def __str__(self) -> str:
        return "To: " + self.notifyUser.username + ", Message: " + self.message
    class Meta:
        ordering = ['-date']

class Favourite(models.Model):
    user_id = models.ForeignKey(to = "User", on_delete=models.CASCADE, db_index=True)
    post_id = models.ForeignKey(to="Post", on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    def __str__(self) -> str:
        return "Username: " + self.user_id.username + ", Post title: " + self.post_id.title
    class Meta:
        ordering = ['-date']
class Like(models.Model):
    user_id = models.ForeignKey(to = "User", on_delete=models.CASCADE, related_name='likes_user', db_index=True)
    post_id = models.ForeignKey(to="Post", on_delete=models.CASCADE, related_name='likes_post', db_index=True)
    date = models.DateTimeField(auto_now_add=True)
    def __str__(self) -> str:
        return "Username: " + self.user_id.username + ", Post title: " + self.post_id.title
    class Meta:
        ordering = ['-date']
INTERACTION_ACTORS_OPTIONS = [
    ('Us', 'User'),
    ('Po', 'Post'),
    ('Ca', 'Category')
]
class Image(models.Model):
    post = models.ForeignKey(to="Post", on_delete=models.CASCADE, related_name='postImage', db_index=True)
    image = CloudinaryField('image')
    order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return "Image of Post: " + str(self.post)
    class Meta:
        ordering = ['order']
class InteractionUserToPost(models.Model):
    user_id = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='interaction_with_posts')
    post_id = models.ForeignKey(to = Post, on_delete=models.CASCADE)
    strength_sum = models.IntegerField(default = 1)
    def __str__(self) -> str:
        return "User: " + str(self.user_id.username) + ", Post: " + self.post_id.title
class InteractionUserToUser(models.Model):
    user_performer = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='friends')
    user_performed_on = models.ForeignKey(to = User, on_delete=models.CASCADE, related_name='fans')
    strength_sum = models.IntegerField(default = 1)
    def __str__(self) -> str:
        return "User: " + str(self.user_performer.username) + ", User2: " + str(self.user_performed_on.username)
class InteractionUserToCategory(models.Model):
    user_id = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='interaction_with_category')
    category_id = models.ForeignKey(to = Category, on_delete=models.CASCADE, related_name='interaction')
    strength_sum = models.IntegerField(default = 1)
    def __str__(self) -> str:
        return "User: " + str(self.user_id.username) + ", Category: " + self.category_id.name
class AssociationCategoryToSeller(models.Model):
    category_id = models.ForeignKey(to = Category, on_delete=models.CASCADE)
    seller_id = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='association_to_category')
    strength = models.IntegerField(default = 1)
    def __str__(self) -> str:
        return "Category: " + str(self.category_id.name) + ", Seller: " + str(self.seller_id.username)


HOW_MUCH_FOLLOWER_STRENGTH_SHOULD_REDUCE_INFLUENCE_ON_NEW_POSTS = 50
class Follower(models.Model):
    user_follower = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='following')
    user_followed = models.ForeignKey(to = User, on_delete=models.CASCADE, related_name='followers')
    strength = models.IntegerField(default = 1)
    date = models.DateTimeField(auto_now_add=True)
    def __str__(self) -> str:
        return "Follower: " + str(self.user_follower.username) + ", Followed: " + str(self.user_followed.username)
    class Meta:
        ordering = ['-date']
class Recommended(models.Model):
    date = models.DateField(auto_now_add=True)
    userId = models.ForeignKey(to=User, on_delete=models.CASCADE)
    postId = models.UUIDField(default=uuid.uuid4)
    tag = models.CharField(max_length = 10)
    rank = models.DecimalField(decimal_places=2, max_digits=10)

class Seen(models.Model):
    user = models.ForeignKey(to = User, on_delete=models.CASCADE)
    post = models.ForeignKey(to = Post, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default = 1)
    date = models.DateTimeField(auto_now_add=True)
    def __str__(self) -> str:
        return 'User: ' + str(self.user) + ", Post: " + str(self.post) + ", Count: " + str(self.count)
    class Meta:
        ordering = ['-date']

class Ads(models.Model):
    postId = models.ForeignKey(to = Post, on_delete=models.CASCADE)
    categoryId = models.ForeignKey(to = Category, on_delete=models.CASCADE)
    strength = models.IntegerField(default = 1)
    payVerified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    transaction = models.ForeignKey(to="Transaction", on_delete = models.DO_NOTHING, null = True, blank = True, related_name='ads')
    def __str__(self) -> str:
        return "Post: " + str(self.postId) + ", Category: " + str(self.categoryId) + ", Amount: " + str(self.strength)
    
    class Meta:
        ordering = ['-strength']

class PayMethod(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    image = CloudinaryField('image')
    isVirtualCurrency = models.BooleanField(default=False)
    hasQRCode = models.BooleanField(default=False)
    hasLink = models.BooleanField(default=False)
    hasAccountNumber = models.BooleanField(default=True)
    accountNumber = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
PAY_TYPE = [
    ('Q', 'QR CODE'),
    ('A', 'Account Number'),
    ('L', 'Link'),
    ('C', 'Coin')
]
class Transaction(models.Model):
    issuedBy = models.ForeignKey(to="User", on_delete=models.DO_NOTHING, related_name = 'byUser')
    issuedFor = models.ForeignKey(to="User", on_delete=models.DO_NOTHING, related_name = 'forUser')
    amount = models.IntegerField()
    reason = models.CharField(max_length=100, null=True, blank =True)
    currency = models.CharField(max_length=CURRENCY_LENGTH, choices=CURRENCY_CHOICES, null=True, blank = True)
    usedVirtualCurrency = models.BooleanField(default=False, blank=True, null=True)
    payMethod = models.ForeignKey(to="PayMethod", on_delete=models.DO_NOTHING)
    payVerified = models.BooleanField(default=False, blank=True, null=True)
    title = models.CharField(max_length=100)
    trueForDepositFalseForWithdraw = models.BooleanField(default=True)
    rejected = models.BooleanField(default=False, blank=True, null=True)
    verificationScreenshot = CloudinaryField('image', null=True, blank = True)
    transactionConfirmationCode = models.CharField(max_length=100, null=True, blank =True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return "For: " + str(self.issuedFor) + ", Amount: " + str(self.amount)
from django.db.models.signals import post_save
from .signals import *
post_save.connect(update_pay_verified, sender=Transaction)
post_save.connect(update_number_of_likes, sender = Like)
post_save.connect(associate_category_with_seller, sender = Post)