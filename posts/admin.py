from django.contrib import admin
from .models import *
from django.contrib.auth.models import Group, Permission
# staff_group, created = Group.objects.get_or_create(name='Edit and add posts using other accounts')
# permission = Permission.objects.get(codename='edit_and_add_posts_of_others')
# # staff_group.permissions.add(permission)
# staff_group.permissions.remove(permission)
# Register your models here.

admin.site.register(User)
admin.site.register(Post)
admin.site.register(Category)
admin.site.register(Favourite)
admin.site.register(Like)
admin.site.register(Notification)
admin.site.register(InteractionUserToPost)
admin.site.register(InteractionUserToCategory)
admin.site.register(InteractionUserToUser)
admin.site.register(AssociationCategoryToSeller)
admin.site.register(Follower)
admin.site.register(Recommended)
admin.site.register(Seen)
admin.site.register(Image)
admin.site.register(Ads)
admin.site.register(Transaction)
admin.site.register(PayMethod)
admin.site.register(Package)
