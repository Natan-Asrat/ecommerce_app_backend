from django.conf import settings

def should_allow_free_post(user):
    allow_free_post = settings.ALLOW_FREE_POST
    if allow_free_post is False:
        return False
    elif user.post_set.count() >= 3:
        return False
    return True