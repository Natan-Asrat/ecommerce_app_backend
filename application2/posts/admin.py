from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(User)
admin.site.register(Post)
admin.site.register(Category)
admin.site.register(Favourite)
admin.site.register(Like)
admin.site.register(Notification)
admin.site.register(Interaction)
admin.site.register(InteractionUserToPost)
admin.site.register(InteractionUserToCategory)
admin.site.register(InteractionUserToUser)
admin.site.register(AssociationCategoryToSeller)
admin.site.register(NewPost)
admin.site.register(Follower)