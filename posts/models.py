from django.db import models
import uuid
from hashlib import sha256

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
    backup_profile_picture = models.ImageField(upload_to="backup/profile_pictures/", null=True, blank=True)
    last_seen = models.DateTimeField(default=timezone.now)
    website = models.TextField(default = "", blank=True)
    REQUIRED_FIELDS = ['phoneNumber']
    created_at = models.DateTimeField(auto_now_add=True)
    coins = models.IntegerField(default = 0, blank = True)



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
    sellerId = models.ForeignKey(to="User", on_delete=models.PROTECT, related_name = 'posts')
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
    
NOTIFICATION_ACTION_FOLLOW = 'F'
NOTIFICATION_ACTIONS = [
    ('L', 'link'),
    ('C', 'call'),
    (NOTIFICATION_ACTION_FOLLOW, 'follow'),
]
GET_NOTIFICATION_IMAGE_FROM = [
    ('U', 'User'),
    ('P', 'Post')
]
class Notification(models.Model):
    date = models.DateField(auto_now_add=True)
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
    backup_image = models.ImageField(upload_to="backup/posts/", null=True, blank=True)
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

PAY_FOR = [
    ('A', 'Ads'),
    ('P', 'Package')
]
PAY_FOR_CHOICES = {
        'A': 'Ads',
        'P': 'Package'
    }

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
    backup_verification_screenshot = models.ImageField(upload_to="backup/transactions/", null=True, blank=True)
    transactionConfirmationCode = models.CharField(max_length=100, null=True, blank =True)
    created_at = models.DateTimeField(auto_now_add=True)
    pay_for = models.CharField(max_length = 1, choices = PAY_FOR)
    coin_amount = models.IntegerField(default=0, blank = True)

    # New fields for blockchain hashing
    previous_hash = models.CharField(max_length=64, null=True, blank=True)
    current_hash = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self):
        return "For: " + str(self.issuedFor) + ", Amount: " + str(self.amount)
    def save(self, *args, **kwargs):
        # Get the previous transaction for this user
        if not self.created_at:
            # Set created_at to the current time if it's not set
            self.created_at = timezone.now()
        if self.pk:
            # Exclude the current transaction from the query when it already exists
            previous_transaction = Transaction.objects.filter(issuedBy=self.issuedBy).exclude(pk=self.pk).order_by('-created_at').first()
        else:
            # For a new transaction (no primary key), query as usual
            previous_transaction = Transaction.objects.filter(issuedBy=self.issuedBy).order_by('-created_at').first()

        if previous_transaction:
            self.previous_hash = previous_transaction.current_hash
        else:
            # If no previous transaction exists, set the previous_hash to an empty string
            self.previous_hash = ""

        # Generate the current hash based on transaction details
        self.current_hash = self.generate_hash()
        print("Transaction hash: ", self.current_hash)
        super().save(*args, **kwargs)

    def generate_hash(self):
        """Generates a hash using transaction details and the previous hash."""
        formatted_created_at = self.created_at.strftime("%b. %d, %Y, %I:%M %p").lower().replace('am', 'a.m.').replace('pm', 'p.m.')
        pay_for_long_version = PAY_FOR_CHOICES.get(self.pay_for, 'Unknown')

        transaction_data = f"{self.issuedBy.username}{self.issuedFor.username}{self.amount}{self.reason}{self.currency}" \
                       f"{self.usedVirtualCurrency}{self.payMethod.name}{self.payVerified}{self.title}" \
                       f"{self.trueForDepositFalseForWithdraw}{formatted_created_at}{pay_for_long_version}{self.previous_hash}"
                       
        print("Transaction data: ", transaction_data)
        return sha256(transaction_data.encode('utf-8')).hexdigest()
class Package(models.Model):
    coin_amount_in_words = models.CharField(max_length=100)
    coin_amount_in_number = models.IntegerField()
    price = models.IntegerField()
    hasDiscount = models.BooleanField()
    originalPriceCurrency = models.CharField(max_length=CURRENCY_LENGTH, choices=CURRENCY_CHOICES, null=True, blank = True)
    discountPriceCurrency = models.CharField(max_length=CURRENCY_LENGTH, choices=CURRENCY_CHOICES, null=True, blank = True)
    original_price_in_words = models.CharField(max_length=100)
    discounted_price_in_words = models.CharField(max_length=100, blank = True, default = "")
    level_of_payment_1_through_4 = models.IntegerField()
    order = models.IntegerField(default=0, blank = True)
    class Meta:
        ordering = ['-order', 'coin_amount_in_number']


class Device(models.Model):
    phone_number = models.CharField(max_length=25)
    android_id = models.CharField(max_length=25)
    verified = models.BooleanField(default=False)
    
from django.db.models.signals import post_save
from .signals import *
post_save.connect(update_pay_verified, sender=Transaction)
post_save.connect(update_number_of_likes, sender = Like)
post_save.connect(associate_category_with_seller, sender = Post)
post_save.connect(send_notification, sender = Notification)