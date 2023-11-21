from django.db import models
import uuid
from django.contrib.auth.models import AbstractUser
from cloudinary.models import CloudinaryField
CURRENCY_CHOICES = [
    ('Br', 'Birr')
]
CURRENCY_LENGTH = 5

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    phone = models.CharField(max_length=255)
    profilePicture = CloudinaryField('image', null=True)
    REQUIRED_FIELDS = ['phone']


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
    categoryId = models.ForeignKey(to="Category", on_delete=models.SET_NULL, null=True, blank = True)
    sellerId = models.ForeignKey(to="User", on_delete=models.PROTECT)
    likes = models.IntegerField(default=0, blank = True)
    engagement = models.DecimalField(decimal_places=2, max_digits=10)
    nextIconAction = models.CharField(max_length=1, choices=NEXT_ICON_ACTION_CHOICES)
    date = models.DateField(auto_now_add=True)
    def __str__(self) -> str:
        return self.title
    class Meta:
        permissions = [
            ("edit_and_add_posts_of_others", "Can edit and add posts of others"),
        ]
class Category(models.Model):
    id = models.UUIDField(primary_key = True, default=uuid.uuid4)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null = True, blank=True)
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

    def __str__(self) -> str:
        return "Username: " + self.user_id.username + ", Post title: " + self.post_id.title

class Like(models.Model):
    user_id = models.ForeignKey(to = "User", on_delete=models.CASCADE, related_name='likes_user', db_index=True)
    post_id = models.ForeignKey(to="Post", on_delete=models.CASCADE, related_name='likes_post', db_index=True)
    def __str__(self) -> str:
        return "Username: " + self.user_id.username + ", Post title: " + self.post_id.title
INTERACTION_ACTORS_OPTIONS = [
    ('Us', 'User'),
    ('Po', 'Post'),
    ('Ca', 'Category')
]
class Image(models.Model):
    post = models.ForeignKey(to="Post", on_delete=models.CASCADE, related_name='postImage', db_index=True)
    image = CloudinaryField('image')
    order = models.PositiveIntegerField(default=1)
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
    category_id = models.ForeignKey(to = Category, on_delete=models.CASCADE)
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
    def __str__(self) -> str:
        return "Follower: " + str(self.user_follower.username) + ", Followed: " + str(self.user_followed.username)
    
class Recommended(models.Model):
    date = models.DateField(auto_now_add=True)
    userId = models.ForeignKey(to=User, on_delete=models.CASCADE)
    postId = models.UUIDField(default=uuid.uuid4)
    tag = models.CharField(max_length = 10)
    rank = models.DecimalField(decimal_places=2, max_digits=10)

class Seen(models.Model):
    user = models.ForeignKey(to = User, on_delete=models.CASCADE)
    post = models.ForeignKey(to = Post, on_delete=models.CASCADE)
    count = models.IntegerField(default = 0)
    def __str__(self) -> str:
        return 'User: ' + str(self.user) + ", Post: " + str(self.post) + ", Count: " + str(self.count)
    