from django.db import models
import uuid
from django.contrib.auth.models import AbstractUser
CURRENCY_CHOICES = [
    ('Br', 'Birr')
]
CURRENCY_LENGTH = 5

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    phone = models.CharField(max_length=255)
    REQUIRED_FIELDS = ['phone']


NEXT_ICON_ACTION_CHOICES = [
    ('D', 'detail'),
    ('L', 'link'),
    ('P', 'pay')
]
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
    strength = models.DecimalField(decimal_places=2, max_digits=10)
    nextIconAction = models.CharField(max_length=1, choices=NEXT_ICON_ACTION_CHOICES)

    def __str__(self) -> str:
        return self.title

class Category(models.Model):
    id = models.UUIDField(primary_key = True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    def __str__(self) -> str:
        return self.name

NOTIFICATION_ACTIONS = [
    ('L', 'link'),
    ('C', 'call'),
    ('F', 'follow'),
]
class Notification(models.Model):
    date = models.DateField()
    message = models.CharField(max_length=255)
    image = models.TextField(default="", blank=True)
    link = models.TextField(default="", blank=True)
    sellerId = models.ForeignKey(to = "User", on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    buttonPressed = models.BooleanField(default=False)
    seen = models.BooleanField(default=False)
    action = models.CharField(max_length=1, choices=NOTIFICATION_ACTIONS)
    def __str__(self) -> str:
        return "To: " + self.sellerId.username + ", Message: " + self.message

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
class Interaction(models.Model):
    action_performer_id = models.UUIDField()
    action_performed_on_id = models.UUIDField()
    last_updated_time_of_strength = models.DateField(auto_now=True)
    label_performer = models.CharField(max_length=2, choices=INTERACTION_ACTORS_OPTIONS)
    label_performed_on = models.CharField(max_length=2, choices=INTERACTION_ACTORS_OPTIONS)
    strength = models.IntegerField(default=1)
    strength_latest = models.DecimalField(decimal_places=2, max_digits=10)
    def __str__(self) -> str:
        return "User: " + str(User.objects.get(id = self.action_performer_id)) + ", Post: " + Post.objects.get(postId = self.action_performed_on_id).title

class InteractionUserToPost(models.Model):
    user_id = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='interaction_with_posts')
    post_id = models.ForeignKey(to = Post, on_delete=models.CASCADE)
    strength_sum = models.IntegerField(default = 1)
    last_updated_time_of_strength = models.DateField(auto_now=True)
    strength_over_time = models.DecimalField(decimal_places=2, max_digits=10)
    def __str__(self) -> str:
        return "User: " + str(self.user_id.username) + ", Post: " + self.post_id.title
class InteractionUserToUser(models.Model):
    user_performer = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='friends')
    user_performed_on = models.ForeignKey(to = User, on_delete=models.CASCADE, related_name='fans')
    strength_sum = models.IntegerField(default = 1)
    last_updated_time_of_strength = models.DateField(auto_now=True)
    strength_over_time = models.DecimalField(decimal_places=2, max_digits=10)
    def __str__(self) -> str:
        return "User: " + str(self.user_performer.username) + ", User2: " + str(self.user_performed_on.username)
class InteractionUserToCategory(models.Model):
    user_id = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='interaction_with_category')
    category_id = models.ForeignKey(to = Category, on_delete=models.CASCADE)
    strength_sum = models.IntegerField(default = 1)
    last_updated_time_of_strength = models.DateField(auto_now=True)
    strength_over_time = models.DecimalField(decimal_places=2, max_digits=10)
    def __str__(self) -> str:
        return "User: " + str(self.user_id.username) + ", Category: " + self.category_id.name
class AssociationCategoryToSeller(models.Model):
    category_id = models.ForeignKey(to = Category, on_delete=models.CASCADE)
    seller_id = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='association_to_category')
    strength = models.IntegerField(default = 1)
    last_updated_time_of_strength = models.DateField(auto_now=True)
    strength_over_time = models.DecimalField(decimal_places=2, max_digits=10)
    def __str__(self) -> str:
        return "Category: " + str(self.category_id.name) + ", Seller: " + str(self.seller_id.username)

class Follower(models.Model):
    user_follower = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='following')
    user_followed = models.ForeignKey(to = User, on_delete=models.CASCADE, related_name='followers')
    strength = models.IntegerField(default = 1)
    last_updated_time_of_strength = models.DateField(auto_now=True)
    strength_over_time = models.DecimalField(decimal_places=2, max_digits=10)
    def __str__(self) -> str:
        return "Follower: " + str(self.user_follower.username) + ", Followed: " + str(self.user_followed.username)
    
class NewPost(models.Model):
    seller_id = models.ForeignKey(to=User, on_delete=models.CASCADE)
    category_id = models.ForeignKey(to = Category, on_delete=models.CASCADE)
    post_id = models.ForeignKey(to = Post, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return "Seller: " + str(self.seller_id.username) + ", New Post: " + self.post_id.title + ", Category: " + str(self.category_id.name)

class Recommended(models.Model):
    date = models.DateField(auto_now_add=True)
    userId = models.ForeignKey(to=User, on_delete=models.CASCADE)
    postId = models.UUIDField(default=uuid.uuid4)
    tag = models.CharField(max_length = 10)
    rank = models.DecimalField(decimal_places=2, max_digits=10)
