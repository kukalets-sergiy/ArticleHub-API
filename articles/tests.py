import pytest
from articles.models import Article
from articles.tasks import analyze_article
from authhub.models import User
from bson import ObjectId
from django.contrib.auth.hashers import make_password
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def clear_articles():
    Article.objects.delete()


@pytest.fixture(autouse=True)
def clear_users():
    User.objects.delete()


@pytest.fixture
def user():
    u = User(email="testuser@example.com", name="Tester", password=make_password("password123"))
    u.save()
    return u


@pytest.fixture
def auth_client(user):
    client = APIClient()
    # Login, get access token
    login_resp = client.post("/api/v1/auth/login/", {
        "email": "testuser@example.com",
        "password": "password123"
    }, format="json")
    token = login_resp.json()["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def test_create_article(auth_client):
    data = {
        "title": "API Test Article",
        "content": "API content",
        "tags": ["api", "pytest"]
    }
    resp = auth_client.post("/api/v1/articles/", data, format="json")
    assert resp.status_code == 201
    result = resp.json()
    assert result["title"] == "API Test Article"
    assert "pytest" in result["tags"]


def test_get_article_list(auth_client):
    Article(title="A", content="x", tags=["foo"], author=ObjectId("507f1f77bcf86cd799439011")).save()
    Article(title="B", content="y", tags=["bar"], author=ObjectId("507f1f77bcf86cd799439011")).save()
    resp = auth_client.get("/api/v1/articles/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2


def test_article_search(auth_client):
    Article(title="Python tips", content="API test", tags=["python"],
            author=ObjectId("507f1f77bcf86cd799439011")).save()
    resp = auth_client.get("/api/v1/articles/?search=python")
    assert resp.status_code == 200
    data = resp.json()
    assert any("Python tips" in a["title"] for a in data)


def test_article_tag_filter(auth_client):
    Article(title="Tagged Article", content="xxx", tags=["special"], author=ObjectId("507f1f77bcf86cd799439011")).save()
    resp = auth_client.get("/api/v1/articles/?tag=special")
    assert resp.status_code == 200
    data = resp.json()
    assert any("special" in a["tags"] for a in data)


def test_update_article(auth_client, user):
    article = Article(title="Old", content="Old content", tags=["old"], author=user.id)
    article.save()
    data = {"title": "New title", "content": "New content", "tags": ["new"]}
    resp = auth_client.put(f"/api/v1/articles/{article.id}/", data, format="json")
    assert resp.status_code == 200
    result = resp.json()
    assert result["title"] == "New title"
    assert result["content"] == "New content"


def test_delete_article(auth_client, user):
    article = Article(title="Delete", content="del", tags=[], author=user.id)
    article.save()
    resp = auth_client.delete(f"/api/v1/articles/{article.id}/")
    assert resp.status_code == 204
    assert not Article.objects(id=article.id).first()


def test_forbidden_update(auth_client):
    # Creating an article with another author
    other = User(email="other@example.com", name="Other", password=make_password("pass456"))
    other.save()
    article = Article(title="Foreign", content="xxx", tags=["f"], author=other.id)
    article.save()
    data = {"title": "hack", "content": "hack"}
    resp = auth_client.put(f"/api/v1/articles/{article.id}/", data, format="json")
    assert resp.status_code == 403


def test_not_found_article(auth_client):
    resp = auth_client.get("/api/v1/articles/507f1f77bcf86cd799439012/")
    assert resp.status_code == 404


# ____________________________________celery____________________________________

def test_analyze_article_updates_analysis_field():
    """
    Checks that the analyze_article Celery task correctly counts words and unique tags in an Article,
    and saves the analysis to the article's 'analysis' field.
    Creates an Article with sample content and tags, calls the analyze_article task synchronously,
    and asserts that both the returned and persisted analysis contain correct word and tag counts.
    """
    article = Article(
        title="Test",
        content="one two three four five",
        tags=["foo", "bar", "foo"],
        author=ObjectId("507f1f77bcf86cd799439011")
    )
    article.save()

    analysis = analyze_article(str(article.id))
    assert analysis is not None
    assert analysis["word_count"] == 5
    assert analysis["unique_tags"] == 2

    updated_article = Article.objects(id=article.id).first()
    assert updated_article.analysis["word_count"] == 5
    assert updated_article.analysis["unique_tags"] == 2


def test_analyze_article_returns_none_for_missing_article():
    """
    Checks that the analyze_article Celery task returns None if there is no Article with the given ID.
    Calls the analyze_article task with a fake, non-existent article ID and asserts that the result is None.
    """
    fake_id = str(ObjectId())
    result = analyze_article(fake_id)
    assert result is None
