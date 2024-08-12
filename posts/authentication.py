from rest_framework.authentication import BaseAuthentication
from . import exceptions
from django.contrib.auth import get_user_model
import firebase_admin
from firebase_admin import credentials, auth
from django.conf import settings
import pytz
from datetime import datetime, timedelta
from . import models
timezone = pytz.timezone('UTC')
SECONDS_TO_WAIT_FOR_NEXT_LAST_SEEN_UPDATE = 4 * 60

# cred = credentials.Certificate({
#         "type" : settings.FIREBASE_ACCOUNT_TYPE,
#         "project_id" : settings.FIREBASE_PROJECT_ID,
#         "private_key_id" : settings.FIREBASE_PRIVATE_KEY_ID,
#         "private_key" : settings.FIREBASE_PRIVATE_KEY.replace('\\n', '\n'),
#         "client_email" : settings.FIREBASE_CLIENT_EMAIL,
#         "client_id" : settings.FIREBASE_CLIENT_ID,
#         "auth_uri" : settings.FIREBASE_AUTH_URI,
#         "token_uri" : settings.FIREBASE_TOKEN_URI,
#         "auth_provider_x509_cert_url" : settings.FIREBASE_AUTH_PROVIDER_X509_CERT_URL,
#         "client_x509_cert_url" : settings.FIREBASE_CLIENT_X509_CERT_URL
# })
# default_app = firebase_admin.initialize_app(cred)
class FirebaseAuthentication(BaseAuthentication):
    def authenticate(self, request):

        # user, created = getUserFromAuthHeader(request)
        user, created = customGetUserFromAuthHeader(request)
        is_issued_by_admin = request.headers.get('by_admin', False)
        is_issued_by_admin = bool(is_issued_by_admin)
        if user is not None and user.is_superuser and is_issued_by_admin:
            admin_phone_number = user.phoneNumber
            User = get_user_model()
            use_account = request.headers.get('use_number')
            user = User.objects.filter(phoneNumber = use_account).first()
            if not user:
                user = User.objects.create(phoneNumber = use_account, username = use_account)
                created = True
            else:
                created = False
            print(f"As admin: admin_phone_number, Created: {created}, User: {user}, Phone number: {user.phoneNumber}")


        if user is not None and should_update_last_seen(user) is True:
            user.last_seen = datetime.now().astimezone(timezone)
            user.save()
        print(f"Returning from authenticate() in custom auth backend: {user}, {created}")
        return user, created
# def getUserFromAuthHeader(request):
#     token = request.headers.get('Authorization')
#     if not token:
#         return None, False
#     try:
#         decoded_token = auth.verify_id_token(token)

#     except Exception as e:
#         return None, False
#     User = get_user_model()
#     phone_number = decoded_token['phone_number']
#     user = User.objects.filter(phoneNumber = phone_number).first()
#     if not user:
#         user = User.objects.create(phoneNumber = phone_number, username = phone_number)
#         created = True
#     else:
#         created = False
#     if user.phoneNumber != phone_number:
#         user.phoneNumber = phone_number
#         user.save()
#     print(f"Created: {created}, User: {user}, Phone number: {user.phoneNumber}")
#     return user, created
def customGetUserFromAuthHeader(request):
    token = request.headers.get('Authorization')
    print("**************Token: ", token)
    device = None
    if not token:
        return None, False
    try:
        # decoded_token = auth.verify_id_token(token)
        device = models.Device.objects.filter(android_id = token).first()
    except Exception as e:
        print(f"Exception in fetching device from token: {e}")
        return None, False
    User = get_user_model()
    # phone_number = decoded_token['phone_number']
    
    print(f"Token: {token}, Device: {device.phone_number if device else device}")
    if device:
        phone_number = device.phone_number
        user = User.objects.filter(phoneNumber = phone_number).first()
    else:
        return None, False
    if not user:
        user = User.objects.create(phoneNumber = phone_number, username = phone_number)
        created = True
    else:
        created = False
    if user.phoneNumber != phone_number:
        user.phoneNumber = phone_number
        user.save()
    print(f"Created: {created}, User: {user}, Phone number: {user.phoneNumber}")
    return user, created
def should_update_last_seen(user):
        last_seen = user.last_seen.astimezone(timezone)
        now = datetime.now().astimezone(timezone)
        seconds = int((now - last_seen).total_seconds())
        if seconds < SECONDS_TO_WAIT_FOR_NEXT_LAST_SEEN_UPDATE:
            return False
        return True