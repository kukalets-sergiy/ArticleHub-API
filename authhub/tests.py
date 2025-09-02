import pytest
from rest_framework.test import APIClient
from bson import ObjectId
from authhub.models import User
from django.contrib.auth.hashers import make_password
from authhub.serializers import UserSerializer, RegisterSerializer, LoginSerializer
import mongoengine
from unittest.mock import patch, mock_open
from authhub.tasks import send_welcome_email


@pytest.fixture(autouse=True)
def clear_users():
    User.objects.delete()


@pytest.fixture
def api():
    return APIClient()


def test_user_creation():
    user = User(email="a@b.com", name="Test", password="pw")
    user.save()
    found = User.objects(email="a@b.com").first()
    assert found is not None
    assert found.name == "Test"
    assert found.password == "pw"


def test_user_unique_email():
    User(email="a@b.com", name="Test1", password="pw1").save()
    with pytest.raises(mongoengine.errors.NotUniqueError):
        User(email="a@b.com", name="Test2", password="pw2").save()


def test_user_required_fields():
    with pytest.raises(mongoengine.errors.ValidationError):
        User(email="missing@b.com").save()  # name and password are required


def test_user_email_format():
    with pytest.raises(mongoengine.errors.ValidationError):
        User(email="not-an-email", name="Test", password="pw").save()


def test_user_update():
    user = User(email="upd@b.com", name="Test", password="pw")
    user.save()
    user.name = "Updated"
    user.save()
    updated = User.objects(email="upd@b.com").first()
    assert updated.name == "Updated"


def test_user_delete():
    user = User(email="del@b.com", name="Test", password="pw")
    user.save()
    user.delete()
    assert User.objects(email="del@b.com").first() is None


def test_user_is_authenticated_property():
    user = User(email="a@b.com", name="Test", password="pw")
    assert user.is_authenticated is True


def test_register_success(api):
    data = {
        "email": "newuser@example.com",
        "name": "Test User",
        "password": "securepass123"
    }
    response = api.post("/api/v1/auth/register/", data, format="json")
    assert response.status_code == 201
    result = response.json()
    assert result["email"] == "newuser@example.com"
    assert result["name"] == "Test User"
    # Verification that the user has been created
    assert User.objects(email="newuser@example.com").count() == 1


def test_register_duplicate_email(api):
    User(email="test@example.com", name="Name", password=make_password("123")).save()
    data = {
        "email": "test@example.com",
        "name": "Another User",
        "password": "otherpass"
    }
    response = api.post("/api/v1/auth/register/", data, format="json")
    assert response.status_code == 400
    assert "error" in response.json()


def test_login_success(api):
    user = User(email="logme@example.com", name="Log Me", password=make_password("pass123"))
    user.save()
    data = {
        "email": "logme@example.com",
        "password": "pass123"
    }
    response = api.post("/api/v1/auth/login/", data, format="json")
    assert response.status_code == 200
    result = response.json()
    assert "access" in result and "refresh" in result


def test_login_wrong_password(api):
    user = User(email="wrong@example.com", name="Wrong Pass", password=make_password("right"))
    user.save()
    data = {
        "email": "wrong@example.com",
        "password": "wrong"
    }
    response = api.post("/api/v1/auth/login/", data, format="json")
    assert response.status_code == 401
    assert "error" in response.json()


def test_profile_authenticated(api):
    # Register and login
    user = User(email="profile@example.com", name="Prof User", password=make_password("pass123"))
    user.save()
    # Get a token
    login_resp = api.post("/api/v1/auth/login/", {"email": "profile@example.com", "password": "pass123"}, format="json")
    token = login_resp.json()["access"]
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    response = api.get("/api/v1/auth/profile/")
    assert response.status_code == 200
    info = response.json()
    assert info["email"] == "profile@example.com"
    assert info["name"] == "Prof User"


def test_profile_unauthenticated(api):
    response = api.get("/api/v1/auth/profile/")
    assert response.status_code == 401 or response.status_code == 403


# ____________________________________serializers tests____________________________________

def test_user_serializer_output():
    user = User(
        id=ObjectId("507f1f77bcf86cd799439011"),
        email="me@example.com",
        name="TestName",
        password="pass123"
    )
    user.save()
    data = UserSerializer(user).data
    assert data["email"] == "me@example.com"
    assert data["name"] == "TestName"
    assert data["id"] == str(user.id)


def test_register_serializer_valid():
    data = {
        "email": "new@example.com",
        "name": "New User",
        "password": "strongpass"
    }
    serializer = RegisterSerializer(data=data)
    assert serializer.is_valid()
    assert serializer.validated_data["email"] == "new@example.com"
    assert serializer.validated_data["name"] == "New User"


def test_register_serializer_invalid_email():
    data = {
        "email": "bademail",
        "name": "User",
        "password": "pass"
    }
    serializer = RegisterSerializer(data=data)
    assert not serializer.is_valid()
    assert "email" in serializer.errors


def test_login_serializer_valid():
    data = {"email": "me@example.com", "password": "pass"}
    serializer = LoginSerializer(data=data)
    assert serializer.is_valid()
    assert serializer.validated_data["email"] == "me@example.com"


def test_login_serializer_missing_field():
    serializer = LoginSerializer(data={"email": "me@example.com"})
    assert not serializer.is_valid()
    assert "password" in serializer.errors


# ____________________________________celery____________________________________

def test_send_welcome_email_creates_log(tmp_path):
    """
    Tests that the Celery task 'send_welcome_email' correctly logs a welcome message and writes the expected entry to
    the log file when a valid user ID is provided.
    Mocks the file writing operation and the logging function to intercept their calls.
    Calls the task with an existing user and checks that the message is written to the file and logged with the correct
    user information.
    """
    user = User(email="celerytest@example.com", name="Celery Test", password="pw")
    user.save()
    # Mock open and logging
    log_path = tmp_path / "welcome_emails.log"
    with patch("builtins.open", mock_open()) as m, \
            patch("logging.info") as log_mock:
        send_welcome_email(str(user.id), user.email, user.name)
        # Verify that logging.info is called
        log_mock.assert_called_once()
        # Checking that open is called for logging
        m.assert_called_with("/tmp/welcome_emails.log", "a")  # Ensure it writes to the correct file
        handle = m()
        expected_msg = f"Welcome email sent to '{user.name}' ({user.email}), user_id={str(user.id)}\n"
        handle.write.assert_called_with(expected_msg)


def test_send_welcome_email_user_not_found(tmp_path):
    """
    Tests that the Celery task 'send_welcome_email' still writes a welcome message to the log file even when the user
    ID provided does not exist in the database.
    Mocks the file writing operation and logging.
    Calls the task with a non-existent user ID and verifies that the log message is written using the provided
    arguments, regardless of user lookup failure.
    """
    # We call a task with a non-existent user_id
    fake_id = str(ObjectId())
    with patch("builtins.open", mock_open()) as m, \
            patch("logging.info") as log_mock:
        send_welcome_email(fake_id, "nouser@example.com", "No User")
        log_mock.assert_called_once()
        m.assert_called_with("/tmp/welcome_emails.log", "a")
        handle = m()
        expected_msg = f"Welcome email sent to 'No User' (nouser@example.com), user_id={fake_id}\n"
        handle.write.assert_called_with(expected_msg)
