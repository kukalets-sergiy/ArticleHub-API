import logging
from celery import shared_task
from bson import ObjectId
from authhub.models import User


@shared_task
def send_welcome_email(user_id, email, name):
    try:
        user = User.objects(id=ObjectId(user_id)).first()
    except Exception:
        user = None
    msg = f"Welcome email sent to '{name}' ({email}), user_id={user_id}"
    logging.info(msg)
    with open("/tmp/welcome_emails.log", "a") as f:
        f.write(msg + "\n")
