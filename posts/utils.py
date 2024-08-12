from django.conf import settings
from django.conf import settings
from PIL import Image
import io
import pyotp

def should_allow_free_post(user):
    allow_free_post = settings.ALLOW_FREE_POST
    if allow_free_post is False:
        return False
    elif user.posts.count() >= 3:
        return False
    return True

def compress_image(image, target_size = 10):
    if settings.COMPRESS_IMAGES:
        if not isinstance(image, Image.Image):
            image = Image.open(image)
        buffer = io.BytesIO()
        quality = 95
        while quality>10:
            image.save(buffer, format='JPEG', quality=quality, optimize=True)
            size_kb = buffer.tell() / 1024
            if size_kb <= target_size or quality <= 10:
                break
            quality -=5
        # image = buffer.seek(0)
        image.save(buffer, format='JPEG', quality=quality, optimize=True)

        # image = buffer
    return image

def generate_otp():
    totp = pyotp.TOTP(pyotp.random_base32(), interval=300)  # 5 minutes validity
    return totp.now()

def verify_otp(otp, user_otp):
    return otp == user_otp