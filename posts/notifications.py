from firebase_admin.messaging import Message, Notification
from fcm_django.models import FCMDevice

def send_notification_to_user(user, title, body, imageUrl, id):
    message = Message(
        notification=Notification(
            title=title,
            body= body,
            image=imageUrl,
            data = {
                "notificationId": id
            }
        )
    )
    devices = FCMDevice.objects.filter(user = user)
    devices.send_message(message)